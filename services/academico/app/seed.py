"""Datos semilla del Servicio Academico."""
import logging

from .database import SessionLocal
from .models import Student

logger = logging.getLogger("academico.seed")

SEED_STUDENTS = [
    {
        "id": "STU-0001",
        "full_name": "Ana Maria Torres",
        "document_id": "1700000001",
        "email": "ana.torres@example.edu",
        "school_id": "SCH-001",
        "grade": "8vo EGB",
    },
    {
        "id": "STU-0002",
        "full_name": "Carlos Andres Lopez",
        "document_id": "1700000002",
        "email": "carlos.lopez@example.edu",
        "school_id": "SCH-001",
        "grade": "9no EGB",
    },
]


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0:
            return
        for data in SEED_STUDENTS:
            db.add(Student(**data))
        db.commit()
        logger.info("Datos semilla del Servicio Academico cargados")
    finally:
        db.close()
