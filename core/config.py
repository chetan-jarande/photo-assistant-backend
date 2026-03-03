from enum import StrEnum
from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.logger import get_logger

logger = get_logger(__name__)


class Environments(StrEnum):
    DEV = "dev"
    PROD = "prod"


class Settings(BaseSettings):
    """
    Application settings.

    Uses pydantic-settings to load from environment variables and .env files.
    Doc: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    # API Settings
    PROJECT_NAME: str = "Photography Assistant AI Backend"
    API_V1_STR: str = "/api/v1"

    CONF_ENV: Environments = Field(
        default=Environments.DEV,
        description="Configuration environment",
    )
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(
        default=8000,
        description="Port for the FastAPI server",
    )

    # SurrealDB Settings
    SURREALDB_URL: str = "ws://localhost:8000/rpc"
    SURREALDB_USER: str = "root"
    SURREALDB_PASS: str = "root"
    SURREALDB_NS: str = "photo_assistant"
    SURREALDB_DB: str = "main"

    # AI Provider Settings
    LLM_API_KEY = SecretStr = Field(
        ...,
        validation_alias="LLM_API_KEY",
        description="Your LLM API key",
    )
    LLM_MODEL: str = "gemini-2.5-pro"

    # Security
    JWT_SECRET_KEY: str = "development_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

MCP_SERVER_URL = f"http://localhost:{settings.SERVER_PORT}/mcp"
