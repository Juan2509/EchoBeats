# Validación de P04 — PostgreSQL y pgvector

Fecha: 12 de noviembre de 2026. Infraestructura comprobada; aplicación musical
todavía pendiente de P05 en adelante.

## Configuración comprobada

- PostgreSQL **17.11** y pgvector **0.8.7** en imagen `pgvector/pgvector:pg17`,
  fijada por digest en Compose.
- Volumen nombrado `echobeats_postgres_data`, separado de los contenedores.
- Acceso publicado solo en `127.0.0.1:5433`; se conservó el servicio ajeno que
  ocupaba 5432. Comunicación interna por `postgres:5432`.
- Contraseña aleatoria generada en `.env` con modo 0600; excluida de Git y contexto Docker.
- Migración Alembic `0001_enable_vector`; aún sin tablas de catálogo ni de embeddings.
- Arranque PostgreSQL → migraciones → backend → frontend.

## Evidencia de pruebas

| Comprobación | Resultado |
| --- | --- |
| Construcción y `docker compose up --detach --wait` | Servicios disponibles; migración finaliza con código 0. |
| `RUN_DB_TESTS=1 ... python -m pytest -W error` | **9 pruebas superadas**, sin avisos. |
| Base de prueba nueva | Antes de migrar: conexión ok, extensión ausente y revisión pendiente. |
| Upgrade y repetición de upgrade | Extensión disponible y revisión correcta; segunda ejecución sin duplicar/recrear datos. |
| Downgrade y upgrade aislados | Extensión retirada/reinstalada en base aleatoria de prueba; base principal intacta. |
| Operador vectorial real | Tabla temporal con dos vectores 3D; distancia del coseno 0 para vector idéntico y 1 para ortogonal; orden correcto. |
| Readiness de esquema pendiente | HTTP 503; health sigue HTTP 200; tras migrar, readiness vuelve a 200. |
| BD detenida temporalmente | Health HTTP 200, ready HTTP 503, sin detalles de credenciales; al iniciar PostgreSQL se recupera. |
| Ready directo y por proxy | HTTP 200 con database/pgvector/migrations en ok. |
| Respaldo lógico | pg_dump custom y manifiesto SHA-256 creados en backups/, excluidos de Git. |
| Restauración real | Base nueva `echobeats_restore_p04_20261112` con pgvector 0.8.7 y revisión 0001_enable_vector. Base activa sin reemplazo. |
| Protecciones de restauración | Destino existente y dump con hash incorrecto rechazados; sin crear base en el segundo caso. |
| Recreación completa de contenedores | `down` sin borrar volumen seguido de `up`; misma identidad de clúster, base principal y restaurada conservadas, misma extensión/revisión y ready HTTP 200. |

Las bases `echobeats_test_<uuid>` se crean y retiran automáticamente por las
pruebas. La base de restauración se deja aislada como evidencia; no es la base
activa de EchoBeats. El dump/manifiesto local también se conservan fuera de Git.

Los vectores de prueba fueron escritos manualmente para comprobar infraestructura.
No son embeddings de música ni evidencia de consumo de IA: P20/P21 siguen pendientes.

## Alcance y continuidad

Se documentó operación y recuperación en [BASE_DATOS.md](BASE_DATOS.md) y se
actualizó el README. Los scripts no sobrescriben `.env` existente, no registran
contraseñas y no restauran sobre una base existente. La restauración no incluye
medios; el procedimiento explica cómo conservar BD y medios cuando existan.

No cambió el frontend, por lo que no se repitió su build de P03. No se realizaron
pruebas de reproducción ni búsqueda musical todavía. No hubo cambios en
dependencias: P04 usa SQLAlchemy, Psycopg y Alembic ya bloqueados en P03.

Al finalizar se detienen los servicios y se conservan volumen, credenciales y
respaldos locales. No se creó commit. Siguiente: **P05, modelo persistente del
catálogo y almacenamiento de recursos**.
