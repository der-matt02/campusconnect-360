"""Modelos de datos del Servicio Academico."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.idempotency import ProcessedEventMixin

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessedEvent(Base, ProcessedEventMixin):
    """Control de idempotencia del servicio (Idempotent Receiver)."""

    __tablename__ = "processed_events"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    document_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=True)
    school_id: Mapped[str] = mapped_column(String, nullable=False)
    grade: Mapped[str] = mapped_column(String, nullable=False)
    # Estado financiero consolidado (se actualiza al consumir PaymentConfirmed).
    financial_status: Mapped[str] = mapped_column(String, default="PENDIENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    events: Mapped[list["StudentEvent"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ACTIVA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="enrollments")


class StudentEvent(Base):
    """Historial basico de eventos asociados a un estudiante (trazabilidad)."""

    __tablename__ = "student_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="events")
