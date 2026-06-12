"""Servicio de Analitica — lado de lectura del CQRS.

Calcula los indicadores consolidados del dashboard directivo agregando sobre
event_log, y expone el historial de eventos procesados (trazabilidad).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from shared.events import EventType

from . import repository as repo
from .consumer import start_consumer_in_background
from .database import get_db, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analitica")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - glue de arranque (requiere infra)
    init_db()
    start_consumer_in_background()
    yield


app = FastAPI(
    title="CampusConnect 360 — Servicio de Analitica",
    description="Vista de lectura (CQRS) que alimenta el dashboard directivo.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "analitica"}


@app.get("/dashboard", tags=["analitica"])
def dashboard(db: Session = Depends(get_db)):
    """Indicadores consolidados del ecosistema (datos reales proyectados)."""
    matriculados = repo.count_by_type(db, EventType.STUDENT_ENROLLED)
    pagos_confirmados = repo.count_by_type(db, EventType.PAYMENT_CONFIRMED)
    return {
        "matriculados": matriculados,
        "pagosConfirmados": pagos_confirmados,
        # Cada matricula genera una deuda; los pendientes son los aun no confirmados.
        "pagosPendientes": max(matriculados - pagos_confirmados, 0),
        "montoConfirmado": repo.sum_confirmed_amount(db),
        "asistencias": repo.count_by_type(db, EventType.ATTENDANCE_RECORDED),
        "incidentes": repo.count_by_type(db, EventType.INCIDENT_REPORTED),
        "eventosProcesados": repo.count_all(db),
        "estado": "OK",
    }


@app.get("/events", tags=["analitica"])
def recent_events(limit: int = 20, db: Session = Depends(get_db)):
    """Ultimos eventos procesados (evidencia de trazabilidad)."""
    return [
        {
            "eventId": r.event_id,
            "eventType": r.event_type,
            "studentId": r.student_id,
            "correlationId": r.correlation_id,
            "occurredAt": r.occurred_at,
        }
        for r in repo.recent_events(db, limit)
    ]


@app.get("/events/by-type", tags=["analitica"])
def events_by_type(db: Session = Depends(get_db)):
    """Conteo de eventos agrupado por tipo."""
    return repo.events_grouped_by_type(db)
