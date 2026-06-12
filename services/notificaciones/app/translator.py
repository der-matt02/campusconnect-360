"""Patron Message Translator.

Traduce un evento de negocio a un mensaje de notificacion legible para el
representante o el actor correspondiente.
"""
from shared.events import Event, EventType


def translate(event: Event) -> tuple[str, str]:
    """Devuelve (student_id, mensaje) a partir del evento."""
    data = event.data
    student_id = data.get("studentId")

    if event.eventType == EventType.STUDENT_ENROLLED:
        return student_id, (
            f"Bienvenido/a {data.get('fullName', '')}: matricula {data.get('enrollmentId')} "
            f"registrada para el periodo {data.get('period')}."
        )
    if event.eventType == EventType.PAYMENT_CONFIRMED:
        return student_id, (
            f"Pago confirmado por {data.get('amount')} ({data.get('concept')}). "
            f"Gracias por su pago."
        )
    if event.eventType == EventType.ATTENDANCE_RECORDED:
        return student_id, (
            f"Registro de asistencia: {data.get('status')} el {data.get('date')}."
        )
    if event.eventType == EventType.INCIDENT_REPORTED:
        return student_id, (
            f"Novedad reportada (severidad {data.get('severity')}): "
            f"{data.get('description')}."
        )
    return student_id, f"Evento {event.eventType} recibido."
