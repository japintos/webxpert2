from sqlalchemy import inspect, text

from app.db.base import Base  # noqa: F401
from app.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_assistant_llm_columns()


def _ensure_assistant_llm_columns() -> None:
    inspector = inspect(engine)
    if "assistants" not in inspector.get_table_names():
        return
    names = {column["name"] for column in inspector.get_columns("assistants")}
    statements: list[str] = []
    if "llm_provider" not in names:
        statements.append("ALTER TABLE assistants ADD COLUMN llm_provider VARCHAR(32) DEFAULT 'openai'")
    if "llm_model" not in names:
        statements.append("ALTER TABLE assistants ADD COLUMN llm_model VARCHAR(80)")
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
