# Validación P08 — Navegación y biblioteca visual

12 de noviembre de 2026. Implementación lista; cierre visual pendiente.

## Entregado

- Inicio, navegación y rutas `/`, `/biblioteca`, `/albumes/:id` y `/explorar`.
  Explorar informa de su disponibilidad futura sin simular búsquedas de IA.
- Biblioteca con tarjetas de álbumes, portadas gestionadas o predeterminadas,
  artistas, cantidad de pistas y lista de canciones con duración.
- Detalle de álbum con pistas paginadas por número, título e ID.
- Búsqueda literal por título, álbum y créditos de pista/álbum, sin distinguir
  mayúsculas y conservando tildes. Hasta 200 caracteres; comodines SQL escapados.
- Paginación de 24 elementos; búsqueda, vista y página en URL, con Atrás/Adelante
  y recarga directa. Estados vacíos, sin coincidencias, carga, error y reintento.
- «Sin álbum» vacío se oculta en el dashboard; sigue disponible en selección de
  P07. Álbumes vacíos creados expresamente siguen visibles.
- Importación y editor P07 conservados; guardados actualizan la biblioteca y los
  formularios permanecen montados al navegar para conservar borradores.
- Peticiones de lectura con timeout, cancelación e invalidación de respuestas
  anteriores. Enlaces con foco visible, etiquetas y salto al contenido principal.
- GET `/library/search` devuelve grupos reales con hasta diez resultados, conteos
  y enlaces filtrados. Playlists solo consulta nombres existentes; su enlace es
  null hasta P11. La biblioteca visual usa directamente `/albums?q` y `/tracks?q`.

## Comprobaciones

- Suite PostgreSQL real aislada: 42 pruebas superadas con `pytest -W error`.
  Incluye filtros por relaciones, ausencia de duplicados, tildes, texto literal,
  paginación, número de pista y validación de consultas antes de acceder a BD.
- TypeScript y build Vite correctos en Windows y en el contenedor de referencia.
- `pip check` correcto en contenedor; `alembic check` sin diferencias de esquema.
- Auditoría de medios de solo lectura sin archivos faltantes, huérfanos o staging.
- Importación real del fixture original `tono_grave.mp3` por proxy del frontend;
  búsquedas por `TONO` y `grave` recuperan pista y álbum reales, con detalle y
  listado de pistas correctos. Ruta directa `/biblioteca?q=TONO` responde HTTP 200.
- Recreación de backend/frontend: misma pista e ID recuperados por la búsqueda.
  Auditoría posterior sin inconsistencias. Servicios de comprobación detenidos
  al finalizar, conservando `.env`, volumen y medios.

## Entorno y límites

En este equipo no existían `.env`, imágenes ni volumen de EchoBeats en Docker.
Se inició Docker Desktop existente y se generó `.env` privado sin imprimirlo.
Compose construyó imágenes desde los locks y creó `echobeats_postgres_data`.
Los otros contenedores y volúmenes del equipo se conservaron. Los datos de
demostración de sesiones anteriores eran de su entorno histórico; no se afirma
que estén presentes aquí. Se conserva la pista sintética importada para P08.

La instalación nativa opcional en Python 3.12 no se completó: el lock generado
para Linux carece de la dependencia condicional Windows `tzdata`. No se omitió
la verificación de hashes ni se alteró el lock para esta implementación; la
validación backend se realizó en Docker, que es el entorno de referencia.

La herramienta de control del navegador se detuvo porque no pudo identificar
la URL de Windows con confianza suficiente para aplicar su política. No hubo
inspección visual ni se usó una vía alternativa para eludir ese bloqueo.
Build y pruebas HTTP no certifican por sí solos el comportamiento visual.

**Pendiente para cerrar P08:** comprobar en navegador a 360, 768 y 1280 px:
inicio → biblioteca → búsqueda → álbum → Atrás/Adelante; importación y actualización
de portadas; foco/teclado; carga/error/reintento y conservación del borrador del
editor al navegar. RF-02 y RF-04 implementados para álbumes/canciones; playlists
completa RF-02 en P11. CA-09 comprobado por API, pendiente su recorrido visual.

No se implementó audio, edición de playlists, muros ni IA. Sin commit automático.
Siguiente: cerrar la revisión visual de P08 y después P09, entrega de audio.
