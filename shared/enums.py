"""Enumeraciones de dominio compartidas entre los microservicios de CampusConnect 360."""
from enum import Enum


class PaymentStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"


class FinancialStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    AL_DIA = "AL_DIA"


class EnrollmentStatus(str, Enum):
    ACTIVA = "ACTIVA"


class AttendanceStatus(str, Enum):
    PRESENTE = "PRESENTE"
    AUSENTE = "AUSENTE"
    TARDE = "TARDE"


class IncidentSeverity(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
