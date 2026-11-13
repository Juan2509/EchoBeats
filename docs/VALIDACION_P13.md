# P13 — Vista del muro, edición y bloqueo

Fecha: 13 de noviembre de 2026. Implementado sin commit.
P12 quedó registrado por el usuario en `4c5c0d4`.

## Resultado

La vista `/albumes/:id` compone panel de portada/datos/pistas, muro y reproductor
compartido. En escritorio usa dos columnas y en ventanas pequeñas se apila.
El lienzo conserva proporción 1000 × 700 y renderiza fondo y objetos persistidos
con centro, tamaño, giro y z_index. La composición queda recortada y aislada del
resto de la interfaz; sus elementos no interceptan clics de controles externos.

Cada entrada empieza en «Diseño bloqueado». «Editar pared» permite seleccionar
color o usar una muestra accesible por teclado. «Guardar fondo» confirma la
composición mediante PUT/If-Match, preservando todos los elementos y excluyendo
campos de solo lectura. «Bloquear diseño» guarda el color pendiente antes de
bloquear; sin cambios no escribe. Una petición en vuelo deshabilita edición y
nuevos guardados. Cambiar modo no crea ni reinicia el elemento de audio.

Este bloque muestra objetos existentes; añadir, mover y eliminar corresponde a
P14, y transformar/ordenar a P15. No hay aún tiradores ni arrastre, tampoco en
modo edición. Restablecimiento desde interfaz y coordinación completa de los
guardados de todas las transformaciones corresponden a P16. El cambio de color
actual se confirma con Guardar fondo o Bloquear diseño; no hay autosave por cada
variación del selector nativo.

## Estados y fallos

Carga, sin cambios, pendientes, guardando, guardado y error visibles. Una imagen
inaccesible muestra una alternativa en su posición. El fallo al cargar el muro
permite recargar y no impide consultar/reproducir las pistas del álbum.

Conflicto 412 conserva el borrador y solicita recargar la pared guardada. Un
fallo de red, respuesta no interpretable o 5xx se trata como resultado incierto:
no se anuncia éxito ni se repite PUT; se debe recargar antes de volver a editar.
La recarga pide confirmar si descarta cambios. Un rechazo confirmado como 422
conserva el borrador y permite reintentar la operación. Las respuestas antiguas
o recibidas después del desmontaje no hidratan otra vista.

Navegación interna, Atrás y cierre advierten sobre cambios pendientes/guardado
en vuelo. Aceptar salir durante una petición no cancela una transacción ya
recibida por el servidor: al regresar se vuelve a leer. No se guardan borradores
tras cerrar la página ni se afirma completada la recuperación integral de P16.

Los GIF guardados se pueden pausar. Con movimiento reducido se muestra un
marcador «GIF en pausa» y no se solicita su imagen hasta activarla; el cambio de
preferencia hacia movimiento reducido vuelve a pausarlos. La carga de GIF
continúa siendo parte de P14.

## Comprobaciones ejecutadas

- **25 pruebas frontend superadas**: 16 previas de reproductor/colas y 9 nuevas
  de muro. Cubren guardado sin pérdida de elementos, bloqueo inicial, una sola
  escritura, conflictos, resultado incierto, reintento confirmado, cargas tardías,
  desmontaje A/B y cabeceras/álbum de la respuesta.
- TypeScript y build Vite correctos. Sin dependencias, migraciones ni cambios de
  backend. No se repitieron las 102 pruebas backend de P12; su evidencia sigue
  en VALIDACION_P12.md.
- Chrome headless con perfil temporal: muros A/B de demostración cargados desde
  PostgreSQL real; fondo y elementos correctos. Anchos **360/768/1280** en modo
  bloqueado y edición, sin desbordamiento horizontal; proporción del lienzo
  medida y capturas revisadas. Un arrastre real con ratón sobre un objeto
  bloqueado no cambió su estilo ni la composición persistida.
- Espacio activó una muestra de color y Guardar fondo desde controles enfocados;
  cambio confirmado por API, con elementos intactos y B sin cambios. Navegar
  A→B→A y recargar mantuvo el fondo de cada muro y reinició el modo bloqueado.
- Tab en 360 × 800 alcanzó Editar pared con su centro visible y sin quedar bajo
  el reproductor. La vista desplaza el foco de los controles del muro si la
  barra lo tapa. Selector, muestras, guardado y bloqueo usan controles nativos.
- PUT 503 simulado solo en el navegador conservó borrador y solicitó recarga.
  Un cambio real por una segunda petición generó conflicto 412 en la vista
  antigua, sin sobrescribir la nueva composición. Recurso bloqueado por la red
  del navegador mostró «Imagen no disponible», conservando controles externos.
- Preferencia de movimiento reducido comprobada con una **fixture de respuesta
  temporal**: GIF pausado por defecto y activable. No se insertó ningún GIF en
  la biblioteca real ni se acredita con esa fixture la subida de GIF de P14.
- El tono sintético empezó a reproducirse desde Canciones y mantuvo la misma
  fuente, paused=false y tiempo creciente al navegar al muro y alternar modos.
  Se pausó al terminar. Esto acredita comportamiento del audio en navegador,
  no escucha audible ni seek manual de todos los formatos.
- Auditoría de medios sin faltantes, huérfanos ni staging. La demostración solo
  cambió el color del muro «Demostración P12 A»; B, recursos, pistas y playlists
  se conservaron. Servicios activos; Chrome temporal cerrado.

CA-08 queda cubierto para la vista y el bloqueo de P13. Al añadir manipulación
en P14/P15 se debe volver a comprobar que solo actúa en modo edición. No se
cierran automáticamente las revisiones previas de P08/P09/P10/O06, ni CA-06/CA-07
visuales completas de decoración, que requieren los próximos incrementos.

## Repetir el recorrido

1. Abrir Biblioteca → un álbum; comprobar que muestra su pared bloqueada.
2. Activar Editar pared, elegir color y Guardar fondo, o Bloquear diseño.
3. Recargar y alternar entre álbumes A/B; comprobar fondos y objetos distintos.
4. Usar Tab y Espacio, ventanas 360/768/1280 y reproducción mientras se edita.
5. Simular fallo/conflicto sin perder borrador ni anunciar guardado; recargar los
   datos persistidos antes de volver a guardar tras un resultado incierto.

Siguiente implementación: **P14 — añadir, mover y eliminar recursos visuales**.
