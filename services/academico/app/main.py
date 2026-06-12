"""Servicio Academico — estudiantes y matriculas.

Publica el evento StudentEnrolled y consume PaymentConfirmed.
"""
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from shared.events import Event, EventType
from shared.messaging import publish_event

from .consumer import start_consumer_in_background
from .database import get_db, init_db
from .models import Enrollment, Student, StudentEvent
from .schemas import (
    EnrollmentCreate,
    EnrollmentOut,
    StudentCreate,
    StudentDetail,
    StudentEventOut,
    StudentOut,
)
from .seed import seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("academico")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    start_consumer_in_background()
    yield


app = FastAPI(
    title="CampusConnect 360 — Servicio Academico",
    description="Gestion de estudiantes y matriculas. Publica StudentEnrolled.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "academico"}


@app.post("/students", response_model=StudentOut, status_code=201, tags=["estudiantes"])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if db.query(Student).filter_by(document_id=payload.document_id).first():
        raise HTTPException(409, "Ya existe un estudiante con ese documento")
    student = Student(id=f"STU-{uuid.uuid4().hex[:8]}", **payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students", response_model=list[StudentOut], tags=["estudiantes"])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.created_at.desc()).all()


@app.get("/students/{student_id}", response_model=StudentDetail, tags=["estudiantes"])
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado")
    return student


@app.get(
    "/students/{student_id}/events",
    response_model=list[StudentEventOut],
    tags=["estudiantes"],
)
def get_student_events(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado")
    return (
        db.query(StudentEvent)
        .filter_by(student_id=student_id)
        .order_by(StudentEvent.occurred_at.desc())
        .all()
    )


@app.post("/enrollments", response_model=EnrollmentOut, status_code=201, tags=["matriculas"])
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    """Crea una matricula y publica el evento StudentEnrolled."""
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado")

    enrollment = Enrollment(
        id=f"ENR-{uuid.uuid4().hex[:8]}",
        student_id=payload.student_id,
        period=payload.period,
    )
    db.add(enrollment)

    # Publica el evento de negocio (Event Message + Publish/Subscribe).
    event = Event.create(
        EventType.STUDENT_ENROLLED,
        data={
            "studentId": student.id,
            "fullName": student.full_name,
            "schoolId": student.school_id,
            "grade": student.grade,
            "enrollmentId": enrollment.id,
            "period": enrollment.period,
        },
    )
    db.add(
        StudentEvent(
            student_id=student.id,
            event_type=event.eventType,
            correlation_id=event.correlationId,
            summary=f"Matricula {enrollment.id} periodo {enrollment.period}",
        )
    )
    db.commit()
    db.refresh(enrollment)

    publish_event(event)
    return enrollment
