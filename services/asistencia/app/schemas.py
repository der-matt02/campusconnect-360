"""Esquemas del Servicio de Asistencia/Bienestar."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    school_id: Optional[str]
    grade: Optional[str]


class AttendanceCreate(BaseModel):
    student_id: str
    date: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    status: str = Field(..., description="PRESENTE | AUSENTE | TARDE")


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    date: str
    status: str
    created_at: datetime


class IncidentCreate(BaseModel):
    student_id: str
    severity: str = Field(..., description="BAJA | MEDIA | ALTA")
    description: str


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    severity: str
    description: str
    created_at: datetime
