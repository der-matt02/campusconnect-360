"""Servicio Academico — estudiantes y matriculas.

Publica el evento StudentEnrolled y consume PaymentConfirmed.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from shared.events import Event, EventType
from shared.messaging import publish_event

from . import repository as repo
from .consumer import start_consumer_in_background
from .database import get_db, init_db
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
    if repo.find_by_document(db, payload.document_id):
        raise HTTPException(409, "Ya existe un estudiante con ese documento")
    return repo.create_student(db, payload.model_dump())


@app.get("/students", response_model=list[StudentOut], tags=["estudiantes"])
def list_students(db: Session = Depends(get_db)):
    return repo.list_students(db)


@app.get("/students/{student_id}", response_model=StudentDetail, tags=["estudiantes"])
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = repo.get_student(db, student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado")
    return student


@app.get(
    "/students/{student_id}/events",
    response_model=list[StudentEventOut],
    tags=["estudiantes"],
)
def get_student_events(student_id: str, db: Session = Depends(get_db)):
    if repo.get_student(db, student_id) is None:
        raise HTTPException(404, "Estudiante no encontrado")
    return repo.list_events(db, student_id)


@app.post("/enrollments", response_model=EnrollmentOut, status_code=201, tags=["matriculas"])
def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    """Crea una matricula y publica el evento StudentEnrolled."""
    student = repo.get_student(db, payload.student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado")

    enrollment = repo.create_enrollment(db, payload.student_id, payload.period)

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
    repo.add_event(
        db,
        student_id=student.id,
        event_type=event.eventType,
        correlation_id=event.correlationId,
        summary=f"Matricula {enrollment.id} periodo {enrollment.period}",
    )
    db.commit()
    db.refresh(enrollment)

    publish_event(event)
    return enrollment
