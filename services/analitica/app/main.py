"""Servicio de Analitica — lado de lectura del CQRS.

Calcula los indicadores consolidados del dashboard directivo agregando sobre
event_log, y expone el historial de eventos procesados (trazabilidad).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.events import EventType

from .consumer import start_consumer_in_background
from .database import get_db, init_db
from .models import EventLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analitica")


@asynccontextmanager
async def lifespan(app: FastAPI):
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


def _count(db: Session, event_type: str) -> int:
    return db.query(EventLog).filter_by(event_type=event_type).count()


@app.get("/dashboard", tags=["analitica"])
def dashboard(db: Session = Depends(get_db)):
    """Indicadores consolidados del ecosistema (datos reales proyectados)."""
    matriculados = _count(db, EventType.STUDENT_ENROLLED)
    pagos_confirmados = _count(db, EventType.PAYMENT_CONFIRMED)
    asistencias = _count(db, EventType.ATTENDANCE_RECORDED)
    incidentes = _count(db, EventType.INCIDENT_REPORTED)
    eventos_procesados = db.query(EventLog).count()

    # Monto total confirmado, sumando el campo amount del payload.
    monto_confirmado = 0.0
    for row in db.query(EventLog).filter_by(event_type=EventType.PAYMENT_CONFIRMED).all():
        monto_confirmado += float(row.payload.get("amount", 0) or 0)

    # Cada matricula genera una deuda; los pendientes son los aun no confirmados.
    pagos_pendientes = max(matriculados - pagos_confirmados, 0)

    return {
        "matriculados": matriculados,
        "pagosConfirmados": pagos_confirmados,
        "pagosPendientes": pagos_pendientes,
        "montoConfirmado": round(monto_confirmado, 2),
        "asistencias": asistencias,
        "incidentes": incidentes,
        "eventosProcesados": eventos_procesados,
        "estado": "OK",
    }


@app.get("/events", tags=["analitica"])
def recent_events(limit: int = 20, db: Session = Depends(get_db)):
    """Ultimos eventos procesados (evidencia de trazabilidad)."""
    rows = (
        db.query(EventLog)
        .order_by(EventLog.occurred_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "eventId": r.event_id,
            "eventType": r.event_type,
            "studentId": r.student_id,
            "correlationId": r.correlation_id,
            "occurredAt": r.occurred_at,
        }
        for r in rows
    ]


@app.get("/events/by-type", tags=["analitica"])
def events_by_type(db: Session = Depends(get_db)):
    """Conteo de eventos agrupado por tipo."""
    rows = (
        db.query(EventLog.event_type, func.count(EventLog.id))
        .group_by(EventLog.event_type)
        .all()
    )
    return {event_type: count for event_type, count in rows}
