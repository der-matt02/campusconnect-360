"""Pruebas del Servicio Academico: endpoints y consumidor."""
import app.consumer as consumer
from app import database, seed
from conftest import nuevo_estudiante

from shared.events import Event, EventType


def test_health(client):
    assert client.get("/health").json()["service"] == "academico"


def test_crear_y_listar_estudiante(client):
    sid = nuevo_estudiante(client)
    estudiantes = client.get("/students").json()
    assert any(e["id"] == sid for e in estudiantes)


def test_documento_duplicado_da_409(client):
    nuevo_estudiante(client, documento="1700000009")
    dup = client.post(
        "/students",
        json={
            "full_name": "Otro",
            "document_id": "1700000009",
            "email": "x@example.edu",
            "school_id": "SCH-001",
            "grade": "8vo EGB",
        },
    )
    assert dup.status_code == 409


def test_estudiante_inexistente_da_404(client):
    assert client.get("/students/NOPE").status_code == 404
    assert client.get("/students/NOPE/events").status_code == 404


def test_matricula_genera_evento_y_historial(client):
    sid = nuevo_estudiante(client)
    resp = client.post("/enrollments", json={"student_id": sid, "period": "2026-1"})
    assert resp.status_code == 201
    eventos = client.get(f"/students/{sid}/events").json()
    assert any(e["event_type"] == EventType.STUDENT_ENROLLED for e in eventos)


def test_matricula_estudiante_inexistente_da_404(client):
    assert client.post("/enrollments", json={"student_id": "NOPE", "period": "x"}).status_code == 404


def test_matricula_periodo_duplicado_da_409(client):
    sid = nuevo_estudiante(client)
    client.post("/enrollments", json={"student_id": sid, "period": "2026-1"})
    resp = client.post("/enrollments", json={"student_id": sid, "period": "2026-1"})
    assert resp.status_code == 409


def test_matricula_periodos_distintos_permitidos(client):
    sid = nuevo_estudiante(client)
    assert client.post("/enrollments", json={"student_id": sid, "period": "2026-1"}).status_code == 201
    assert client.post("/enrollments", json={"student_id": sid, "period": "2026-2"}).status_code == 201


def test_ficha_incluye_matriculas_y_eventos(client):
    sid = nuevo_estudiante(client)
    client.post("/enrollments", json={"student_id": sid, "period": "2026-1"})
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": sid, "amount": 300}))
    ficha = client.get(f"/students/{sid}").json()
    assert len(ficha["enrollments"]) == 1
    assert ficha["financial_status"] == "AL_DIA"
    tipos = {e["event_type"] for e in ficha["events"]}
    assert EventType.STUDENT_ENROLLED in tipos
    assert EventType.PAYMENT_CONFIRMED in tipos


def test_consumidor_actualiza_estado_financiero(client):
    sid = nuevo_estudiante(client)
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": sid, "amount": 250}))
    assert client.get(f"/students/{sid}").json()["financial_status"] == "AL_DIA"


def test_consumidor_publica_student_status_updated(client, monkeypatch):
    publicados = []
    monkeypatch.setattr(consumer, "publish_event", lambda e: publicados.append(e))
    sid = nuevo_estudiante(client)
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": sid, "amount": 250}))
    assert any(e.eventType == EventType.STUDENT_STATUS_UPDATED for e in publicados)
    evt = next(e for e in publicados if e.eventType == EventType.STUDENT_STATUS_UPDATED)
    assert evt.data["newStatus"] == "AL_DIA"
    assert evt.data["previousStatus"] == "PENDIENTE"


def test_consumidor_ignora_otros_eventos(client):
    consumer.handle_event(Event.create(EventType.ATTENDANCE_RECORDED, {"studentId": "X"}))


def test_consumidor_estudiante_inexistente_no_falla(client):
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": "NOPE", "amount": 1}))


def test_consumidor_es_idempotente(client):
    sid = nuevo_estudiante(client)
    event = Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": sid, "amount": 250})
    consumer.handle_event(event)
    consumer.handle_event(event)
    eventos = client.get(f"/students/{sid}/events").json()
    assert sum(1 for e in eventos if e["event_type"] == EventType.PAYMENT_CONFIRMED) == 1


def test_init_db_y_seed():
    database.init_db()
    seed.seed_data()
    seed.seed_data()  # segundo llamado: no duplica (cubre la rama de retorno)
