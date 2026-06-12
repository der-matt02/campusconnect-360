"""Patron Repository: acceso a datos del Servicio de Notificaciones."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from .models import Notification


def add_notification(
    db: Session, *, event_id: str, event_type: str, student_id: str, message: str, correlation_id: str
) -> Notification:
    notification = Notification(
        id=f"NOT-{uuid.uuid4().hex[:8]}",
        event_id=event_id,
        event_type=event_type,
        student_id=student_id,
        message=message,
        status="ENVIADA",
        correlation_id=correlation_id,
    )
    db.add(notification)
    return notification


def list_notifications(db: Session) -> list[Notification]:
    return db.query(Notification).order_by(Notification.created_at.desc()).all()


def count_sent(db: Session) -> int:
    return db.query(Notification).filter_by(status="ENVIADA").count()
