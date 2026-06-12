"""Modelos del Servicio de Pagos.

El servicio mantiene una copia local minima de los estudiantes (proyeccion
alimentada por el evento StudentEnrolled), de modo que no depende en linea del
Servicio Academico para listar pagos.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.idempotency import ProcessedEventMixin

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessedEvent(Base, ProcessedEventMixin):
    """Control de idempotencia del servicio (Idempotent Receiver)."""

    __tablename__ = "processed_events"


class StudentRef(Base):
    """Proyeccion local del estudiante (datos minimos)."""

    __tablename__ = "student_refs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    school_id: Mapped[str] = mapped_column(String, nullable=True)
    grade: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    payments: Mapped[list["Payment"]] = relationship(back_populates="student")


class Payment(Base):
    """Obligacion de pago / deuda de un estudiante."""

    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_refs.id"), nullable=False)
    concept: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDIENTE")  # PENDIENTE | CONFIRMADO
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentRef"] = relationship(back_populates="payments")
