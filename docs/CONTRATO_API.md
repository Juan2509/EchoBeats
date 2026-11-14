# Contrato inicial de API de EchoBeats

P02 · 12 de noviembre de 2026. Especificación previa a implementación.
P03 implementó health, P04 ready y P06 imports. P07 incorpora lectura/edición de
pistas y álbumes, listas paginadas de selección, extracción y assets de portada.
P08 incorpora búsqueda textual, listados filtrados y búsqueda agrupada.
P09 incorpora entrega de audio original y rangos de bytes.
O06 amplía formatos a MP3, WAV PCM, FLAC y Ogg Vorbis/Opus (.ogg/.opus).
P11 implementa playlists y P12 la API de muros; editor visual e IA siguen pendientes.
El OpenAPI generado por FastAPI se
contrastará con este contrato durante los pasos correspondientes.

Ver [modelo](MODELO_DATOS.md), [decisiones](DECISIONES.md) y
[recorridos de interfaz](DISENO_PANTALLAS.md).

## 1. Convenciones

Prefijo `/api/v1`; JSON UTF-8, campos `snake_case`, IDs UUID y fechas ISO 8601 UTC.
No devolver rutas de disco ni claves externas. La instancia es local de un usuario.
Todos los límites de archivos y consultas de D08 se aplican en servidor.

