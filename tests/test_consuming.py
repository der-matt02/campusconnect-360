"""Pruebas del helper make_idempotent_handler (shared.consuming)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.consuming import make_idempotent_handler
from shared.db import new_base
from shared.events import Event, EventType
from shared.idempotency import ProcessedEventMixin

Base = new_base()


class ProcessedEvent(Base, ProcessedEventMixin):
    __tablename__ = "processed_events"


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def test_procesa_y_marca(session_factory):
    visto = []
    handler = make_idempotent_handler(
        session_factory=session_factory,
        consumer_name="svc",
        processed_model=ProcessedEvent,
        on_event=lambda db, e: visto.append(e.eventId),
    )
    event = Event.create(EventType.STUDENT_ENROLLED, {})
    handler(event)
    assert visto == [event.eventId]


def test_ignora_duplicados(session_factory):
    contador = {"n": 0}

    def on_event(db, e):
        contador["n"] += 1

    handler = make_idempotent_handler(
        session_factory=session_factory,
        consumer_name="svc",
        processed_model=ProcessedEvent,
        on_event=on_event,
    )
    event = Event.create(EventType.PAYMENT_CONFIRMED, {})
    handler(event)
    handler(event)  # mismo evento: no debe reprocesar
    assert contador["n"] == 1


def test_propaga_excepcion_y_no_marca(session_factory):
    def boom(db, e):
        raise RuntimeError("fallo")

    handler = make_idempotent_handler(
        session_factory=session_factory,
        consumer_name="svc",
        processed_model=ProcessedEvent,
        on_event=boom,
    )
    event = Event.create(EventType.INCIDENT_REPORTED, {})
    with pytest.raises(RuntimeError):
        handler(event)
