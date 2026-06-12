"""Consumidor del Servicio de Pagos.

Escucha StudentEnrolled para crear la proyeccion local del estudiante y generar
una obligacion de pago inicial (matricula).
"""
import logging
import threading

from shared.consuming import make_idempotent_handler
from shared.events import Event, EventType
from shared.messaging import EventConsumer

from . import repository as repo
from .database import SessionLocal
from .models import ProcessedEvent

logger = logging.getLogger("pagos.consumer")
CONSUMER_NAME = "pagos"

MATRICULA_FEE = 250.0


def on_event(db, event: Event) -> None:
    """Crea la proyeccion del estudiante y su deuda de matricula."""
    if event.eventType != EventType.STUDENT_ENROLLED:
        return
    student_id = event.data.get("studentId")
    repo.ensure_student(
        db,
        student_id=student_id,
        full_name=event.data.get("fullName", "Sin nombre"),
        school_id=event.data.get("schoolId"),
        grade=event.data.get("grade"),
    )
    repo.add_payment(
        db,
        student_id=student_id,
        concept=f"Matricula periodo {event.data.get('period', 'N/A')}",
        amount=MATRICULA_FEE,
    )
    logger.info("Deuda de matricula creada para %s", student_id)


handle_event = make_idempotent_handler(
    session_factory=SessionLocal,
    consumer_name=CONSUMER_NAME,
    processed_model=ProcessedEvent,
    on_event=on_event,
)


def start_consumer_in_background() -> None:  # pragma: no cover - hilo/infra real
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=[EventType.STUDENT_ENROLLED],
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
