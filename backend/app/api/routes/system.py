from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.schemas.api import HealthResponse, ReadyResponse


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadyResponse:
    database = pgvector = active_snapshot = False
    details: dict[str, str] = {}
    try:
        await db.execute(text("SELECT 1"))
        database = True
        pgvector = bool(
            (
                await db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"))
            ).scalar()
        )
        active_snapshot = bool(
            (
                await db.execute(text("SELECT EXISTS(SELECT 1 FROM dataset_snapshots WHERE is_active=true)"))
            ).scalar()
        )
    except Exception as exc:
        details["database"] = type(exc).__name__
    configured = settings.openrouter_ready
    is_ready = database and pgvector and active_snapshot and configured
    if not configured:
        details["llm"] = "OPENROUTER_API_KEY is not configured"
    return ReadyResponse(
        ready=is_ready,
        database=database,
        pgvector=pgvector,
        active_snapshot=active_snapshot,
        llm_configured=configured,
        details=details,
    )

