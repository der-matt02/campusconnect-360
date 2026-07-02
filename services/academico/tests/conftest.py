"""Configuracion de pruebas del Servicio Academico (SQLite en memoria)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import app.consumer as consumer_module
import app.main as main_module
import pytest
from app.database import Base, engine
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _db(monkeypatch):
    # Crea el esquema en SQLite y evita publicar a RabbitMQ durante las pruebas.
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(main_module, "publish_event", lambda event: None)
    monkeypatch.setattr(consumer_module, "publish_event", lambda event: None)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(main_module.app)


def nuevo_estudiante(client, documento="1700000001"):
    resp = client.post(
        "/students",
        json={
            "full_name": "Estudiante Prueba",
            "document_id": documento,
            "email": "prueba@example.edu",
            "school_id": "SCH-001",
            "grade": "8vo EGB",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]
