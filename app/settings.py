import os
import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    """
    Application configuration that reads variables in this priority order:
    1. System environment variables (os.environ) - FIRST PRIORITY
    2. .env file in project root - SECOND PRIORITY
    3. Default values defined in fields - THIRD PRIORITY
    """
    model_config = SettingsConfigDict(
        # First reads from system environment variables
        # Then from .env file if not found in environment
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        # This configuration prioritizes environment variables over .env
        case_sensitive=False,
    )
    API_VERSION: str = "/api/v1"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    CLIENT_HOST: str = os.environ.get("CLIENT_HOST", "http://localhost:5173")
    ENVIRONMENT: Literal["local", "dev", "production"] = os.environ.get("ENVIRONMENT", "local")  # type: ignore
    DEBUG: bool = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS] + [
            self.CLIENT_HOST
        ]

    PROJECT_NAME: str = os.environ.get("PROJECT_NAME", "Mony API")
    PG_SERVER: str = os.environ.get("PG_SERVER", "localhost")
    PG_PORT: int = int(os.environ.get("PG_PORT", "5432"))
    PG_USER: str = os.environ.get("PG_USER", "postgres")
    PG_PASSWORD: str = os.environ.get("PG_PASSWORD", "")
    PG_DB: str = os.environ.get("PG_DB", "mony_db")

    OPEN_AI_SECRET_KEY: str = os.environ.get("OPEN_AI_SECRET_KEY", "")
    OPEN_AI_MODEL: str = os.environ.get("OPEN_AI_MODEL", "gpt-4o-mini")

    AZURE_STORAGE_CONNECTION_STRING: str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_CONTAINER_NAME: str = os.environ.get("AZURE_CONTAINER_NAME", "receipts")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        # First try to use complete DATABASE_URL (as Azure Web App provides it)
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Convert to asyncpg if necessary
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            return PostgresDsn(database_url)
        
        # If DATABASE_URL doesn't exist, build from individual components
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",  # Changed to use asyncpg
            username=self.PG_USER,
            password=self.PG_PASSWORD,
            host=self.PG_SERVER,
            port=self.PG_PORT,
            path=self.PG_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        """For compatibility with Azure Web App variables"""
        return str(self.SQLALCHEMY_DATABASE_URI)

    def _check_default_secret(self, field_name: str, value: str) -> None:
        if not value or value == "":
            message = f"{field_name} cannot be empty. Set it as environment variable or in .env file"
            warnings.warn(message, UserWarning)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        # Only validate in production or if there are no environment variables
        if self.ENVIRONMENT == "production":
            self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
            self._check_default_secret("PG_PASSWORD", self.PG_PASSWORD)
        
        return self

    def get_config_source_info(self) -> dict[str, str]:
        """
        Utility method for debugging - shows where each configuration comes from
        """
        info = {}
        config_fields = [
            "SECRET_KEY", "ENVIRONMENT", "DEBUG", "DATABASE_URL", 
            "PG_SERVER", "PG_USER", "PG_DB", "AZURE_STORAGE_CONNECTION_STRING"
        ]
        
        for field in config_fields:
            if field in os.environ:
                info[field] = "Environment Variable"
            else:
                info[field] = ".env file or default value"
                
        return info


settings = Settings()
