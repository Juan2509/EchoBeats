# P23 — Explorar con fuentes y reproducción

14 de noviembre de 2026. **Implementación lista; cierre real y revisión visual pendientes.**
Se respeta la solicitud de no repetir llamadas reales mientras siga pendiente
la disponibilidad de créditos. No se llamó a OpenAI ni se alteró el índice personal.

## Entrega

Pantalla Explorar con consulta textual/semántica/híbrida, filtros, estados,
referencia por pista, fichas y fuentes versionadas. Modo textual inicial y selección
de citas con IA desactivada; abrir la vista no consulta al proveedor ni reproduce.
La reproducción explícita usa la cola exacta de resultados y el reproductor único.

POST /explore/search admite explain=false por defecto; POST /explore/similar
permite selección de citas explícita. El GET previo de similares no genera texto.
Una solicitud de generación como máximo, contexto acotado a cinco fichas,
sin audio y sin transacción abierta durante red. Solo se publica selección de
citas literales comprobadas, nunca la prosa libre del modelo. Ante fallo se
conservan descripciones registradas. Se revalidan versiones, elegibilidad y
filtros después de la generación; referencia modificada devuelve 409.
Contrato, límites y política en [EXPLORACION.md](EXPLORACION.md).

## Verificación

- Regresión backend completa: **213 pruebas aprobadas**, con avisos tratados
  como errores (`pytest -W error`), PostgreSQL/pgvector y bases aisladas.

- 16 casos nuevos de backend, con PostgreSQL/pgvector en bases aisladas y
  proveedores simulados: citas válidas/ajenas/inventadas, prosa no publicada,
  cuota/timeout/refusal, modelo/uso inválidos, UTF-8/contexto acotado,
  fichas/referencia modificadas, retirada de playlist y ausencia de resultados.
- 51 pruebas frontend aprobadas, incluidas seis nuevas: respuestas tardías,
  cancelación, errores, validación de fuentes y audio, petición explícita y
  reproducción de la instantánea exacta. El reproductor usa un doble de audio.
- Build frontend y comprobación TypeScript aprobados.
- Backend reiniciado con la versión final y saludable; ready, OpenAPI, búsqueda
  textual por proxy con explain=false y HTML de Explorar comprobados por HTTP.
  Estas comprobaciones no sustituyen inspección visual ni escucha.
  La colección personal respondió no_indexed_tracks, cero resultados y
  explanations_requested=false: no se crearon vectores ni se consumió API.
- Sin migraciones ni dependencias nuevas; .env, medios, volúmenes y respaldos
  conservados. Docker Desktop estaba detenido y se arrancó para las pruebas.

## Pendientes de cierre

El host de navegador no está disponible; el intento de inspección nativa también
encontró la ventana minimizada. No se acredita recorrido visual, teclado,
360/768/1280, escucha ni seek real. Mantener los pendientes P08/P15/P16/audio.

P20–P23 conservan pendiente el flujo completo con API real, índice real y
evaluación P17; no se eligió umbral con vectores simulados. Las pruebas locales
no certifican calidad musical, pertinencia ni integración externa. RF-12–RF-16
y CA-11/CA-12 no se declaran cerrados por estos dobles y pruebas de controlador.
La selección de citas tampoco demuestra que la interpretación editorial sea un
hecho acústico. Resultados sin calibración siguen siendo candidatos.

Siguiente implementación prevista: P24, favoritos, cuando el usuario lo solicite.
No se creó commit.
