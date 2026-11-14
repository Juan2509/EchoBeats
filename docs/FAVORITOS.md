# Favoritos — P24

Favoritos explícitos para la instalación local de un usuario. No hay cuentas,
propiedad por tenant ni historial de escucha. Escuchar o decorar un muro no añade
favoritos. P24 no cambia recuperación, distancias, RRF ni recomendaciones: P25
definirá y evaluará ese uso de preferencias.

## Uso

Pulsar el corazón junto a una pista en Biblioteca/álbum, playlist, Explorar o
reproductor. El botón muestra el estado confirmado por el servidor; pulsarlo de
nuevo lo desmarca. En **Biblioteca → Favoritos** se consultan las canciones
guardadas, con búsqueda por título, artista o álbum y páginas de 24.
La reproducción obtiene únicamente la cola de favoritos del filtro seleccionado,
sin reiniciar el audio al marcar o desmarcar. Una cola que ya está sonando conserva
su selección; quitar un favorito no interrumpe ni elimina la canción.

El estado se comparte entre controles de una misma sesión. Mientras guarda, todos
los controles de esa pista quedan bloqueados. No se anuncia éxito optimista ni
se repite automáticamente una escritura. Si se pierde la respuesta, se muestra
resultado incierto y se exige **Consultar estado** antes de otra modificación.
El servidor puede completar una solicitud ya enviada aunque se pierda su respuesta.
Al volver a enfocar la ventana se consultan de nuevo los controles visibles; entre
ventanas se aplica el último estado escrito en el servidor, sin sincronización en
tiempo real. Reabrir la página recupera siempre PostgreSQL, no almacenamiento local.

## Contrato

- `GET /api/v1/tracks/{id}/favorite`: `{track_id, favorite, created_at}`.
- `PUT /api/v1/tracks/{id}/favorite`: cuerpo `{favorite: true|false}` estricto,
  sin campos adicionales. Devuelve el estado confirmado. Es idempotente: repetir
  true conserva la fecha original, repetir false no crea filas ni historial.
- `GET /api/v1/favorites?q=&limit=24&offset=0`: página habitual de pistas completas,
  total y paginación. `limit` 1–100; texto literal hasta 200 caracteres. Orden por
  título e ID, igual al catálogo; la búsqueda conserva tildes y escapa `%`, `_`, `\`.

Pista inexistente: 404; entrada inválida: 422; origen de escritura ajeno: 403;
BD no disponible: 503. Respuestas sin caché. UUID validado y SQL parametrizado.
No se devuelve ni se usa una clave API. No hay solicitudes a OpenAI en este flujo.

## Persistencia y concurrencia

Migración `0009_favorites`, después de `0008_track_embeddings`. Tabla `favorite`:
`track_id` UUID PK/FK hacia track con RESTRICT y `created_at` con zona horaria.
Una fila por canción, sin duplicados. Las escrituras toman bloqueo de la pista,
aplican el estado solicitado y confirman en una transacción; incluso las primeras
escrituras sobre una pista quedan serializadas. No cambian revisión de metadatos,
fichas, vectores, playlist ni medios originales.

El listado usa una instantánea REPEATABLE READ para total y elementos. Downgrade
rechazado si existen favoritos para evitar perder preferencias. Probar reversiones
solo en bases aisladas. Respaldo previo y evidencia en [VALIDACION_P24.md](VALIDACION_P24.md).
