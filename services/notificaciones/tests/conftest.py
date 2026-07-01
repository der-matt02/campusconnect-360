"""Configuracion de pruebas del Servicio de Notificaciones (SQLite en memoria)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import app.consumer as consumer
import app.main as main_module
import pytest
from app.database import Base, engine
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    # Evita tocar RabbitMQ: la DLQ se simula.
    monkeypatch.setattr(main_module, "dlq_depth", lambda: 0)
    monkeypatch.setattr(main_module, "reprocess_dlq", lambda: {"reprocessed": 0, "still_failed": 0})
    consumer.chaos["enabled"] = False
    yield
    consumer.chaos["enabled"] = False
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(main_module.app)
