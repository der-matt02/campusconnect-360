"""Esquemas del Servicio de Pagos."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DebtCreate(BaseModel):
    student_id: str
    concept: str
    amount: float


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    concept: str
    amount: float
    status: str
    created_at: datetime
    confirmed_at: Optional[datetime]


class StudentWithPayments(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    school_id: Optional[str]
    grade: Optional[str]
    payments: List[PaymentOut] = []
