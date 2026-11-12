# Validación P10 — Reproductor compartido y estado musical

12 de noviembre de 2026. Implementación lista; recorrido manual de audio pendiente.

## Entregado

- Un PlayerProvider con un único elemento audio, fuera del contenido que cambia
  con la ruta. Navegar por Inicio/Biblioteca/Álbum/Explorar no desmonta el audio.
- Selección por botones accesibles en la lista de canciones o dentro de un álbum.
  La pista activa se identifica en las listas; la barra muestra sus datos propios,
  aunque la vista muestre un álbum distinto.
- Reproducir/pausar, anterior/siguiente, avance temporal y volumen (incluido cero).
  Anterior en la primera pista vuelve a cero; Siguiente en la última se deshabilita.
  Fin de pista continúa con la siguiente y fin de lista se detiene.
- Portada propia/heredada/predeterminada, título, artista, álbum, tiempo real y
  duración. La duración inicial de la ficha se sustituye por la del audio cargado.
- El avance se habilita al disponer de metadatos reales; muestra una previsualización
  al arrastrar y confirma al soltar, terminar una tecla o perder foco.
- Cola completa del álbum o búsqueda, recuperando todas las páginas de fichas;
  el clic inicia audio antes de esperar al fetch para conservar el gesto del usuario.
  No se descargan todos los MP3. La cola no cambia por navegar a otra pantalla.
- Lista pendiente con controles de cambio deshabilitados; un fallo de recuperación
  usa las pistas de la página seleccionada y muestra esa limitación.
- Errores de carga/decodificación/red y rechazo de play con mensajes y reintento.
  No se presenta reproducción exitosa solo por haber pulsado el botón.
- Promesas, colas y eventos obsoletos no actualizan otra pista. La pausa durante
  una carga cancela la intención de reproducir; también se manejan pausas externas.
- Guardados de metadatos actualizan la ficha activa sin reiniciar el MP3. Respuestas
  de revisión anterior no sustituyen los cambios nuevos.
- Barra en el layout, adaptable a ventanas pequeñas, con etiquetas, foco y rangos
  nativos utilizables por teclado. Sin restaurar pista/posición al recargar ni autoplay.

P10 no añade autenticación, servicios externos, migraciones ni dependencias.
Los botones de playlists se incorporan en P11; aleatorio/repetición siguen en O08.

## Pruebas automáticas

`npm test` usa node:test y la eliminación de tipos de Node 24, sin librerías nuevas.
Hay **13 casos superados en Windows y Docker** sobre el controlador real con un doble de HTMLAudioElement y la
recuperación de colas con respuestas HTTP controladas:

- Inicio sin autoplay, selección, sincronización de datos y tiempo y pausa/reanudación.
- Rechazo tardío de play, selección rápida y colas antiguas.
- Pausa durante play pendiente, pausa externa y pause natural de fin de pista.
- Anterior/siguiente, límites, fin de lista y conservación del volumen.
- Fin durante preparación de cola, con continuación o pausa explícita.
- Seek antes/después de metadatos, valores fuera de rango y volumen cero.
- Bloqueo de reproducción del navegador, errores de red y reintento.
- Eventos de otra fuente y revisiones antiguas de metadata.
- Desmontaje y liberación de recursos con peticiones/promesas pendientes.
- Eventos antiguos encolados frente a una fuente nueva sana.
- Recuperación de 103 pistas en varias páginas, conservando filtros y sin pedir audio.
- Fallo de lista completa y alternativa de página visible.

Varias condiciones se comprueban en el mismo caso. Los dobles no son prueba de
decodificación, escucha audible, gestos de slider o continuidad real en navegador.

La suite backend con PostgreSQL aislado mantiene **57 pruebas superadas**, sin
avisos; incluye audio real, rangos, importación, metadata y persistencia de datos.
TypeScript y build Vite correctos en Windows y Docker; Compose válido.
Las imágenes base mantienen locks y digests previos; se reconstruyó frontend
para incorporar el script de pruebas. No se añadieron dependencias.
Auditoría final de medios sin faltantes, huérfanos, staging ni modificaciones.
Servicios de comprobación detenidos, conservando `.env`, volumen y MP3 existentes.

Comandos desde la raíz con servicios iniciados e imagen frontend actualizada:

```bash
docker compose exec frontend npm test
docker compose exec frontend npm run build
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error
```

En Windows también: `cd frontend`, `npm ci`, `npm test`, `npm run build`.
Compose monta tests como solo lectura para que la suite refleje el código actual.

## Revisión manual pendiente y límites de la evidencia

El control nativo de Brave detectó actividad del usuario en la ventana y no
permitió abrir la prueba. Se detuvieron las acciones UI; no se afirma reproducción,
continuidad audible, captura visual ni aceptación funcional completa de CA-01/CA-03.
P08 y P09 conservan sus comprobaciones manuales pendientes.

Para cerrar P10, con MP3 propios o fixtures autorizados:

1. Importar y abrir Canciones o un álbum; reproducir una pista. Verificar datos,
   progreso real, pausa/reanudación, seek a mitad del audio y volumen cero/parcial.
2. Mantener audio y navegar Inicio → Biblioteca → otro álbum → Explorar → Atrás.
   Confirmar que sigue la misma pista/posición y que la barra no adopta el álbum visto.
3. Con dos pistas, comprobar anterior en primera, siguiente, avance automático
   al terminar y detención al final. Verificar que no queda audio superpuesto.
4. Probar cambios rápidos de pista y error de archivo en un entorno de prueba;
   reintentar y comprobar que biblioteca/navegación siguen disponibles.
5. Revisar teclado y anchos 360/768/1280, barra/progreso/foco y ausencia de controles
   ocultos por la barra. Recargar y comprobar que no comienza audio automáticamente.

No usar archivos de la biblioteca principal para simular pérdidas o corrupción.
La cola y el volumen viven en memoria de la pestaña; persistirlos no está incluido.
Sin commit automático. Siguiente implementación: P11, gestión de playlists.
