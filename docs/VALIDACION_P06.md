# Validación P05/P06 — Catálogo e importación

12 de noviembre de 2026. El usuario solicitó P06; P05 seguía pendiente y se
implementó como dependencia necesaria, sin crear commits automáticamente.

## Resultado entregado

- Migración `0002_catalog`: ocho tablas, índices, restricciones y álbum «Sin álbum».
- Metadata SQLAlchemy compartida con Alembic; sin `create_all` al arrancar.
- Almacenamiento gestionado con staging, claves UUID y rechazo de rutas arbitrarias.
- Endpoint multipart `POST /api/v1/imports` y selección/carga múltiple en frontend.
- Mutagen **1.48.1**, única dependencia añadida; versión/hashes en requirements.lock.
- Detección SHA-256 de duplicados con bloqueo transaccional entre procesos.
- Compensación de fallos y comando `python -m app.media_audit` de solo lectura.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `RUN_DB_TESTS=1 ... python -m pytest -W error` | **24 pruebas superadas sin avisos**, con bases aleatorias aisladas y directorios temporales. |
| Migraciones desde base vacía y roundtrip | Upgrade repetido, downgrade/upgrade solo en pruebas y readiness coherente. |
| `alembic check` | Sin diferencias pendientes entre modelos y esquema. |
| Integridad de catálogo | FK impide referencias inexistentes/borrado de recursos usados; orden de playlist único; álbum desconocido referenciado protegido. |
| Lote mixto HTTP de pruebas | Válidos, MP3 sin etiquetas, duplicado, texto renombrado y archivo vacío reciben resultados por archivo. |
| Límites | Límite por archivo, cantidad y cuerpo total verificados; también transmisión sin Content-Length. Formulario erróneo no deja registros. |
| Concurrencia | Dos importaciones paralelas del mismo contenido dejan un único archivo, pista e ID. |
| Fallos de almacenamiento/SQL | Rollback sin registros incompletos; archivo nuevo sin commit se retira solo cuando se comprueba que no está referenciado. |
| COMMIT con respuesta perdida | Se verifica confirmación y se conserva el medio; no se borra un archivo ya registrado. |
| Medio perdido | Reimportar bytes idénticos repone el archivo manteniendo el ID. |
| Rutas y staging | Rutas arbitrarias y symlinks fuera de raíz rechazados; stream excesivo limpia su staging. |
| Frontend | TypeScript y build Vite correctos dentro del contenedor Node 24. |

### Prueba sobre servicios reales

Se envió la colección sintética de siete archivos por el proxy del frontend,
sin dobles de base de datos ni del almacenamiento:

1. Primer envío: cuatro pistas importadas, un duplicado y dos rechazados.
2. Se retiraron y recrearon todos los contenedores, conservando volumen y medios.
3. Segundo envío: cinco duplicados, dos rechazados y los mismos IDs de pista.
4. Informe de medios: sin assets faltantes, archivos huérfanos o temporales.

Los cuatro audios técnicos quedan en la biblioteca local y sus originales en
MEDIA_ROOT. No se importó música externa ni se borraron datos existentes.
La lectura/escucha desde el reproductor se comprobará en P09/P10.

## Recuperación de configuración local

Al iniciar esta sesión no existía `.env`, mientras el volumen P04 seguía presente.
Se generó configuración privada y se sincronizó únicamente la contraseña del rol
local de EchoBeats con ese archivo, conservando base, volumen y datos. La contraseña
no se imprimió ni se incorporó al repositorio. El servicio ajeno en 5432 se dejó intacto.

## Límites de esta entrega

- Sin inspección visual automatizada en navegador; build y HTTP no prueban el render.
- La validación MPEG es básica; no certifica la decodificación completa de cada audio.
- Título de archivo y álbum desconocido provisionales. Etiquetas/portadas/edición en P07.
- Sin listado visual de biblioteca, reproducción, muros, recomendaciones ni API de IA.
- Los archivos de cuerpo multipart se reciben antes de confirmar importaciones:
  un formulario fuera de límites no aplica cambios; un lote admitido confirma por archivo.
- Ante interrupción abrupta o confirmación SQL imposible de comprobar, se puede
  conservar un huérfano para revisión; no hay borrado automático de medios.

Ver [IMPORTACION_MP3.md](IMPORTACION_MP3.md) para uso y consistencia.
Se detienen servicios al finalizar y se conservan medios/volumen/.env local.
Siguiente: **P07 — extracción y edición de metadatos**.
