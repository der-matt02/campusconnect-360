"""Modelos del Servicio de Asistencia/Bienestar."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StudentRef(Base):
    """Proyeccion local del estudiante (alimentada por StudentEnrolled)."""

    __tablename__ = "student_refs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    school_id: Mapped[str] = mapped_column(String, nullable=True)
    grade: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Attendance(Base):
    """Registro de asistencia de un estudiante."""

    __tablename__ = "attendances"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_refs.id"), nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String, nullable=False)  # PRESENTE | AUSENTE | TARDE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Incident(Base):
    """Novedad o incidente reportado sobre un estudiante."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_refs.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)  # BAJA | MEDIA | ALTA
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
