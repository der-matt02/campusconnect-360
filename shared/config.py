"""Configuracion comun leida desde variables de entorno."""
import os


class MessagingConfig:
    """Parametros de conexion y topologia de RabbitMQ."""

    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "campus")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "campus_secret")

    # Exchange principal de eventos (tipo topic) y exchange de mensajes muertos.
    EVENTS_EXCHANGE = os.getenv("EVENTS_EXCHANGE", "campusconnect.events")
    DLX_EXCHANGE = os.getenv("DLX_EXCHANGE", "campusconnect.dlx")


class SecurityConfig:
    """Parametros de JWT compartidos por Gateway y servicios."""

    JWT_SECRET = os.getenv("JWT_SECRET", "cambia-este-secreto-en-produccion")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
