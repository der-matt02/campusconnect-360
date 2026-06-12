"""Consumidor del Servicio de Notificaciones (patron Publish/Subscribe).

Se suscribe a los cuatro eventos de negocio y genera una notificacion simulada
por cada uno (Message Translator). Implementa:
  - Idempotencia (Idempotent Receiver).
  - Modo de fallo controlado ("chaos") para demostrar reintentos + DLQ.
"""
import logging
import threading
import uuid

from shared.events import Event, EventType
from shared.idempotency import already_processed, mark_processed
from shared.messaging import EventConsumer

from .database import SessionLocal
from .models import Notification
from .translator import translate

logger = logging.getLogger("notificaciones.consumer")
CONSUMER_NAME = "notificaciones"

# Bandera de fallo simulado para demostrar el escenario de resiliencia.
# Cuando esta activa, el procesamiento falla y los mensajes terminan en la DLQ.
chaos = {"enabled": False}

ALL_EVENTS = [
    EventType.STUDENT_ENROLLED,
    EventType.PAYMENT_CONFIRMED,
    EventType.ATTENDANCE_RECORDED,
    EventType.INCIDENT_REPORTED,
]


def process_event(event: Event) -> None:
    """Genera y persiste la notificacion. Lanza excepcion si chaos esta activo."""
    if chaos["enabled"]:
        raise RuntimeError("Fallo simulado en el Servicio de Notificaciones")

    db = SessionLocal()
    try:
        if already_processed(db, event.eventId, CONSUMER_NAME):
            logger.info("Evento %s ya procesado; se ignora", event.eventId)
            return

        student_id, message = translate(event)
        db.add(
            Notification(
                id=f"NOT-{uuid.uuid4().hex[:8]}",
                event_id=event.eventId,
                event_type=event.eventType,
                student_id=student_id,
                message=message,
                status="ENVIADA",
                correlation_id=event.correlationId,
            )
        )
        mark_processed(db, event.eventId, CONSUMER_NAME)
        db.commit()
        logger.info("Notificacion generada para %s (%s)", student_id, event.eventType)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_consumer_in_background() -> None:
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=ALL_EVENTS,
        handler=process_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
