"""Patron Repository: acceso a datos del Servicio Academico.

Aisla las consultas de SQLAlchemy del resto de la aplicacion (endpoints y
consumidores), facilitando pruebas y mantenimiento.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from shared.utils import new_id

from .models import Enrollment, Student, StudentEvent


def list_students(db: Session) -> list[Student]:
    return db.query(Student).order_by(Student.created_at.desc()).all()


def get_student(db: Session, student_id: str) -> Student | None:
    return db.get(Student, student_id)


def find_by_document(db: Session, document_id: str) -> Student | None:
    return db.query(Student).filter_by(document_id=document_id).first()


def create_student(db: Session, data: dict) -> Student:
    student = Student(id=new_id("STU"), **data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def create_enrollment(db: Session, student_id: str, period: str) -> Enrollment:
    enrollment = Enrollment(id=new_id("ENR"), student_id=student_id, period=period)
    db.add(enrollment)
    return enrollment


def add_event(db: Session, student_id: str, event_type: str, correlation_id: str, summary: str) -> None:
    db.add(
        StudentEvent(
            student_id=student_id,
            event_type=event_type,
            correlation_id=correlation_id,
            summary=summary,
        )
    )


def list_events(db: Session, student_id: str) -> list[StudentEvent]:
    return (
        db.query(StudentEvent)
        .filter_by(student_id=student_id)
        .order_by(StudentEvent.occurred_at.desc())
        .all()
    )
