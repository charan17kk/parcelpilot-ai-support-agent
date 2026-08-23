from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext
from app.config import Settings
from app.db.models import (
    ChatMessage,
    ChatSession,
    MessageCitation,
    PendingAction,
    ToolRun,
)
from app.db.repositories import SupportRepository


class ChatService:
    def __init__(self, db: AsyncSession, auth: AuthContext, settings: Settings):
        self.db = db
        self.auth = auth
        self.settings = settings
        self.repository = SupportRepository(db, auth)

    async def create(
        self,
        *,
        mode: str,
        title: str | None,
        account_external_id: str | None,
    ) -> ChatSession:
        if not self.auth.is_internal and mode != "customer":
            raise HTTPException(status_code=403, detail="Customer users require customer chat mode")
        account = None
        if account_external_id:
            account = await self.repository.account_by_external_id(account_external_id)
            if account is None:
                raise HTTPException(status_code=404, detail="Account not found")
        elif not self.auth.is_internal:
            accounts = await self.repository.list_accounts()
            if len(accounts) != 1:
                raise HTTPException(status_code=409, detail="Customer account context is unavailable")
            account = accounts[0]

        chat = ChatSession(
            owner_user_id=self.auth.user_id,
            mode=mode,
            title=title or "New support conversation",
            account_context_id=account.id if account else None,
        )
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def list(self) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.owner_user_id == self.auth.user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, chat_id: uuid.UUID) -> ChatSession:
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.id == chat_id,
                ChatSession.owner_user_id == self.auth.user_id,
            )
        )
        chat = result.scalar_one_or_none()
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat

    async def run_message(self, chat_id: uuid.UUID, content: str) -> tuple[ChatMessage, ChatMessage, object]:
        # Import the AI stack only when a message is run; this keeps health checks and
        # authentication fast on Docker Desktop despite the sizeable provider SDK.
        from app.agent import AgentRunner

        chat = await self.get(chat_id)
        snapshot = await self.repository.active_snapshot()
        user_message = ChatMessage(
            chat_session_id=chat.id,
            role="user",
            content=content,
            snapshot_id=snapshot.id,
            run_status="completed",
        )
        self.db.add(user_message)
        await self.db.flush()

        runner = AgentRunner(
            self.db,
            self.auth,
            self.settings,
            chat_session_id=chat.id,
            account_context_id=chat.account_context_id,
        )
        try:
            result = await runner.run(content)
            assistant_message = ChatMessage(
                chat_session_id=chat.id,
                role="assistant",
                content=result.content,
                confidence=result.confidence,
                snapshot_id=snapshot.id,
                run_status="awaiting_confirmation" if result.pending_action else "completed",
            )
            self.db.add(assistant_message)
            await self.db.flush()
            for citation in result.citations:
                self.db.add(
                    MessageCitation(
                        message_id=assistant_message.id,
                        document_chunk_id=citation.get("chunk_id"),
                        entity_type=citation.get("entity_type"),
                        entity_id=citation.get("entity_id"),
                        citation_label=citation["label"],
                        reliability_class=citation["reliability_class"],
                        supports_claim=citation.get("supports_claim"),
                    )
                )
            for event in result.tool_events:
                now = datetime.now(UTC)
                self.db.add(
                    ToolRun(
                        chat_session_id=chat.id,
                        message_id=assistant_message.id,
                        tool_name=event["tool_name"],
                        safe_input_summary=event["input_summary"],
                        safe_output_summary=event.get("output_summary"),
                        status=event["status"],
                        started_at=now,
                        completed_at=now,
                        duration_ms=event.get("duration_ms"),
                        request_id=self.auth.request_id,
                    )
                )
            chat.updated_at = datetime.now(UTC)
            if chat.title == "New support conversation":
                chat.title = content[:80]
            await self.db.commit()
            await self.db.refresh(user_message)
            await self.db.refresh(assistant_message)
            return user_message, assistant_message, result
        except Exception:
            assistant_message = ChatMessage(
                chat_session_id=chat.id,
                role="assistant",
                content=(
                    "I could not complete this request safely. Please retry shortly or contact "
                    "ParcelPilot support if the issue is urgent."
                ),
                confidence="unresolved",
                snapshot_id=snapshot.id,
                run_status="failed",
                error_code="AGENT_UNAVAILABLE",
            )
            self.db.add(assistant_message)
            await self.db.commit()
            raise

    async def messages(self, chat_id: uuid.UUID) -> list[ChatMessage]:
        await self.get(chat_id)
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == chat_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def pending_action_for_message(self, chat_id: uuid.UUID) -> PendingAction | None:
        result = await self.db.execute(
            select(PendingAction)
            .where(
                PendingAction.chat_session_id == chat_id,
                PendingAction.owner_user_id == self.auth.user_id,
                PendingAction.status == "pending",
            )
            .order_by(PendingAction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
