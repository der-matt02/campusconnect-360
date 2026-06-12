"""Configuracion de pruebas del Servicio de Pagos (SQLite en memoria)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
import app.consumer as consumer
from app.database import Base, engine

from shared.events import Event, EventType


@pytest.fixture(autouse=True)
def _db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(main_module, "publish_event", lambda event: None)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(main_module.app)


def proyectar_estudiante(sid="STU-1"):
    """Simula la llegada de StudentEnrolled (crea estudiante + deuda)."""
    consumer.handle_event(
        Event.create(
            EventType.STUDENT_ENROLLED,
            {"studentId": sid, "fullName": "Prueba", "schoolId": "SCH-001", "grade": "8vo", "period": "2026-1"},
        )
    )
