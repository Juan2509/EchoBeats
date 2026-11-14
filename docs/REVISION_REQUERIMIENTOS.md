# Revisión de los requerimientos académicos

**Directriz posterior del usuario, 13 de noviembre de 2026:** incorporar desde
ahora lo descrito en los requerimientos al desarrollo de EchoBeats. Esta revisión
debe utilizarse para adaptar las próximas etapas y comprobar su cobertura;
las diferencias técnicas identificadas se mantienen explícitas hasta resolverlas.

13 de noviembre de 2026. Fuente completa: [Requerimientos.md](../Requerimientos.md).
Revisión de documentación y código; no se implementaron integraciones ni se
cambió el stack. Los pasos del archivo son el flujo descrito, no órdenes para
ejecutar instalaciones, subir documentos o eliminar originales.

## Confirmación del usuario y alcance de la fuente

El usuario confirma que el proyecto es libre siempre que utilice lo visto en
clase. Esto resuelve la duda sobre usar EchoBeats como temática en lugar de
DevFlow. No demuestra por sí solo libertad de lenguaje, framework o despliegue.

El archivo describe un sistema RAG para PDF: Java/Spring Boot, VPS, HTTPS,
autenticación/autorización, separación por tenant, procesamiento asíncrono,
OCR, fragmentos, OpenAI Embeddings, PostgreSQL/pgvector y respuestas con citas.
Debe aclararse cuáles de esas elecciones son exigencias de evaluación y cuáles
pertenecen al caso documental usado para explicar la arquitectura.

## Relación con EchoBeats

Actualización P22: recuperación vectorial exacta y textual/híbrida con filtros,
compatibilidad de índice y evidencia versionada implementada; evaluador P17 sin red.
Sin llamadas reales ni calibración mientras siga pendiente reanudar tras créditos.
No declarar API real/RAG/pertinencia demostrados con rankings de prueba aislados.
P23 integrará experiencia y generación fundamentada. Ver RECUPERACION_SEMANTICA.md.

Actualización P21: almacenamiento pgvector, indexación asíncrona de fichas,
versiones/modelo/receta y prevención de duplicados implementados. Pruebas PostgreSQL
reales con proveedor simulado aprobadas; no equivalen a vectores reales del proveedor.
El usuario deja pendiente esa prueba por créditos API. Se incorpora estructura
de indexación/compatibilidad, sin declarar aún cumplidos API real, RAG ni recuperación
híbrida. Ver EMBEDDINGS.md y VALIDACION_P21.md.

Actualización P20: adaptador OpenAI para embeddings/generación, configuración
privada, validación y manejo de fallos preparados. 167 pruebas backend, 45 frontend
y build aprobados; intentos reales rechazados por credit_balance_exhausted, sin
respuestas validadas. No declarar cumplida la API real ni el RAG hasta cerrar esta
prueba y P21–P23. Ver INTEGRACION_IA.md y VALIDACION_P20.md.

Actualización P19: fichas musicales con fuente/evidencia por atributo, historial
versionado y separación explícita de interpretaciones ya implementadas. Se preparó
el corpus controlado por hash sin emociones provisionales. Es una base trazable
para RAG futuro; no equivale a proveedor, embeddings, recuperación híbrida ni citas
generadas. Ver FICHAS_MUSICALES.md y VALIDACION_P19.md.

Actualización P18: ya existe procesamiento asíncrono durable local para preparar
metadatos, con estados, revisión de entrada, reintento e historial. Ver
PROCESAMIENTO.md. Esto incorpora el patrón de asincronía/trazabilidad; sigue sin
OCR/PDF, proveedor de IA, fichas/embeddings ni recuperación híbrida. La tabla
siguiente conserva el diagnóstico recibido inicialmente donde no se indique actualización.

