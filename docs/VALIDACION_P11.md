# P11 — Playlists persistentes y apariencia

Fecha: 13 de noviembre de 2026. Implementado sin commit.

## Resultado

Biblioteca incorpora la pestaña Playlists, búsqueda por nombre, paginación y
creación. `/playlists/:id` permite renombrar, añadir/quitar canciones, subir/bajar
su posición y guardar. Imagen PNG/JPEG propia o predeterminada, con presentación
de vinilo o tarjeta. No hay borrado de playlists ni muro por playlist.

La reproducción selecciona la lista guardada completa en su orden explícito,
sin descargar previamente sus audios. Un borrador debe guardarse antes de
reproducirlo. Editar una playlist no modifica álbumes ni archivos originales.
La cola activa conserva su selección hasta elegir otra pista, igual que P10.

Se reutilizan las tablas de P05: no hay migración ni nuevas dependencias.
GET devuelve ETag; PATCH y PUT de pistas exigen If-Match. Bloqueo de fila y
transacción protegen dos escrituras concurrentes. Sin revisión: 428; revisión
antigua o `*`: 412. Listas vacías válidas, máximo 1000 pistas sin duplicados;
UUID inexistente o datos inválidos: 422 sin modificar la secuencia anterior.

La imagen reutiliza `/assets` con `purpose=playlist`: PNG/JPEG verificado,
normalizado a PNG, hasta 5 MiB y límites de dimensiones de P07. Se conservan
recursos compartidos. No se admiten GIF/SVG para la imagen de una playlist.

Nombre/apariencia/imagen y pistas se guardan en dos solicitudes serializadas,
con la revisión devuelta por la primera. Si falla la segunda, la primera puede
haber persistido: la interfaz conserva el borrador, informa el posible guardado
parcial y permite recargar/reintentar. Elegir/retirar imagen guarda también el
borrador actual. Navegación, Atrás y cierre advierten sobre cambios pendientes.

## Comprobaciones ejecutadas

- 76 pruebas backend con PostgreSQL real y avisos como errores. Cada prueba
  usa una base aleatoria aislada; la principal no recibe downgrades ni tests.
- Casos nuevos: creación, recorte de nombre, orden, retirada/vaciado, imagen,
  reapertura con otra aplicación, álbumes intactos, conflicto real concurrente,
  UUID repetidos/inexistentes, null inválido, consulta literal y paginación.
- 16 pruebas frontend, incluidas cola de playlist en orden, selección siguiente,
  lista vacía y fallo HTTP; los tests del reproductor usan doble de audio.
- TypeScript y build Vite correctos; `pip check` correcto y `alembic check`
  sin operaciones nuevas. Auditoría de medios sin faltantes, huérfanos ni staging.
- Chrome headless con perfil temporal: crear lista, añadir canción, guardar,
  cambiar nombre/apariencia y cargar imagen mediante input real. Recarga recupera
  la lista. Otro recorrido añadió segunda pista, bajó la primera, guardó el orden
  y quitó una pista. Tab recorrió los campos, acciones y reproducción; controles
  de orden son botones
  nativos con etiquetas por canción. Capturas revisadas a 360/768/1280, sin
  desbordamiento horizontal. Chrome avanzó currentTime con paused=false al
  seleccionar la pista; esto no acredita escucha audible.

Se recrearon PostgreSQL, backend y frontend conservando el volumen; tras
completar el arranque, la respuesta HTTP coincidió exactamente con la guardada
antes del reinicio (ID, nombre, secuencia, imagen, apariencia y revisión), y la
imagen siguió respondiendo 200. Los servicios quedan activos para revisión local.

## Persistencia y entorno

El entorno Docker disponible no contenía contenedores/volúmenes EchoBeats ni
`.env`. Se creó configuración privada y volumen nuevo, sin alterar recursos de
otros proyectos. Se importaron únicamente los audios sintéticos `tono_grave.mp3` y
`pulsos_medios.mp3` y se
creó «Selección P11 verificada» con una imagen sintética de color turquesa.
No se editaron canciones del usuario. Medios, volumen y `.env` se conservan.

Los cierres manuales anteriores de P08/P09/P10/O06 no se consideran completados
por este recorrido limitado de P11. No se afirma escucha audible, seek manual
multiformato ni una revisión completa de accesibilidad de toda la aplicación.

## Repetir el recorrido

1. Arrancar según README y abrir Biblioteca → Playlists.
2. Crear lista, añadir dos canciones, cambiar orden con Subir/Bajar y guardar.
3. Renombrar, elegir apariencia y PNG/JPEG; comprobar la confirmación de guardado.
4. Recargar y reiniciar servicios conservando el volumen; revisar nombre,
   secuencia e imagen. Abrir los álbumes y comprobar que conservan sus pistas.
5. Abrir la misma lista en dos pestañas; guardar una y verificar que la segunda
   informa conflicto en lugar de sobrescribir. Recargar antes de reintentar.
6. Seleccionar una pista guardada y comprobar la cola y su orden en el reproductor.

Siguiente bloque: P12, muros persistentes por álbum.
