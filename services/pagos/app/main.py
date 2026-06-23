"""Servicio de Pagos — deudas y confirmacion de pagos.

Consume StudentEnrolled (genera deuda de matricula) y publica PaymentConfirmed.
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from shared.enums import PaymentStatus
from shared.events import Event, EventType
from shared.messaging import publish_event

from . import repository as repo
from .consumer import start_consumer_in_background
from .database import get_db, init_db
from .schemas import DebtCreate, PaymentOut, StudentWithPayments
from .seed import seed_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pagos")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - glue de arranque (requiere infra)
    init_db()
    seed_data()
    start_consumer_in_background()
    yield


app = FastAPI(
    title="CampusConnect 360 — Servicio de Pagos",
    description="Gestion de deudas y pagos. Publica PaymentConfirmed.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "pagos"}


@app.get("/students", response_model=list[StudentWithPayments], tags=["estudiantes"])
def list_students(db: Session = Depends(get_db)):
    """Estudiantes matriculados con su detalle de pagos."""
    return repo.list_students(db)


@app.get("/students/{student_id}", response_model=StudentWithPayments, tags=["estudiantes"])
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = repo.get_student(db, student_id)
    if student is None:
        raise HTTPException(404, "Estudiante no encontrado en el modulo de pagos")
    return student


@app.post("/debts", response_model=PaymentOut, status_code=201, tags=["pagos"])
def create_debt(payload: DebtCreate, db: Session = Depends(get_db)):
    """Registra una obligacion de pago (o simula una deuda)."""
    if repo.get_student(db, payload.student_id) is None:
        raise HTTPException(404, "Estudiante no encontrado en el modulo de pagos")
    payment = repo.add_payment(db, payload.student_id, payload.concept, payload.amount)
    db.commit()
    db.refresh(payment)
    return payment


@app.get("/payments", response_model=list[PaymentOut], tags=["pagos"])
def list_payments(
    status: Optional[str] = Query(None, description="PENDIENTE o CONFIRMADO"),
    db: Session = Depends(get_db),
):
    return repo.list_payments(db, status)


@app.post("/payments/{payment_id}/confirm", response_model=PaymentOut, tags=["pagos"])
def confirm_payment(payment_id: str, db: Session = Depends(get_db)):
    """Confirma un pago y publica el evento PaymentConfirmed."""
    payment = repo.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(404, "Pago no encontrado")
    if payment.status == PaymentStatus.CONFIRMADO:
        raise HTTPException(409, "El pago ya estaba confirmado")

    repo.mark_confirmed(db, payment)
    event = Event.create(
        EventType.PAYMENT_CONFIRMED,
        data={
            "paymentId": payment.id,
            "studentId": payment.student_id,
            "concept": payment.concept,
            "amount": payment.amount,
        },
    )
    db.commit()
    db.refresh(payment)

    publish_event(event)
    return payment
