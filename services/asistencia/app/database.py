"""Conexion y `Base` declarativo del Servicio de Asistencia/Bienestar."""
import os

from shared.db import make_engine, make_session_factory, new_base

DB_NAME = os.getenv("DB_ASISTENCIA", "asistencia_db")

Base = new_base()

engine = make_engine(DB_NAME)
SessionLocal = make_session_factory(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