Listados: `limit` (24 por defecto, máximo 100) y `offset` (mínimo 0).
Respuesta `{items, total, limit, offset}`; orden estable por título/nombre e ID,
salvo pistas de álbum por número y luego título/ID, y playlists por position.
La búsqueda textual ignora mayúsculas y conserva tildes. `q` se recorta y admite
hasta 200 caracteres sin NUL; `%`, `_` y `\` se buscan literalmente, con parámetros SQL.
Pistas coinciden por título, álbum y artistas de pista/álbum; álbumes también
coinciden por sus canciones. No hay duplicados por múltiples créditos.
La búsqueda semántica tiene su
propia respuesta ordenada por relevancia.

Errores controlados:

```json
{
  "error": {
    "code": "asset_too_large",
    "message": "La imagen supera el límite de 5 MiB.",
    "fields": [{"field": "file", "reason": "max_size"}],
    "request_id": "peticion-de-ejemplo"
  }
}
```

`request_id` permite diagnóstico local sin registrar secretos. Mensajes de API
en español; code estable para decisiones del cliente. 404 recurso inexistente;
413 tamaño de petición excedido; 415 formato no admitido; 422 datos inválidos;
409 conflicto de estado; 412 revisión desactualizada; 428 falta de precondición;
503 dependencia no disponible. Nunca devolver stack traces al cliente.

## 2. Catálogo, importación y recursos

| Método y ruta | Entrada / salida principal | Cierre / paso |
| --- | --- | --- |
| `GET /health` | `{status: "ok"}`; confirma proceso, sin secretos. | P03. |
| `GET /ready` | `{status, checks: {database, pgvector, migrations}}`; 200 si todos están ok y 503 en caso contrario. No consulta proveedor de IA. | P04 implementado. |
| `POST /imports` | multipart files: .mp3, .wav (PCM entero), .flac, .ogg (Vorbis/Opus), .opus (Opus); hasta 20 archivos. Contenido/extensión validados sin confiar en MIME declarado. Respuesta 200 por archivo; cuerpo excesivo 413. | P06/O06 implementado. |
| `GET /tracks` | album_id opcional, q y paginación; fichas de pistas. Dentro de álbum ordena por número, título e ID; sin álbum por título e ID. | P07/P08 implementado. |
| `GET /tracks/{id}` | Pista, álbum, artistas, duración, portada heredada y procedencia; `revision`. | P07. |
| `PATCH /tracks/{id}` | title, artist_names, album_id, track_number y cover_asset_id; `If-Match` requerido. Duración/archivo/procedencia no editables. | P07 implementado. |
| `POST /tracks/{id}/extract-metadata` | `If-Match` requerido; relee el original y conserva campos manuales. | P07 implementado. |
| `GET /albums` | q, paginación; id, título, artistas, portada y número de pistas. include_empty_system=false oculta «Sin álbum» cuando no tiene pistas; por defecto true conserva selección de P07. | P07/P08 implementado. |
| `POST /albums` | `{title, artist_names}`; crea álbum explícito y devuelve 201 con ID. | P07. |
| `GET /albums/{id}` | Resumen, datos, procedencia y ETag. Pistas se consultan paginadas en /tracks. | P07 implementado. |
| `PATCH /albums/{id}` | title/artist_names/cover_asset_id con `If-Match`; no permite cambiar system_key ni renombrar el álbum de sistema. | P07 implementado. |
| `GET /library/search` | q obligatoria no vacía; query y grupos tracks/albums/playlists con items/total/limit/offset/href, máximo 10 por grupo. href enlaza a biblioteca filtrada; playlists busca nombres y enlaza a vista=playlists. | P08 implementado. |
| `POST /assets` | multipart file y purpose=cover, playlist o wall; cover/playlist admiten PNG/JPEG, wall añade GIF verificado y preview. Devuelve 201, content_url y para wall static_preview_url/frame_count. | P07/P11/P14 implementado. |
| `GET /assets/{id}/content` | PNG/JPEG validado con nosniff y caché privada; sin rutas arbitrarias ni audio. GIF se incorpora después. | P07 para portadas. |
| `GET` o `HEAD /tracks/{id}/audio` | MIME real (audio/mpeg, audio/wav, audio/flac, audio/ogg), inline. GET 200 completo o 206 con Content-Range para rangos válidos (también sufijos y rangos abiertos/múltiples); 416 fuera de tamaño, 400 sintaxis inválida. HEAD 200 describe el archivo completo sin cuerpo e ignora Range. If-Range compatible por ETag o Last-Modified; token distinto devuelve 200 completo. | P09/O06 implementado. |

Un archivo inválido dentro de un lote admitido no impide procesar los otros.
Si una petición no puede analizarse por multipart inválido o límite global, es
un error de solicitud y no una lista de supuestos resultados por archivo.

```json
{
  "results": [
    {"index": 0, "file_name": "tono_grave.mp3", "status": "imported", "track_id": "11111111-1111-4111-8111-111111111111"},
    {"index": 1, "file_name": "copia.mp3", "status": "duplicate", "track_id": "11111111-1111-4111-8111-111111111111"},
    {"index": 2, "file_name": "invalido.mp3", "status": "rejected", "error": {"code": "invalid_audio", "message": "El archivo no contiene audio MP3 válido."}}
  ]
}
```

`index` corresponde al orden enviado, aunque dos nombres coincidan. `imported`
significa archivo y registro confirmados; el análisis de IA no forma parte de esa
promesa. Una pista sin etiquetas recibe datos provisionales con su procedencia.

Resumen de pista: `id`, `title`, `artists: [{id, name}]`, `album_id`, `album_title`,
`duration_ms`, `cover_url` nullable y procedencia. P09 añade `audio_url`, relativa
a `/api/v1/tracks/{id}/audio`; también se devuelve en los listados de pistas.
O06 añade `audio_mime_type`, determinado al importar por contenido, para los
avisos de compatibilidad del reproductor. Es informativo y no editable por PATCH.
P07 añade cover_source para imagen propia, manual, heredada o predeterminada.
Un título provisional no implica
identificación. Asset perdido devuelve 404 con code `media_missing`; no devuelve
un archivo distinto ni elimina la pista. Rangos se prueban también después de
reiniciar y al mover la barra desde el navegador.

Audio incluye `Accept-Ranges: bytes`, `Content-Length`, `ETag`, `Last-Modified`,
`X-Content-Type-Options: nosniff` y `Cache-Control: private, no-cache`. No incluye
nombre original ni clave de almacenamiento. Solo resuelve recursos de audio admitido
gestionados, regulares y con el tamaño registrado; duración en `duration_ms`.
Desde O06 también sirve los otros formatos admitidos con su MIME correspondiente;
las reglas de acceso y rangos no cambian. Opus bajo .ogg se guarda con extensión
interna canónica .opus, conservando todos los bytes y el nombre original como dato.
Archivo ausente/inválido devuelve 404 `media_missing`; acceso denegado u otro
fallo de almacenamiento devuelve 503 `media_unavailable`, conservando la pista.
Errores de rango los genera FileResponse: 400/416 pueden tener cuerpo de texto
del framework; 416 incluye `Content-Range: bytes */tamaño`.

## 3. Playlists

Implementado en P11, sin nueva migración. Máximo 1000 canciones por lista.
Listado devuelve image_url y track_count sin items; detalle y escrituras devuelven
items completos en orden. Ver [validación](VALIDACION_P11.md).

| Método y ruta | Entrada / salida | Regla |
| --- | --- | --- |
| `GET /playlists` | q y paginación. | Resumen con apariencia e imagen. |
| `POST /playlists` | name, appearance opcional (vinyl por defecto), image_asset_id opcional. | 201; lista inicialmente vacía. |
| `GET /playlists/{id}` | Nombre, apariencia, imagen, revision e items ordenados (resúmenes de pista). | ETag versionado. |
| `PATCH /playlists/{id}` | name/appearance/image_asset_id; null retira imagen. | `If-Match` obligatorio; valida asset. |
| `PUT /playlists/{id}/tracks` | `{track_ids: [UUID, ...]}` en orden. | `If-Match` obligatorio; reemplazo atómico, sin IDs repetidos ni inexistentes. |

Guardar cambios de nombre/imagen y orden utiliza peticiones serializadas con
la revisión devuelta, no dos escrituras simultáneas con la misma revisión.
Cada éxito devuelve playlist completa y nuevo ETag. Lista vacía válida;
una pista por lista como máximo. Operaciones de usuario en P11 incluyen añadir,
quitar y reordenar usando el reemplazo de secuencia. No se borra la pista original.

Actualización P14 de recursos: purpose=wall acepta PNG/JPEG (normalizados sin
reducir dimensiones dentro del límite) y GIF de hasta 5 MiB, 4096 por lado/16 MP,
200 fotogramas y 32 MP decodificados totales. Verifica todos los fotogramas y
crea preview PNG del primero. SVG y APNG no admitidos. Respuesta de wall:
`id`, `mime_type`, `width_px`, `height_px`, `frame_count`, `content_url` y
`static_preview_url` (null para estáticos). GIF conserva bytes verificados;
estáticos se normalizan a PNG y deben seguir cabiendo en 5 MiB. Repetir carga
idéntica recupera el asset existente. Quitar objetos no borra estos recursos.

## 4. Muro por álbum y concurrencia

Implementado en P12 con `0005_album_walls`; ver [validación](VALIDACION_P12.md).
Fondo inicial #242038, esquema/revisión 1 y elements vacíos. Colores se devuelven
en mayúsculas; rotación normalizada a [−180,180), valores finitos. Comprobación
rotada sobre lienzo 1000 × 700 con tolerancia `1e-7` unidades. Orden por z_index/UUID.
Referencias visuales PNG/JPEG existentes; GIF requiere recurso gestionado GIF con
máximo 200 fotogramas (subida implementada en P14). GET de contenido admite ese recurso GIF.
Campos adicionales o recursos incompatibles/ausentes: 422 sin reemplazo parcial.
P13/P14 implementan renderizado, edición de fondo y carga/movimiento/borrado.

| Método y ruta | Función |
| --- | --- |
| `GET /albums/{id}/wall` | Devuelve composición persistida y ETag; un álbum tiene muro inicial creado en P12. |
| `PUT /albums/{id}/wall` | Reemplaza color y lista completa con `If-Match`; éxito 200 con composición y ETag nuevos. |
| `POST /albums/{id}/wall/reset` | `If-Match` obligatorio; vuelve a fondo predeterminado y elements vacíos, incrementando revisión. |

Regla compartida para recursos versionados: GET devuelve ETag opaco con tipo,
ID y revisión, por ejemplo `"wall-22222222-2222-4222-8222-222222222222-3"`.
La escritura manda ese valor en `If-Match`. Sin cabecera, 428; si no coincide,
412 con code `revision_conflict`, `current_revision` y `current_etag`, además
de cabecera ETag actual, para recargar. Comprobación
e incremento deben ser atómicos en BD. No se admite `If-Match: *` para saltar
el control. La misma regla aplica a tracks, álbumes, playlists y fichas con sus prefijos.

Ejemplo de PUT; UUIDs y datos ilustrativos, sin correspondencia con una BD real:

```json
{
  "schema_version": 1,
  "background_color": "#242038",
  "elements": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "asset_id": "44444444-4444-4444-8444-444444444444",
      "kind": "poster",
      "cx": 0.3,
      "cy": 0.4,
      "width": 0.2,
      "height": 0.3,
      "rotation_deg": 15,
      "z_index": 0
    }
  ]
}
```

La respuesta añade `id` del muro, `album_id`, `revision`, `updated_at` y URLs
de visualización resueltas para los assets (content_url y static_preview_url); solo los campos del ejemplo se
envían al guardar. UUID de elemento nuevo puede generarse en cliente y debe ser
único. No se aceptan IDs de otro muro, assets de audio ni posiciones fuera de los
límites rotados del modelo. Máximo 30 elementos, sin IDs repetidos; validación
de toda la composición antes de sustituir filas, con rollback completo si falla.

Cliente conserva ID de álbum y secuencia de edición por petición; una respuesta
de A nunca se usa para hidratar B. Un fallo de red no garantiza si el servidor
confirmó: GET y comparación de composición/revisión resuelven estado antes de
reintentar. No reenviar escrituras de forma ciega tras timeout.

## 5. Fichas, trabajos e IA

### P18 implementado: preparación de metadatos

P18 usa `prepare_metadata`, sin análisis acústico, ficha ni embedding. No confundir
«completed» con indexación semántica. Migración `0006_processing_jobs`.

| Método y ruta | Contrato efectivo P18 |
| --- | --- |
| `POST /tracks/{id}/processing-jobs` | JSON `{}` o `{ "operation": "prepare_metadata" }`; 202 con trabajo completo. Campos adicionales/otra operación: 422. Captura revisión de pista en servidor. Reutiliza la misma fila de pista/operación/versión, incluso si está terminada o fallida. |
| `GET /tracks/{id}/processing-jobs` | `{items, limit:10}`, diez trabajos más recientes; no-store. No devuelve un listado completo paginado. |
| `GET /jobs/{id}` | Trabajo con id, track_id, operation, input_version, status, attempts, error_code/error_message, result, is_current, status_url y fechas. 404 si no existe. |
| `POST /jobs/{id}/retry` | 202, reutiliza fila. Solo error/stale, entrada actual y menos de tres adquisiciones; de otro modo 409. No requiere reimportar audio. |

Estados: pending/processing/completed/error/stale. attempts aumenta al adquirir,
no al solicitar. Un reinicio convierte processing en error/interrupted sin
reintento automático; pending permanece en cola. is_current compara versión
histórica con revisión de pista actual, incluso después de completar.
result solo aparece en completados y contiene metadatos ya existentes, hash y aviso
de alcance; errores no publican excepciones, rutas privadas ni credenciales.
No modifica pista ni su ETag. El trabajador local serializa ejecución y la API
no espera su resultado. Ver PROCESAMIENTO.md y VALIDACION_P18.md.

### Diseño posterior: fichas, embeddings y exploración

**Actualización P19:** GET/PUT /tracks/{id}/description ya están implementados.
GET devuelve 404 description_missing si no existe, o ficha con ETag. PUT devuelve
200, exige If-None-Match:* al crear e If-Match al actualizar; 428 si falta condición,
412 si hay conflicto, 422 si son inválidos el cuerpo/condiciones simultáneas.
Admite source manual/verified/metadata y source_details obligatorio. text puede
ser vacío; features es lista de {name,value,source,evidence,interpretation} con
atributos permitidos y límites en FICHAS_MUSICALES.md. model no es admisible.
Version/content_hash cambian al corregir contenido; no-op conserva versión/ETag.
Respuesta añade can_index, needs_indexing, index_status=not_indexed,
input_track_revision, metadata_stale e index_notice. No son pruebas de embeddings.
GET /tracks/{id}/description/versions/{version} consulta snapshot con historical=true
o 404 description_version_missing. GET de pista añade content_sha256 de solo lectura
para vincular corpus por hash; no cambia su revisión por crear/corregir ficha.
Las rutas index-jobs/explore/search y el estado compuesto de indexación de pista
siguen siendo diseño P20–P23. El contrato efectivo P19 tiene prioridad sobre las
propuestas de la tabla histórica siguiente. Ver VALIDACION_P19.md.

La tabla siguiente y `index_status` son diseño para P19–P23; no están implementados
por P18. GET /jobs y retry ya existen con el contrato efectivo anterior; se
extenderán al habilitar nuevas operaciones y versiones de entrada.

Contratos reservados para P18–P23; no requieren elegir proveedor en P02.

| Método y ruta | Entrada / salida | Condición |
| --- | --- | --- |
| `GET /tracks/{id}/description` | Ficha con text, features, source, source_details y version, o 404 `description_missing`. | Fuente e inferencias explícitas. |
| `PUT /tracks/{id}/description` | text, features y fuente manual/verified; `If-Match` de ficha. | Para creación únicamente `If-None-Match: *`; conflicto si ya existe. Fuente model solo desde integración interna. |
| `POST /tracks/{id}/index-jobs` | Solicita indexación de ficha actual; devuelve 202 `{job_id, status, status_url}`. | Trabajo activo equivalente se reutiliza; sin ficha, 409. |
| `GET /jobs/{id}` | Estado, operación, input_version, error_code y mensaje seguro. | No exponer prompts privados completos ni credenciales. |
| `POST /jobs/{id}/retry` | Nuevo intento controlado, 202 con trabajo/URL. | Solo error recuperable e input actual; si cambió, 409 y pedir nueva indexación. |
| `POST /explore/search` | `{query, limit}`; query 1–1000 caracteres tras recorte, limit 1–20. | Respuesta 200 ordenada o error de proveedor 503/timeout 504. |

Editar ficha aumenta version; no obliga al usuario a esperar una indexación
para escuchar. El GET de pista también expone `index_status`:
`missing_description`, `not_indexed`, `pending`, `processing`, `ready`, `stale`, `error`.
No presentar stale como ready ni enviar un vector de otra configuración al buscador.

Respuesta semántica propuesta:

```json
{
  "query": "electrónica tranquila",
  "status": "ok",
  "model_key": "proveedor-modelo-configuracion-por-seleccionar",
  "results": [
    {
      "track_id": "11111111-1111-4111-8111-111111111111",
      "distance": 0.21,
      "description_version": 2,
      "explanation": "Su ficha registra sintetizadores suaves y energía baja.",
      "explanation_source": "generated",
      "evidence": [{"field": "features.energy", "value": "low"}]
    }
  ],
  "warnings": []
}
```

El ejemplo ilustra estructura, no el resultado de un modelo real. `distance`
es distancia según la métrica registrada, no confianza; no se muestra como %.
`status` distingue `ok`, `no_library`, `no_indexed_tracks`, `no_matches`.
Sin resultados, devolver results vacíos y estado pertinente. No hay un umbral
universal ya aprobado; calibrar criterio de coincidencia con P17/P22.

Si solo falla generación de explicación, `explanation_source` será `recorded`
y se usará texto basado en la ficha con warning. Si falla generar embedding,
no se simulan coincidencias. Resultados se validan contra pistas/fichas recuperadas
antes de responder y se completan con resúmenes para la interfaz. Una ficha
eliminada/cambiada durante la consulta se excluye o se vuelve a recuperar.

## 6. Cambios futuros y comprobación

P20 efectivo: GET /ai/status (200, no-store) devuelve provider, enabled, configured,
available, embedding_model, dimensions, generation_model, prompt_version,
verification=not_checked y notice. No devuelve clave ni llama a OpenAI; available
es solo configuración, no cuota/conectividad demostrada. No hay ruta pública de
generación/embedding ni prueba facturable por HTTP en P20. Adaptadores internos
y comando explícito app.ai_check --live en INTEGRACION_IA.md. Los rechazos reales
por credit_balance_exhausted mantienen pendiente el cierre real de la integración.

No se exponen endpoints de favoritos, estaciones, reconocimiento, cuentas ni
locutor antes de habilitar sus pasos. El API de cada función aparece con su
implementación; P03 solo necesita health y estructura, no rutas ficticias que
simulen resultados finales.

Al implementar, comprobar: validación de esquema, estados HTTP, paginación,
archivos inválidos, duplicados concurrentes, revisiones en conflicto, rollback,
audio parcial y caída de IA. Mantener ejemplos sincronizados con el OpenAPI real.
En P02 únicamente se revisó coherencia entre contrato, datos y pantallas; no se
han ejecutado pruebas HTTP ni de base de datos.
