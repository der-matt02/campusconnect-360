"""Patron Repository: acceso al modelo de lectura (CQRS) del Servicio de Analitica."""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.events import EventType

from .models import EventLog


def add_event(db: Session, *, event_id: str, event_type: str, student_id: str, correlation_id: str, payload: dict) -> None:
    db.add(
        EventLog(
            event_id=event_id,
            event_type=event_type,
            student_id=student_id,
            correlation_id=correlation_id,
            payload=payload,
        )
    )


def count_by_type(db: Session, event_type: str) -> int:
    return db.query(EventLog).filter_by(event_type=event_type).count()


def count_all(db: Session) -> int:
    return db.query(EventLog).count()


def sum_confirmed_amount(db: Session) -> float:
    total = 0.0
    rows = db.query(EventLog).filter_by(event_type=EventType.PAYMENT_CONFIRMED).all()
    for row in rows:
        total += float(row.payload.get("amount", 0) or 0)
    return round(total, 2)


def recent_events(db: Session, limit: int = 20) -> list[EventLog]:
    return db.query(EventLog).order_by(EventLog.occurred_at.desc()).limit(limit).all()


def events_grouped_by_type(db: Session) -> dict:
    rows = (
        db.query(EventLog.event_type, func.count(EventLog.id))
        .group_by(EventLog.event_type)
        .all()
    )
    return {event_type: count for event_type, count in rows}
