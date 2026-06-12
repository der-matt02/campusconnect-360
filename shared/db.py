"""Fabrica de conexiones a la base de datos para los microservicios.

Cada servicio usa su propia base de datos Y su propio `Base` declarativo
(esquema independiente por servicio), evitando acoplar el modelo de datos entre
microservicios.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


def new_base() -> type[DeclarativeBase]:
    """Crea un `Base` declarativo independiente para un servicio."""

    class Base(DeclarativeBase):
        pass

    return Base


def build_database_url(db_name: str) -> str:
    user = os.getenv("POSTGRES_USER", "campus")
    password = os.getenv("POSTGRES_PASSWORD", "campus_secret")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


def make_engine(db_name: str):
    """Crea el engine del servicio.

    Si `DATABASE_URL` esta definida (p. ej. SQLite en pruebas) se usa esa;
    de lo contrario se construye la URL de PostgreSQL del servicio.
    """
    url = os.getenv("DATABASE_URL") or build_database_url(db_name)
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    return create_engine(url, pool_pre_ping=True, future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
