"""Patron Repository: acceso a datos del Servicio de Asistencia/Bienestar."""
from __future__ import annotations

from sqlalchemy.orm import Session

from shared.utils import new_id

from .models import Attendance, Incident, StudentRef


def list_students(db: Session) -> list[StudentRef]:
    return db.query(StudentRef).order_by(StudentRef.created_at.desc()).all()


def get_student(db: Session, student_id: str) -> StudentRef | None:
    return db.get(StudentRef, student_id)


def ensure_student(db: Session, student_id: str, full_name: str, school_id: str, grade: str) -> None:
    if db.get(StudentRef, student_id) is None:
        db.add(StudentRef(id=student_id, full_name=full_name, school_id=school_id, grade=grade))


def add_attendance(db: Session, student_id: str, date: str, status: str) -> Attendance:
    record = Attendance(id=new_id("ATT"), student_id=student_id, date=date, status=status.upper())
    db.add(record)
    return record


def add_incident(db: Session, student_id: str, severity: str, description: str) -> Incident:
    incident = Incident(
        id=new_id("INC"), student_id=student_id, severity=severity.upper(), description=description
    )
    db.add(incident)
    return incident


def list_attendance(db: Session, student_id: str) -> list[Attendance]:
    return (
        db.query(Attendance)
        .filter_by(student_id=student_id)
        .order_by(Attendance.created_at.desc())
        .all()
    )


def list_incidents(db: Session, student_id: str) -> list[Incident]:
    return (
        db.query(Incident)
        .filter_by(student_id=student_id)
        .order_by(Incident.created_at.desc())
        .all()
    )
