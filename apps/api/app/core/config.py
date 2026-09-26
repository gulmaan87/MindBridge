"""Application Configuration Module.

Reads environment variables using Pydantic Settings, providing
fail-safe defaults and runtime validation without logging secret values.
(Engineering Rules §4, Backend Project Structure §5.1)
"""

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings and environment variables."""

    # Core Application
    app_name: str = Field(default="MindBridge Cognitive Platform", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")

    # Server Networking & CORS
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ORIGINS"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [i.strip().strip("'\"") for i in v.strip("[]").split(",") if i.strip()]
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # PostgreSQL Database
    database_url: str = Field(
        default="postgresql+asyncpg://mindbridge_user:mindbridge_dev_password@localhost:5432/mindbridge_db",
        alias="DATABASE_URL"
    )
    sync_database_url: str = Field(
        default="postgresql+psycopg2://mindbridge_user:mindbridge_dev_password@localhost:5432/mindbridge_db",
        alias="SYNC_DATABASE_URL"
    )

    # Redis Cache & Ephemeral State
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Security & JWT Tokens (Engineering Rules §6)
    jwt_secret_key: str = Field(
        default="dev_insecure_jwt_secret_change_me_in_production_min_32_bytes",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # AI Gateway
    ai_gateway_provider: str = Field(default="mock", alias="AI_GATEWAY_PROVIDER")
    ai_gateway_api_key: str = Field(default="dev_dummy_api_key", alias="AI_GATEWAY_API_KEY")
    ai_chat_model: str = Field(default="gpt-4o-mini", alias="AI_CHAT_MODEL")
    ai_embedding_model: str = Field(default="text-embedding-3-small", alias="AI_EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
