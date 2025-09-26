import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
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
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_VERSION: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    CLIENT_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "development", "production"] = "local"

    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS] + [
            self.CLIENT_HOST
        ]

    PROJECT_NAME: str
    PG_SERVER: str
    PG_PORT: int = 5432
    PG_USER: str
    PG_PASSWORD: str = ""
    PG_DB: str = ""

    OPEN_AI_SECRET_KEY: str
    OPEN_AI_MODEL: str = "gpt-4o-mini"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.PG_USER,
            password=self.PG_PASSWORD,
            host=self.PG_SERVER,
            port=self.PG_PORT,
            path=self.PG_DB,
        )

    def _check_default_secret(self, field_name: str, value: str) -> None:
        if not value or value == "":
            raise ValueError(f"{field_name} cannot be empty")

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("PG_PASSWORD", self.PG_PASSWORD)

        return self


settings = Settings()
