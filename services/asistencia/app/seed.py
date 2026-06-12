"""Datos semilla del Servicio de Asistencia/Bienestar.

Asegura que exista al menos un estudiante proyectado para poder registrar
asistencia o incidentes en la demostracion sin depender de otro servicio.
"""
import logging

from .database import SessionLocal
from .models import StudentRef

logger = logging.getLogger("asistencia.seed")


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(StudentRef).count() > 0:
            return
        db.add(
            StudentRef(
                id="STU-0001",
                full_name="Ana Maria Torres",
                school_id="SCH-001",
                grade="8vo EGB",
            )
        )
        db.commit()
        logger.info("Datos semilla del Servicio de Asistencia cargados")
    finally:
        db.close()
