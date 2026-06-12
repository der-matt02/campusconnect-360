"""Datos semilla del Servicio de Pagos.

Nota: la mayoria de los estudiantes y deudas se generan dinamicamente al
consumir StudentEnrolled. Este seed solo asegura que exista un estudiante con
una deuda pendiente para poder demostrar la confirmacion de pago de inmediato.
"""
import logging
import uuid

from .database import SessionLocal
from .models import Payment, StudentRef

logger = logging.getLogger("pagos.seed")


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(StudentRef).count() > 0:
            return
        student = StudentRef(
            id="STU-0001",
            full_name="Ana Maria Torres",
            school_id="SCH-001",
            grade="8vo EGB",
        )
        db.add(student)
        db.add(
            Payment(
                id=f"PAY-{uuid.uuid4().hex[:8]}",
                student_id="STU-0001",
                concept="Matricula periodo 2026-1",
                amount=250.0,
                status="PENDIENTE",
            )
        )
        db.commit()
        logger.info("Datos semilla del Servicio de Pagos cargados")
    finally:
        db.close()