| Elemento de la fuente | Situación en EchoBeats | Adaptación o decisión pendiente |
| --- | --- | --- |
| Cliente web y API | React/TypeScript y FastAPI; aplicación funcional hasta P14. | Base ya disponible para la experiencia de exploración de P23. |
| PostgreSQL + pgvector | BD y extensión reales desde P04; todavía no hay embeddings musicales. | P21/P22 deben almacenar y consultar vectores musicales reales. Tener instalada la extensión no completa la búsqueda semántica. |
| Procesamiento asíncrono | Diseñado en P18; sin implementación de indexación. | Estados persistidos, reintentos y versiones de entrada para preparar fichas/embeddings sin bloquear la escucha. |
| Extracción de información | Ya se leen etiquetas y portadas, con procedencia. | No equivale a extraer texto de PDF ni a analizar acústicamente el sonido; preparar fichas verificadas en P19. |
| Fragmentación/OCR | Sin PDF ni OCR. | Para fichas breves puede usarse una unidad por canción. Fragmentar textos largos sería una adaptación; PDF/OCR solo si son obligatorios para todos los proyectos o se acuerda un caso útil. |
| OpenAI Embeddings en el MVP | No hay proveedor/modelo configurado ni consumo real de API. | La fuente nombra OpenAI expresamente; tratarlo como dirección académica a concretar en P20. No hay credenciales, dimensiones ni coste aprobados por esta revisión. |
| Modelo compatible entre índice y pregunta | Ya previsto en decisiones y P21/P22. | Registrar proveedor/modelo/configuración/dimensiones/versiones y no mezclar espacios vectoriales. |
| Búsqueda híbrida y selección de evidencias | Existe búsqueda textual; no hay búsqueda semántica ni combinación de resultados. | Ampliar P17/P22 con casos de evaluación y combinación texto/vector cuando corresponda; reranking se aplica si aporta valor, como indica «cuando convenga» en la fuente. |
| Respuestas fundamentadas con citas | Previsto en P23, sin implementar. | Referenciar pista/álbum, ficha, versión y campos que respaldan la explicación. No inventar instrumentos, emociones o identidades a partir de etiquetas insuficientes. |
| Permisos/tenant y consulta remota | MVP local de un usuario, sin autenticación ni VPS. | Si son obligatorios, revisar D01 y propiedad de datos, autenticación, filtros y HTTPS antes de exponer el sistema. No simular multitenancy en la instalación local. |
| Original PDF local y copia temporal del servidor | EchoBeats conserva copias gestionadas de audios e imágenes para reproducirlos. | La política de borrar PDF temporales no se traslada a los MP3/otros audios importados. Consultar fichas sin el original no permite reproducir un audio ausente. |
| Java/Spring Boot | Backend Python/FastAPI. | Si es una exigencia cerrada, la arquitectura actual no cumple ese punto; si es la tecnología del ejemplo, los patrones RAG pueden aplicarse al stack vigente. No migrar por inferencia. |

## Ejemplo de adaptación propuesta

Consulta: «Quiero electrónica alegre para una tarde lluviosa».

1. Una tarea prepara fichas musicales con datos verificados y procedencia.
2. Se generan embeddings de esas fichas y se guardan con su modelo/versión.
3. Se genera el embedding compatible de la consulta.
4. PostgreSQL recupera fichas mediante pgvector y, si resulta útil, búsqueda textual.
5. El modelo explica los resultados usando exclusivamente las evidencias recuperadas.
6. La interfaz muestra pistas existentes, referencias a sus fichas y reproducción.

Esto es una adaptación razonada al dominio musical, no una confirmación de que
la evaluación acepte sustituir cada requisito documental por su equivalente.
No requiere identificar canciones por audio ni enviar originales musicales al
proveedor para construir una primera búsqueda sobre descripciones verificadas.

## Inconsistencia técnica de la fuente

La línea «SpringBoot + Pgvector.EntityFrameworkCore» mezcla tecnologías:
Pgvector.EntityFrameworkCore pertenece al ecosistema .NET, según el
[repositorio oficial](https://github.com/pgvector/pgvector-dotnet#entity-framework-core).
Spring AI documenta una integración propia con pgvector en su
[referencia oficial](https://docs.spring.io/spring-ai/reference/api/vectordbs/pgvector.html).
No tomar esa combinación literal como una dependencia instalable de Spring Boot.
Esto requiere aclaración/corrección del documento, no cambiar EchoBeats a .NET.

El archivo no exige explícitamente n8n, LangChain ni LangGraph. Su presencia en
el material del curso no basta para convertirlos en dependencias obligatorias
de esta entrega; mantener separada la rúbrica adicional que eventualmente se reciba.

## Consecuencia para el plan

P14 sigue siendo el avance funcional actual; P15/P16 completan la pared.
La correspondencia principal de estos requerimientos está en P17–P23, todavía
pendientes. Antes de implementar esa fase, cerrar la matriz académica con:

- Carácter obligatorio o ilustrativo de Java/Spring Boot y VPS/usuarios/tenants.
- Si PDF/OCR son el caso de clase o entregables universales.
- OpenAI como proveedor exigido y alcance esperado de búsqueda híbrida/citas.

La temática libre queda confirmada por el usuario. No se declara cumplida la
rúbrica RAG por disponer de biblioteca, reproductor y muros; la integración
de IA, embeddings y recuperación con evidencias aún debe construirse.
