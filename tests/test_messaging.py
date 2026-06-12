"""Pruebas de la configuracion del consumidor de eventos (sin conexion real)."""
from shared.events import EventType
from shared.messaging import MAX_RETRIES, EventConsumer


def _noop(_event):
    pass


def test_nombres_de_cola_y_dlq():
    consumer = EventConsumer("notificaciones", [EventType.STUDENT_ENROLLED], _noop)
    assert consumer.queue_name == "notificaciones.events"
    assert consumer.dlq_name == "notificaciones.events.dlq"


def test_routing_keys_se_conservan():
    keys = [EventType.STUDENT_ENROLLED, EventType.PAYMENT_CONFIRMED]
    consumer = EventConsumer("analitica", keys, _noop)
    assert consumer.routing_keys == keys


def test_hay_politica_de_reintentos():
    assert MAX_RETRIES >= 1
