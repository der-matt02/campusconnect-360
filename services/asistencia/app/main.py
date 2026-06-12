"""Servicio de Asistencia/Bienestar.

Registra asistencia e incidentes y publica los eventos AttendanceRecorded e
IncidentReported. Consume StudentEnrolled para proyectar estudiantes.
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
    AttendanceCreate,
    AttendanceOut,
    IncidentCreate,
    IncidentOut,
    StudentOut,
)
from .seed import seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("asistencia")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - glue de arranque (requiere infra)
    init_db()
    seed_data()
    start_consumer_in_background()
    yield


app = FastAPI(
    title="CampusConnect 360 — Servicio de Asistencia/Bienestar",
    description="Registra asistencia e incidentes. Publica AttendanceRecorded e IncidentReported.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "asistencia"}


@app.get("/students", response_model=list[StudentOut], tags=["estudiantes"])
def list_students(db: Session = Depends(get_db)):
    return repo.list_students(db)


@app.post("/attendance", response_model=AttendanceOut, status_code=201, tags=["asistencia"])
def register_attendance(payload: AttendanceCreate, db: Session = Depends(get_db)):
    """Registra asistencia y publica AttendanceRecorded."""
    if repo.get_student(db, payload.student_id) is None:
        raise HTTPException(404, "Estudiante no encontrado en el modulo de asistencia")

    record = repo.add_attendance(db, payload.student_id, payload.date, payload.status)
    event = Event.create(
        EventType.ATTENDANCE_RECORDED,
        data={
            "attendanceId": record.id,
            "studentId": record.student_id,
            "date": record.date,
            "status": record.status,
        },
    )
    db.commit()
    db.refresh(record)

    publish_event(event)
    return record


@app.post("/incidents", response_model=IncidentOut, status_code=201, tags=["incidentes"])
def register_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Registra un incidente/novedad y publica IncidentReported."""
    if repo.get_student(db, payload.student_id) is None:
        raise HTTPException(404, "Estudiante no encontrado en el modulo de asistencia")

    incident = repo.add_incident(db, payload.student_id, payload.severity, payload.description)
    event = Event.create(
        EventType.INCIDENT_REPORTED,
        data={
            "incidentId": incident.id,
            "studentId": incident.student_id,
            "severity": incident.severity,
            "description": incident.description,
        },
    )
    db.commit()
    db.refresh(incident)

    publish_event(event)
    return incident


@app.get(
    "/students/{student_id}/attendance",
    response_model=list[AttendanceOut],
    tags=["asistencia"],
)
def student_attendance(student_id: str, db: Session = Depends(get_db)):
    return repo.list_attendance(db, student_id)


@app.get(
    "/students/{student_id}/incidents",
    response_model=list[IncidentOut],
    tags=["incidentes"],
)
def student_incidents(student_id: str, db: Session = Depends(get_db)):
    return repo.list_incidents(db, student_id)
