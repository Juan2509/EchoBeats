# Guía de la documentación académica

Fuente: `referencias/LangChain_LangGraph2026.md`. Los números indican líneas
del original conservado sin modificaciones. Esta guía resume lo leído y permite
recuperar ejemplos; no certifica vigencia ni ejecución de los fragmentos.

## Índice de lectura

| Líneas | Contenido |
| --- | --- |
| 1–168 | Programa de doce sesiones, seis competencias, resultados, evidencias, matriz curricular y evaluación; proyecto integrador DevFlow. |
| 169–949 | Sesión 1: IA generativa, SDLC, enfoque orientativo 10-80-10, alucinaciones, lógica, seguridad, autonomía, validación y ejercicio manual frente a IA. |
| 950–2040 | Sesión 2: prompts con contexto, objetivo, restricciones, datos, formato y aceptación; zero/one/few-shot, descomposición, refinamiento, comprensión/generación/refactorización/depuración/pruebas, Context Engineering y separación de instrucciones/datos. |
| 2041–2596 | Búsqueda léxica y semántica, embeddings, espacios vectoriales, metadatos, índices, métricas, ANN/HNSW/IVFFlat, tecnologías vectoriales, recuperación y RAG; SQL ilustrativo con pgvector. |
| 2597–2899 | Entorno JupyterLab en Docker, configuración, dependencias, Chroma, variables de entorno, persistencia y reapertura de una colección del caso Banco Andino/Conavi. |
| 2900–3086 | Embeddings mediante API, ejemplo de OpenAI, generación por lotes, inserción en Chroma y consulta en el mismo espacio vectorial. |
| 3087–3439 | Caso ficticio Embotelladora Santander: políticas, fragmentos con condiciones/excepciones, Top 3, evaluación cualitativa; Chroma obligatorio en ese ejercicio y comparación opcional de embeddings. |
| 3440–3631 | LangChain: modelos de lenguaje/chat/embeddings, prompts, chains, tools y agentes. |
| 3632–4302 | Docker/Compose/DevContainer, dependencias, PostgreSQL, Streamlit, variables y prueba de modelo/conexión; instalación Linux, Windows y macOS. |
| 4303–4547 | Entornos virtuales, intérprete de VS Code, variables, configuración de proyecto y credenciales de proveedor. |
| 4548–4581 | Ejemplos mínimos de invocación de modelos de chat de Gemini y OpenAI. |
| 4582–4983 | Runnables/LCEL: invoke, batch, stream y variantes async; RunnableLambda, Sequence, Parallel y Passthrough; mini proyecto de resumen y sentimientos. |
| 4984–5185 | Prompt Engineering frente a PromptTemplate; ChatPromptTemplate, mensajes con roles y construcción del prompt antes de invocar al modelo. |
| 5186–5422 | Ejercicio de migración de chatbot a ChatPromptTemplate, configuración de personalidad e historial inicialmente interpolado como texto. |
| 5423–5806 | MessagesPlaceholder, historial con roles/orden, optional y n_messages, diferencias respecto a memoria persistente; few-shot/ICL y plantillas por rol. |
| 5807–6046 | Output parsers, Pydantic, with_structured_output, instrucciones de formato, parseo, validación, cadenas y manejo de errores. |
| 6047–6356 | Streamlit: reruns, session_state, chat, diseño, secretos, caché y ejemplos de chatbot con streaming y selección de proveedor. |

## Comprensión aplicada a EchoBeats

**Proceso de desarrollo.** La guía prioriza comprender requisitos, trabajar por
incrementos, revisar código generado, diagnosticar con evidencias y demostrar
funcionamiento. 10-80-10 es una orientación pedagógica, no un porcentaje obligatorio.
Los ejercicios de estudiantes, carritos, bancos y políticas comerciales enseñan
patrones; sus reglas de negocio no pertenecen a EchoBeats.

**Búsqueda.** El modelo genera embeddings; la base los guarda/consulta; la
recuperación devuelve los datos asociados; un LLM puede generar una explicación
con ese contexto. La BD vectorial no redacta respuestas por sí misma. Indexación
y consultas deben usar un modelo y configuración compatibles. Dimensiones,
métrica y versión son parte de la configuración que habrá que concretar.
La consulta ilustrativa de pgvector ordena por distancia del coseno usando `<=>`.
Los índices ANN intercambian exhaustividad por velocidad; no hay que asumir que
todo prototipo necesita inmediatamente un índice aproximado.

