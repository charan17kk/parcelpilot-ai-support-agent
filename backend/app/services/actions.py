import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext
from app.config import Settings
from app.db.models import Escalation, PendingAction
from app.db.repositories import SupportRepository
from app.observability import write_audit_event


class ActionService:
    def __init__(self, db: AsyncSession, auth: AuthContext, settings: Settings):
        self.db = db
        self.auth = auth
        self.settings = settings
        self.repository = SupportRepository(db, auth)

    async def prepare_escalation(
        self,
        *,
        chat_session_id: uuid.UUID,
        reason: str,
        summary: str,
        priority: str,
        account_external_id: str | None = None,
        related_order_external_id: str | None = None,
        related_ticket_external_id: str | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> PendingAction:
        accounts = await self.repository.list_accounts()
        if account_external_id:
            account = next((item for item in accounts if item.external_id == account_external_id), None)
        elif len(accounts) == 1:
            account = accounts[0]
        else:
            account = None
        if account is None:
            raise ValueError("A single authorized account must be identified before escalation")

        related_order_id = None
        related_ticket_id = None
        target_entity_type = None
        target_entity_id = None
        if related_order_external_id:
            order_row = await self.repository.order_by_external_id(related_order_external_id)
            if order_row is None or order_row[1].id != account.id:
                raise ValueError("Related order is not available in the authorized account")
            related_order_id = order_row[0].id
            target_entity_type = "order"
            target_entity_id = related_order_id
        if related_ticket_external_id:
            ticket_row = await self.repository.ticket_by_external_id(related_ticket_external_id)
            if ticket_row is None or ticket_row[1].id != account.id:
                raise ValueError("Related ticket is not available in the authorized account")
            related_ticket_id = ticket_row[0].id
            target_entity_type = "ticket"
            target_entity_id = related_ticket_id

        priority = priority.lower()
        if priority not in {"low", "normal", "high", "urgent"}:
            raise ValueError("Unsupported escalation priority")
        payload = {
            "reason": reason.strip(),
            "summary": summary.strip(),
            "priority": priority,
            "account_external_id": account.external_id,
            "related_order_id": str(related_order_id) if related_order_id else None,
            "related_ticket_id": str(related_ticket_id) if related_ticket_id else None,
            "evidence": evidence or [],
        }
        signature = hashlib.sha256(
            f"{self.auth.user_id}:{chat_session_id}:{payload}".encode()
        ).hexdigest()
        result = await self.db.execute(
            select(PendingAction).where(
                PendingAction.idempotency_key == signature,
                PendingAction.status == "pending",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        action = PendingAction(
            owner_user_id=self.auth.user_id,
            chat_session_id=chat_session_id,
            action_type="create_escalation",
            target_account_id=account.id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            proposed_payload=payload,
            display_summary=f"Create a {priority} escalation for {account.name}: {summary.strip()}",
            status="pending",
            expires_at=datetime.now(UTC)
            + timedelta(minutes=self.settings.action_confirmation_ttl_minutes),
            idempotency_key=signature,
        )
        self.db.add(action)
        await self.db.flush()
        await write_audit_event(
            self.db,
            request_id=self.auth.request_id,
            actor_user_id=self.auth.user_id,
            event_type="action.proposed",
            resource_type="pending_action",
            resource_id=action.id,
            outcome="pending",
            metadata={"action_type": action.action_type, "account": account.external_id},
        )
        return action

    async def confirm(self, action_id: uuid.UUID) -> tuple[PendingAction, Escalation]:
        result = await self.db.execute(
            select(PendingAction).where(PendingAction.id == action_id).with_for_update()
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
        if action.owner_user_id != self.auth.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action not permitted")
        if action.status == "executed" and action.result_entity_id:
            escalation = await self.db.get(Escalation, action.result_entity_id)
            if escalation is None:
                raise HTTPException(status_code=409, detail="Executed action result is unavailable")
            return action, escalation
        if action.status != "pending":
            raise HTTPException(status_code=409, detail=f"Action is {action.status}")
        if action.expires_at <= datetime.now(UTC):
            action.status = "expired"
            await self.db.commit()
            raise HTTPException(status_code=409, detail="Action has expired")
        if not self.auth.is_internal and action.target_account_id not in self.auth.permitted_account_ids:
            raise HTTPException(status_code=403, detail="Action not permitted")

        payload = action.proposed_payload
        reference = f"ESC-{datetime.now(UTC):%Y%m%d}-{str(action.id)[:8].upper()}"
        escalation = Escalation(
            external_reference=reference,
            account_id=action.target_account_id,
            created_by_user_id=self.auth.user_id,
            source_chat_session_id=action.chat_session_id,
            related_order_id=uuid.UUID(payload["related_order_id"]) if payload.get("related_order_id") else None,
            related_ticket_id=uuid.UUID(payload["related_ticket_id"]) if payload.get("related_ticket_id") else None,
            reason=payload["reason"],
            summary=payload["summary"],
            priority=payload["priority"],
            evidence_summary=payload.get("evidence", []),
        )
        self.db.add(escalation)
        await self.db.flush()
        action.status = "executed"
        action.confirmed_at = datetime.now(UTC)
        action.executed_at = datetime.now(UTC)
        action.result_entity_type = "escalation"
        action.result_entity_id = escalation.id
        await write_audit_event(
            self.db,
            request_id=self.auth.request_id,
            actor_user_id=self.auth.user_id,
            event_type="action.executed",
            resource_type="escalation",
            resource_id=escalation.id,
            outcome="success",
            metadata={"action_id": str(action.id), "reference": reference},
        )
        await self.db.commit()
        await self.db.refresh(action)
        await self.db.refresh(escalation)
        return action, escalation

    async def cancel(self, action_id: uuid.UUID, reason: str | None = None) -> PendingAction:
        result = await self.db.execute(
            select(PendingAction).where(PendingAction.id == action_id).with_for_update()
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise HTTPException(status_code=404, detail="Action not found")
        if action.owner_user_id != self.auth.user_id:
            raise HTTPException(status_code=403, detail="Action not permitted")
        if action.status != "pending":
            raise HTTPException(status_code=409, detail=f"Action is {action.status}")
        action.status = "cancelled"
        await write_audit_event(
            self.db,
            request_id=self.auth.request_id,
            actor_user_id=self.auth.user_id,
            event_type="action.cancelled",
            resource_type="pending_action",
            resource_id=action.id,
            outcome="success",
            metadata={"reason": reason} if reason else {},
        )
        await self.db.commit()
        await self.db.refresh(action)
        return action

