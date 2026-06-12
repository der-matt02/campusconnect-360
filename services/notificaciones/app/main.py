"""Servicio de Notificaciones.

Consume los eventos de negocio y genera notificaciones simuladas. Expone
endpoints para consultar notificaciones y para demostrar el escenario de
resiliencia (fallo controlado + DLQ + reprocesamiento).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import repository as repo
from .consumer import chaos, start_consumer_in_background
from .database import get_db, init_db
from .dlq import dlq_depth, reprocess_dlq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notificaciones")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_consumer_in_background()
    yield


app = FastAPI(
    title="CampusConnect 360 — Servicio de Notificaciones",
    description="Consume eventos (Pub/Sub) y genera notificaciones. Maneja DLQ y resiliencia.",
    version="1.0.0",
    lifespan=lifespan,
)


class ChaosRequest(BaseModel):
    enabled: bool


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "notificaciones"}


@app.get("/notifications", tags=["notificaciones"])
def list_notifications(db: Session = Depends(get_db)):
    return [
        {
            "id": n.id,
            "eventType": n.event_type,
            "studentId": n.student_id,
            "message": n.message,
            "status": n.status,
            "createdAt": n.created_at,
        }
        for n in repo.list_notifications(db)
    ]


@app.get("/stats", tags=["notificaciones"])
def stats(db: Session = Depends(get_db)):
    """Resumen para el dashboard: enviadas y mensajes fallidos (en la DLQ)."""
    return {
        "enviadas": repo.count_sent(db),
        "fallidas": dlq_depth(),
        "chaos": chaos["enabled"],
    }


@app.get("/dlq", tags=["resiliencia"])
def get_dlq():
    """Cantidad de mensajes en la Dead Letter Queue."""
    return {"dlqDepth": dlq_depth()}


@app.post("/dlq/reprocess", tags=["resiliencia"])
def post_reprocess_dlq():
    """Reprocesa los mensajes fallidos de la DLQ (reprocesamiento manual)."""
    return reprocess_dlq()


@app.get("/chaos", tags=["resiliencia"])
def get_chaos():
    return {"enabled": chaos["enabled"]}


@app.post("/chaos", tags=["resiliencia"])
def set_chaos(req: ChaosRequest):
    """Activa/desactiva el fallo simulado para demostrar reintentos + DLQ."""
    chaos["enabled"] = req.enabled
    logger.warning("Modo chaos %s", "ACTIVADO" if req.enabled else "DESACTIVADO")
    return {"enabled": chaos["enabled"]}
