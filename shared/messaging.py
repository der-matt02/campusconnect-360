"""Utilidades de mensajeria sobre RabbitMQ (patron Message Channel).

Provee:
  - setup_topology:   declara el exchange de eventos y el exchange de mensajes
                      muertos (Dead Letter Exchange).
  - publish_event:    publica un evento de negocio (Publish/Subscribe).
  - EventConsumer:    consumidor con reintentos y Dead Letter Queue (DLQ).

La estrategia de resiliencia es:
  1. El handler procesa el mensaje.
  2. Si falla, se reintenta en proceso hasta MAX_RETRIES veces.
  3. Si sigue fallando, el mensaje se rechaza sin re-encolar (basic_nack) y
     RabbitMQ lo enruta automaticamente a la Dead Letter Queue del consumidor.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Callable, Iterable

import pika
from pika.exceptions import AMQPConnectionError

from .config import MessagingConfig
from .events import Event

logger = logging.getLogger("messaging")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def _connection_params() -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(
        MessagingConfig.RABBITMQ_USER, MessagingConfig.RABBITMQ_PASSWORD
    )
    return pika.ConnectionParameters(
        host=MessagingConfig.RABBITMQ_HOST,
        port=MessagingConfig.RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
    )


def connect_with_retry(max_attempts: int = 30, delay: int = 2) -> pika.BlockingConnection:
    """Abre una conexion a RabbitMQ reintentando hasta que el broker este listo."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return pika.BlockingConnection(_connection_params())
        except AMQPConnectionError:
            if attempt >= max_attempts:
                raise
            logger.warning(
                "RabbitMQ no disponible (intento %s/%s); reintentando en %ss",
                attempt, max_attempts, delay,
            )
            time.sleep(delay)


def setup_topology(channel) -> None:
    """Declara el exchange principal de eventos y el de mensajes muertos."""
    # Exchange de eventos de negocio (topic -> routing key = eventType).
    channel.exchange_declare(
        exchange=MessagingConfig.EVENTS_EXCHANGE,
        exchange_type="topic",
        durable=True,
    )
    # Dead Letter Exchange para mensajes que no se pudieron procesar.
    channel.exchange_declare(
        exchange=MessagingConfig.DLX_EXCHANGE,
        exchange_type="topic",
        durable=True,
    )


def publish_event(event: Event) -> None:
    """Publica un evento de negocio en el exchange de eventos.

    Patron Publish/Subscribe: la routing key es el tipo de evento, y cualquier
    consumidor suscrito a ese patron recibira una copia.
    """
    connection = connect_with_retry()
    try:
        channel = connection.channel()
        setup_topology(channel)
        channel.basic_publish(
            exchange=MessagingConfig.EVENTS_EXCHANGE,
            routing_key=event.eventType,
            body=event.model_dump_json(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # mensaje persistente
                message_id=event.eventId,
                correlation_id=event.correlationId,
                type=event.eventType,
            ),
        )
        logger.info(
            "Evento publicado: %s (%s) corr=%s",
            event.eventType, event.eventId, event.correlationId,
        )
    finally:
        connection.close()


class EventConsumer:
    """Consumidor de eventos con DLQ y reintentos.

    Parametros:
      service_name:   nombre del servicio (define el nombre de la cola).
      routing_keys:   tipos de evento a los que se suscribe.
      handler:        funcion que procesa cada Event. Si lanza excepcion, se
                      reintenta y, si persiste, el mensaje va a la DLQ.
    """

    def __init__(
        self,
        service_name: str,
        routing_keys: Iterable[str],
        handler: Callable[[Event], None],
    ) -> None:
        self.service_name = service_name
        self.routing_keys = list(routing_keys)
        self.handler = handler
        self.queue_name = f"{service_name}.events"
        self.dlq_name = f"{service_name}.events.dlq"

    def _declare(self, channel) -> None:
        setup_topology(channel)

        # Dead Letter Queue: aqui aterrizan los mensajes que fallan.
        channel.queue_declare(queue=self.dlq_name, durable=True)
        channel.queue_bind(
            queue=self.dlq_name,
            exchange=MessagingConfig.DLX_EXCHANGE,
            routing_key=self.queue_name,
        )

        # Cola principal del servicio, con enrutamiento a la DLX al fallar.
        channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": MessagingConfig.DLX_EXCHANGE,
                "x-dead-letter-routing-key": self.queue_name,
            },
        )
        for key in self.routing_keys:
            channel.queue_bind(
                queue=self.queue_name,
                exchange=MessagingConfig.EVENTS_EXCHANGE,
                routing_key=key,
            )

    def _on_message(self, channel, method, properties, body) -> None:
        try:
            payload = json.loads(body)
            event = Event(**payload)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            # Mensaje con formato invalido -> directo a la DLQ.
            logger.error("Mensaje invalido enviado a DLQ: %s", exc)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.handler(event)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            except Exception as exc:  # noqa: BLE001 - se registra y reintenta
                logger.warning(
                    "Error procesando %s (intento %s/%s): %s",
                    event.eventType, attempt, MAX_RETRIES, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)

        # Se agotaron los reintentos -> a la Dead Letter Queue.
        logger.error(
            "Evento %s (%s) movido a DLQ tras %s intentos",
            event.eventType, event.eventId, MAX_RETRIES,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self) -> None:
        """Bucle bloqueante de consumo. Pensado para correr en un hilo."""
        connection = connect_with_retry()
        channel = connection.channel()
        self._declare(channel)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=self.queue_name, on_message_callback=self._on_message
        )
        logger.info(
            "Consumidor '%s' escuchando %s", self.service_name, self.routing_keys
        )
        channel.start_consuming()
