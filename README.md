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
#    RabbitMQ (panel):                http://localhost:15672  (campus / campus_secret)
```

## Usuarios de prueba

| Usuario | Rol | Contraseña |
|---------|-----|------------|
| `secretaria` | Portal Académico | `campus123` |
| `finanzas` | Portal Financiero | `campus123` |
| `docente` | Portal Docente | `campus123` |
| `director` | Dashboard Directivo | `campus123` |

## Demostración: "un día de operación"

1. **Secretaría** registra un estudiante y crea su matrícula → evento `StudentEnrolled`.
2. **Notificaciones** registra la bienvenida; **Pagos** genera la deuda de matrícula.
3. **Finanzas** confirma el pago → evento `PaymentConfirmed`.
4. El **Servicio Académico** actualiza el estado financiero a `AL_DIA`.
5. **Docente** registra asistencia/incidente → `AttendanceRecorded` / `IncidentReported`.
6. El **Dashboard** muestra los indicadores consolidados (CQRS) en tiempo real.
7. **Escenario de falla**: desde el Dashboard se activa el "fallo simulado", se
   genera un evento que cae a la **DLQ**, y luego se **reprocesa** (resiliencia).

## Puertos

| Componente | Puerto |
|------------|--------|
| Frontend | 3000 |
| API Gateway | 8000 |
| Académico / Pagos / Notificaciones / Asistencia / Analítica | 8001–8005 |
| PostgreSQL | 5432 |
| RabbitMQ (AMQP / panel) | 5672 / 15672 |

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

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Cubren los contratos de eventos, el patrón Idempotent Receiver y la
configuración del consumidor (colas y DLQ).

## Documentación

- [Documento de arquitectura](docs/arquitectura.md)
- [Bitácora de trabajo](docs/bitacora.md)
- [Colección Postman](docs/postman/CampusConnect360.postman_collection.json) — respaldo técnico; ejecuta "Auth / Login" primero para guardar el JWT.
