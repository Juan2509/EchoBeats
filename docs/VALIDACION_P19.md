# P19 — Fichas musicales con procedencia

13 de noviembre de 2026. Implementación y pruebas completadas; revisión visual
del editor pendiente. Próxima implementación P20.

## Entregables

- Ficha actual e historial durable con migración `0007_track_descriptions`.
- GET/PUT con precondiciones, versión, hash, fuente y evidencia por atributo;
  lectura de versiones históricas. Campos desconocidos se dejan sin inventar.
- Fuentes manual/verified/metadata; emoción, energía y contexto como
  interpretaciones manuales. No se admite source=model desde el editor/API.
- Fichas vacías/incompletas permitidas; no bloquean audio. Estado explícito de
  ausencia de embedding y necesidad de indexar posteriormente. Datos derivados de
  metadatos se señalan obsoletos cuando cambia la revisión de pista.
- Editor modal por canción, con protección de borrador ante conflicto, error,
  cierre y navegación. Compatible con el montaje de React StrictMode.
- Cinco propuestas P17 por hash sin emociones provisionales y cargador local
  con simulación predeterminada; conserva fichas existentes.

Uso y límites: [FICHAS_MUSICALES.md](FICHAS_MUSICALES.md).

## Evidencia ejecutada

- `docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error`:
  **135 pruebas aprobadas** en la versión final. Incluye **15 casos P19**:
  creación/actualización/historial, creación concurrente, precondiciones/conflictos,
  nueve entradas inválidas sin reemplazar la ficha, ficha incompleta/no-op,
  interpretación explícita, obsolescencia por metadatos, P18 sin sobrescribir ficha,
  downgrade protegido y corpus real. Algunas comprobaciones se agrupan en un caso.
- Las cinco propuestas de fichas se validaron contra sus WAV reales: importación
  a catálogo aislado, coincidencia SHA-256 expuesta por la API, creación de ficha y
  GET de audio con los mismos bytes. No se importaron a la biblioteca personal.
- `npm.cmd test`: **45 pruebas aprobadas**, incluidas tres nuevas de controlador:
  conflicto conserva borrador, guardado bloquea cambios, respuesta tardía de A no
  altera B y gateway envía condiciones correctas de creación/edición.
- `npm.cmd run build`: TypeScript y compilación Vite aprobados.
- Scripts preparar/cargar fichas: sintaxis Node comprobada; `--help` funciona.
  Generador produjo fichas.json sin API. Cargador ejecutado en simulación contra
  API local: cinco coincidencias ausentes omitidas, sin modificaciones.
- `git diff --check`: sin errores.

La prueba de obsolescencia verifica que cambiar metadatos no reescribe la ficha,
inhabilita su elegibilidad si deriva de ellos y permite corregirla en nueva versión.
No se anuncia invalidación de un vector real inexistente: P21 aún debe almacenar
modelo/configuración y versión indexada. No hubo llamadas a proveedores ni coste.

## Operación local

Antes de migrar desde 0006 se conservó el respaldo privado
`backups/echobeats_pre_p19_b6d41.dump` con manifiesto/hash
`backups/echobeats_pre_p19_b6d41.json`. Cabecera PGDMP y SHA-256 registrados.
El dump no incluye medios; MEDIA_ROOT y volumen existentes se conservaron.
Se aplicó 0007 y se recreó backend para incorporar código y montaje de solo lectura
`pruebas/semantica` para pruebas, sin dependencias nuevas. Migrate terminó y backend
quedó saludable. Tras cargar el último ajuste, /ready respondió ready con BD,
pgvector y migraciones ok, y OpenAPI publicó fichas e historial.

Las primeras consultas inmediatamente tras el último reinicio encontraron el
servicio aún arrancando; se esperó a healthy y se repitieron correctamente.
Las pruebas de downgrade y escritura se hicieron solo en bases aisladas.

## Pendiente manual

Computer Use devolvió `The browser access host is unavailable`, sin navegadores
conectados; no se hicieron acciones UI. Comprobar «Ficha musical» con teclado y
360/768/1280 px: creación incompleta, atributos, interpretación, corrección/versión,
conflicto en dos pestañas, recarga con confirmación, Escape, cierre con borrador,
Atrás/Adelante y reapertura. Comprobar también acceso al reproductor al cerrar el
diálogo y continuidad de audio; las pruebas HTTP no equivalen a escucha real.
Se mantienen pendientes de P08/P15/P16/P18 y audio.

Esta etapa implementa fichas/evidencia del recorrido académico y prepara P20–P23.
Todavía no acredita IA, embeddings, recuperación híbrida ni CA-10/CA-11.
