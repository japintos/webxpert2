from app.core.config import cors_origin_from_host, normalize_database_url


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


def test_cors_origin_from_host():
    assert cors_origin_from_host("webxpert.up.railway.app") == "https://webxpert.up.railway.app"
    assert cors_origin_from_host("https://www.webxpert.com.ar/") == "https://www.webxpert.com.ar"
    assert cors_origin_from_host("  ") is None
    assert cors_origin_from_host(None) is None
