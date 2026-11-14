# Recuperación musical — P22

## Alcance

P22 implementa API de recuperación exacta por coseno, modo textual e híbrido,
similitud desde una pista, filtros y evaluación de informes guardados. No genera
explicaciones nuevas ni completa la interfaz Explorar: ese recorrido es P23.
Conservar la prueba real de P20/P21 pendiente por petición del usuario; no llamar
al proveedor para suplirla con datos ficticios ni anunciar CA-10/CA-11 superados.

## API

POST /api/v1/explore/search admite JSON:

```json
{"query":"campanas sintetizadas","limit":3,"mode":"hybrid"}
```

query: 1–1000 caracteres tras recorte, sin NUL; limit: entero 1–20, por defecto 5.
mode: semantic, lexical o hybrid (por defecto). album_id y playlist_id son UUID
opcionales y se aplican conjuntamente. Referencias inexistentes devuelven 404;
campos adicionales/modelos suministrados por cliente se rechazan con 422.

semantic/hybrid generan un único embedding de la consulta con el adaptador P20:
se envía ese texto, no audios ni fichas. Requieren proveedor habilitado/configurado
y créditos. lexical no consume API; compara solo el mismo subconjunto con vector
vigente para que el baseline y el híbrido sean comparables. La biblioteca textual
ordinaria de P08 sigue siendo independiente y también encuentra pistas sin índice.

GET /api/v1/tracks/{id}/similar?limit=3 usa el vector almacenado de una pista,
excluye esa pista y no genera embedding nuevo. Admite los mismos filtros de álbum
y playlist sobre los candidatos; la referencia puede estar fuera del filtro.
Si la pista existe pero no tiene vector vigente devuelve 409 reference_not_indexed,
sin fingir que simplemente no hay canciones parecidas.

## Compatibilidad y consistencia

Solo son elegibles vectores con ID/versión/hash de ficha actuales, model_key
activo y receta description-v1, texto no vacío y metadatos derivados vigentes.
El modelo/dimensión de la consulta se validan antes de ejecutar ranking; los
vectores históricos, de otra receta o de otro espacio no entran en resultados.
La dimensión P21 sigue siendo 1536; otra configuración requiere migración/reindexación.

Antes de consumir proveedor se comprueba biblioteca, filtros e índice. La conexión
se libera antes de esperar red. Después se abre una instantánea REPEATABLE READ:
se vuelven a aplicar filtros/versiones y se completan pista/ficha/evidencia en esa
misma instantánea. Una ficha modificada durante la espera se excluye. Los datos
son coherentes con esa instantánea, no una promesa de que nadie editará después
de responder. La búsqueda no cambia audio, pistas, fichas, índices ni trabajos.

Cada candidato incluye resumen de pista reproducible, ficha con ID/versión/hash,
fuente/atributos/procedencia, evidencia literal de su texto, distancia cuando
procede y posiciones de ranking. No devuelve el vector ni inventa una explicación:
explanation_source=recorded identifica evidencias guardadas, no un LLM ejecutado.
No envía títulos, audios o fichas al proveedor en el flujo de consulta de P22.

## Orden y fusión

