# Contratos de eventos — CampusConnect 360

Todos los eventos comparten una **envoltura común** (patrón Event Message) y se
publican en el exchange topic `campusconnect.events` con la *routing key* igual
al `eventType`.

## Envoltura común

```json
{
  "eventId": "evt-ab12cd34ef56",
  "eventType": "StudentEnrolled",
  "occurredAt": "2026-07-15T10:30:00+00:00",
  "correlationId": "corr-9f8e7d6c5b4a",
  "data": { }
}
```

| Campo | Descripción |
|-------|-------------|
| `eventId` | Identificador único del evento |
| `eventType` | Tipo de evento |
| `occurredAt` | Fecha/hora de ocurrencia (UTC, ISO-8601) |
| `correlationId` | Identificador de correlación / trazabilidad |
| `data` | Datos específicos del evento |

## Eventos de negocio

### `StudentEnrolled`
Se publica cuando se crea una matrícula. Consumido por Pagos, Asistencia,
Notificaciones y Analítica.

```json
{
  "eventType": "StudentEnrolled",
  "data": {
    "studentId": "STU-0001",
    "fullName": "Ana Maria Torres",
    "schoolId": "SCH-001",
    "grade": "8vo EGB",
    "enrollmentId": "ENR-ab12cd34",
    "period": "2026-1"
  }
}
```

### `PaymentConfirmed`
Se publica al confirmar un pago. Consumido por Académico, Notificaciones y Analítica.

```json
{
  "eventType": "PaymentConfirmed",
  "data": {
    "paymentId": "PAY-ab12cd34",
    "studentId": "STU-0001",
    "concept": "Matricula periodo 2026-1",
    "amount": 250.0
  }
}
```

### `AttendanceRecorded`
Se publica al registrar asistencia. Consumido por Notificaciones y Analítica.

```json
{
  "eventType": "AttendanceRecorded",
  "data": {
    "attendanceId": "ATT-ab12cd34",
    "studentId": "STU-0001",
    "date": "2026-06-12",
    "status": "PRESENTE"
  }
}
```

### `IncidentReported`
Se publica al registrar una novedad/incidente. Consumido por Notificaciones y Analítica.

```json
{
  "eventType": "IncidentReported",
  "data": {
    "incidentId": "INC-ab12cd34",
    "studentId": "STU-0001",
    "severity": "MEDIA",
    "description": "Llego tarde reiteradamente"
  }
}
```

## Matriz de publicación / consumo

| Evento | Publica | Consumen |
|--------|---------|----------|
| `StudentEnrolled` | Académico | Pagos, Asistencia, Notificaciones, Analítica |
| `PaymentConfirmed` | Pagos | Académico, Notificaciones, Analítica |
| `AttendanceRecorded` | Asistencia | Notificaciones, Analítica |
| `IncidentReported` | Asistencia | Notificaciones, Analítica |
