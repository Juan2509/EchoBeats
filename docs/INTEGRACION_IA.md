# Proveedor de IA — P20

## Decisión de trabajo y documentación verificada

Proveedor: OpenAI, siguiendo Requerimientos.md. Embeddings de texto con
`text-embedding-3-small`, 1536 dimensiones explícitas y encoding float. La guía
oficial documenta ese tamaño y la opción dimensions; son modelos de texto, no
reconocimiento acústico. [Guía oficial de embeddings](https://developers.openai.com/api/docs/guides/embeddings).

Generación: `gpt-6-luna` por Responses API, razonamiento none, salida JSON Schema
estricta y máximo 512 tokens de salida. La documentación oficial lo presenta para
tareas enfocadas y confirma Responses/Structured Outputs. Es una elección de
trabajo para probar explicaciones breves, no una afirmación de calidad musical
ya medida. El acceso efectivo depende de la cuenta y se comprueba con la prueba
real, no con el listado de modelos. [Modelo](https://developers.openai.com/api/docs/models/gpt-6-luna).

Structured Outputs no sustituye comprobar rechazos, respuestas incompletas y
reglas de negocio. El adaptador valida esquema y citas contra las fuentes recibidas.
Una cita válida no demuestra por sí sola que toda la explicación sea correcta;
la evaluación factual de P17/P23 sigue siendo necesaria.
[Documentación oficial](https://developers.openai.com/api/docs/guides/structured-outputs).

Se usa REST con httpx 0.28.1 ya presente y bloqueado en requirements.lock; no se
añaden SDK, dependencias o modelos locales. Los adaptadores embed/generate mantienen
separada la integración. LangChain/LangGraph/n8n no son necesarios para estas dos
llamadas; su eventual uso depende de utilidad y requisitos docentes explícitos.

## Configuración privada

Variables en `.env` local, nunca en VITE_* ni en código del cliente:

| Variable | Valor inicial / alcance |
| --- | --- |
| AI_ENABLED | false; no se activa IA al arrancar por disponer de una clave. |
| OPENAI_API_KEY | Clave privada de la cuenta/proyecto OpenAI; no pegarla en chats ni versionarla. |
| AI_EMBEDDING_MODEL | text-embedding-3-small; único modelo admitido en esta etapa. |
| AI_EMBEDDING_DIMENSIONS | 1536; configuración 1–1536. Cambiarla cambia model_key y exigirá índice compatible. |
| AI_GENERATION_MODEL | gpt-6-luna; único modelo admitido en esta etapa. |
| AI_TIMEOUT_SECONDS | 20 segundos totales por operación; rango configurable 1–60. |
| AI_RATE_LIMIT_RETRIES | 0 por defecto, máximo 1; solo 429 temporal con espera de hasta 2 s. |

Después de guardar variables en `.env`, recrear backend con
`docker compose up -d --wait backend`. Compose inyecta el entorno al crear el
contenedor: reiniciar un contenedor antiguo no incorpora por sí solo valores
nuevos del archivo. No imprimir `.env`, tokens, headers ni excepciones originales.
No hay endpoint para guardar/ver la clave desde el navegador.

Configuración → «Integración de IA» consulta GET /api/v1/ai/status. Devuelve solo
estado y nombres de modelos/configuración, nunca credenciales. `available` significa
habilitado con clave presente, no conectividad, saldo, acceso ni integración real
verificada. `verification=not_checked` es intencional: esta ruta no consume API.
Las rutas de reproducción y /ready no dependen del proveedor externo.

## Límites del adaptador

- Host HTTPS fijo api.openai.com/v1; sin redirecciones ni base URL configurable.
  No hereda proxies del entorno. El transporte de pruebas solo se inyecta en código.
- Una operación en vuelo por instancia; otra devuelve ai_busy. No es un límite
  distribuido ni un control de gasto entre procesos. P20 no expone una ruta pública
  que genere contenido o facture al pulsar repetidamente un botón.
- Embedding: un texto no vacío, sin NUL, hasta 6000 bytes UTF-8; validación de modelo,
  cardinalidad/índice, dimensión, números finitos sin booleanos, vector no nulo y usage.
- Generación: consulta hasta 4000 bytes, 1–5 fuentes con ID/versión/texto, cada texto
  hasta 6000 bytes y contenido serializado hasta 12000 bytes. Estos topes locales
  son conservadores; no se anuncian como ventana máxima del modelo ni conteo exacto
  de tokens. Una ficha P19 extensa requiere revisar su presupuesto antes de indexar.
- Respuesta hasta 1 MB; el presupuesto total incluye solicitud, lectura y espera
  de un eventual reintento. Se configuran también límites de conexión/pool.
- Sin reintento automático en timeout, error de red, 5xx, rechazo o salida inválida:
  podría haber consumo aunque no se confirmase respuesta. 429 insufficient_quota
  tampoco se repite. No hay fallback a otro modelo o espacio vectorial.
- Salida de generación: texto y 1–5 citas. Cada cita exige ID/version recibidos y
  fragmento literal de esa fuente; se rechazan citas ajenas, repetidas o inventadas.
  El formato correcto no acredita entailment semántico ni calidad de explicación.
- Sin tools, historial conversacional, audio, imágenes ni escritura automática de
  fichas. Datos de consulta/fuentes nunca se convierten en instrucciones ejecutables.

Los códigos de error públicos son fijos: disabled/not_configured/busy/timeout,
authentication/quota/rate_limit/unavailable/invalid_response/refusal/input_invalid,
con prefijo ai_. No se propagan cuerpos de error ni excepciones del proveedor.

Los códigos documentados de créditos/límites de gasto/uso se clasifican como cuota,
no como límite temporal reintentable. Solo se conserva su nombre de una lista
cerrada; mensajes/cuerpos originales no se publican.
[Códigos oficiales](https://developers.openai.com/api/docs/guides/error-codes).

Comprobación local P20: la cuenta devolvió credit_balance_exhausted. No se obtuvo
vector ni generación válidos; la prueba real queda pendiente de créditos API.
No repetir --live hasta resolver ese estado externo. No se activó IA en la app.

## Prueba real controlada, separada de pytest

`docker compose exec backend python -m app.ai_check` solo informa configuración.
No hace llamadas externas. `--help` explica la operación.

`docker compose exec backend python -m app.ai_check --live` solicita explícitamente
una comprobación facturable con clave privada presente. Solo esta ejecución activa
el adaptador, aunque AI_ENABLED permanezca false para la app. No cambia `.env`.
Hace como máximo dos solicitudes: un embedding y una generación estructurada;
si falla la primera, no hace la segunda. Reintentos automáticos forzados a cero.
Repetir el comando es otra operación potencialmente facturable, no una prueba gratis.

Datos exactos enviados: texto sintético fijo «Fragmento sintético: onda sinusoidal
de 220 Hz, sin voces.», una consulta fija para describirlo, ID artificial p20-control,
versión 1, instrucciones y esquema. No lee ni envía canciones, fichas personales,
archivos originales, nombres del usuario o contenido de la biblioteca.
La generación usa store=false; esto no implica retención cero de todos los sistemas
del proveedor. Consultar los controles de datos de la cuenta.
[Controles oficiales de datos](https://developers.openai.com/api/docs/guides/your-data).

El recibo privado en data/ai_checks conserva fecha, modelos/model_key, hash de
entrada, validación, dimensiones, usage por operación y estado/error seguro.
No conserva clave, vector completo, prompt personal ni respuesta textual. Un recibo
failed o not_run no se presenta como éxito; una respuesta no confirmada puede haber
consumido tokens. La disponibilidad/cuota/precios efectivos dependen de la cuenta.

`pytest` usa MockTransport y claves falsas exclusivamente. No ejecuta el comando
--live. La documentación de validación distingue evidencia real de dobles.

## Continuidad

P20 no añade tablas ni persiste vectores. P21 usa la clave base del proveedor
`openai:text-embedding-3-small:dimensions=1536:float:v1` más `:description-v1`
para identificar la receta de preparación del texto, versión/hash de ficha y
trabajos durables; P22 deberá consultar con el mismo espacio; P23 evaluará citas
y explicaciones con el protocolo P17. Cambiar modelo/dimensiones exige nueva
configuración/índice y reindexación; no mezclar espacios incompatibles.
Las diferencias Spring Boot, VPS/tenants y PDF/OCR siguen explícitas en
REVISION_REQUERIMIENTOS.md; no se habilita exposición pública.
