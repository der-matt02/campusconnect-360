"""Consumidor del Servicio de Notificaciones (patron Publish/Subscribe).

Se suscribe a los cuatro eventos de negocio y genera una notificacion simulada
por cada uno (Message Translator). Implementa:
  - Idempotencia (Idempotent Receiver) via make_idempotent_handler.
  - Modo de fallo controlado ("chaos") para demostrar reintentos + DLQ.
"""
import logging
import threading

from shared.consuming import make_idempotent_handler
from shared.events import EventType
from shared.messaging import EventConsumer

from . import repository as repo
from .database import SessionLocal
from .models import ProcessedEvent
from .translator import translate

logger = logging.getLogger("notificaciones.consumer")
CONSUMER_NAME = "notificaciones"

# Bandera de fallo simulado para demostrar el escenario de resiliencia.
chaos = {"enabled": False}

ALL_EVENTS = [
    EventType.STUDENT_ENROLLED,
    EventType.PAYMENT_CONFIRMED,
    EventType.ATTENDANCE_RECORDED,
    EventType.INCIDENT_REPORTED,
]


def on_event(db, event) -> None:
    """Genera y persiste la notificacion. Lanza excepcion si chaos esta activo."""
    if chaos["enabled"]:
        raise RuntimeError("Fallo simulado en el Servicio de Notificaciones")
    student_id, message = translate(event)
    repo.add_notification(
        db,
        event_id=event.eventId,
        event_type=event.eventType,
        student_id=student_id,
        message=message,
        correlation_id=event.correlationId,
    )
    logger.info("Notificacion generada para %s (%s)", student_id, event.eventType)


handle_event = make_idempotent_handler(
    session_factory=SessionLocal,
    consumer_name=CONSUMER_NAME,
    processed_model=ProcessedEvent,
    on_event=on_event,
)


def start_consumer_in_background() -> None:
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=ALL_EVENTS,
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
