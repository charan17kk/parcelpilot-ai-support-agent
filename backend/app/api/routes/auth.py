from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, AuthService, get_auth_context
from app.config import Settings, get_settings
from app.db import get_db
from app.db.models import UserAccountScope
from app.db.repositories import SupportRepository
from app.observability import write_audit_event
from app.schemas.api import AccountSummary, LoginRequest, LoginResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["authentication"])


def permissions_for_role(role: str) -> list[str]:
    common = ["chat:read", "chat:write", "source:read", "escalation:create"]
    if role in {"support_agent", "operations_manager"}:
        common.extend(["internal:read", "account:cross_read", "ticket:read"])
    if role == "operations_manager":
        common.extend(["insights:read", "ticket:update"])
    return common


async def user_response(db: AsyncSession, auth: AuthContext) -> UserResponse:
    repository = SupportRepository(db, auth)
    accounts = await repository.list_accounts()
    return UserResponse(
        id=auth.user_id,
        email=auth.email,
        display_name=auth.display_name,
        role=auth.role,
        accounts=[
            AccountSummary(id=account.id, external_id=account.external_id, name=account.name, plan=account.plan)
            for account in accounts
        ],
        permissions=permissions_for_role(auth.role),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    result = await AuthService(settings).login(db, payload.email, payload.password)
    if result is None:
        await write_audit_event(
            db,
            request_id=request.state.request_id,
            event_type="auth.login",
            outcome="denied",
            metadata={"reason": "invalid_credentials"},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user, token, expires_at = result
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        expires=expires_at,
        path="/",
    )
    auth = AuthContext(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        permitted_account_ids=tuple(
            (
                await db.execute(
                    select(UserAccountScope.account_id).where(UserAccountScope.user_id == user.id)
                )
            ).scalars().all()
        ),
        request_id=request.state.request_id,
    )
    await write_audit_event(
        db,
        request_id=request.state.request_id,
        actor_user_id=user.id,
        event_type="auth.login",
        resource_type="user",
        resource_id=user.id,
        outcome="success",
    )
    await db.commit()
    return LoginResponse(user=await user_response(db, auth), expires_at=expires_at)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await AuthService(settings).logout(db, token)
    response.delete_cookie(settings.session_cookie_name, path="/")


@router.get("/me", response_model=UserResponse)
async def me(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    return await user_response(db, auth)
