# Documento de Arquitectura — CampusConnect 360

> Documento vivo. Se completa de forma incremental durante el desarrollo.

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
dashboard directivo.

## 3. Actores del ecosistema

| Actor | Interactúa con |
|-------|----------------|
| Secretaría Académica | Portal Académico |
| Finanzas | Portal Financiero |
| Docente / Bienestar | Portal Docente |
| Dirección | Dashboard Directivo |

## 4. Diagrama de arquitectura

_(Pendiente — se incluye diagrama en `docs/diagramas/`.)_

## 5. Diagrama de flujo de eventos

_(Pendiente.)_

## 6. Servicios implementados

| Servicio | Responsabilidad | Base de datos |
|----------|-----------------|---------------|
| Gateway | Entrada centralizada + JWT | — |
| Académico | Estudiantes y matrículas | `academico_db` |
| Pagos | Deudas y pagos | `pagos_db` |
| Asistencia | Asistencia e incidentes | `asistencia_db` |
| Notificaciones | Consumo de eventos | — (in-memory / log) |
| Analítica | Vista de lectura (CQRS) | `analitica_db` |

## 7. Contratos de APIs

_(Se documentan vía Swagger/OpenAPI en cada servicio: `/docs`.)_

## 8. Contratos de eventos

Estructura mínima de todo evento:

```json
{
  "eventId": "evt-001",
  "eventType": "StudentEnrolled",
  "occurredAt": "2026-07-15T10:30:00Z",
  "correlationId": "corr-20260715-001",
  "data": { }
}
```

| Evento | Datos relevantes |
|--------|------------------|
| `StudentEnrolled` | studentId, schoolId, grade |
| `PaymentConfirmed` | paymentId, studentId, amount |
| `AttendanceRecorded` | studentId, date, status |
| `IncidentReported` | incidentId, studentId, severity |

## 9. Patrones de integración aplicados

| Patrón | Dónde se evidencia |
|--------|--------------------|
| API Gateway | Servicio `gateway` |
| Publish/Subscribe | `notificaciones` y `analitica` consumen el mismo evento |
| Point-to-Point | Cola dedicada con un único consumidor |
| Message Channel | Exchange + colas en RabbitMQ |
| Event Message | Estructura de eventos de negocio |
| Message Translator | Evento → modelo de notificación / proyección |
| Idempotent Receiver | Control de `eventId` ya procesados |
| Dead Letter Channel | DLQ para mensajes fallidos |
| CQRS | Servicio `analitica` como vista de lectura |
| Health Check API | `/health` en cada servicio |

## 10. Decisiones arquitectónicas

- **FastAPI** para todos los servicios: simplicidad, Swagger automático, el
  equipo domina Python.
- **API Gateway propio en FastAPI**: máxima comprensión y capacidad de defensa.
- **RabbitMQ** sobre Kafka: más simple de demostrar Pub/Sub, P2P y DLQ.
- **Una base de datos por servicio**: aislamiento de datos.

## 11. Seguridad

_(JWT emitido por el Gateway; servicios validan token. Pendiente de detallar.)_

## 12. Resiliencia y manejo de errores

_(Reintentos, idempotencia y DLQ. Pendiente de detallar.)_

## 13. Observabilidad

_(Logs estructurados, health checks. Pendiente de detallar.)_

## 14. Integración de datos y dashboard

_(Proyección CQRS hacia `analitica_db`. Pendiente de detallar.)_

## 15. Limitaciones conocidas

_(Pendiente.)_

## 16. Mejoras futuras

_(Pendiente.)_

## 17. Declaración de uso de IA y recursos externos

_(Pendiente — se declara el uso de herramientas de apoyo según corresponda.)_
