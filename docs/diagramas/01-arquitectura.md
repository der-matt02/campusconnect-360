# Diagrama de arquitectura — CampusConnect 360

Vista de componentes del ecosistema. El navegador solo habla con el **API
Gateway**, que autentica (JWT) y enruta a los microservicios. Los servicios se
comunican de forma asíncrona por **RabbitMQ** (eventos). Cada servicio tiene su
propia base de datos.

```mermaid
flowchart TB
    subgraph Cliente
        UI["Frontend React<br/>Portales + Dashboard<br/>:3000"]
    end

    GW["API Gateway (FastAPI)<br/>JWT + enrutamiento + health<br/>:8000"]

    subgraph Microservicios
        AC["Academico<br/>:8001"]
        PG["Pagos<br/>:8002"]
        NO["Notificaciones<br/>:8003"]
        AS["Asistencia<br/>:8004"]
        AN["Analitica (CQRS)<br/>:8005"]
    end

    subgraph Infraestructura
        MQ["RabbitMQ<br/>exchange topic + DLX"]
        DBAC[("academico_db")]
        DBPG[("pagos_db")]
        DBAS[("asistencia_db")]
        DBNO[("notificaciones_db")]
        DBAN[("analitica_db")]
    end

    UI -->|HTTPS + JWT| GW
    GW --> AC & PG & NO & AS & AN

    AC -- publica/consume --> MQ
    PG -- publica/consume --> MQ
    AS -- publica --> MQ
    MQ -- entrega --> NO
    MQ -- entrega --> AN

    AC --- DBAC
    PG --- DBPG
    AS --- DBAS
    NO --- DBNO
    AN --- DBAN
```

## Responsabilidades

| Componente | Responsabilidad |
|------------|-----------------|
| Frontend | Interfaces funcionales (3 portales + dashboard) |
| API Gateway | Entrada única, autenticación JWT, enrutamiento, health agregado |
| Académico | Estudiantes y matrículas; publica `StudentEnrolled` |
| Pagos | Deudas y pagos; publica `PaymentConfirmed` |
| Asistencia | Asistencia e incidentes; publica `AttendanceRecorded`, `IncidentReported` |
| Notificaciones | Consume eventos (Pub/Sub), genera notificaciones, maneja DLQ |
| Analítica | Proyección CQRS para el dashboard |
| RabbitMQ | Canal de mensajes (exchange topic) + Dead Letter Exchange |
| PostgreSQL | Una base de datos por servicio (persistencia separada) |
