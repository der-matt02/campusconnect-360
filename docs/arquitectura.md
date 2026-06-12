# Documento de Arquitectura — CampusConnect 360

## 1. Descripción del problema

Una organización educativa administra una red de colegios en crecimiento. Cada
colegio usa sistemas distintos para gestionar estudiantes, matrículas, pagos,
asistencia, notificaciones, reportes e incidentes. Los principales problemas:

- La información de estudiantes vive en múltiples sistemas.
- Los pagos no se reflejan oportunamente en el sistema académico.
- Las notificaciones a representantes son manuales o tardías.
- La asistencia y novedades no se consolidan en tiempo real.
- Los reportes directivos requieren trabajo manual.
- No hay trazabilidad clara de eventos importantes.
- No existe una capa estándar de APIs ni mecanismos de seguridad/resiliencia.

## 2. Alcance de la solución

CampusConnect 360 integra estos sistemas mediante microservicios orientados a
eventos, con entrada centralizada (API Gateway), mensajería asíncrona
(RabbitMQ), seguridad básica (JWT) y una vista analítica (CQRS) que alimenta un
dashboard directivo. Toda la experiencia ocurre desde interfaces funcionales.

## 3. Actores del ecosistema

| Actor | Portal | Usuario de prueba |
|-------|--------|-------------------|
| Secretaría Académica | Portal Académico | `secretaria` |
| Finanzas | Portal Financiero | `finanzas` |
| Docente / Bienestar | Portal Docente | `docente` |
| Dirección | Dashboard Directivo | `director` |

Contraseña de todos: `campus123`.

## 4. Diagrama de arquitectura

```
   Navegador (React SPA :3000)
            │  HTTP + JWT
            ▼
   ┌───────────────────┐
   │   API Gateway      │  :8000   (login JWT, enrutamiento, health agregado)
   └─────────┬─────────┘
             │ HTTP /api/{servicio}/...
   ┌─────────┼───────────┬───────────┬───────────┐
   ▼         ▼           ▼           ▼           ▼
 Académico  Pagos     Asistencia  Notificac.  Analítica
 :8001      :8002     :8004       :8003       :8005
   │ DB       │ DB       │ DB        │ DB         │ DB
   └──────────┴──────────┴──────────┴────────────┘
             │ publican / consumen eventos
             ▼
        ┌───────────┐
        │ RabbitMQ  │  exchange topic + Dead Letter Exchange
        └───────────┘
```

Cada servicio tiene su propia base de datos PostgreSQL (persistencia separada).

## 5. Diagrama de flujo de eventos

```
Académico ──StudentEnrolled──►┌─ Pagos        (crea deuda de matrícula)
                              ├─ Asistencia   (proyecta estudiante)
                              ├─ Notificaciones (notifica bienvenida)
                              └─ Analítica    (proyecta indicador)

Pagos ──────PaymentConfirmed─►┌─ Académico    (estado financiero = AL_DIA)
                              ├─ Notificaciones
                              └─ Analítica

Asistencia ─AttendanceRecorded►┌─ Notificaciones
                               └─ Analítica
Asistencia ─IncidentReported──►┌─ Notificaciones
                               └─ Analítica
```

Un mismo evento es consumido por varios servicios (Publish/Subscribe).

## 6. Servicios implementados

| Servicio | Responsabilidad | Base de datos | Publica | Consume |
|----------|-----------------|---------------|---------|---------|
| Gateway | Entrada + JWT + ruteo | — | — | — |
| Académico | Estudiantes y matrículas | `academico_db` | StudentEnrolled | PaymentConfirmed |
| Pagos | Deudas y pagos | `pagos_db` | PaymentConfirmed | StudentEnrolled |
| Asistencia | Asistencia e incidentes | `asistencia_db` | AttendanceRecorded, IncidentReported | StudentEnrolled |
| Notificaciones | Notificaciones simuladas | `notificaciones_db` | — | los 4 eventos |
| Analítica | Vista de lectura (CQRS) | `analitica_db` | — | los 4 eventos |

## 7. Contratos de APIs

Cada servicio documenta su API con Swagger/OpenAPI en `/docs`. El Gateway expone
todo bajo `/api/{servicio}/...` y su propia documentación en `:8000/docs`.

Endpoints principales (vía Gateway, requieren JWT salvo `/auth/login` y `/health`):

- `POST /auth/login` → emite JWT
- `GET  /api/academico/students`, `POST /api/academico/students`, `POST /api/academico/enrollments`
- `GET  /api/pagos/payments`, `POST /api/pagos/payments/{id}/confirm`
- `POST /api/asistencia/attendance`, `POST /api/asistencia/incidents`
- `GET  /api/analitica/dashboard`, `GET /api/analitica/events`
- `GET  /api/notificaciones/notifications`, `POST /api/notificaciones/dlq/reprocess`

