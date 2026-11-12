# Validación P09 — Entrega de audio y avance temporal

12 de noviembre de 2026. Implementación lista; reproducción/seek manual pendientes.

## Implementación

- GET `/api/v1/tracks/{id}/audio` resuelve el asset desde la pista, sin admitir
  rutas del cliente ni exponer nombres originales/ubicaciones del almacenamiento.
- Solo sirve MP3 gestionados: kind audio, MIME audio/mpeg, archivo regular dentro
  de MEDIA_ROOT y tamaño igual al registrado. Comprueba apertura antes de enviar.
- FileResponse de Starlette 1.10.0 transmite por bloques de 64 KiB y soporta
  rangos de bytes, sufijos, rangos abiertos/múltiples y validación If-Range.
  Sin lectura completa ni cálculo de hash del audio por cada petición.
- 200 completo, 206 parcial con Content-Range, 416 fuera del tamaño y 400 para
  rango mal formado. Los errores de rango conservan el formato nativo de Starlette.
- HEAD devuelve cabeceras del recurso completo, sin cuerpo e ignorando Range.
- Content-Type audio/mpeg, inline, nosniff, Accept-Ranges bytes, Content-Length,
  ETag, Last-Modified y caché privada con revalidación.
- `audio_url` relativa en detalle/listados de pistas; duración mediante duration_ms.
- 404 para pista inexistente o audio ausente/inválido; 503 de almacenamiento
  inaccesible. Mensajes controlados sin rutas; ningún error elimina la pista.
- Sin migraciones, dependencias nuevas ni reescritura de originales. La interfaz
  y estado musical compartido pertenecen a P10.

Se revisó el código instalado y la [documentación oficial de FileResponse](https://starlette.dev/responses/#fileresponse).
Las comprobaciones siguientes corresponden a la versión bloqueada del proyecto.

## Pruebas automáticas y HTTP

Suite PostgreSQL en bases aleatorias aisladas, `pytest -W error`: **57 pruebas**.
Los archivos ausentes, corruptos, enlaces externos, directorios y permisos se
simulan exclusivamente en fixtures temporales; no en la biblioteca principal.

Cobertura de P09:

- Bytes completos iguales al MP3 original, cabeceras y URL pública.
- Rangos inicial, intermedio, abierto, sufijo y final limitado por tamaño.
- If-Range por ETag/fecha y token obsoleto; rangos múltiples y Content-Length.
- 400, 416 con tamaño; UUID inválido y pista inexistente.
- Ausencia, truncamiento, directorio, kind incompatible, symlink externo y fallo
  de permisos, sin exponer rutas ni perder datos del catálogo.
- HEAD sin cuerpo, incluido Range; contrato OpenAPI con GET/HEAD distintos.
- TypeScript y build Vite correctos. No cambia el esquema de PostgreSQL.

Por HTTP real a través de Vite en localhost:5173, la pista sintética de P08
`af8bf4b6-2583-44a4-8b07-f457e62f94ed` devolvió HEAD 200, audio/mpeg, 96.675 bytes,
y GET Range 1000–1999 devolvió 206, longitud 1.000 y
`Content-Range: bytes 1000-1999/96675`. No se importaron nuevos archivos ni se
modificaron canciones del usuario para esta prueba.

Tras recrear el backend, el mismo rango conservó ID, tamaño, ETag y respuesta
206. Auditoría final sin medios faltantes, huérfanos, staging ni modificaciones.
Servicios de comprobación detenidos, conservando `.env`, volumen y medios.

## Navegador y cierre pendiente

Brave cargó la URL local del MP3 en su reproductor nativo: su árbol accesible
mostró controles de reproducción/volumen y duración de aproximadamente 12,084 s.
No se confirmó reproducir/pausar ni cambiar posición: el control UI reportó
actividad del usuario en la ventana e interrumpió los intentos de interacción.
La captura de pantalla tampoco proporcionó evidencia visual fiable del navegador.
No se afirma escucha audible ni recorrido completo del reproductor.

Para cerrar P09, abrir `audio_url` en el navegador, reproducir y mover la barra a
un punto intermedio; verificar avance y ausencia de error. La entrega parcial de
bytes ya está probada por API/proxy. P08 conserva su propia revisión visual.

El usuario autorizó P09 expresamente; depende de P07, sin requerir cerrar P08.
El siguiente bloque de implementación es P10. Sin commit automático.
