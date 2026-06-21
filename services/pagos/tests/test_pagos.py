"""Pruebas del Servicio de Pagos: endpoints y consumidor."""
import app.consumer as consumer
import app.main as main_module
from app import database, seed
from conftest import proyectar_estudiante

from shared.events import Event, EventType


def test_health(client):
    assert client.get("/health").json()["service"] == "pagos"


def test_consumidor_crea_estudiante_y_deuda(client):
    proyectar_estudiante("STU-1")
    data = client.get("/students/STU-1").json()
    assert data["id"] == "STU-1"
    assert len(data["payments"]) == 1
    assert data["payments"][0]["status"] == "PENDIENTE"


def test_estudiante_inexistente_da_404(client):
    assert client.get("/students/NOPE").status_code == 404


def test_registrar_deuda(client):
    proyectar_estudiante("STU-2")
    resp = client.post("/debts", json={"student_id": "STU-2", "concept": "Transporte", "amount": 50})
    assert resp.status_code == 201
    assert resp.json()["concept"] == "Transporte"


def test_registrar_deuda_sin_estudiante_da_404(client):
    assert client.post("/debts", json={"student_id": "NOPE", "concept": "X", "amount": 10}).status_code == 404


def test_confirmar_pago(client):
    proyectar_estudiante("STU-3")
    pago = client.get("/students/STU-3").json()["payments"][0]["id"]
    resp = client.post(f"/payments/{pago}/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMADO"
    # Segundo intento: ya confirmado -> 409
    assert client.post(f"/payments/{pago}/confirm").status_code == 409


def test_confirmar_pago_publica_evento_con_datos_correctos(client, monkeypatch):
    publicados = []
    monkeypatch.setattr(main_module, "publish_event", lambda e: publicados.append(e))
    proyectar_estudiante("STU-6")
    pago = client.get("/students/STU-6").json()["payments"][0]["id"]
    client.post(f"/payments/{pago}/confirm")
    assert len(publicados) == 1
    evt = publicados[0]
    assert evt.eventType == EventType.PAYMENT_CONFIRMED
    assert evt.data["studentId"] == "STU-6"
    assert evt.data["paymentId"] == pago
    assert evt.data["amount"] > 0


def test_listar_estudiantes_devuelve_estructura_correcta(client):
    proyectar_estudiante("STU-7")
    estudiantes = client.get("/students").json()
    assert any(e["id"] == "STU-7" for e in estudiantes)
    stu = next(e for e in estudiantes if e["id"] == "STU-7")
    assert "payments" in stu
    assert isinstance(stu["payments"], list)


def test_confirmar_pago_inexistente_da_404(client):
    assert client.post("/payments/NOPE/confirm").status_code == 404


def test_filtrar_pagos_por_estado(client):
    proyectar_estudiante("STU-4")
    pendientes = client.get("/payments?status=PENDIENTE").json()
    assert all(p["status"] == "PENDIENTE" for p in pendientes)
    assert len(client.get("/payments").json()) >= 1


def test_consumidor_idempotente(client):
    event = Event.create(
        EventType.STUDENT_ENROLLED,
        {"studentId": "STU-5", "fullName": "X", "schoolId": "S", "grade": "8vo", "period": "2026-1"},
    )
    consumer.handle_event(event)
    consumer.handle_event(event)
    assert len(client.get("/students/STU-5").json()["payments"]) == 1


def test_consumidor_ignora_otros_eventos(client):
    consumer.handle_event(Event.create(EventType.PAYMENT_CONFIRMED, {"studentId": "X"}))
    assert client.get("/students/X").status_code == 404


def test_init_db_y_seed():
    database.init_db()
    seed.seed_data()
    seed.seed_data()
