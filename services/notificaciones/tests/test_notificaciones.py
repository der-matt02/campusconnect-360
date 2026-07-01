"""Pruebas del Servicio de Notificaciones: consumidor, translator y resiliencia."""
import app.consumer as consumer
import pytest
from app import database
from app.translator import translate

from shared.events import Event, EventType


def _evento(tipo, data=None):
    return Event.create(tipo, data or {"studentId": "STU-1"})


def test_health(client):
    assert client.get("/health").json()["service"] == "notificaciones"


def test_consumidor_genera_notificacion(client):
    consumer.handle_event(_evento(EventType.STUDENT_ENROLLED, {"studentId": "STU-1", "fullName": "Ana", "enrollmentId": "ENR-1", "period": "2026-1"}))
    notifs = client.get("/notifications").json()
    assert len(notifs) == 1
    assert notifs[0]["status"] == "ENVIADA"


def test_stats(client):
    consumer.handle_event(_evento(EventType.ATTENDANCE_RECORDED, {"studentId": "STU-1", "date": "2026-06-12", "status": "PRESENTE"}))
    stats = client.get("/stats").json()
    assert stats["enviadas"] == 1
    assert stats["fallidas"] == 0
    assert stats["chaos"] is False


def test_chaos_endpoints(client):
    assert client.get("/chaos").json()["enabled"] is False
    assert client.post("/chaos", json={"enabled": True}).json()["enabled"] is True
    assert consumer.chaos["enabled"] is True


def test_chaos_provoca_fallo(client):
    consumer.chaos["enabled"] = True
    with pytest.raises(RuntimeError):
        consumer.handle_event(_evento(EventType.INCIDENT_REPORTED, {"studentId": "STU-1", "severity": "ALTA", "description": "x"}))


def test_dlq_endpoints(client):
    assert client.get("/dlq").json()["dlqDepth"] == 0
    assert client.post("/dlq/reprocess").json()["reprocessed"] == 0


def test_translator_todos_los_tipos():
    sid, msg = translate(_evento(EventType.STUDENT_ENROLLED, {"studentId": "STU-1", "fullName": "Ana", "enrollmentId": "ENR-1", "period": "2026-1"}))
    assert sid == "STU-1" and "matricula" in msg.lower()
    _, msg = translate(_evento(EventType.PAYMENT_CONFIRMED, {"studentId": "STU-1", "amount": 250, "concept": "Matricula"}))
    assert "pago" in msg.lower()
    _, msg = translate(_evento(EventType.ATTENDANCE_RECORDED, {"studentId": "STU-1", "date": "2026-06-12", "status": "PRESENTE"}))
    assert "asistencia" in msg.lower()
    _, msg = translate(_evento(EventType.INCIDENT_REPORTED, {"studentId": "STU-1", "severity": "ALTA", "description": "Novedad"}))
    assert "novedad" in msg.lower()


def test_translator_tipo_desconocido():
    _, msg = translate(_evento("OtroEvento"))
    assert "OtroEvento" in msg


def test_consumidor_payment_confirmed_genera_notificacion(client):
    consumer.handle_event(_evento(
        EventType.PAYMENT_CONFIRMED,
        {"studentId": "STU-2", "amount": 150, "concept": "Matricula 2026-1"},
    ))
    notifs = client.get("/notifications").json()
    assert len(notifs) == 1
    assert "pago" in notifs[0]["message"].lower()


def test_consumidor_incident_reported_genera_notificacion(client):
    consumer.handle_event(_evento(
        EventType.INCIDENT_REPORTED,
        {"studentId": "STU-3", "severity": "ALTA", "description": "Conducta disruptiva"},
    ))
    notifs = client.get("/notifications").json()
    assert any("novedad" in n["message"].lower() for n in notifs)


def test_consumidor_idempotente(client):
    evento = _evento(EventType.STUDENT_ENROLLED, {
        "studentId": "STU-4", "fullName": "X", "enrollmentId": "ENR-X", "period": "2026-1",
    })
    consumer.handle_event(evento)
    consumer.handle_event(evento)
    assert len(client.get("/notifications").json()) == 1


def test_notificaciones_almacenan_student_id_y_tipo(client):
    consumer.handle_event(_evento(
        EventType.ATTENDANCE_RECORDED,
        {"studentId": "STU-5", "date": "2026-06-12", "status": "PRESENTE"},
    ))
    notifs = client.get("/notifications").json()
    assert notifs[0]["studentId"] == "STU-5"
    assert notifs[0]["eventType"] == EventType.ATTENDANCE_RECORDED


def test_init_db():
    database.init_db()
