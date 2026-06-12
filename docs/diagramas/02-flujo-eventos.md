# Diagramas de flujo de eventos — CampusConnect 360

## 1. Registro y matrícula (`StudentEnrolled`)

Un mismo evento es consumido por varios servicios (Publish/Subscribe).

```mermaid
sequenceDiagram
    actor Sec as Secretaria
    participant GW as API Gateway
    participant AC as Academico
    participant MQ as RabbitMQ
    participant PG as Pagos
    participant AS as Asistencia
    participant NO as Notificaciones
    participant AN as Analitica

    Sec->>GW: POST /api/academico/enrollments (JWT)
    GW->>AC: crea matricula
    AC->>MQ: publica StudentEnrolled
    AC-->>Sec: 201 matricula
    MQ-->>PG: StudentEnrolled
    PG->>PG: proyecta estudiante + deuda de matricula
    MQ-->>AS: StudentEnrolled
    AS->>AS: proyecta estudiante
    MQ-->>NO: StudentEnrolled
    NO->>NO: notificacion de bienvenida
    MQ-->>AN: StudentEnrolled
    AN->>AN: proyecta indicador (CQRS)
```

## 2. Confirmación de pago (`PaymentConfirmed`)

```mermaid
sequenceDiagram
    actor Fin as Finanzas
    participant GW as API Gateway
    participant PG as Pagos
    participant MQ as RabbitMQ
    participant AC as Academico
    participant NO as Notificaciones
    participant AN as Analitica

    Fin->>GW: POST /api/pagos/payments/{id}/confirm (JWT)
    GW->>PG: confirma pago
    PG->>MQ: publica PaymentConfirmed
    PG-->>Fin: 200 pago confirmado
    MQ-->>AC: PaymentConfirmed
    AC->>AC: estado financiero = AL_DIA
    MQ-->>NO: PaymentConfirmed
    MQ-->>AN: PaymentConfirmed
```

## 3. Asistencia / incidente (`AttendanceRecorded`, `IncidentReported`)

```mermaid
sequenceDiagram
    actor Doc as Docente
    participant GW as API Gateway
    participant AS as Asistencia
    participant MQ as RabbitMQ
    participant NO as Notificaciones
    participant AN as Analitica

    Doc->>GW: POST /api/asistencia/attendance | /incidents (JWT)
    GW->>AS: registra
    AS->>MQ: publica AttendanceRecorded / IncidentReported
    AS-->>Doc: 201
    MQ-->>NO: evento
    MQ-->>AN: evento
```

## 4. Escenario de resiliencia (fallo → DLQ → reprocesamiento)

```mermaid
sequenceDiagram
    participant MQ as RabbitMQ
    participant NO as Notificaciones
    participant DLQ as Dead Letter Queue

    MQ-->>NO: evento
    NO->>NO: procesar (modo fallo activo)
    NO--xNO: error (reintenta 3 veces)
    NO->>DLQ: nack -> mensaje a la DLQ
    Note over NO,DLQ: El dashboard muestra "mensajes fallidos"
    NO->>DLQ: POST /dlq/reprocess (fallo desactivado)
    DLQ-->>NO: reentrega
    NO->>NO: procesar OK -> notificacion enviada
```
