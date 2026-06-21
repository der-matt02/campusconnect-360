# Catálogo de patrones aplicados — CampusConnect 360

## Patrones de integración (mensajería)

| Patrón | Dónde se evidencia | Archivo |
|--------|--------------------|---------|
| **API Gateway** | Entrada única con JWT, autorización por rol (RBAC) y enrutamiento | `gateway/app/main.py` |
| **Message Channel** | Exchange topic `campusconnect.events` y colas por servicio | `shared/messaging.py` |
| **Event Message** | Envoltura común de eventos (eventId, eventType, occurredAt, correlationId, data) | `shared/events.py` |
| **Publish/Subscribe** | Notificaciones y Analítica consumen el mismo evento | `services/*/app/consumer.py` |
| **Point-to-Point** | Cada cola de servicio tiene un único consumidor | `shared/messaging.py` |
| **Message Translator** | Evento de negocio → mensaje de notificación | `services/notificaciones/app/translator.py` |
| **Idempotent Receiver** | Tabla `processed_events` evita reprocesar duplicados | `shared/idempotency.py`, `shared/consuming.py` |
| **Dead Letter Channel** | DLX `campusconnect.dlx` + colas `*.events.dlq` | `shared/messaging.py`, `services/notificaciones/app/dlq.py` |

## Patrones de arquitectura

| Patrón | Aplicación |
|--------|-----------|
| **Microservicios** | Servicios independientes, desplegables por separado, con su propia base de datos |
| **Event-Driven Architecture** | Comunicación asíncrona por eventos vía RabbitMQ |
| **CQRS** | Analítica como modelo de lectura separado, alimentado por proyección de eventos |
| **Database per Service** | Cada servicio es dueño de su esquema; proyecciones locales en vez de FK entre bases |

## Patrones de diseño (código)

| Patrón | Aplicación | Archivo |
|--------|-----------|---------|
| **Repository** | Aísla el acceso a datos de endpoints y consumidores | `services/*/app/repository.py` |
| **Factory** | `new_base()` crea un `Base` declarativo por servicio | `shared/db.py` |
| **Mixin** | `ProcessedEventMixin` reutilizable y Base-agnóstico | `shared/idempotency.py` |
| **Dependency Injection** | `Depends(get_db)` inyecta la sesión en FastAPI | `services/*/app/main.py` |
| **Higher-Order Function** | `make_idempotent_handler` envuelve la lógica de negocio (DRY) | `shared/consuming.py` |

## Resiliencia

| Mecanismo | Descripción |
|-----------|-------------|
| **Reintentos** | El consumidor reintenta cada mensaje hasta 3 veces |
| **Dead Letter Queue** | Tras agotar reintentos (o formato inválido), el mensaje va a la DLQ |
| **Idempotencia** | `processed_events` evita efectos duplicados ante reentregas |
| **Reprocesamiento manual** | `POST /api/notificaciones/dlq/reprocess` reinyecta mensajes de la DLQ |
| **Health checks** | `/health` por servicio y agregado en el Gateway |

## Principios

- **KISS**: soluciones simples y legibles; sin sobre-ingeniería.
- **DRY**: lógica de consumo idempotente centralizada en `shared/consuming.py`.
- **Separación de responsabilidades**: endpoints (API) ↔ repository (datos) ↔
  consumer (eventos).
