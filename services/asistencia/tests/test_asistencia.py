"""Pruebas del Servicio de Asistencia: endpoints y consumidor."""
import app.consumer as consumer
from app import database, seed
from conftest import proyectar_estudiante

from shared.events import Event, EventType


def test_health(client):
    assert client.get("/health").json()["service"] == "asistencia"


def test_consumidor_proyecta_estudiante(client):
    proyectar_estudiante("STU-1")
    estudiantes = client.get("/students").json()
    assert any(e["id"] == "STU-1" for e in estudiantes)


def test_registrar_asistencia(client):
    proyectar_estudiante("STU-2")
    resp = client.post("/attendance", json={"student_id": "STU-2", "date": "2026-06-12", "status": "presente"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "PRESENTE"
    historial = client.get("/students/STU-2/attendance").json()
    assert len(historial) == 1


def test_registrar_asistencia_sin_estudiante_da_404(client):
    assert client.post("/attendance", json={"student_id": "NOPE", "date": "x", "status": "presente"}).status_code == 404


def test_registrar_incidente(client):
    proyectar_estudiante("STU-3")
    resp = client.post("/incidents", json={"student_id": "STU-3", "severity": "alta", "description": "Novedad"})
    assert resp.status_code == 201
    assert resp.json()["severity"] == "ALTA"
    assert len(client.get("/students/STU-3/incidents").json()) == 1


def test_registrar_incidente_sin_estudiante_da_404(client):
    assert client.post("/incidents", json={"student_id": "NOPE", "severity": "baja", "description": "x"}).status_code == 404


def test_consumidor_idempotente(client):
    event = Event.create(
        EventType.STUDENT_ENROLLED,
        {"studentId": "STU-9", "fullName": "X", "schoolId": "S", "grade": "8vo"},
    )
    consumer.handle_event(event)
    consumer.handle_event(event)
    assert sum(1 for e in client.get("/students").json() if e["id"] == "STU-9") == 1


def test_consumidor_ignora_otros_eventos(client):
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": "X"}))
    assert not any(e["id"] == "X" for e in client.get("/students").json())


def test_historial_asistencia_vacio(client):
    proyectar_estudiante("STU-7")
    assert client.get("/students/STU-7/attendance").json() == []


def test_historial_incidentes_vacio(client):
    proyectar_estudiante("STU-8")
    assert client.get("/students/STU-8/incidents").json() == []


def test_normaliza_status_asistencia_a_mayusculas(client):
    proyectar_estudiante("STU-10")
    for valor in ("presente", "PRESENTE", "Presente"):
        resp = client.post("/attendance", json={"student_id": "STU-10", "date": "2026-06-15", "status": valor})
        assert resp.status_code == 201
        assert resp.json()["status"] == "PRESENTE"


def test_normaliza_severity_incidente_a_mayusculas(client):
    proyectar_estudiante("STU-11")
    for valor in ("alta", "ALTA", "Alta"):
        resp = client.post("/incidents", json={"student_id": "STU-11", "severity": valor, "description": "x"})
        assert resp.status_code == 201
        assert resp.json()["severity"] == "ALTA"


def test_init_db_y_seed():
    database.init_db()
    seed.seed_data()
    seed.seed_data()
