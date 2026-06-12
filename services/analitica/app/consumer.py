"""Consumidor del Servicio de Analitica (lado de escritura del CQRS).

Se suscribe a los cuatro eventos de negocio y proyecta cada uno en event_log.
Junto con Notificaciones, demuestra Publish/Subscribe: dos consumidores
independientes reaccionan al mismo evento.
"""
import logging
import threading

from shared.events import Event, EventType
from shared.idempotency import already_processed, mark_processed
from shared.messaging import EventConsumer

from .database import SessionLocal
from .models import EventLog

logger = logging.getLogger("analitica.consumer")
CONSUMER_NAME = "analitica"

ALL_EVENTS = [
    EventType.STUDENT_ENROLLED,
    EventType.PAYMENT_CONFIRMED,
    EventType.ATTENDANCE_RECORDED,
    EventType.INCIDENT_REPORTED,
]


def handle_event(event: Event) -> None:
    db = SessionLocal()
    try:
        if already_processed(db, event.eventId, CONSUMER_NAME):
            logger.info("Evento %s ya procesado; se ignora", event.eventId)
            return

        db.add(
            EventLog(
                event_id=event.eventId,
                event_type=event.eventType,
                student_id=event.data.get("studentId"),
                correlation_id=event.correlationId,
                payload=event.data,
            )
        )
        mark_processed(db, event.eventId, CONSUMER_NAME)
        db.commit()
        logger.info("Evento %s proyectado en analitica", event.eventType)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_consumer_in_background() -> None:
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=ALL_EVENTS,
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
