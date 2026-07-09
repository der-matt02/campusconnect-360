# Bitácora de trabajo — CampusConnect 360

## Integrantes del grupo

| Integrante | Responsabilidades |
|------------|-------------------|
| Diego Correa | Backend Developer & QA Lead (17 commits). Lideró el desarrollo del RBAC en el Gateway y pruebas unitarias de roles. Diseñó pruebas de resiliencia (reintentos, DLQ e idempotencia) y rediseñó el login de la UI. |
| Mathew Baquero | Arquitecto de Software & Principal Fullstack Developer (47 commits). Inicializó la estructura del monorepo, capa compartida (RabbitMQ y eventos), Gateway, scaffolding en React, portales operacionales, y documentó la arquitectura. |
| Luis Pineda | Backend Developer (Refactorización y UI Docente) (10 commits). Refactorizó funciones comunes y constantes HTTP. Implementó validaciones de Pydantic (email/deudas) y mejoras en el portal del Docente (vistas y validaciones). |
| Mateo Herrera | Backend Developer (Servicio Académico) (7 commits). Cimentó el Servicio Académico, incluyendo Dockerfile, ORM (SQLAlchemy), schemas (Pydantic), Outbox pattern para StudentEnrolled y consumidor de PaymentConfirmed. |
| Galo Guevara | DevSecOps Specialist & Backend Developer (37 commits). Diseñó el pipeline CI/CD en GitHub Actions (Ruff, Snyk, GitLeaks, Trivy, OWASP ZAP). Configuró Flux CD, Helm en Minikube y automatizó el túnel con start_tunnel.py. |

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
