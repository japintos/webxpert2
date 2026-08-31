from app.core.config import normalize_database_url


def test_railway_postgres_url_becomes_psycopg():
    assert (
        normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert (
        normalize_database_url("postgresql://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )
    already = "postgresql+psycopg://user:pass@host:5432/db"
    assert normalize_database_url(already) == already
    sqlite = "sqlite:///./webxpert.db"
    assert normalize_database_url(sqlite) == sqlite
