import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.db import get_db
from app.schemas.api import ActionCancelRequest, ActionResultResponse, PendingActionResponse
from app.services.actions import ActionService


router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/{action_id}/confirm", response_model=ActionResultResponse)
async def confirm_action(
    action_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ActionResultResponse:
    action, escalation = await ActionService(db, auth, settings).confirm(action_id)
    return ActionResultResponse(
        action=PendingActionResponse.model_validate(action),
        escalation=escalation,
    )


@router.post("/{action_id}/cancel", response_model=PendingActionResponse)
async def cancel_action(
    action_id: uuid.UUID,
    payload: ActionCancelRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PendingActionResponse:
    action = await ActionService(db, auth, settings).cancel(action_id, payload.reason)
    return PendingActionResponse.model_validate(action)
