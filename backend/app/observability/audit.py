import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent


async def write_audit_event(
    db: AsyncSession,
    *,
    request_id: str,
    event_type: str,
    outcome: str,
    actor_user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            request_id=request_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            safe_metadata=metadata or {},
        )
    )

