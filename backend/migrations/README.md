# Migraciones

Alembic administra cambios de esquema. `0001_enable_vector` activa la extensión;
0002_catalog crea el catálogo y 0003_metadata añade portada de pista y procedencia
de álbum. No usar `create_all` ni borrar el esquema al arrancar.

Compose ejecuta `migrate` antes del backend. Para aplicar cambios nuevos:
`docker compose run --rm migrate`. Para consultar la revisión:
`docker compose exec backend python -m alembic current`.

Consultar `docs/BASE_DATOS.md` desde la raíz para operación, respaldo y restauración.
Los downgrades se comprueban solo en bases aisladas de pruebas. No usar CASCADE.
