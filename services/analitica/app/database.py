"""Conexion a la base de datos del Servicio de Analitica (modelo de lectura CQRS)."""
import os

from shared.db import Base, make_engine, make_session_factory

DB_NAME = os.getenv("DB_ANALITICA", "analitica_db")

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
