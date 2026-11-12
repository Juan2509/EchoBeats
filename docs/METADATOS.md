# Metadatos, álbumes y portadas — P07

12 de noviembre de 2026. Leer y corregir información de música ya importada.
No se consulta internet ni se utiliza IA para identificar una canción.

## 1. Uso desde la interfaz

La página inicial conserva la importación y añade «Revisa los datos de tu música».

1. Importar un MP3 o seleccionar una canción ya guardada.
2. Revisar título, artistas, álbum, número de pista, duración y portada.
3. Corregir los campos necesarios; introducir un artista por línea y seleccionar
   un álbum existente o crear otro para asignarlo.
4. Elegir una portada PNG/JPEG o solicitar la predeterminada si se desea.
5. Guardar. El formulario confirma los datos persistidos y su procedencia.

La duración proviene del audio y no se edita. Crear un álbum no mueve la canción
hasta guardar la asignación. Editar nombre/artistas de un álbum compartido afecta
a todas sus pistas; el diálogo lo indica y requiere guardar por separado. Primero
guardar o descartar cambios de la canción antes de editar el álbum.

Hay estados de carga, error, guardado y cambios pendientes. Cambiar de canción o
recargar datos pide descartar los cambios sin guardar. Al cerrar la pestaña con
un formulario modificado se utiliza el aviso del navegador. Un conflicto entre
pestañas conserva el formulario y pide recargar; nunca se reintenta una escritura
con una revisión nueva sin que el usuario revise los datos.

## 2. Datos del archivo y provisionales

Se leen etiquetas ID3v1/ID3v2 mediante Mutagen: título, artistas, título y artistas
del álbum, número de pista y portada APIC. `2/10` se interpreta como pista 2.
Los créditos múltiples se conservan en orden; no se divide un nombre como AC/DC
por barras o comas. La duración ya se calcula al importar.

Si faltan datos, título desde el nombre del archivo, artista desconocido, álbum
«Sin álbum», número vacío e imagen predeterminada. El audio sigue importado.
Datos vacíos o ausentes no se sustituyen por identidades inventadas.

La agrupación automática requiere título de álbum y créditos disponibles del
álbum, o artistas de la pista si no existen créditos de álbum. Se compara título
y créditos normalizados: álbumes homónimos con artistas distintos permanecen
separados. Si falta evidencia para agrupar, se mantiene «Sin álbum».

Los nombres de artista normalizados comparten identidad; se reutiliza la primera
grafía registrada. Editar créditos reasigna artistas de esa pista, no renombra
globalmente a un artista compartido. Los álbumes creados manualmente tienen ID
propio y no se fusionan por coincidir únicamente en el nombre.

La clave de agrupación del álbum importado se conserva al corregir su nombre o
créditos: nuevas pistas con las etiquetas originales pueden unirse al álbum ya
corregido. Las correcciones compartidas tampoco se deshacen al releer pistas.

## 3. Procedencia y prioridad de edición

`metadata_sources` distingue por campo `file`, `fallback` y `manual`.
Solo los campos efectivamente enviados en PATCH se marcan como manuales.
La interfaz envía cambios, no una copia completa de campos sin modificar.

«Volver a leer etiquetas del original» completa campos automáticos y conserva
los manuales, incluidos artistas vacíos, número nulo y portada predeterminada
elegida expresamente. Reimportar un duplicado actualiza sus campos automáticos
con la misma regla, mantiene ID y respeta las correcciones.

Cambiar datos de una pista no renombra su álbum. La asignación manual a otro
álbum es estable. El álbum de sistema no se renombra; seleccionar o crear otro.

Los MP3 originales no se reescriben: su hash y bytes siguen intactos. Estas
correcciones pertenecen a la base de datos. La revisión aumenta al cambiar la ficha
y queda disponible para la futura invalidación de descripciones/embeddings;
esos módulos todavía no existen y no se anuncia reindexación implementada.

