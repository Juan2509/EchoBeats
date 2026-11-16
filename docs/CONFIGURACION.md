# Configuración efectiva — P28

La sección visual **Configuración** de la aplicación tiene Fondo principal,
Álbumes (selector del que se quiere editar), Colores y estilo y Conexión y estado.
El muro se configura desde **Editar pared → Fondo**. Ver [APARIENCIA.md](APARIENCIA.md).
Este documento describe las variables operativas del servidor.

Fuente de verdad: .env.example, backend/app/config.py y compose.yaml. No pegar
valores privados en incidencias, documentación o capturas. La instalación local
es de un usuario; no existe autenticación/tenant que la haga apta para Internet.

| Variable | Uso / valor de referencia |
| --- | --- |
| BACKEND_PORT / FRONTEND_PORT | 8000 / 5173 en localhost. |
| POSTGRES_PORT | 5433 en host; Compose fuerza 5432 internamente. |
| POSTGRES_HOST | 127.0.0.1 nativo; Compose fuerza postgres. |
| POSTGRES_DB / POSTGRES_USER | echobeats; se inicializan con volumen vacío. |
| POSTGRES_PASSWORD | Solo .env privado; aleatoria por preparador. Cambiar .env no cambia rol existente. |
| DATABASE_URL | Opcional nativo, esquema postgresql+psycopg; vacía usa POSTGRES_*. Compose la vacía explícitamente. |
| MEDIA_ROOT | Nativo: ruta absoluta recomendada. Compose fuerza /app/data/media desde ./data. |
| ALLOWED_HOSTS | localhost,127.0.0.1,backend. No incluir comodines para exposición pública. |
| ALLOWED_ORIGINS | Orígenes locales completos con puerto/esquema para escrituras del navegador; no es autenticación. |
| PROCESSING_WORKER_ENABLED | true por defecto: worker local y cola durable. false pausa procesamiento; no elimina trabajos. |
| AI_ENABLED | false por defecto. No habilitar mientras el usuario mantenga pendiente la prueba real. |
| OPENAI_API_KEY | Privada, vacía para el arranque local sin IA; nunca VITE_* ni frontend. |
| AI_EMBEDDING_MODEL | text-embedding-3-small, identidad de modelo configurada. |
| AI_EMBEDDING_DIMENSIONS | 1536 para pgvector almacenado. No mezclar dimensiones/espacios. |
| AI_GENERATION_MODEL | gpt-6-luna configurado en el adaptador. Disponibilidad/éxito con la cuenta real no acreditados. |
| AI_TIMEOUT_SECONDS | 20; validación 1–60. Límite de proveedor, no garantía de latencia. |
| AI_RATE_LIMIT_RETRIES | 0; configuración admite 0–1. No reintentar cuota ni resultado incierto. |
| SEARCH_MAX_COSINE_DISTANCE | Omitido: candidatos sin umbral calibrado. No elegirlo con vectores ficticios ni llamarlo confianza. |
| API_PROXY_TARGET | Solo proceso frontend: http://backend:8000 en Compose, localhost:8000 nativo; sin credenciales. |

Las variables VITE_* se incorporan al cliente: ninguna clave allí. Frontend Compose
solo recibe el destino del proxy. Cambios de entorno requieren recrear el proceso
correspondiente y comprobar estado; no se convierten en validación de proveedor.

## Identidad de IA y procedencia

Prompt versionado en app/integrations/ai.py. Embeddings P20 identifican proveedor,
modelo y dimensiones; el índice P21 añade receta `:description-v1`. Elegibilidad
exige ficha/versión/hash/modelo/receta y vigencia de metadatos derivados. No sustituir
modelo/dimensiones para rescatar vectores incompatibles ni presentar históricos como actuales.

Preparación de etiquetas no analiza audio ni genera fichas/índice por completarse.
Fichas se guardan manualmente con fuentes/atributos; interpretaciones no son hechos
acústicos. Indexar envía texto/atributos/evidencias de la ficha, no audio, mediante
cola; guardar no dispara esa llamada. Consulta semántica/híbrida envía texto; citas
optativas envían hasta cinco extractos acotados. Prosa libre generada no se publica.

El estado /ai/status solo indica configuración. No autoriza consumo ni acredita
créditos, proveedor, embeddings o pertinencia. Cierre real/evaluación pendientes
por solicitud del usuario; no ejecutar --live ni indexar para completar una demo
sin resolver y reanudar explícitamente. Ver INTEGRACION_IA.md y EMBEDDINGS.md.
