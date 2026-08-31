from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.chat import router as chat_router
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.rate_limit import limiter
from app.db.init_db import init_db

setup_logging()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Webxpert AI Assistant API",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.on_event("startup")
    def on_startup():
        settings.validate_for_runtime()
        init_db()
        from app.db.session import SessionLocal
        from app.seed import seed

        db = SessionLocal()
        try:
            seed(db)
        except Exception:
            logger.exception("seed skipped or failed")
        finally:
            db.close()
        logger.info("startup environment=%s", settings.ENVIRONMENT)

    @app.get("/health")
    @limiter.limit("30/minute")
    def health(request: Request):
        return {"status": "ok", "service": "webxpert-assistant"}

    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
