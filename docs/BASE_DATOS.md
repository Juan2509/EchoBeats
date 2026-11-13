# PostgreSQL y pgvector — Operación local

P18 añade `0006_processing_jobs`, sin modificar catálogo/medios. Se aplicó tras
respaldo privado y se comprobó readiness. Conserva historial de trabajos y rechaza
downgrade si hay filas; probar reversión solo en bases aisladas. Detalles de
operación, respaldo y evidencia en [VALIDACION_P18.md](VALIDACION_P18.md).

Entregable P04, 12 de noviembre de 2026. Configuración para una instalación local
de un usuario. PostgreSQL 17 con pgvector, imagen fijada por digest en Compose.
El esquema musical se crea en P05; no hay aún tabla de embeddings de canciones.

## 1. Preparación y arranque

Desde la raíz:

```bash
python3 scripts/preparar_entorno.py
docker compose up --build --detach --wait
```

El script crea `.env` con permisos 0600 y contraseña aleatoria, sin mostrarla.
Si el archivo ya existe lo conserva: añadir los campos POSTGRES_* de
`.env.example` cuando se migre desde P03 y establecer una contraseña propia.
No sobrescribir configuraciones existentes ni versionar `.env`.

Orden de inicio: PostgreSQL sano → servicio `migrate` aplica `alembic upgrade head`
→ backend listo → frontend. `migrate` termina con código 0; no es un servicio
permanente ni un error por aparecer como «Exited». Si falla, backend no inicia.
Reintentar tras corregir la causa con `docker compose up --detach --wait`.

| Parámetro | Valor inicial |
| --- | --- |
| Servicio de BD | `postgres`, puerto interno 5432. |
| Acceso desde el host | `127.0.0.1:5433` (configurable por POSTGRES_PORT). |
| Base / usuario | `echobeats` / `echobeats` (configurables al inicializar). |
| Contraseña | Solo `.env` local; sin valor real en el repositorio. |
| Volumen | `echobeats_postgres_data`, montado en `/var/lib/postgresql/data`. |
| Migración inicial | `0001_enable_vector`: `CREATE EXTENSION IF NOT EXISTS vector`. |

5433 evita el servicio que ya ocupaba 5432 en el equipo. No se detuvo ni modificó
ese servicio. Dentro de Compose, backend y migraciones usan siempre postgres:5432;
la configuración nativa usa POSTGRES_HOST/POSTGRES_PORT o DATABASE_URL opcional.

El rol creado por la imagen dispone de permisos de administración en esta
instalación local para aplicar la extensión y crear bases aisladas de prueba.
No es una configuración de roles para exposición pública. Contraseña, usuario
y nombre se usan al inicializar un volumen vacío: editar `.env` no cambia los
roles existentes. Conservar las credenciales con el volumen y hacer cambios
de rol deliberados si se necesita rotarlas.

## 2. Estado y migraciones

```bash
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:8000/api/v1/ready
docker compose exec backend python -m alembic current
docker compose exec backend python -m alembic heads
docker compose run --rm migrate
```

`health` confirma que el proceso responde. `ready` verifica conexión real,
extensión `vector` y revisión Alembic igual a las cabeceras del código:

```json
{
  "status": "ready",
  "checks": {"database": "ok", "pgvector": "ok", "migrations": "ok"}
}
```

Una dependencia caída o esquema pendiente produce HTTP 503 con estados seguros,
sin DSN ni contraseña. Una caída de IA no afecta este endpoint. El motor usa
pool con comprobación previa de conexiones y timeout de conexión; cada consulta
de readiness tiene tiempo máximo en PostgreSQL.

Las migraciones no ejecutan `create_all`, borrados de volumen ni recreación de
tablas al arrancar. Repetir upgrade no elimina datos. `downgrade` se usa solo
en bases aisladas durante las pruebas; la migración inicial elimina la extensión
sin CASCADE y se negará a hacerlo si existen dependencias que lo impidan.

Para cambios nuevos, crear una revisión Alembic desde `backend`, revisar el SQL
y su estrategia de reversión, y aplicar `migrate`. En P05 se conectará la metadata
de modelos a `migrations/env.py` antes de usar autogeneración del catálogo.

## 3. Parada y persistencia

```bash
docker compose down
docker compose up --detach --wait
```

