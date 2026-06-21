"""Pruebas de shared.messaging usando un pika simulado (sin broker real)."""
import pytest

import shared.messaging as m
from shared.events import Event, EventType


class FakeMethod:
    def __init__(self, delivery_tag=1):
        self.delivery_tag = delivery_tag


class FakeChannel:
    def __init__(self):
        self.acks = []
        self.nacks = []
        self.published = []
        self.declared_exchanges = []
        self.declared_queues = []
        self.consuming = False

    def exchange_declare(self, exchange, **kw):
        self.declared_exchanges.append(exchange)

    def queue_declare(self, queue, **kw):
        self.declared_queues.append(queue)

    def queue_bind(self, **kw):
        pass

    def basic_qos(self, **kw):
        pass

    def basic_consume(self, queue, on_message_callback):
        self.callback = on_message_callback

    def basic_publish(self, exchange, routing_key, body, properties=None):
        self.published.append((exchange, routing_key, body))

    def basic_ack(self, delivery_tag):
        self.acks.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue=False):
        self.nacks.append((delivery_tag, requeue))

    def start_consuming(self):
        self.consuming = True


class FakeConnection:
    def __init__(self, channel):
        self._channel = channel
        self.closed = False

    def channel(self):
        return self._channel

    def close(self):
        self.closed = True


@pytest.fixture
def fake_channel(monkeypatch):
    channel = FakeChannel()
    monkeypatch.setattr(m.pika, "BlockingConnection", lambda *a, **k: FakeConnection(channel))
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)
    return channel


def test_publish_event(fake_channel):
    event = Event.create(EventType.STUDENT_ENROLLED, {"studentId": "STU-1"})
    m.publish_event(event)
    assert len(fake_channel.published) == 1
    exchange, routing_key, _ = fake_channel.published[0]
    assert routing_key == EventType.STUDENT_ENROLLED


def test_connect_with_retry_reintenta(monkeypatch):
    intentos = {"n": 0}
    channel = FakeChannel()

    def flaky(*a, **k):
        intentos["n"] += 1
        if intentos["n"] < 2:
            raise m.AMQPConnectionError("aun no")
        return FakeConnection(channel)

    monkeypatch.setattr(m.pika, "BlockingConnection", flaky)
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)
    conn = m.connect_with_retry()
    assert isinstance(conn, FakeConnection)
    assert intentos["n"] == 2


def test_consumer_declara_y_consume(fake_channel):
    consumer = m.EventConsumer("notificaciones", [EventType.STUDENT_ENROLLED], lambda e: None)
    consumer.start()
    assert "campusconnect.events" in fake_channel.declared_exchanges
    assert "notificaciones.events" in fake_channel.declared_queues
    assert "notificaciones.events.dlq" in fake_channel.declared_queues
    assert fake_channel.consuming is True


def _build_consumer(handler):
    return m.EventConsumer("svc", [EventType.STUDENT_ENROLLED], handler)


def test_on_message_exito_hace_ack(fake_channel):
    event = Event.create(EventType.STUDENT_ENROLLED, {})
    consumer = _build_consumer(lambda e: None)
    consumer._on_message(fake_channel, FakeMethod(7), None, event.model_dump_json())
    assert fake_channel.acks == [7]


def test_on_message_falla_va_a_dlq(fake_channel):
    def boom(_event):
        raise RuntimeError("fallo")

    event = Event.create(EventType.STUDENT_ENROLLED, {})
    consumer = _build_consumer(boom)
    consumer._on_message(fake_channel, FakeMethod(8), None, event.model_dump_json())
    # Tras agotar reintentos, nack sin re-encolar (va a la DLQ).
    assert fake_channel.nacks == [(8, False)]


def test_on_message_invalido_va_a_dlq(fake_channel):
    consumer = _build_consumer(lambda e: None)
    consumer._on_message(fake_channel, FakeMethod(9), None, b"esto no es json")
    assert fake_channel.nacks == [(9, False)]


def test_connect_with_retry_agota_intentos(monkeypatch):
    monkeypatch.setattr(m.pika, "BlockingConnection", lambda *a, **k: (_ for _ in ()).throw(m.AMQPConnectionError("siempre cae")))
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)
    with pytest.raises(m.AMQPConnectionError):
        m.connect_with_retry(max_attempts=3)


def test_on_message_handler_recupera_en_segundo_intento(fake_channel):
    intentos = {"n": 0}

    def flaky(event):
        intentos["n"] += 1
        if intentos["n"] < 2:
            raise RuntimeError("fallo transitorio")

    event = Event.create(EventType.PAYMENT_CONFIRMED, {})
    consumer = _build_consumer(flaky)
    consumer._on_message(fake_channel, FakeMethod(10), None, event.model_dump_json())
    assert fake_channel.acks == [10]
    assert intentos["n"] == 2
