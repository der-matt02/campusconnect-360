# Bitácora de trabajo — CampusConnect 360

## Integrantes del grupo

| Integrante | Responsabilidades |
|------------|-------------------|
| _(completar)_ | _(completar)_ |

## Principales decisiones tomadas

- **Stack:** FastAPI (backend), React + Vite (frontend), RabbitMQ (mensajería),
  PostgreSQL (persistencia), Docker Compose (orquestación).
- **API Gateway propio** en FastAPI para centralizar entrada y seguridad JWT.
- Una base de datos por microservicio (persistencia separada).
- Proyecciones locales de estudiantes en Pagos y Asistencia para no acoplar
  servicios en línea.
- GitFlow: `main` (producción) y `develop` (integración); cada componente en su
  feature branch con PR hacia `develop`.

## Registro de avance

| Hito | Avance |
|------|--------|
| 1 | Estructura base e infraestructura (PostgreSQL + RabbitMQ) |
| 2 | Capa compartida: contratos de eventos y mensajería con DLQ |
| 3 | Servicio Académico (StudentEnrolled) |
| 4 | Servicio Pagos (PaymentConfirmed) |
| 5 | Servicio Asistencia (AttendanceRecorded, IncidentReported) |
| 6 | Servicio Notificaciones (Pub/Sub + DLQ + resiliencia) |
| 7 | Servicio Analítica (CQRS + dashboard) |
| 8 | API Gateway (JWT + enrutamiento + health agregado) |
| 9 | Frontend React (3 portales + dashboard) |
| 10 | Integración final, arranque limpio y pruebas end-to-end |

## Problemas encontrados

- En un arranque con volumen existente, las nuevas bases de datos no se creaban
  automáticamente (el script de init solo corre con volumen vacío). Se resolvió
  documentando el arranque limpio (`docker compose down -v`) y verificándolo.

## Cambios importantes realizados

- Reconstrucción del historial a GitFlow limpio (main + develop + feature branches).

## Herramientas utilizadas

- Docker / Docker Compose
- FastAPI, React + Vite, nginx
- RabbitMQ, PostgreSQL
- Git / GitHub (GitFlow)

## Uso de IA generativa y recursos externos

Se usaron herramientas de apoyo para generar código base, documentación y
estructura. El equipo comprende, adapta y puede defender cada componente.

## Enlace al repositorio Git

https://github.com/der-matt02/campusconnect-360 (privado)