semantic y similitud usan `<=>` de pgvector con parámetros enlazados, orden por
distancia ascendente y UUID para desempatar. Se evalúa búsqueda exacta: no se añade
HNSW/IVFFlat sin medir necesidad. Referencia: [pgvector](https://github.com/pgvector/pgvector).

lexical usa to_tsvector/plainto_tsquery con configuración simple y ts_rank_cd:
título, álbum, artistas, texto descriptivo y valores de atributos. No indexa las
rutas/evidencias como palabras musicales. simple conserva un baseline sin stemming
ni eliminación lingüística de stopwords; no promete equivalencia con búsquedas
semánticas o con el filtro literal de P08. El JSONPath de valores es fijo/tipado;
los textos del usuario son parámetros, nunca SQL o operadores tsquery ejecutables.
[Referencia PostgreSQL](https://www.postgresql.org/docs/17/textsearch-controls.html).

hybrid combina hasta 100 candidatos de cada ranking con Reciprocal Rank Fusion,
constante de trabajo 60: `score = suma(1 / (60 + posición))`, posiciones desde 1.
No suma distancias y scores textuales de escalas diferentes. Desempata por distancia
y UUID. La ventana limita candidatos por rama, no indica un algoritmo ANN ni una
garantía de exhaustividad del ranking híbrido fuera de los primeros 100 de cada rama.
limit solo controla hasta 20 resultados finales; el protocolo P17 se puntúa a K=3.

## Estados, límites y coincidencias débiles

status distingue ok, no_library, no_indexed_tracks y no_matches. Un filtro válido
sin pistas produce no_matches/empty_filter sin consumo; un índice ausente produce
no_indexed_tracks. Falta de referencia indexada es 409, no resultado vacío. Los
errores del proveedor son errores: timeout 504, busy/rate_limit 429 y otros errores
seguros de proveedor 503; entrada inválida 422. No convertir cuota o timeout en
lista vacía exitosa. /ready y reproducción no dependen de OpenAI.

Por defecto **no hay umbral de distancia calibrado**. Una consulta semántica puede
devolver vecinos aunque no haya evidencia suficiente para recomendar. Por eso la
respuesta declara relevance=candidates_only y un aviso de pertinencia pendiente;
ok significa recuperación técnica, no recomendación correcta. No usar distancia,
posición o fusion_score como porcentaje de confianza. No afirmar instrumentos,
artistas o estados de ánimo por ser un vecino cercano.

SEARCH_MAX_COSINE_DISTANCE puede definirse en backend entre 0 y 2 para excluir
candidatos por distancia. No definir la variable significa sin corte; no usar una
cadena vacía ni copiar el valor de un test. En hybrid se aplica a ambas ramas
antes de fusionar; lexical no tiene distancia de consulta y no aplica ese corte.
La configuración no certifica que el umbral haya sido calibrado. Elegirlo solo
con desarrollo P17 y congelarlo antes de las reservadas. Las pruebas usan valores
artificiales para comprobar la mecánica, no para recomendar un umbral musical.

## Evaluación preparada, sin consumo

Se conserva consultas.json de P17 sin alterar grados ni seleccionar resultados
favorables. Cuando exista índice de API real, registrar modos/model_key/receta,
fecha/commit, límites, filtros, consulta, UUID/versión/hash y usage; mapear UUID a
Mxx por hashes del corpus, no por títulos. Ejecutar desarrollo a K=3 y elegir
configuración antes de reservadas. Q16/Q17 siguen exploratorias y Q18 de seguridad
requiere revisión separada; las citas/explicaciones se evalúan en P23.

El evaluador local no llama a la API:

```bash
docker compose exec backend python -m app.evaluate_retrieval --report /app/data/informe.json --partition desarrollo
```

Informe: collection=echobeats-p17-v1, k=3 y runs con exactamente una entrada por
consulta de la partición. Cada entrada: query_id, results (lista ordenada de Mxx,
hasta tres) y decision: candidates, abstain, supported o error. Deben incluirse
también errores, respuestas vacías y negativos. No omitir consultas desfavorables.
El archivo lo prepara una ejecución documentada; el evaluador no verifica que
provenga realmente de API/pgvector ni ejecuta automáticamente ese flujo.

Calcula Hit@3 directo, nDCG@3, precisión de lo devuelto, cobertura directa, errores,
abstenciones negativas y apoyos inseguros. Rechaza IDs desconocidos/duplicados,
referencia excluida, K distinto o consultas omitidas. Un error/positivo vacío cuenta
como cero, no desaparece del denominador. candidates no equivale a abstención.
numerical_gates_met resume objetivos P17 del archivo; real_api_verified=false es
intencional: las métricas por sí solas no acreditan API, citas ni calidad factual.

Con la prueba real pendiente por créditos no se escogió umbral, no se ejecutaron
las reservadas y no se reportan métricas favorables de pertinencia musical. Las
pruebas de P22 acreditan mecánica SQL, filtros y fórmulas con dobles en bases
aisladas, sin insertar vectores ficticios en la biblioteca personal.
