"""Esquemas de entrada/salida del Servicio Academico."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentCreate(BaseModel):
    full_name: str
    document_id: str
    email: Optional[EmailStr] = None
    school_id: str
    grade: str


class EnrollmentCreate(BaseModel):
    student_id: str
    period: str


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    period: str
    status: str
    created_at: datetime


class StudentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: str
    correlation_id: Optional[str]
    summary: Optional[str]
    occurred_at: datetime


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    document_id: str
    email: Optional[str]
    school_id: str
    grade: str
    financial_status: str
    created_at: datetime
    enrollments: List[EnrollmentOut] = []


class StudentDetail(StudentOut):
    events: List[StudentEventOut] = []
