"""Pruebas de la inspeccion y reprocesamiento de la DLQ (pika simulado)."""
import app.dlq as dlq

from shared.events import Event, EventType


class FakeMethod:
    delivery_tag = 1


class FakeChannel:
    def __init__(self, messages=None, depth=0):
        self.messages = list(messages or [])
        self.depth = depth
        self.acks = []
        self.nacks = []

    def queue_declare(self, queue, durable=True, passive=False):
        class Result:
            class method:
                message_count = self.depth
        return Result()

    def basic_get(self, queue, auto_ack=False):
        if self.messages:
            return (FakeMethod(), None, self.messages.pop(0))
        return (None, None, None)

    def basic_ack(self, delivery_tag):
        self.acks.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue=False):
        self.nacks.append(requeue)


class FakeConnection:
    def __init__(self, channel):
        self._channel = channel

    def channel(self):
        return self._channel

    def close(self):
        pass


def test_dlq_depth(monkeypatch):
    channel = FakeChannel(depth=3)
    monkeypatch.setattr(dlq, "connect_with_retry", lambda: FakeConnection(channel))
    assert dlq.dlq_depth() == 3


def test_reprocess_dlq_exitoso(monkeypatch):
    event = Event.create(EventType.STUDENT_ENROLLED, {"studentId": "STU-1", "fullName": "Ana", "enrollmentId": "ENR-1", "period": "2026-1"})
    channel = FakeChannel(messages=[event.model_dump_json()])
    monkeypatch.setattr(dlq, "connect_with_retry", lambda: FakeConnection(channel))
    result = dlq.reprocess_dlq()
    assert result["reprocessed"] == 1
    assert result["still_failed"] == 0
    assert channel.acks == [1]


def test_reprocess_dlq_mensaje_invalido(monkeypatch):
    channel = FakeChannel(messages=[b"no es json"])
    monkeypatch.setattr(dlq, "connect_with_retry", lambda: FakeConnection(channel))
    result = dlq.reprocess_dlq()
    assert result["still_failed"] == 1
    assert channel.nacks == [True]
