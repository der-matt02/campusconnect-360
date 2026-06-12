# CampusConnect 360

> Ecosistema funcional de integración para una red de colegios.
> Proyecto Integrador — Integración de Sistemas.

CampusConnect 360 conecta los distintos sistemas de una red de colegios
(académico, pagos, asistencia/bienestar, notificaciones y analítica) mediante
una arquitectura de **microservicios orientada a eventos**, con un **API Gateway**
de entrada centralizada, mensajería con **RabbitMQ** y un **dashboard directivo**
alimentado por una vista analítica (CQRS).

## Arquitectura (resumen)

```
                         ┌─────────────────┐
   Portales (React) ───► │   API Gateway   │ ── JWT ──┐
   Académico             │   (FastAPI)     │          │
   Financiero            └────────┬────────┘          │
   Docente                        │ HTTP              │
   Dashboard                      ▼                   │
        ┌──────────┬──────────┬──────────┐            │
        ▼          ▼          ▼          ▼            │
   Académico    Pagos    Asistencia   Analítica ◄─────┘
        │          │          │          ▲
        └──────────┴──────────┴──────────┘ eventos
                   │  (publican)            │ (proyecta)
                   ▼                        │
            ┌─────────────┐                 │
            │  RabbitMQ   │ ────────────────┘
            │  (eventos)  │
            └──────┬──────┘
                   │ consume
                   ▼
            Notificaciones  (+ DLQ para fallos)
```

## Servicios

| Servicio | Puerto | Responsabilidad |
|----------|--------|-----------------|
| `gateway` | 8000 | Entrada centralizada, autenticación JWT, enrutamiento |
| `academico` | 8001 | Estudiantes y matrículas. Publica `StudentEnrolled` |
| `pagos` | 8002 | Deudas y pagos. Publica `PaymentConfirmed` |
| `notificaciones` | 8003 | Consume eventos y registra notificaciones (Pub/Sub) |
| `asistencia` | 8004 | Asistencia e incidentes. Publica `AttendanceRecorded`, `IncidentReported` |
| `analitica` | 8005 | Vista de lectura (CQRS) que alimenta el dashboard |

## Eventos de negocio

| Evento | Se publica cuando... |
|--------|----------------------|
| `StudentEnrolled` | Se matricula un estudiante |
| `PaymentConfirmed` | Se confirma un pago |
| `AttendanceRecorded` | Se registra asistencia |
| `IncidentReported` | Se registra un incidente o novedad |

## Requisitos

- Docker y Docker Compose
- (Opcional para desarrollo) Node.js 20+ y Python 3.11+

## Cómo ejecutar

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar todo el ecosistema
docker compose up --build

# 3. Abrir las interfaces
#    Frontend (portales + dashboard): http://localhost:3000
#    API Gateway (Swagger):           http://localhost:8000/docs
#    RabbitMQ (panel):                http://localhost:15672
```

## Estructura del repositorio

```
campusconnect-360/
├── docker-compose.yml      # Orquestación de todo el ecosistema
├── .env.example            # Variables de entorno de ejemplo
├── gateway/                # API Gateway (FastAPI)
├── services/               # Microservicios de negocio
│   ├── academico/
│   ├── pagos/
│   ├── asistencia/
│   ├── notificaciones/
│   └── analitica/
├── shared/                 # Contratos de eventos y utilidades comunes
├── frontend/               # Portales y dashboard (React + Vite)
├── infra/                  # Scripts de inicialización (DB, etc.)
└── docs/                   # Documentación de arquitectura
```

## Documentación

- [Documento de arquitectura](docs/arquitectura.md)
- [Bitácora de trabajo](docs/bitacora.md)
