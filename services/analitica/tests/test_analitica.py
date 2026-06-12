"""Pruebas del Servicio de Analitica (CQRS): proyeccion e indicadores."""
import app.consumer as consumer
from app import database

from shared.events import Event, EventType


def _proyectar(tipo, data):
    consumer.handle_event(Event.create(tipo, data))


def test_health(client):
    assert client.get("/health").json()["service"] == "analitica"


def test_dashboard_vacio(client):
    data = client.get("/dashboard").json()
    assert data["matriculados"] == 0
    assert data["eventosProcesados"] == 0
    assert data["estado"] == "OK"


def test_dashboard_consolida_eventos(client):
    _proyectar(EventType.STUDENT_ENROLLED, {"studentId": "STU-1"})
    _proyectar(EventType.PAYMENT_CONFIRMED, {"studentId": "STU-1", "amount": 250})
    _proyectar(EventType.ATTENDANCE_RECORDED, {"studentId": "STU-1"})
    _proyectar(EventType.INCIDENT_REPORTED, {"studentId": "STU-1"})
    data = client.get("/dashboard").json()
    assert data["matriculados"] == 1
    assert data["pagosConfirmados"] == 1
    assert data["pagosPendientes"] == 0
    assert data["montoConfirmado"] == 250.0
    assert data["asistencias"] == 1
    assert data["incidentes"] == 1
    assert data["eventosProcesados"] == 4


def test_events_y_by_type(client):
    _proyectar(EventType.STUDENT_ENROLLED, {"studentId": "STU-2"})
    eventos = client.get("/events").json()
    assert len(eventos) == 1
    assert eventos[0]["eventType"] == EventType.STUDENT_ENROLLED
    por_tipo = client.get("/events/by-type").json()
    assert por_tipo[EventType.STUDENT_ENROLLED] == 1


def test_consumidor_idempotente(client):
    event = Event.create(EventType.STUDENT_ENROLLED, {"studentId": "STU-3"})
    consumer.handle_event(event)
    consumer.handle_event(event)
    assert client.get("/dashboard").json()["matriculados"] == 1


def test_init_db():
    database.init_db()
