"""Esquemas del Servicio de Asistencia/Bienestar."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.enums import AttendanceStatus, IncidentSeverity


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    school_id: Optional[str]
    grade: Optional[str]


class AttendanceCreate(BaseModel):
    student_id: str
    date: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    status: AttendanceStatus

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    date: str
    status: str
    created_at: datetime


class IncidentCreate(BaseModel):
    student_id: str
    severity: IncidentSeverity
    description: str

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    severity: str
    description: str
    created_at: datetime
