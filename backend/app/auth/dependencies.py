import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.config import Settings, get_settings
from app.db import get_db
from app.db.models import AuthSession, User, UserAccountScope


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    email: str
    display_name: str
    role: str
    permitted_account_ids: tuple[uuid.UUID, ...]
    request_id: str

    @property
    def is_internal(self) -> bool:
        return self.role in {"support_agent", "operations_manager"}


async def get_auth_context(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    session_token: Annotated[str | None, Cookie(alias="parcelpilot_session")] = None,
) -> AuthContext:
    token = request.cookies.get(settings.session_cookie_name) or session_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    token_hash = AuthService(settings).hash_token(token)
    result = await db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.token_hash == token_hash,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        )
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    session, user = row

    await db.execute(
        update(AuthSession).where(AuthSession.id == session.id).values(last_seen_at=datetime.now(UTC))
    )

    scope_result = await db.execute(
        select(UserAccountScope.account_id).where(UserAccountScope.user_id == user.id)
    )
    account_ids = tuple(scope_result.scalars().all())
    return AuthContext(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        permitted_account_ids=account_ids,
        request_id=getattr(request.state, "request_id", "unknown"),
    )


async def require_internal(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> AuthContext:
    if not auth.is_internal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal access required")
    return auth

