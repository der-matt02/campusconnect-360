"""Patron Repository: acceso a datos del Servicio de Pagos."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from shared.enums import PaymentStatus
from shared.utils import new_id

from .models import Payment, StudentRef


def list_students(db: Session) -> list[StudentRef]:
    return db.query(StudentRef).order_by(StudentRef.created_at.desc()).all()


def get_student(db: Session, student_id: str) -> StudentRef | None:
    return db.get(StudentRef, student_id)


def ensure_student(db: Session, student_id: str, full_name: str, school_id: str, grade: str) -> None:
    if db.get(StudentRef, student_id) is None:
        db.add(StudentRef(id=student_id, full_name=full_name, school_id=school_id, grade=grade))


def add_payment(db: Session, student_id: str, concept: str, amount: float) -> Payment:
    payment = Payment(id=new_id("PAY"), student_id=student_id, concept=concept, amount=amount)
    db.add(payment)
    return payment


def get_payment(db: Session, payment_id: str) -> Payment | None:
    return db.get(Payment, payment_id)


def list_payments(db: Session, status: str | None = None) -> list[Payment]:
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status.upper())
    return query.order_by(Payment.created_at.desc()).all()


def mark_confirmed(db: Session, payment: Payment) -> None:
    payment.status = PaymentStatus.CONFIRMADO
    payment.confirmed_at = datetime.now(timezone.utc)
