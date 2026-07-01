"""Configuracion de pruebas del Servicio de Analitica (SQLite en memoria)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import app.main as main_module
import pytest
from app.database import Base, engine
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(main_module.app)