**Evaluación de recuperación.** Conservar consultas de prueba y resultados
esperados; revisar pertinencia y suficiencia de los primeros resultados, fuentes
y filtros. Una distancia no es un porcentaje de confianza. Las distancias de
modelos diferentes no forman una escala común de calidad. Aplicar estos patrones
a fichas musicales, sin importar las políticas ficticias del laboratorio.
El uso de Chroma en los ejercicios no reemplaza el requisito pgvector del concepto.

**Orquestación.** En LCEL, `|` pasa la salida de un componente al siguiente;
sus contratos de entrada/salida deben coincidir. `batch` procesa varias entradas
con un componente; `RunnableParallel` ramifica una entrada entre varios.
`RunnablePassthrough` conserva datos originales, útil para mantener la petición
mientras se recuperan fichas. El streaming depende de los pasos de la cadena.
Un workflow sigue un recorrido definido; un agente selecciona herramientas
dinámicamente. Son alternativas que deben justificarse por el caso de uso.

**Prompts y memoria.** PromptTemplate prepara texto; ChatPromptTemplate prepara
mensajes con roles. Preparar/invocar la plantilla no equivale a consultar un LLM.
MessagesPlaceholder inserta mensajes recibidos y conserva su orden/rol, pero no
los almacena. LangGraph se menciona en relación con estado/checkpointers y
orquestación; este archivo no contiene un tutorial completo de implementación
de grafos. n8n figura en el currículo con triggers, webhooks, HTTP Request,
Code Node, IF/Switch/Merge, subworkflows, reintentos y trazabilidad, sin un desarrollo
paso a paso comparable al dedicado a LCEL.

**Salidas.** Pedir JSON no asegura un esquema válido. El material muestra
PydanticOutputParser y salida estructurada del modelo. En EchoBeats convendría
validar campos y valores de descripciones, interpretaciones y explicaciones.
Las descripciones de un Field por sí solas no imponen rangos ni categorías.
Una puntuación generada por IA no equivale a una probabilidad calibrada.

**Interfaz y persistencia.** Streamlit vuelve a ejecutar el script con las
interacciones. session_state conserva datos durante la sesión, no satisface el
guardado de muros tras cerrar/reabrir. Caché, estado de sesión, historial enviado
al modelo y persistencia duradera son responsabilidades distintas. Streamlit es
una alternativa de prototipado; la elección visual de EchoBeats sigue abierta.

## Observaciones sobre los ejemplos antes de reutilizarlos

Estas observaciones provienen de leer el archivo, sin ejecutar sus fragmentos ni
verificar documentación externa. Antes de implementar se deben comprobar las
versiones y las capacidades vigentes en las fuentes oficiales pertinentes.

- Se mezclan rutas de importación `langchain.*` y `langchain_core.*`, nombres
  de modelos y versiones de paquetes de distintas partes del material.
  No se ha seleccionado ni probado una combinación para EchoBeats.
- Algunos fragmentos están incompletos o tienen formato/sintaxis defectuosos:
  imports partidos, ejemplos compactados en una sola línea, `rom` por `from`,
  un paréntesis faltante y ejercicios con marcadores para completar.
- El Compose de desarrollo cambia el comando del servicio a `sleep infinity`,
  aunque otra sección indica que al levantarlo se abre la aplicación. Habrá que
  definir explícitamente el arranque de la app cuando se construya el entorno.
- El ejemplo de PostgreSQL declara `postgres:16-alpine`; incluir la dependencia
  Python de pgvector no demuestra que la extensión esté instalada/activada en
  el servidor. Habrá que comprobarla con una base real.
- El material contiene ejemplos de credenciales y una impresión directa de una
  variable de API. No reutilizar valores de muestra ni imprimir claves en la app.
- Un ejemplo convierte un error de parseo en sentimiento «neutro». Para EchoBeats
  los errores y el estado desconocido deben distinguirse de un resultado válido.
- Las cifras de precios, límites, versiones y nombres de modelos del documento
  se conservan como información de la fuente, no como hechos vigentes verificados.
- Las imágenes relativas a `images/` no se recibieron junto con los Markdown;
  las copias preservan los enlaces originales, pero no incluyen esas imágenes.

## Evidencias académicas que conviene conservar al desarrollar

Decisiones de arquitectura y configuración reproducible, prompts versionados,
pruebas funcionales y de fallos, consultas reales y resultados, ejemplos de
recuperación musical pertinente, demostración de persistencia, documentación
del repositorio y capacidad de explicar la implementación. Workflows exportados,
agentes y sustentación individual forman parte del marco curricular; confirmar
su aplicación concreta al proyecto alternativo EchoBeats.
