"""Consumidor del Servicio de Pagos.

Escucha StudentEnrolled para crear la proyeccion local del estudiante y generar
una obligacion de pago inicial (matricula).
"""
import logging
import threading
import uuid

from shared.events import Event, EventType
from shared.idempotency import already_processed, mark_processed
from shared.messaging import EventConsumer

from .database import SessionLocal
from .models import Payment, StudentRef

logger = logging.getLogger("pagos.consumer")
CONSUMER_NAME = "pagos"

MATRICULA_FEE = 250.0


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
            # Genera la deuda inicial de matricula.
            db.add(
                Payment(
                    id=f"PAY-{uuid.uuid4().hex[:8]}",
                    student_id=student_id,
                    concept=f"Matricula periodo {event.data.get('period', 'N/A')}",
                    amount=MATRICULA_FEE,
                    status="PENDIENTE",
                )
            )
            logger.info("Deuda de matricula creada para %s", student_id)

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
