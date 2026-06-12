"""Conexion a la base de datos del Servicio Academico."""
import os

from shared.db import Base, make_engine, make_session_factory

DB_NAME = os.getenv("DB_ACADEMICO", "academico_db")

engine = make_engine(DB_NAME)
SessionLocal = make_session_factory(engine)


def get_db():
    """Dependencia de FastAPI: entrega una sesion y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas si no existen."""
    # Importa los modelos para registrarlos en el metadata antes de crear.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
