"""Consumidor del Servicio de Analitica (lado de escritura del CQRS).

Se suscribe a los cuatro eventos de negocio y proyecta cada uno en event_log.
Junto con Notificaciones, demuestra Publish/Subscribe: dos consumidores
independientes reaccionan al mismo evento.
"""
import logging
import threading

from shared.consuming import make_idempotent_handler
from shared.events import EventType
from shared.messaging import EventConsumer

from . import repository as repo
from .database import SessionLocal
from .models import ProcessedEvent

logger = logging.getLogger("analitica.consumer")
CONSUMER_NAME = "analitica"

ALL_EVENTS = [
    EventType.STUDENT_ENROLLED,
    EventType.PAYMENT_CONFIRMED,
    EventType.ATTENDANCE_RECORDED,
    EventType.INCIDENT_REPORTED,
]


def on_event(db, event) -> None:
    """Proyecta el evento en el modelo de lectura."""
    repo.add_event(
        db,
        event_id=event.eventId,
        event_type=event.eventType,
        student_id=event.data.get("studentId"),
        correlation_id=event.correlationId,
        payload=event.data,
    )
    logger.info("Evento %s proyectado en analitica", event.eventType)


handle_event = make_idempotent_handler(
    session_factory=SessionLocal,
    consumer_name=CONSUMER_NAME,
    processed_model=ProcessedEvent,
    on_event=on_event,
)


def start_consumer_in_background() -> None:  # pragma: no cover - hilo/infra real
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=ALL_EVENTS,
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
