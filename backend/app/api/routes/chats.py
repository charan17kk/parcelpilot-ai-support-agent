import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_auth_context
from app.config import Settings, get_settings
from app.db import get_db
from app.db.models import Document, DocumentChunk, MessageCitation, PendingAction, ToolRun
from app.schemas.api import (
    ChatCreateRequest,
    ChatDetailResponse,
    ChatSummary,
    CitationResponse,
    MessageRequest,
    MessageResponse,
    MessageRunResponse,
    PendingActionResponse,
    ToolEventResponse,
)
from app.services.chats import ChatService


router = APIRouter(prefix="/chats", tags=["chats"])


async def serialize_message(
    db: AsyncSession,
    message: object,
    pending_action: PendingAction | None = None,
) -> MessageResponse:
    citation_rows = (
        await db.execute(
            select(MessageCitation, DocumentChunk, Document)
            .outerjoin(DocumentChunk, DocumentChunk.id == MessageCitation.document_chunk_id)
            .outerjoin(Document, Document.id == DocumentChunk.document_id)
            .where(MessageCitation.message_id == message.id)
        )
    ).all()
    citations = [
        CitationResponse(
            id=citation.id,
            document_id=document.id if document else None,
            chunk_id=chunk.id if chunk else None,
            entity_type=citation.entity_type,
            entity_id=citation.entity_id,
            label=citation.citation_label,
            reliability_class=citation.reliability_class,
            page_start=chunk.page_start if chunk else None,
            page_end=chunk.page_end if chunk else None,
            supports_claim=citation.supports_claim,
        )
        for citation, chunk, document in citation_rows
    ]
    tool_rows = (
        await db.execute(
            select(ToolRun).where(ToolRun.message_id == message.id).order_by(ToolRun.started_at)
        )
    ).scalars().all()
    tools = [
        ToolEventResponse(
            id=item.id,
            tool_name=item.tool_name,
            status=item.status,
            input_summary=item.safe_input_summary,
            output_summary=item.safe_output_summary,
            duration_ms=item.duration_ms,
        )
        for item in tool_rows
    ]
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        confidence=message.confidence,
        run_status=message.run_status,
        created_at=message.created_at,
        citations=citations,
        tool_events=tools,
        pending_action=(PendingActionResponse.model_validate(pending_action) if pending_action else None),
    )


@router.post("", response_model=ChatSummary)
async def create_chat(
    payload: ChatCreateRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatSummary:
    chat = await ChatService(db, auth, settings).create(
        mode=payload.mode,
        title=payload.title,
        account_external_id=payload.account_external_id,
    )
    return ChatSummary.model_validate(chat)


@router.get("", response_model=list[ChatSummary])
async def list_chats(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ChatSummary]:
    chats = await ChatService(db, auth, settings).list()
    return [ChatSummary.model_validate(chat) for chat in chats]


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatDetailResponse:
    service = ChatService(db, auth, settings)
    chat = await service.get(chat_id)
    messages = await service.messages(chat_id)
    pending = await service.pending_action_for_message(chat_id)
    serialized = [
        await serialize_message(db, message, pending if message.run_status == "awaiting_confirmation" else None)
        for message in messages
    ]
    return ChatDetailResponse(chat=ChatSummary.model_validate(chat), messages=serialized)


@router.post("/{chat_id}/messages", response_model=MessageRunResponse)
async def send_message(
    chat_id: uuid.UUID,
    payload: MessageRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MessageRunResponse:
    service = ChatService(db, auth, settings)
    try:
        user_message, assistant_message, agent_result = await service.run_message(chat_id, payload.content)
    except RuntimeError as exc:
        if "OpenRouter is not configured" in str(exc):
            raise HTTPException(status_code=503, detail="The AI provider is not configured") from exc
        raise HTTPException(status_code=503, detail="The AI provider is temporarily unavailable") from exc
    except Exception as exc:
        text = str(exc).lower()
        if "429" in text or "rate limit" in text:
            raise HTTPException(status_code=429, detail="The free AI endpoint rate limit has been reached") from exc
        raise HTTPException(status_code=503, detail="The support agent is temporarily unavailable") from exc
    snapshot = await service.repository.active_snapshot()
    return MessageRunResponse(
        user_message_id=user_message.id,
        assistant_message=await serialize_message(db, assistant_message, agent_result.pending_action),
        snapshot_at=snapshot.snapshot_at,
    )

