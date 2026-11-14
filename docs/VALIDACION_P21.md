# P21 — Indexación versionada en pgvector

13 de noviembre de 2026. **Implementación lista; cierre con proveedor real pendiente.**
El usuario confirmó que aún no se resolvieron los créditos API y pidió dejar
pendiente la prueba real. No se hicieron llamadas a OpenAI durante este paso.

## Resultado

Almacenamiento vector(1536), trabajos index_description en la cola durable,
publicación transaccional, deduplicación por ficha/versión/modelo y comprobación
de hash/elegibilidad/modelo antes y después del proveedor. API y controles de
estado/indexación/reintento en la ficha. Vectores anteriores conservados pero
no presentados como vigentes. Receta description-v1 incluida en model_key.
Ver [EMBEDDINGS.md](EMBEDDINGS.md).

## Pruebas ejecutadas

- `docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error --tb=short`:
  **175 pruebas aprobadas**, con bases aisladas. Incluye ocho casos nuevos P21.
- pgvector/PostgreSQL reales con proveedor simulado: cinco solicitudes concurrentes
  producen un trabajo; adquisición concurrente única; dimensión/vector persistidos
  y recuperados por nueva conexión; finalización duplicada ignorada; solicitud
  repetida no regenera; edición en vuelo no publica vector viejo; estado stale tras
  editar; dimensión incompatible rechazada; entradas vacías/extensas/IA desactivada
  no encolan; cuota no se repite sola y admite reintento explícito; recuperación
  descarta intento anterior; vector inválido no se publica; downgrade protege
  vectores/trabajos; cambios de metadatos derivados invalidan elegibilidad.
- Se comprueba acceso a audio tras indexación y que el resultado público del trabajo
  no contiene el vector completo. Los datos simulados solo existieron en bases
  efímeras de pruebas y no se presentan como embeddings de API real.
- `npm.cmd test`: **45 pruebas aprobadas**. `npm.cmd run build`: TypeScript y Vite
  aprobados. No hay prueba DOM nueva del panel de indexación.
- `git diff --check`: sin errores.

La regresión detectó un mensaje index_notice distinto entre GET y PUT de ficha;
se unificó y la repetición final aprobó los 175 casos. La migración contempla los
nombres heredados del CHECK de operación sin volver a aplicarles la convención.

## Operación local

Respaldo privado previo: `backups/echobeats_pre_p21_e8f32.dump` y manifiesto/hash
`backups/echobeats_pre_p21_e8f32.json`, PGDMP comprobado, revisión 0007 confirmada.
El dump no incluye medios; volumen y MEDIA_ROOT existentes se conservaron.

Se aplicó `0008_track_embeddings`, se reinició backend y se esperó a healthy.
La migración conserva trabajos existentes y no modifica originales/fichas.
GET /ready devolvió BD/pgvector/migraciones ok; OpenAPI publicó las rutas P21.
Lectura del esquema confirmó columna vectorial de 1536 dimensiones y **cero
vectores en la base personal**. No se insertaron vectores ficticios ni se creó
una cola personal de indexación para aparentar el cierre.

## Pendientes explícitos

P20 registró credit_balance_exhausted. El usuario pidió dejar pendiente la prueba
real; no se habilitó IA ni se reintentó la cuenta. Para cerrar P21 hará falta evidencia
de embeddings de API real persistidos, nueva conexión, versión/modelo/hash/usage y
deduplicación sin llamada adicional. Hasta entonces P20/P21 siguen sin marcar cerrados.

Computer Use no expuso navegadores y reportó `The browser access host is unavailable`.
Pendiente revisar con teclado y 360/768/1280 px los controles en la ficha, guardado
previo, estado al reabrir, bloqueos con borrador y acceso al reproductor al cerrar
el diálogo. No provocar cargos o fallos en la biblioteca para sustituir la prueba
aislada. Se mantienen pendientes visuales y de audio anteriores.

P22 es la siguiente implementación prevista; búsqueda real/pertinencia CA-10/CA-11
no están demostradas. Consultar EMBEDDINGS.md para retomar cuando se resuelva la
disponibilidad de créditos y se autorice reanudar la prueba real pendiente.
