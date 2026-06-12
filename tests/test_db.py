"""Pruebas de shared.db (fabrica de conexiones y Base por servicio)."""
from shared.db import build_database_url, make_engine, new_base


def test_build_database_url():
    url = build_database_url("academico_db")
    assert url.startswith("postgresql+psycopg2://")
    assert url.endswith("/academico_db")


def test_make_engine_postgres():
    # Sin DATABASE_URL se construye la URL de PostgreSQL (engine perezoso).
    engine = make_engine("academico_db")
    assert "postgresql" in str(engine.url)


def test_make_engine_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    engine = make_engine("ignorado")
    assert engine.url.get_backend_name() == "sqlite"


def test_new_base_son_independientes():
    a, b = new_base(), new_base()
    assert a.metadata is not b.metadata