`down` retira contenedores y red; conserva el volumen nombrado. Nunca añadir
opciones que borren volúmenes al flujo normal. `stop postgres` / `start postgres`
permiten detener y recuperar solo la BD. Los datos de prueba y restauración
pertenecen también al volumen y sobreviven a la recreación del contenedor.

El arranque no debe actualizar PostgreSQL de versión mayor automáticamente.
Un cambio mayor requiere plan de migración y respaldo, no reutilizar sin más
el directorio físico con otra versión. El digest actual se conserva para reproducir
la validación; actualizarlo deliberadamente y repetir pruebas.

## 4. Respaldo lógico y restauración sin reemplazo

Con PostgreSQL iniciado:

```bash
python3 scripts/base_datos.py respaldar
```

Genera `backups/echobeats_<fechaUTC>_<id>.dump` en formato custom de pg_dump,
junto con manifiesto JSON que registra SHA-256, versión PostgreSQL, extensión
y revisión. Carpeta excluida de Git/Docker; dump creado con permisos 0600.
El script confirma éxito solo tras terminar pg_dump. No copia secretos al manifiesto.

Para comprobar una copia, usar el nombre real generado:

```bash
python3 scripts/base_datos.py restaurar backups/echobeats_FECHA_ID.dump --base echobeats_restore_comprobacion
```

El destino debe ser un nombre nuevo `echobeats_restore_<nombre>`. Se valida hash
antes de crear la base; se rechaza si existe o coincide con la activa. Se restaura
con `pg_restore --exit-on-error --no-owner --no-acl`, sin `--clean`. Un fallo puede
dejar la base nueva incompleta para diagnóstico; no se elimina ni se toca la activa.
No borrar la base original para probar una restauración.

Comprobar tablas, revisión, extensión y datos dentro de la nueva base antes de
considerar cambiar la conexión de la aplicación. Una restauración de esquema
anterior requiere aplicar migraciones pendientes en ese destino. El script no
cambia la configuración de EchoBeats automáticamente.

### Archivos musicales y visuales

El dump **solo contiene BD**: no incluye audios o imágenes de MEDIA_ROOT.
Para un respaldo completo, detener frontend/backend/trabajos para que no haya
escrituras, mantener PostgreSQL activo, generar dump y copiar `data/media`
al mismo conjunto de respaldo. Conservar el manifiesto de esa copia y mantener
el par BD/medios correspondiente al mismo punto de operación. Reiniciar servicios
después. En P04 aún no se importan medios reales.

Al restaurar una biblioteca futura, recuperar también sus medios en una ubicación
separada y validar referencias antes de sustituir MEDIA_ROOT. Nunca copiar una
carpeta de medios antigua encima de la activa como método de comprobación.

## 5. Pruebas reproducibles

```bash
docker compose exec backend python -m pytest -W error
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error
```

El primer comando no exige pruebas de BD y las omite explícitamente. El segundo
crea una base con nombre aleatorio `echobeats_test_<uuid>` usando el rol local;
prueba upgrade repetido, downgrade/upgrade, operación real de distancia del coseno
y estados HTTP de readiness. Solo elimina la base que acaba de crear. No modifica
el esquema de la base principal. No ejecutar esos tests contra un servidor ajeno.

Los vectores tridimensionales de esta prueba verifican el operador de PostgreSQL,
no son embeddings generados mediante IA ni cumplen por sí solos RF-13/RF-14.
La tabla es temporal y se retira al terminar su transacción.

Ver [VALIDACION_P04.md](VALIDACION_P04.md) para resultados de esta sesión.

Fuentes oficiales consultadas:
[pgvector](https://github.com/pgvector/pgvector),
[Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
[respaldo PostgreSQL](https://www.postgresql.org/docs/17/backup-dump.html).

## Actualización P12 — Muros por álbum

`0005_album_walls` crea wall/wall_element y rellena muros iniciales para todos los
álbumes existentes sin modificar pistas, playlists, metadatos ni medios. El
servicio crea los muros de álbumes nuevos en su misma transacción. Aplicar con
el servicio migrate o `alembic upgrade head`, conservando volumen y respaldos.

Antes de aplicar P12 se creó un respaldo local con manifiesto/hash; comprobar
MEDIA_ROOT por separado. No probar downgrade en la principal: 0005 rechaza la
reversión si hay elementos, fondo personalizado o revisión > 1 para conservar
los diseños. Las pruebas de reversión usan exclusivamente bases aisladas.
Evidencias de migración y persistencia A/B: [VALIDACION_P12.md](VALIDACION_P12.md).
