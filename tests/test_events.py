"""Pruebas de los contratos de eventos (capa compartida)."""
import json

from shared.events import Event, EventType


def test_event_create_genera_identificadores():
    event = Event.create(EventType.STUDENT_ENROLLED, {"studentId": "STU-1"})
    assert event.eventType == "StudentEnrolled"
    assert event.eventId.startswith("evt-")
    assert event.correlationId.startswith("corr-")
    assert event.occurredAt  # timestamp presente
    assert event.data["studentId"] == "STU-1"


def test_event_respeta_correlation_id_explicito():
    event = Event.create(EventType.PAYMENT_CONFIRMED, {}, correlation_id="corr-fijo")
    assert event.correlationId == "corr-fijo"


def test_event_serializa_y_deserializa():
    original = Event.create(EventType.INCIDENT_REPORTED, {"severity": "ALTA"})
    restored = Event(**json.loads(original.model_dump_json()))
    assert restored.eventId == original.eventId
    assert restored.data["severity"] == "ALTA"


def test_existen_los_cuatro_eventos_de_negocio():
    tipos = {
        EventType.STUDENT_ENROLLED,
        EventType.PAYMENT_CONFIRMED,
        EventType.ATTENDANCE_RECORDED,
        EventType.INCIDENT_REPORTED,
    }
    assert len(tipos) == 4
