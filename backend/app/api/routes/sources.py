import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_auth_context
from app.db import get_db
from app.db.repositories import SupportRepository
from app.schemas.api import SourceChunkResponse


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/{document_id}/chunks/{chunk_id}", response_model=SourceChunkResponse)
async def get_source_chunk(
    document_id: uuid.UUID,
    chunk_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceChunkResponse:
    row = await SupportRepository(db, auth).document_chunk_by_id(document_id, chunk_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Source not found")
    chunk, document = row
    return SourceChunkResponse(
        document_id=document.id,
        chunk_id=chunk.id,
        title=document.title,
        document_type=document.document_type,
        version=document.version,
        status=document.status,
        authority_class=document.authority_class,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        section_heading=chunk.section_heading,
        excerpt=chunk.content,
    )

