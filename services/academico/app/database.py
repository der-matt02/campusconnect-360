"""Conexion y `Base` declarativo del Servicio Academico."""
import os

from shared.db import make_engine, make_session_factory, new_base

DB_NAME = os.getenv("DB_ACADEMICO", "academico_db")

# Cada servicio es dueno de su propio esquema (Base independiente).
Base = new_base()

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
    from . import models  # noqa: F401  (registra los modelos en el metadata)

    Base.metadata.create_all(bind=engine)