## 8. Contratos de eventos

Estructura común (Event Message):

```json
{
  "eventId": "evt-ab12cd34",
  "eventType": "StudentEnrolled",
  "occurredAt": "2026-07-15T10:30:00Z",
  "correlationId": "corr-20260715-001",
  "data": { "studentId": "STU-0001", "schoolId": "SCH-001", "grade": "8vo EGB" }
}
```

| Evento | data relevante |
|--------|----------------|
| `StudentEnrolled` | studentId, fullName, schoolId, grade, enrollmentId, period |
| `PaymentConfirmed` | paymentId, studentId, concept, amount |
| `AttendanceRecorded` | attendanceId, studentId, date, status |
| `IncidentReported` | incidentId, studentId, severity, description |

## 9. Patrones de integración aplicados

| Patrón | Evidencia |
|--------|-----------|
| API Gateway | Servicio `gateway`: entrada única y JWT |
| Publish/Subscribe | Notificaciones y Analítica consumen el mismo evento |
| Point-to-Point | Cada cola de servicio tiene un único consumidor |
| Message Channel | Exchange topic `campusconnect.events` + colas por servicio |
| Event Message | Envoltura común de eventos (`shared/events.py`) |
| Message Translator | `notificaciones/translator.py`: evento → mensaje |
| Idempotent Receiver | Tabla `processed_events` (`shared/idempotency.py`) |
| Dead Letter Channel | DLX `campusconnect.dlx` + colas `*.events.dlq` |
| CQRS | `analitica` proyecta eventos a un modelo de lectura |
| Health Check API | `/health` en cada servicio + agregado en el Gateway |

## 10. Decisiones arquitectónicas

- **FastAPI** en todos los servicios: Swagger automático, el equipo domina Python.
- **API Gateway propio en FastAPI**: máxima comprensión y capacidad de defensa.
- **RabbitMQ** sobre Kafka: más simple de demostrar Pub/Sub, P2P y DLQ.
- **Una base de datos por servicio**: aislamiento de datos.
- **Proyecciones locales** (StudentRef en Pagos/Asistencia): cada servicio no
  depende en línea de otro para operar.

## 11. Seguridad

- El Gateway emite un **JWT** (HS256) en `/auth/login` con `sub`, `role` y `name`.
- Todas las rutas `/api/**` exigen `Authorization: Bearer <token>`; sin token
  responden **401**.
- Usuarios de prueba por rol (secretaría, finanzas, docente, dirección).

## 12. Resiliencia y manejo de errores

- **Reintentos**: el consumidor reintenta cada mensaje hasta 3 veces.
- **Dead Letter Queue**: si se agotan los reintentos (o el mensaje tiene formato
  inválido), va a la DLQ del servicio vía el Dead Letter Exchange.
- **Idempotencia**: `processed_events` evita reprocesar eventos duplicados.
- **Reprocesamiento manual**: `POST /api/notificaciones/dlq/reprocess` reinyecta
  los mensajes de la DLQ.
- **Escenario demostrable**: el modo "chaos" en Notificaciones fuerza fallos para
  evidenciar reintentos → DLQ → reprocesamiento desde el Dashboard.

## 13. Observabilidad

- **Health checks** en cada servicio y agregados en el Gateway (`/health`).
- **Logs** estructurados por servicio (publicación/consumo de eventos, reintentos,
  DLQ).
- **Trazabilidad**: `correlationId` en cada evento; `analitica` expone
  `/events` con el historial de eventos procesados.

## 14. Integración de datos y dashboard

- `analitica` consume los eventos y los proyecta en `event_log` (lado de escritura
  del CQRS).
- El **Dashboard Directivo** lee indicadores consolidados (`/dashboard`):
  matriculados, pagos confirmados/pendientes, monto, asistencias, incidentes,
  eventos procesados, más estado de salud y mensajes fallidos (DLQ).

## 15. Limitaciones conocidas

- Las credenciales de usuarios son de prueba (en código), no un IdP real.
- Las notificaciones son simuladas (no envían correo/SMS reales).
- `pagosPendientes` se estima como matriculados − pagos confirmados.
- El secreto JWT y las contraseñas están en `.env` de ejemplo (no producción).

## 16. Mejoras futuras

- Autorización por rol a nivel de Gateway (cada portal solo a su servicio).
- Hashing de contraseñas e integración con un proveedor de identidad.
- Reintentos con backoff exponencial y reprocesamiento automático de la DLQ.
- Métricas (Prometheus/Grafana) y trazas distribuidas.

## 17. Declaración de uso de IA y recursos externos

Se utilizaron herramientas de apoyo para generar código base, documentación y
estructura del proyecto. El equipo comprende, adapta y puede defender cada
componente: arquitectura, contratos de API y eventos, patrones de integración,
seguridad y resiliencia.