## 4. Portadas

Se prefiere APIC de portada frontal; si no es válida se prueban otras candidatas
acotadas. Solo PNG/JPEG con hasta 5 MiB, dimensiones de hasta 4096 × 4096 y
16 millones de píxeles. Pillow verifica y decodifica la imagen, crea una versión
PNG estática de hasta 1024 × 1024 y descarta metadatos/contenido extra.
No se guardan referencias a imágenes remotas del archivo.

Una portada inválida se ignora con advertencia; no convierte un audio ya guardado
en rechazo. La interfaz usa un SVG propio predeterminado si falta o no carga la
imagen. El original APIC sigue dentro del MP3 intacto.

Cada pista puede tener portada propia. El grupo «Sin álbum» no recibe la portada
de una de sus canciones. Un álbum identificado puede tomar portada automática
si no tiene otra ni una decisión manual. Una portada manual del álbum no es
sobrescrita al extraer después otras canciones.

En la pista, portada propia prevalece sobre la heredada del álbum. Seleccionar
explícitamente la predeterminada guarda null manual y evita volver a heredarla.
Las portadas normalizadas idénticas reutilizan un recurso. Subir una portada y
cancelar su asignación puede dejar un recurso válido sin uso; no se borra solo,
para evitar perder imágenes compartidas o pendientes de asignación.

## 5. API disponible

| Método / ruta bajo `/api/v1` | Uso |
| --- | --- |
| `GET /tracks`, `GET /albums` | Listas paginadas para selección. `limit` 1–100, `offset` no negativo; pistas admiten album_id. Búsqueda textual q se añade en P08. |
| `GET /tracks/{id}`, `GET /albums/{id}` | Información y ETag. |
| `PATCH /tracks/{id}` | title, artist_names, album_id, track_number, cover_asset_id. |
| `POST /tracks/{id}/extract-metadata` | Releer el archivo conservando campos manuales. |
| `POST /albums` | Crear con title y artist_names. |
| `PATCH /albums/{id}` | Corregir title, artist_names o cover_asset_id compartidos. |
| `POST /assets` | Multipart con file y purpose=cover; por ahora solo portadas PNG/JPEG. |
| `GET /assets/{id}/content` | Solo imágenes de tipo admitido; nunca audio ni rutas arbitrarias. |

PATCH y extracción explícita requieren el `If-Match` exacto de la última lectura.
Sin él, 428; revisión desactualizada, 412; datos inválidos, 422; recurso ausente,
404; base no disponible, 503. Duración y procedencia no pueden modificarse desde
el cliente. Artistas vacíos y número/portada nulos son válidos para limpiar campos;
título y álbum no admiten null. Claves extra se rechazan.

`GET /tracks/{id}` incluye `cover_source` para distinguir la imagen propia, manual,
del álbum o predeterminada; la revisión y procedencia se guardan en BD. No se
incluyen todavía controles de reproducción ni búsqueda semántica.

## 6. Cambios de esquema y continuidad

`0003_metadata` añade portada individual a track, procedencia e import_key al
álbum. Conserva pistas, recursos, playlists y archivos existentes. No lee archivos
durante la migración ni intenta sobrescribir correcciones.

Para las pistas importadas antes de P07, usar «Volver a leer etiquetas» o reimportar
el mismo MP3: se detecta duplicado y se completa información automática con el
mismo ID. No se vuelve a subir una biblioteca completa como requisito de migración.

Consulta [VALIDACION_P07.md](VALIDACION_P07.md), [contrato](CONTRATO_API.md) y
[modelo](MODELO_DATOS.md). Siguiente: P08, navegación y biblioteca visual.

Fuentes consultadas:
[ID3 de Mutagen](https://mutagen.readthedocs.io/en/latest/api/id3_frames.html),
[Image de Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html),
[conflictos SQLAlchemy/PostgreSQL](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#insert-on-conflict-upsert).
