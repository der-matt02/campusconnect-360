"""Consumidor del Servicio de Asistencia/Bienestar.

Escucha StudentEnrolled para mantener una proyeccion local de estudiantes y
poder listarlos en el portal docente sin depender en linea del Servicio Academico.
"""
import logging
import threading

from shared.consuming import make_idempotent_handler
from shared.events import Event, EventType
from shared.messaging import EventConsumer

from . import repository as repo
from .database import SessionLocal
from .models import ProcessedEvent

logger = logging.getLogger("asistencia.consumer")
CONSUMER_NAME = "asistencia"


def on_event(db, event: Event) -> None:
    """Proyecta el estudiante recien matriculado."""
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
    logger.info("Estudiante %s proyectado en asistencia", student_id)


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
