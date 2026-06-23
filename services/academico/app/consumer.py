"""Consumidor de eventos del Servicio Academico.

Escucha PaymentConfirmed para actualizar el estado financiero del estudiante
y publica StudentStatusUpdated para notificar el cambio de estado (flujo 5.2).
"""
import logging
import threading

from shared.consuming import make_idempotent_handler
from shared.enums import FinancialStatus
from shared.events import Event, EventType
from shared.messaging import EventConsumer, publish_event

from .database import SessionLocal
from .models import ProcessedEvent
from .repository import add_event, get_student

logger = logging.getLogger("academico.consumer")
CONSUMER_NAME = "academico"


def on_event(db, event: Event) -> None:
    """Logica de negocio: actualiza el estado financiero ante un pago confirmado."""
    if event.eventType != EventType.PAYMENT_CONFIRMED:
        return
    student = get_student(db, event.data.get("studentId"))
    if student is None:
        logger.warning("Estudiante %s no encontrado", event.data.get("studentId"))
        return
    estado_anterior = student.financial_status
    student.financial_status = FinancialStatus.AL_DIA
    add_event(
        db,
        student_id=student.id,
        event_type=event.eventType,
        correlation_id=event.correlationId,
        summary=f"Pago confirmado por {event.data.get('amount')}",
    )
    logger.info("Estado financiero actualizado para %s", student.id)

    status_event = Event.create(
        EventType.STUDENT_STATUS_UPDATED,
        data={
            "studentId": student.id,
            "previousStatus": estado_anterior,
            "newStatus": "AL_DIA",
            "triggeredBy": event.eventType,
        },
        correlation_id=event.correlationId,
    )
    publish_event(status_event)


handle_event = make_idempotent_handler(
    session_factory=SessionLocal,
    consumer_name=CONSUMER_NAME,
    processed_model=ProcessedEvent,
    on_event=on_event,
)


def start_consumer_in_background() -> None:  # pragma: no cover - hilo/infra real
    consumer = EventConsumer(
        service_name=CONSUMER_NAME,
        routing_keys=[EventType.PAYMENT_CONFIRMED],
        handler=handle_event,
    )
    thread = threading.Thread(target=consumer.start, daemon=True)
    thread.start()
