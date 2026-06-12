"""Pruebas del patron Idempotent Receiver usando SQLite en memoria."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.db import new_base
from shared.idempotency import ProcessedEventMixin, already_processed, mark_processed

# Base de prueba con el modelo de control declarado sobre el mixin.
Base = new_base()


class ProcessedEvent(Base, ProcessedEventMixin):
    __tablename__ = "processed_events"


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_evento_no_procesado_inicialmente(db):
    assert already_processed(db, ProcessedEvent, "evt-1", "notificaciones") is False


def test_marcar_evento_como_procesado(db):
    mark_processed(db, ProcessedEvent, "evt-1", "notificaciones")
    db.commit()
    assert already_processed(db, ProcessedEvent, "evt-1", "notificaciones") is True


def test_idempotencia_por_consumidor(db):
    mark_processed(db, ProcessedEvent, "evt-1", "notificaciones")
    db.commit()
    # Mismo evento, otro consumidor: aun no procesado para 'analitica'.
    assert already_processed(db, ProcessedEvent, "evt-1", "analitica") is False
