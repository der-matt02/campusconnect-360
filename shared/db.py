"""Fabrica de conexiones a PostgreSQL para los microservicios.

Cada servicio usa su propia base de datos (persistencia separada por servicio).
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def build_database_url(db_name: str) -> str:
    user = os.getenv("POSTGRES_USER", "campus")
    password = os.getenv("POSTGRES_PASSWORD", "campus_secret")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


def make_engine(db_name: str):
    """Crea el engine de SQLAlchemy reintentando hasta que la BD este lista."""
    return create_engine(
        build_database_url(db_name),
        pool_pre_ping=True,
        future=True,
    )


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
