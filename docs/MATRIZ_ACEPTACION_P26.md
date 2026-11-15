# Matriz de aceptación integrada — P26

Actualización P28: otro proyecto vacío aprobó build/migraciones/dependencias,
62 tests frontend, importación/rangos/proxy y medio después de recrear contenedor;
dump/restauración a nueva BD y copia de medios sintéticos verificados. Complementa
el arranque/transporte/persistencia de CA-01 a nivel técnico; no sustituye los
otros recorridos P26, navegador/escucha ni CA-10/CA-11.
Guía repetible en GUIA_DEMOSTRACION.md, evidencia en VALIDACION_P28.md.

14 de noviembre de 2026. Fuente de aceptación: ALCANCE_MVP.md, CA-01–CA-13.
**Ningún recorrido audible/visual se declara superado solo por HTTP o dobles.**
Pruebas ejecutadas sin OpenAI real, con PostgreSQL/pgvector y medios aislados.
Detalle de ejecución y artefactos en [VALIDACION_P26.md](VALIDACION_P26.md).

| Caso | Resultado observado | Evidencia repetible | Pendiente de aceptación completa |
| --- | --- | --- | --- |
| CA-01 Importar y reiniciar | Aprobado en API: biblioteca vacía, lote mixto, duplicado, bytes originales tras procesos nuevos. | test_runtime_integration.py: test_real_http_restart_preserves_import_metadata_playlist_walls_assets_and_reset; test_imports.py. | Visibilidad en navegador y reproducción audible. |
| CA-02 Sin etiquetas y corrección | Aprobado en API: título fallback/portada predeterminada, edición manual de título/artista/álbum, duplicado conserva edición y datos tras reinicio. | Mismo recorrido HTTP y test_metadata.py. | Escucha y recorrido del editor visual. |
| CA-03 Controles de audio | Transporte aprobado: GET/HEAD, 206 y bytes exactos intermedios/finales tras reinicio; 416 fuera del archivo. Controlador aprobado con doble para play/pausa/seek/volumen/cola. | Recorrido HTTP, test_audio.py, test_audio_formats.py; player.test.ts, incluido flujo integrado P26. | Escucha, seek decodificado y tiempo visible en navegador; formatos O06. Un rango no demuestra seek audible. |
| CA-04 Playlist y reinicio | Aprobado en API: crear, renombrar y guardar pertenencia/orden; igualdad de contenido y ETag tras proceso nuevo; originales intactos. | Recorrido HTTP y test_playlists.py. | Recorrido visual de edición y cola guardada con audio real. |
| CA-05 Imagen/apariencia | Aprobado en API: imagen PNG, apariencia image, rechazo inválido sin pérdida; imagen válida decodificable e idéntica tras reinicio. | Recorrido HTTP, test_playlists.py y test_visuals.py. | Presentación vinilo/tarjeta en navegador. |
| CA-06 Decorar y persistir | Aprobado en API: color, PNG/GIF, preview, centros/tamaños/giros/capas e IDs conservados tras reinicio; reset persiste en tercer proceso. | Recorrido HTTP; test_walls.py/test_visuals.py; walls/wall-saving/wall-transforms.test.ts. | Arrastre, giro, tamaño y capas reales, autoguardado visible y recarga de interfaz. |
| CA-07 Aislamiento A/B | Aprobado en API: A/B distintos, revisión ajena rechazada y composiciones independientes antes/después de dos reinicios; reset A no cambia B. Respuestas tardías cubiertas con controlador. | Recorrido HTTP, test_walls.py y wall-saving/walls.test.ts. | Alternar visualmente A/B y verificar selección/recursos después de reinicio. |
| CA-08 Bloqueo y audio | Aprobado con dobles: muro arranca bloqueado, rechaza cambio, editar/guardar/bloquear y fallo de Explorar no interrumpen seek, volumen y cola del mismo reproductor. | player.test.ts: flujo integrado P26; walls.test.ts. | Intento real de arrastre bloqueado y controles accesibles con audio en los tres anchos. |
| CA-09 Búsqueda textual | Aprobado en API: título/artista/álbum y ausencia de coincidencias, sin perder catálogo. | Recorrido HTTP y test_library.py. | Teclado, foco y estados de vacío/carga/error visibles. |
| CA-10 API/vector real | Pendiente por petición del usuario: no se repitieron llamadas tras falta de créditos. SQL/pgvector con proveedor simulado aprobado como evidencia técnica complementaria. | test_indexing.py/test_search.py; VALIDACION_P20–P22.md. | Embeddings y consulta de API real compatibles, recibo sin secretos y evaluación. Vectores artificiales no cuentan. |
| CA-11 Sensaciones y escucha | Pendiente real/musical. Recuperación, fuentes/versiones, citas literales, preferencias y cola verificadas técnicamente. | test_exploration.py/test_preferences.py; explore/player.test.ts; corpus P17. | Consultas y música autorizada, pertinencia, explicación y reproducción audible con API real. No calibrar con reservadas ni vectores ficticios. |
| CA-12 Fallos de proveedor | Aprobado en API/controladores: cuota/timeout/respuesta inválida, catálogo/playlist/favoritos y rangos utilizables; consulta textual disponible y proveedor simulado recuperado en petición posterior explícita. Generación con fallback/citas inválidas cubierta en P23. | test_runtime_integration.py: test_provider_failure_then_recovery_keeps_catalog_audio_and_preferences_usable (3 variantes); test_exploration.py; flujo integrado player.test.ts. | Estado visual y audio audible durante fallo. Simular fallo no acredita RF-14 ni éxito del proveedor real. |
| CA-13 Reconocimiento | **No aplica: reconocimiento no incluido (O01/RF-18 aplazados).** | Alcance vigente y ausencia de integración de identificación. | Solo se ejecutará si se habilita O01. Nunca registrar como superado. |

## Ampliaciones activadas

- O06: formatos y rangos verificados técnicamente en test_audio_formats.py;
  reproducción/seek reales siguen pendientes.
- RF-17/P24–P25: favoritos sobreviven a procesos nuevos y se desmarcan; regla de
  preferencias/filtros/cambios durante red comprobada en bases aisladas. Coherencia
  visual y valoración musical siguen pendientes; no se afirma aprendizaje.

## Resultado de cierre

Matriz elaborada y evidencias automáticas repetibles disponibles. **P26 no cierra
el MVP**: conserva aceptación visual/audio y CA-10/CA-11 pendientes. P08, P15,
P16 y P20–P25 mantienen sus limitaciones registradas. El protocolo pendiente está
en [RECORRIDOS_P26.md](RECORRIDOS_P26.md). Avanzar de etapa no borra estas deudas.
