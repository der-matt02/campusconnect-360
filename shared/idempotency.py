"""Patron Idempotent Receiver.

Registra los eventos ya procesados para evitar reprocesar mensajes duplicados
(por reintentos o reentregas de RabbitMQ).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    consumer: Mapped[str] = mapped_column(String, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def already_processed(db, event_id: str, consumer: str) -> bool:
    """Indica si un evento ya fue procesado por este consumidor."""
    return (
        db.query(ProcessedEvent)
        .filter_by(event_id=event_id, consumer=consumer)
        .first()
        is not None
    )


def mark_processed(db, event_id: str, consumer: str) -> None:
    """Marca un evento como procesado por este consumidor."""
    db.add(ProcessedEvent(event_id=event_id, consumer=consumer))
