"""Consumidor del Servicio de Asistencia/Bienestar.

Escucha StudentEnrolled para mantener una proyeccion local de estudiantes y
poder listarlos en el portal docente sin depender en linea del Servicio Academico.
"""
import logging
import threading

from shared.events import Event, EventType
from shared.idempotency import already_processed, mark_processed
from shared.messaging import EventConsumer

from .database import SessionLocal
from .models import StudentRef

logger = logging.getLogger("asistencia.consumer")
CONSUMER_NAME = "asistencia"


def handle_event(event: Event) -> None:
    db = SessionLocal()
    try:
        if already_processed(db, event.eventId, CONSUMER_NAME):
            logger.info("Evento %s ya procesado; se ignora", event.eventId)
            return

        if event.eventType == EventType.STUDENT_ENROLLED:
            student_id = event.data.get("studentId")
            if db.get(StudentRef, student_id) is None:
                db.add(
                    StudentRef(
                        id=student_id,
                        full_name=event.data.get("fullName", "Sin nombre"),
                        school_id=event.data.get("schoolId"),
                        grade=event.data.get("grade"),
                    )
                )
                logger.info("Estudiante %s proyectado en asistencia", student_id)

        mark_processed(db, event.eventId, CONSUMER_NAME)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def start_consumer_in_background() -> None:
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=[EventType.STUDENT_ENROLLED],
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
