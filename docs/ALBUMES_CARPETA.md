# Álbumes como carpetas y retirada de canciones

Ampliación solicitada el 15 de noviembre de 2026, posterior a P28.

## Uso

- Inicio → Crear álbum: nombre, Vinilo o Portada e imagen PNG/JPEG opcional
  (hasta 5 MiB), con vista previa. El álbum puede estar vacío.
- Biblioteca → importar: primero elegir un álbum; sin destino no se habilitan
  los archivos. Dentro del álbum, Añadir música a este álbum fija ese destino.
- Las etiquetas del archivo no sustituyen la carpeta elegida. Un duplicado activo
  en otro álbum se conserva allí y se informa: importar no mueve canciones.
- Fichas y opciones del álbum → elegir canción → Eliminar canción de la biblioteca.
  En el listado general también está dentro de Ficha y opciones. Hay confirmación.
- La canción retirada desaparece del catálogo, favoritos visibles, playlists,
  búsquedas y acceso al audio. Si estaba sonando se detiene. El archivo original,
  fichas, versiones, favoritos y asociaciones históricas se conservan. Volver a
  importar el mismo contenido restaura el mismo ID y permite elegir su destino.

El nombre y portada se guardan en la base de datos. La presentación Vinilo/Portada
y los fondos continúan siendo preferencias locales de navegador/origen. Se quitó
la alternativa redundante «Usar predeterminada» de la presentación por álbum.

## Fondos y lienzo

La X está sobre la miniatura de imagen propia, tanto para descartar una imagen
preparada como para quitar la seleccionada. No aparece en Synthwave, Vaporwave
ni en la tarjeta de herencia del fondo principal. Quitar libera la selección local,
sin borrar archivos compartidos. Principal, álbum y muro conservan su ámbito.

El lienzo muestra el recorte: arrastrar mueve, doble clic/R o el botón Rotar
cambia al giro con cursor, flechas ajustan y Shift aumenta el paso. La rueda
acerca/aleja (Ctrl/Meta se reservan al navegador); también hay deslizador de zoom,
encuadre y Centrar. Aplicar conserva posición y giro sin modificar el original.
El usuario puede aumentar zoom para cubrir los espacios que deje una rotación.

## API y consistencia

- `POST /api/v1/albums` admite `cover_asset_id` opcional y valida su propósito.
- `POST /api/v1/imports?album_id=<uuid>` fija destino. La interfaz lo exige;
  el parámetro sigue opcional en API por compatibilidad con clientes anteriores.
  Sin él permanece la importación por etiquetas.
- `DELETE /api/v1/tracks/{id}` exige `If-Match` vigente (428 ausente, 412 obsoleto).
  La respuesta confirma `deleted` y `original_preserved`. Ante respuesta incierta
  la interfaz consulta antes de permitir otra acción; no reintenta DELETE solo.
- La retirada es lógica (`track.deleted_at`), versionada y atómica. Las playlists
  relacionadas cambian de revisión y ocultan la pista. Los trabajos pendientes o
  en curso quedan obsoletos y no pueden publicar resultados después de retirarla.
  Las lecturas y recuperación semántica excluyen las pistas retiradas.
- Reimportar el hash retirado restaura la fila y conserva su historia. No hay
  purga física de medios ni borrado del historial como parte de esta función.

## Migración y validación

`0010_track_deletion`, después de `0009_favorites`, aplicada a la instalación
principal tras respaldo privado:
`backups/echobeats_before_track_deletion_1794760458317.dump` (43 315 bytes),
con manifiesto SHA-256. No contiene copia de medios. Downgrade rechaza filas
retiradas; esa protección se probó exclusivamente en una base aislada.
`alembic current` confirmó head y `alembic check` no encontró nuevas operaciones.

- 244 pruebas backend aprobadas, con bases y medios temporales y sin proveedor IA.
  Las tres nuevas cubren creación/portada, destino, duplicados, eliminación HTTP,
  precondiciones, filtros, conservación, trabajadores y restauración por hash.
- 95 pruebas frontend y build de producción aprobados.
- Chrome aislado: crear con portada, importar al destino, retirar una canción,
  seleccionar destino obligatorio en biblioteca, X protegida, arrastre/giro
  persistidos y creación a 360/768 px. Capturas locales `folder-create*.png`,
  `folder-deleted.png`, `wallpaper-cursor-crop.png` revisadas. Canvas real;
  catálogo, subidas y escrituras simulados en el navegador. No se borraron canciones
  ni se crearon álbumes de prueba en la instalación personal.

No se reanudaron llamadas reales a OpenAI ni se cierran pendientes de escucha,
evaluación y aceptación previos. Se conservan todos los medios, incluidos los
506 MP3 sin fila. No se creó commit.
