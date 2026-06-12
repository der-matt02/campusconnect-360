# Diagrama de despliegue — CampusConnect 360

Todo el ecosistema se orquesta con **Docker Compose**. Cada componente es un
contenedor; PostgreSQL y RabbitMQ son la infraestructura compartida.

```mermaid
flowchart TB
    subgraph host["Host (docker compose)"]
        FE["frontend<br/>nginx :3000"]
        GW["gateway :8000"]
        AC["academico :8001"]
        PG["pagos :8002"]
        NO["notificaciones :8003"]
        AS["asistencia :8004"]
        AN["analitica :8005"]
        PGSQL[("postgres :5432<br/>5 bases de datos")]
        RMQ["rabbitmq<br/>:5672 / :15672"]
    end

    FE --> GW
    GW --> AC & PG & NO & AS & AN
    AC & PG & NO & AS & AN --> PGSQL
    AC & PG & NO & AS & AN --> RMQ
```

## Puertos publicados

| Servicio | Puerto host |
|----------|-------------|
| frontend | 3000 |
| gateway | 8000 |
| academico / pagos / notificaciones / asistencia / analitica | 8001–8005 |
| postgres | 5432 |
| rabbitmq (AMQP / panel) | 5672 / 15672 |

## Orden de arranque (dependencias)

```mermaid
flowchart LR
    PGSQL[postgres] --> AC[academico]
    RMQ[rabbitmq] --> AC
    PGSQL --> PG[pagos] & NO[notificaciones] & AS[asistencia] & AN[analitica]
    RMQ --> PG & NO & AS & AN
    AC & PG & NO & AS & AN --> GW[gateway]
    GW --> FE[frontend]
```

Los servicios esperan a que PostgreSQL y RabbitMQ estén *healthy* antes de
arrancar (definido con `depends_on` + `healthcheck` en `docker-compose.yml`).
