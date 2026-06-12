"""Consumidor de eventos del Servicio Academico.

Escucha PaymentConfirmed para actualizar el estado financiero del estudiante
(flujo 5.2 de la consigna).
"""
import logging
import threading

from shared.events import Event, EventType
from shared.idempotency import already_processed, mark_processed
from shared.messaging import EventConsumer

from .database import SessionLocal
from .models import Student, StudentEvent

logger = logging.getLogger("academico.consumer")
CONSUMER_NAME = "academico"


def handle_event(event: Event) -> None:
    db = SessionLocal()
    try:
        if already_processed(db, event.eventId, CONSUMER_NAME):
            logger.info("Evento %s ya procesado; se ignora", event.eventId)
            return

        if event.eventType == EventType.PAYMENT_CONFIRMED:
            student_id = event.data.get("studentId")
            student = db.get(Student, student_id)
            if student is None:
                logger.warning("Estudiante %s no encontrado", student_id)
            else:
                student.financial_status = "AL_DIA"
                db.add(
                    StudentEvent(
                        student_id=student.id,
                        event_type=event.eventType,
                        correlation_id=event.correlationId,
                        summary=f"Pago confirmado por {event.data.get('amount')}",
                    )
                )
                logger.info("Estado financiero actualizado para %s", student_id)

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
        routing_keys=[EventType.PAYMENT_CONFIRMED],
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
