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


def test_dashboard_pagos_pendientes_parciales(client):
    # 3 matriculados, solo 2 pagos confirmados -> 1 pendiente
    for i in range(3):
        _proyectar(EventType.STUDENT_ENROLLED, {"studentId": f"STU-P{i}"})
    for i in range(2):
        _proyectar(EventType.PAYMENT_CONFIRMED, {"studentId": f"STU-P{i}", "amount": 100})
    data = client.get("/dashboard").json()
    assert data["matriculados"] == 3
    assert data["pagosConfirmados"] == 2
    assert data["pagosPendientes"] == 1
    assert data["montoConfirmado"] == 200.0


def test_events_limit_restringe_resultados(client):
    for i in range(5):
        _proyectar(EventType.ATTENDANCE_RECORDED, {"studentId": f"STU-L{i}"})
    assert len(client.get("/events?limit=3").json()) == 3
    assert len(client.get("/events?limit=1").json()) == 1


def test_events_by_type_multiples_tipos(client):
    _proyectar(EventType.STUDENT_ENROLLED, {"studentId": "STU-BT1"})
    _proyectar(EventType.PAYMENT_CONFIRMED, {"studentId": "STU-BT1", "amount": 50})
    _proyectar(EventType.INCIDENT_REPORTED, {"studentId": "STU-BT1"})
    por_tipo = client.get("/events/by-type").json()
    assert por_tipo[EventType.STUDENT_ENROLLED] == 1
    assert por_tipo[EventType.PAYMENT_CONFIRMED] == 1
    assert por_tipo[EventType.INCIDENT_REPORTED] == 1


def test_init_db():
    database.init_db()
