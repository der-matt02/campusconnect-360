"""Contratos de eventos de negocio de CampusConnect 360.

Todo evento comparte una envoltura comun (Event Message pattern) con:
  - eventId:        identificador unico del evento
  - eventType:      tipo de evento
  - occurredAt:     fecha y hora de ocurrencia (UTC, ISO-8601)
  - correlationId:  identificador de correlacion / trazabilidad
  - data:           datos especificos del evento
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------- Tipos de evento (constantes) ----------
class EventType:
    STUDENT_ENROLLED = "StudentEnrolled"
    PAYMENT_CONFIRMED = "PaymentConfirmed"
    ATTENDANCE_RECORDED = "AttendanceRecorded"
    INCIDENT_REPORTED = "IncidentReported"
    STUDENT_STATUS_UPDATED = "StudentStatusUpdated"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class Event(BaseModel):
    """Envoltura comun de todos los eventos de negocio."""

    eventId: str = Field(default_factory=lambda: _new_id("evt"))
    eventType: str
    occurredAt: str = Field(default_factory=_now_iso)
    correlationId: str = Field(default_factory=lambda: _new_id("corr"))
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> "Event":
        """Crea un evento nuevo con identificadores y timestamp generados."""
        event = cls(eventType=event_type, data=data)
        if correlation_id:
            event.correlationId = correlation_id
        return event
