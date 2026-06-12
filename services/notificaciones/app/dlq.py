"""Inspeccion y reprocesamiento de la Dead Letter Queue del servicio.

Permite ver cuantos mensajes fallidos hay y reprocesarlos manualmente
(mecanismo de resiliencia: reprocesamiento manual).
"""
import json
import logging

from shared.events import Event
from shared.messaging import connect_with_retry

from .consumer import CONSUMER_NAME, process_event

logger = logging.getLogger("notificaciones.dlq")

DLQ_NAME = f"{CONSUMER_NAME}.events.dlq"


def dlq_depth() -> int:
    """Cantidad de mensajes actualmente en la DLQ."""
    connection = connect_with_retry()
    try:
        channel = connection.channel()
        result = channel.queue_declare(queue=DLQ_NAME, durable=True, passive=True)
        return result.method.message_count
    finally:
        connection.close()


def reprocess_dlq(limit: int = 100) -> dict:
    """Reprocesa los mensajes de la DLQ reaplicando el handler.

    Devuelve un resumen con los reprocesados con exito y los que volvieron a fallar.
    """
    connection = connect_with_retry()
    reprocessed, failed = 0, 0
    try:
        channel = connection.channel()
        channel.queue_declare(queue=DLQ_NAME, durable=True, passive=True)
        for _ in range(limit):
            method, properties, body = channel.basic_get(queue=DLQ_NAME, auto_ack=False)
            if method is None:
                break  # no hay mas mensajes
            try:
                event = Event(**json.loads(body))
                process_event(event)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                reprocessed += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Mensaje sigue fallando; se devuelve a la DLQ: %s", exc)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                failed += 1
        return {"reprocessed": reprocessed, "still_failed": failed}
    finally:
        connection.close()
