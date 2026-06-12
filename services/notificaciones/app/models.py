"""Modelos del Servicio de Notificaciones."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.idempotency import ProcessedEventMixin

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessedEvent(Base, ProcessedEventMixin):
    """Control de idempotencia del servicio (Idempotent Receiver)."""

    __tablename__ = "processed_events"


class Notification(Base):
    """Notificacion simulada generada a partir de un evento de negocio."""

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    student_id: Mapped[str] = mapped_column(String, nullable=True)
    channel: Mapped[str] = mapped_column(String, default="SIMULADO")
    message: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ENVIADA")  # ENVIADA | FALLIDA
    correlation_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
