import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class AccountSummary(BaseModel):
    id: uuid.UUID
    external_id: str
    name: str
    plan: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    accounts: list[AccountSummary]
    permissions: list[str]


class LoginResponse(BaseModel):
    user: UserResponse
    expires_at: datetime


class ChatCreateRequest(BaseModel):
    mode: Literal["customer", "internal"]
    title: str | None = Field(default=None, max_length=255)
    account_external_id: str | None = Field(default=None, max_length=64)


class ChatSummary(BaseModel):
    id: uuid.UUID
    mode: str
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    client_request_id: str | None = Field(default=None, max_length=128)


class CitationResponse(BaseModel):
    id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    chunk_id: uuid.UUID | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    label: str
    reliability_class: str
    page_start: int | None = None
    page_end: int | None = None
    supports_claim: str | None = None


class ToolEventResponse(BaseModel):
    id: uuid.UUID | None = None
    tool_name: str
    status: str
    input_summary: str
    output_summary: str | None = None
    duration_ms: int | None = None


class PendingActionResponse(BaseModel):
    id: uuid.UUID
    action_type: str
    display_summary: str
    status: str
    expires_at: datetime
    proposed_payload: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    confidence: str | None
    run_status: str
    created_at: datetime
    citations: list[CitationResponse] = Field(default_factory=list)
    tool_events: list[ToolEventResponse] = Field(default_factory=list)
    pending_action: PendingActionResponse | None = None


class ChatDetailResponse(BaseModel):
    chat: ChatSummary
    messages: list[MessageResponse]


class MessageRunResponse(BaseModel):
    user_message_id: uuid.UUID
    assistant_message: MessageResponse
    snapshot_at: datetime


class ActionCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class EscalationResponse(BaseModel):
    id: uuid.UUID
    external_reference: str
    account_id: uuid.UUID
    reason: str
    summary: str
    priority: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionResultResponse(BaseModel):
    action: PendingActionResponse
    escalation: EscalationResponse | None = None


class SourceChunkResponse(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    title: str
    document_type: str
    version: str | None
    status: str
    authority_class: str
    page_start: int
    page_end: int
    section_heading: str | None
    excerpt: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str = "parcelpilot-backend"


class ReadyResponse(BaseModel):
    ready: bool
    database: bool
    pgvector: bool
    active_snapshot: bool
    llm_configured: bool
    details: dict[str, str] = Field(default_factory=dict)


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False
    field_errors: list[dict[str, Any]] | None = None
