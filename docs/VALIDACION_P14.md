# P14 — Añadir, mover y quitar recursos visuales

Fecha: 13 de noviembre de 2026. Implementado sin commit.
P13 registrado por el usuario en `655add4`.

## Resultado

En «Editar pared» se pueden importar PNG/JPEG/GIF locales. Las imágenes estáticas
se añaden como póster, sticker o imagen; un GIF se identifica por su contenido y
se añade como GIF. Cada objeto recibe UUID propio y referencia a un recurso
persistido. Reimportar el mismo recurso devuelve su asset existente; dos objetos
pueden compartirlo sin compartir su identidad o posición.

Seleccionar un objeto permite arrastrarlo, moverlo con flechas (Mayús: paso mayor)
o con botones Izquierda/Arriba/Abajo/Derecha. El movimiento limita el rectángulo
rotado completo al lienzo 1000 × 700, incluso para diseños girados de P12.
Escape o pointercancel revierte solo el gesto actual. Quitar objeto o Supr/Retroceso
retira el objeto del borrador; el foco vuelve al campo de carga.

Solo se manipula en edición. Bloqueado no hay captura de puntero ni objetos
alcanzables por Tab. El lienzo contiene las decoraciones y sigue separado de las
pistas, navegación y reproductor. «Guardar pared» o «Bloquear diseño» confirma
fondo y objetos con el ETag actual. Guardado, carga y gesto en vuelo se serializan;
una respuesta de una vista abandonada no añade recursos al siguiente álbum.

No hay controles de tamaño, rotación ni orden todavía (P15). El guardado manual
y al bloquear conserva este incremento; autosave de todas las operaciones,
restablecimiento desde interfaz y recuperación integral siguen en P16.

## Archivos y límites

`POST /api/v1/assets` admite `purpose=wall`. `cover` y `playlist` conservan su
comportamiento PNG/JPEG anterior. El contenido real se inspecciona con Pillow,
sin confiar en MIME o nombre del cliente. SVG, formatos ajenos, archivos truncados
y PNG animado se rechazan. No se añaden dependencias ni migraciones.

- Hasta **5 MiB** por archivo y **6 MiB** por solicitud multipart.
- Hasta **4096 × 4096**, máximo **16 millones de píxeles** por imagen.
- GIF: hasta **200 fotogramas** y **32 millones de píxeles decodificados en total**.
  Se verifica cada fotograma y la estabilidad de las dimensiones del lienzo.
- Hasta **30 objetos** por muro, comprobado tanto por cliente como por API de muro.

PNG/JPEG se normalizan a PNG, conservando dimensiones dentro del límite y
transparencia; se retiran metadatos. El PNG normalizado también debe caber en
5 MiB. GIF conserva los bytes verificados y añade una preview PNG estática del
primer fotograma, hasta 1024 px por lado. Nunca se sobrescribe el archivo local
seleccionado ni se altera un audio original.

Recurso y preview se publican en la misma transacción de BD, con staging,
deduplicación y compensación conservadora ante rollback. Un fallo de disco se
traduce a 503 sin exponer rutas. Composición y carga son operaciones separadas:
si se abandona el borrador tras importar, el recurso puede quedar registrado sin
objetos asociados; no se borra automáticamente. Quitar un objeto tampoco borra
su archivo ni la preview, ni afecta otra composición que lo utilice.

La respuesta de carga incluye MIME, dimensiones, frame_count, content_url y
static_preview_url. La lectura del muro incorpora static_preview_url por objeto.
Es un campo de lectura; PUT sigue enviando solo los campos del contrato P12.

## GIF y accesibilidad

Con movimiento reducido se muestra la preview estática y no se solicita la
animación. El control «Animar GIF» permite activarla. Para referencias antiguas
sin preview se conserva el marcador «GIF en pausa». Imagen inaccesible mantiene
su alternativa visual y no bloquea los controles externos.

Los objetos en edición son botones con nombre por tipo/posición. Se puede
seleccionar con Tab y mover con flechas o botones sin arrastrar. Los controles
mantienen foco visible por encima de la barra de reproducción en móvil.

## Evidencias

- **112 pruebas backend superadas** con PostgreSQL real y avisos como errores:
  las 102 previas y 10 nuevas de visuales. Bases aleatorias aisladas.
- PNG/JPEG normalizados a dimensiones originales, metadatos retirados y
  deduplicación estable. GIF real de 3 y 200 fotogramas con preview PNG; rechazo
  de 201, presupuesto de decodificación, dimensiones/peso inválidos y SVG falso.
- Retirar un objeto de A conserva el GIF/preview y el objeto de B que comparte
  ese recurso. Fallo simulado al publicar GIF después de su preview revierte
  ambas filas y limpia únicamente los archivos nuevos de la operación fallida.
- **29 pruebas frontend superadas**, incluidas edición/bloqueo, movimiento y
  cancelación, límites rotados, identidad estable al guardar, límite 30, preview
  y tipo GIF real, archivo vacío y respuesta tardía al abandonar A.
- TypeScript/build correctos; `alembic check` sin diferencias y `pip check`
  correcto. La comprobación específica de visuales se repitió después de añadir
  la validación de dimensiones por fotograma.
- Chrome headless con perfil temporal: carga desde input real de PNG y GIF
  sintéticos, rechazo de SVG sin romper la pared, arrastre real, Escape,
  flechas, botones de movimiento y borrado con Supr. PUT/GET reales guardaron
  los cambios; recarga recuperó el muro bloqueado y el GIF restante.
- GIF local real pausado mediante su preview y activado mediante checkbox;
  respuesta HTTP con MIME image/gif. Esta vez no se usó una fixture de respuesta
  para acreditar la importación de GIF.
- Anchos **360/768/1280** sin desbordamiento horizontal y capturas revisadas.
  En 360 px se comprobó que el objeto enfocado estaba visible y respondía al
  teclado. Arrastrar estando bloqueado no cambió posición ni composición.
- Reinicio real del backend conservó composición, IDs, posición, recursos,
  preview, revisión y ETag. B no cambió y el PNG quitado siguió disponible.
- Audio sintético conservó fuente, paused=false y tiempo creciente al navegar,
  mover, guardar y bloquear. Se pausó al terminar; no acredita escucha audible
  ni seek manual de todos los formatos.
- Auditoría sin faltantes, archivos sin registro ni staging; los **2 audios
  originales** locales conservaron sus hashes SHA-256.

## Entorno y continuidad

Se crearon únicamente «Demostración P14 A» y «Demostración P14 B», vacíos de pistas,
y recursos sintéticos locales. A conserva un GIF movido; B conserva su muro
inicial. El PNG retirado permanece gestionado. Los archivos fuente de prueba se
conservan en data/, excluido de Git; no son una colección musical ni material
ajeno. Volumen, `.env`, respaldos y medios anteriores se conservan.

Servicios activos; Chrome temporal cerrado. CA-08 se revalidó con manipulación
real y bloqueo. CA-06/CA-07 completos y los pendientes previos de P08/P09/P10/O06
siguen sujetos a sus recorridos; esta entrega no los cierra automáticamente.

Siguiente: **P15 — rotar, redimensionar y ordenar objetos**.
