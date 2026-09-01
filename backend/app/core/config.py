import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def cors_origin_from_host(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().rstrip("/")
    if not raw:
        return None
    if "://" in raw:
        return raw
    return f"https://{raw}"


def normalize_database_url(url: str) -> str:
    raw = url.strip()
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://webxpert:webxpert@localhost:5432/webxpert"

    JWT_SECRET: str = "dev-only-change-me-before-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    ADMIN_EMAIL: str = "admin@webxpert.com"
    ADMIN_PASSWORD: str = "changeme"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    LLM_MAX_OUTPUT_TOKENS: int = 1536

    LOG_LEVEL: str = "INFO"
    LOG_MESSAGE_BODY: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return normalize_database_url(value)

    def validate_for_runtime(self) -> None:
        if not self.is_production:
            return
        secret = self.JWT_SECRET.strip()
        if len(secret) < 32 or secret.startswith("dev-only"):
            raise RuntimeError(
                "En producción JWT_SECRET debe tener al menos 32 caracteres y no ser el valor de desarrollo."
            )
        if self.ADMIN_PASSWORD in {"changeme", "admin", "password"}:
            import logging

            logging.getLogger("webxpert").warning(
                "ADMIN_PASSWORD sigue siendo un valor por defecto; cambialo en Railway."
            )

    @property
    def cors_origin_list(self) -> list[str]:
        items: list[str] = []
        seen: set[str] = set()
        candidates = [part.strip().rstrip("/") for part in self.CORS_ORIGINS.split(",") if part.strip()]
        for extra in (os.getenv("RAILWAY_PUBLIC_DOMAIN"), os.getenv("RAILWAY_STATIC_URL")):
            origin = cors_origin_from_host(extra)
            if origin:
                candidates.append(origin)
        for item in candidates:
            if item not in seen:
                seen.add(item)
                items.append(item)
        return items

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY.strip())

    @property
    def gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY.strip())


settings = Settings()
