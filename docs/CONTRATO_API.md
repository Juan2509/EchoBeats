# Contrato inicial de API de EchoBeats

P02 · 12 de noviembre de 2026. Especificación previa a implementación.
P03 implementó health, P04 ready y P06 imports. P07 incorpora lectura/edición de
pistas y álbumes, listas paginadas de selección, extracción y assets de portada.
P08 incorpora búsqueda textual, listados filtrados y búsqueda agrupada.
Las rutas de audio, gestión de playlists, muros e IA siguen pendientes.
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
| `POST /imports` | multipart `files`, hasta 20 MP3. Respuesta 200 con resultado por archivo; cuerpo total excesivo rechaza solicitud con 413. | P06 implementado. |
| `GET /tracks` | album_id opcional, q y paginación; fichas de pistas. Dentro de álbum ordena por número, título e ID; sin álbum por título e ID. | P07/P08 implementado. |
| `GET /tracks/{id}` | Pista, álbum, artistas, duración, portada heredada y procedencia; `revision`. | P07. |
| `PATCH /tracks/{id}` | title, artist_names, album_id, track_number y cover_asset_id; `If-Match` requerido. Duración/archivo/procedencia no editables. | P07 implementado. |
| `POST /tracks/{id}/extract-metadata` | `If-Match` requerido; relee el original y conserva campos manuales. | P07 implementado. |
| `GET /albums` | q, paginación; id, título, artistas, portada y número de pistas. include_empty_system=false oculta «Sin álbum» cuando no tiene pistas; por defecto true conserva selección de P07. | P07/P08 implementado. |
| `POST /albums` | `{title, artist_names}`; crea álbum explícito y devuelve 201 con ID. | P07. |
| `GET /albums/{id}` | Resumen, datos, procedencia y ETag. Pistas se consultan paginadas en /tracks. | P07 implementado. |
| `PATCH /albums/{id}` | title/artist_names/cover_asset_id con `If-Match`; no permite cambiar system_key ni renombrar el álbum de sistema. | P07 implementado. |
| `GET /library/search` | q obligatoria no vacía; query y grupos tracks/albums/playlists con items/total/limit/offset/href, máximo 10 por grupo. href enlaza a biblioteca filtrada; playlists busca nombres existentes pero href=null hasta P11. | P08 implementado. |
| `POST /assets` | multipart file y purpose=cover; PNG/JPEG verificado, normalizado a PNG, devuelve 201. wall/playlist/GIF se incorporan después. | P07 para portadas; P11/P14 para otros usos. |
| `GET /assets/{id}/content` | PNG/JPEG validado con nosniff y caché privada; sin rutas arbitrarias ni audio. GIF se incorpora después. | P07 para portadas. |
| `GET` o `HEAD /tracks/{id}/audio` | Audio de pista válida. GET 200 completo o 206 para rango válido; 416 no satisfacible. HEAD devuelve cabeceras sin cuerpo. | P09. |

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
`duration_ms`, `cover_url` nullable y procedencia. `audio_url` corresponde a P09.
P07 añade cover_source para imagen propia, manual, heredada o predeterminada.
Un título provisional no implica
identificación. Asset perdido devuelve 404 con code `media_missing`; no devuelve
un archivo distinto ni elimina la pista. Rangos se prueban también después de
reiniciar y al mover la barra desde el navegador.

## 3. Playlists

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

## 4. Muro por álbum y concurrencia

| Método y ruta | Función |
| --- | --- |
| `GET /albums/{id}/wall` | Devuelve composición persistida y ETag; un álbum tiene muro inicial creado en P12. |
| `PUT /albums/{id}/wall` | Reemplaza color y lista completa con `If-Match`; éxito 200 con composición y ETag nuevos. |
| `POST /albums/{id}/wall/reset` | `If-Match` obligatorio; vuelve a fondo predeterminado y elements vacíos, incrementando revisión. |

Regla compartida para recursos versionados: GET devuelve ETag opaco con tipo,
ID y revisión, por ejemplo `"wall-22222222-2222-4222-8222-222222222222-3"`.
La escritura manda ese valor en `If-Match`. Sin cabecera, 428; si no coincide,
412 con code `revision_conflict` y revisión actual para recargar. Comprobación
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
de visualización resueltas para los assets; solo los campos del ejemplo se
envían al guardar. UUID de elemento nuevo puede generarse en cliente y debe ser
único. No se aceptan IDs de otro muro, assets de audio ni posiciones fuera de los
límites rotados del modelo. Máximo 30 elementos, sin IDs repetidos; validación
de toda la composición antes de sustituir filas, con rollback completo si falla.

Cliente conserva ID de álbum y secuencia de edición por petición; una respuesta
de A nunca se usa para hidratar B. Un fallo de red no garantiza si el servidor
confirmó: GET y comparación de composición/revisión resuelven estado antes de
reintentar. No reenviar escrituras de forma ciega tras timeout.

## 5. Fichas, trabajos e IA

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

No se exponen endpoints de favoritos, estaciones, reconocimiento, cuentas ni
locutor antes de habilitar sus pasos. El API de cada función aparece con su
implementación; P03 solo necesita health y estructura, no rutas ficticias que
simulen resultados finales.

Al implementar, comprobar: validación de esquema, estados HTTP, paginación,
archivos inválidos, duplicados concurrentes, revisiones en conflicto, rollback,
audio parcial y caída de IA. Mantener ejemplos sincronizados con el OpenAPI real.
En P02 únicamente se revisó coherencia entre contrato, datos y pantallas; no se
han ejecutado pruebas HTTP ni de base de datos.
