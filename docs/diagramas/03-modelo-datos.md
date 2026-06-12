# Modelo de datos — CampusConnect 360

Cada microservicio es dueño de su propio esquema (base de datos independiente).
Los servicios que necesitan datos de estudiantes mantienen una **proyección
local** (`StudentRef`) alimentada por el evento `StudentEnrolled`, evitando el
acoplamiento directo entre bases de datos.

Todos los servicios que consumen eventos incluyen además la tabla
`processed_events` (Idempotent Receiver).

## Servicio Académico (`academico_db`)

```mermaid
erDiagram
    students ||--o{ enrollments : tiene
    students ||--o{ student_events : registra
    students {
        string id PK
        string full_name
        string document_id UK
        string email
        string school_id
        string grade
        string financial_status
        datetime created_at
    }
    enrollments {
        string id PK
        string student_id FK
        string period
        string status
        datetime created_at
    }
    student_events {
        int id PK
        string student_id FK
        string event_type
        string correlation_id
        string summary
        datetime occurred_at
    }
```

## Servicio de Pagos (`pagos_db`)

```mermaid
erDiagram
    student_refs ||--o{ payments : adeuda
    student_refs {
        string id PK
        string full_name
        string school_id
        string grade
        datetime created_at
    }
    payments {
        string id PK
        string student_id FK
        string concept
        float amount
        string status
        datetime created_at
        datetime confirmed_at
    }
```

## Servicio de Asistencia (`asistencia_db`)

```mermaid
erDiagram
    student_refs ||--o{ attendances : tiene
    student_refs ||--o{ incidents : tiene
    student_refs {
        string id PK
        string full_name
        string school_id
        string grade
    }
    attendances {
        string id PK
        string student_id FK
        string date
        string status
    }
    incidents {
        string id PK
        string student_id FK
        string severity
        string description
    }
```

## Servicio de Notificaciones (`notificaciones_db`)

```mermaid
erDiagram
    notifications {
        string id PK
        string event_id
        string event_type
        string student_id
        string channel
        string message
        string status
        string correlation_id
        datetime created_at
    }
```

## Servicio de Analítica (`analitica_db`) — modelo de lectura (CQRS)

```mermaid
erDiagram
    event_log {
        int id PK
        string event_id
        string event_type
        string student_id
        string correlation_id
        json payload
        datetime occurred_at
    }
```

## Tabla común de idempotencia (en cada servicio consumidor)

```mermaid
erDiagram
    processed_events {
        string event_id PK
        string consumer PK
        datetime processed_at
    }
```
