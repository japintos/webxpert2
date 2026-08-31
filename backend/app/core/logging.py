import logging
import sys

from app.core.config import settings

SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "authorization",
    "api_key",
    "openai_api_key",
    "gemini_api_key",
    "secret",
    "jwt_secret",
    "verify_token",
}


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("webxpert")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    logger.propagate = False
    return logger


logger = setup_logging()


def redact(data: dict | None) -> dict:
    if not data:
        return {}
    clean: dict = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS or "token" in key.lower() or "secret" in key.lower():
            clean[key] = "[redacted]"
        else:
            clean[key] = value
    return clean
