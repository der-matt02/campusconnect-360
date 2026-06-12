"""Utilidad para construir consumidores idempotentes (DRY).

Encapsula el patron repetido en todos los servicios:
  abrir sesion -> verificar idempotencia -> ejecutar logica de negocio ->
  marcar procesado -> commit (o rollback ante error).
"""
from __future__ import annotations

import logging
from typing import Callable

from .events import Event
from .idempotency import already_processed, mark_processed

logger = logging.getLogger("consuming")


def make_idempotent_handler(
    *,
    session_factory: Callable,
    consumer_name: str,
    processed_model,
    on_event: Callable[[object, Event], None],
) -> Callable[[Event], None]:
    """Devuelve un handler que aplica idempotencia y manejo de sesion.

    `on_event(db, event)` contiene solo la logica de negocio del servicio.
    """

    def handler(event: Event) -> None:
        db = session_factory()
        try:
            if already_processed(db, processed_model, event.eventId, consumer_name):
                logger.info("Evento %s ya procesado por %s; se ignora", event.eventId, consumer_name)
                return
            on_event(db, event)
            mark_processed(db, processed_model, event.eventId, consumer_name)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return handler
