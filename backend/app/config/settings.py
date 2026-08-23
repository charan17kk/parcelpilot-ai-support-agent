from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://parcelpilot:parcelpilot_local@localhost:5432/parcelpilot"

    session_cookie_name: str = "parcelpilot_session"
    session_ttl_minutes: int = 480
    session_cookie_secure: bool = False
    session_token_pepper: str = "local-development-pepper-change-me"

    llm_provider: Literal["openrouter"] = "openrouter"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 1
    agent_max_llm_calls: int = 6
    agent_max_tool_steps: int = 6

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    document_top_k: int = 6
    rag_chunk_tokens: int = 750
    rag_chunk_overlap_tokens: int = 100

    data_pack_dir: Path = Path("../data/raw")
    data_manifest_path: Path = Path("../data/manifest.yml")
    action_confirmation_ttl_minutes: int = 15

    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    rate_limit_login: str = "10/minute"
    rate_limit_chat: str = "20/minute"
    demo_user_password: str = "ParcelPilotDemo!"

    @field_validator("session_token_pepper")
    @classmethod
    def validate_session_pepper(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("SESSION_TOKEN_PEPPER must not be empty")
        return value

    @field_validator("agent_max_llm_calls", "agent_max_tool_steps")
    @classmethod
    def validate_positive_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Agent limits must be positive")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def openrouter_ready(self) -> bool:
        return bool(self.openrouter_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
