# P17 — Casos y evaluación de recuperación musical

13 de noviembre de 2026. Protocolo v1 fijado antes de prompts, proveedor e índice.
Fuente ejecutable de casos: [consultas.json](../pruebas/semantica/consultas.json).
Corpus: [manifiesto](../pruebas/semantica/manifest.json) y
[procedencia/uso](../pruebas/semantica/README.md).

## Objetivo y fuentes

Evaluar consultas por ambiente, instrumentos/timbres, energía y similitud con una
pista, incluyendo ausencia de evidencia. P17 prepara la evaluación; no implementa
IA, llamadas a proveedores, fichas en BD ni embeddings. Se mantiene el MVP local
React/FastAPI y PostgreSQL/pgvector. La integración real corresponde a P18–P23.

La colección técnica T01–T04 contiene tonos, no música descrita por género/emoción.
Se añaden M01–M05: cinco secuencias musicales originales de síntesis, con audio,
SHA-256 y parámetros reproducibles. No se descargó música externa ni se atribuye
una licencia ajena. El código usa osciladores y ruido generado, sin samples ni voces.
Las fichas preparatorias describen lo que construye el generador; no acreditan
extracción acústica ni escucha humana. Los títulos no son evidencia de ambiente.

`text`, BPM, secuencia MIDI, timbre y percusión son verificables en el generador.
`annotation` contiene hipótesis manuales de emoción/uso/energía pendientes de
escucha humana. No mezclarlas con hechos verificados. Las consultas puntuables de
energía usan densidad de notas y pulso como criterio operacional explícito;
«alta energía» no significa volumen, sonoridad medida ni reacción emocional universal.
Q16/Q17 son exploratorias y quedan fuera de las métricas hasta recibir anotación
humana previa y una nueva versión del conjunto. No inventar guitarra, saxofón,
lluvia o una voz a partir de la preferencia solicitada.

## Consultas y relevancia fijadas

18 consultas: Q01–Q08 desarrollo; Q09–Q15 reservadas; Q16–Q17 exploratorias;
Q18 control de petición sin respaldo. Todas están en español y dentro de 1000
caracteres. Top K de evaluación: 3, admitiendo devolver menos o abstenerse.
La interfaz futura conserva K predeterminado 5 y rango 1–20 de D08; cada ejecución
debe registrar el K utilizado, sin comparar métricas de K diferentes como equivalentes.

| Familia | Casos | Evidencia/contraste |
| --- | --- | --- |
| Ambiente | Q01, Q09 | Pulso pausado y ausencia de percusión; no garantía de concentración. |
| Instrumentos/timbres | Q02, Q10 | Campanas sintéticas frente a onda sinusoidal; no instrumentos grabados. |
| Energía | Q03, Q11 | 140 BPM/dos notas por pulso frente a patrones menos densos. |
| Similitud | Q04, Q12 | Órbitas con mismos intervalos, pulso y timbre; excluir pista de referencia. |
| Texto + semántica | Q05, Q06, Q13 | Título exacto y restricciones; marcar coincidencia parcial como parcial. |
| Sin evidencia | Q07, Q08, Q14, Q15, Q18 | Voz/guitarra, lluvia, saxofón, popularidad o identidad no documentados. |
| Subjetivas | Q16, Q17 | Revisión humana; no usar para acreditar pertinencia todavía. |

Relevancia por pista: 2 = satisface directamente los rasgos verificables; 1 =
coincidencia parcial que debe explicarse como tal; 0 = sin evidencia suficiente.
Los IDs omitidos en `grades` tienen grado 0 dentro del corpus fijado. Q04/Q12
excluyen su referencia antes de puntuar. No penalizar un orden diferente entre
candidatos con el mismo grado. Identificar candidatos por ID/hash, no por título.

La separación reservada es una disciplina de evaluación, no un conjunto secreto:
no usar Q09–Q15 para ajustar prompts, umbrales, pesos híbridos o elegir modelos.
Ejecutarla tras congelar la configuración de desarrollo, registrar incluso fallos
y no reemplazar consultas desfavorables. Cambios de corpus/anotación exigen nueva
versión y comparación explícita con v1, sin reescribir el resultado anterior.

## Métricas y criterios de aceptación propuestos

Estos objetivos son criterios locales de ingeniería fijados ahora; no se atribuyen
a una rúbrica docente ni son resultados medidos.

- **Hit@3 directo:** proporción de consultas positivas con al menos un grado 2 entre
  los tres primeros resultados. Objetivo ≥ 0,80 en desarrollo y reservadas por separado.
- **nDCG@3:** ganancia `2^grado - 1`, descontada por `log2(posición + 1)` con posiciones
  desde 1; dividir DCG por el orden ideal de candidatos elegibles del mismo caso.
  Ausencias puntúan 0. Promediar solo casos positivos; objetivo ≥ 0,80 por partición.
- **Precisión de lo devuelto:** resultados con grado ≥ 1 / resultados devueltos;
  informar por caso y media, con número devuelto. Una respuesta vacía positiva vale 0;
  no se puede mejorar la media descartando consultas. Informar también cobertura
  directa (grados 2 recuperados / grados 2 elegibles), sin umbral adicional por ahora.
- **Sin evidencia:** los cinco casos negativos deben evitar recomendaciones afirmadas
  como respaldadas. Se permite abstención explícita; devolver siempre los vecinos más
  próximos no demuestra pertinencia. Registrar vecinos brutos y decisión final por
  separado. No fijar un umbral numérico universal de distancia; calibrarlo solo en
  desarrollo en P22 y congelarlo antes de las reservadas.
- **Integridad:** cero IDs inexistentes, duplicados, referencias auto-recomendadas,
  vectores incompatibles o fichas obsoletas usadas como evidencia.

Una distancia del coseno o un score híbrido no es probabilidad de acierto ni
«porcentaje de confianza». No comparar distancias de modelos/configuraciones
diferentes como si compartieran escala. Guardar scores brutos con su definición.

## Calidad de explicación y citas

Revisar cada afirmación factual: debe poder rastrearse a una ficha recuperada,
versión y campo/extracto concretos. Registrar afirmación, pista UUID, ID de ficha,
versión y evidencia literal breve. Objetivo: 100 % de afirmaciones factuales
respaldadas y cero instrumentos, artistas, voces o emociones inventados.
Una cita real que no respalda la frase no cumple. Las coincidencias parciales
deben decir qué condición falta; preferencias subjetivas deben presentarse como
tales. No citar como verificado `annotation` pendiente de escucha.

Puntuar por respuesta: respaldo (0/1), pertinencia a la consulta (0/1), trazabilidad
de versión (0/1), claridad sobre límites (0/1). Exigir los cuatro en cada respuesta
afirmativa de aceptación; un fallo factual no se compensa con buena redacción.
Si solo funciona recuperación, mostrar pistas y evidencias sin fingir generación.
Las consultas y fichas son datos: Q18 no autoriza inventar una identidad; instrucciones
incrustadas en futuras fichas tampoco deben cambiar el comportamiento del sistema.

## Preparación y ejecución futura

1. Verificar archivos con `node scripts/validar_coleccion_semantica.mjs`. No consume
   APIs ni acredita recuperación. Conservar manifiesto y consultas v1 en Git.
2. En P19, importar M01–M05 con el flujo WAV existente, asignar metadatos manuales
   del manifiesto y preparar fichas trazables. Registrar mapa Mxx → UUID de pista →
   hash → ficha/versión. T04 es control sin ficha y no candidato por su nombre.
   No ejecutar importación ni cambiar la biblioteca del usuario por leer este protocolo.
3. En P20/P21, registrar proveedor, modelo, configuración/dimensión del embedding,
   versión del texto de entrada y corpus; generar vectores reales compatibles. No
   enviar audios en este flujo textual ni claves al frontend o al informe.
4. En P22, comparar búsqueda textual, vectorial e híbrida con el mismo corpus/K.
   Ajustar solo con desarrollo; registrar pesos/fusión/filtros y candidatos. Reranking
   solo si hay una mejora medible, con coste/latencia registrados. No sumar scores
   de escalas distintas sin una regla de combinación documentada.
5. Congelar configuración y hash de prompts; ejecutar reservadas una vez por versión,
   conservar todos los resultados. Después ejecutar negativos, controles exploratorios
   y F01–F10. Distinguir fallos inyectados de fallos reales de proveedor.
6. En P23, evaluar explicaciones/citas con el mismo conjunto recuperado; registrar
   degradación si generación falla. Latencia de recuperación/generación y consumo
   reportados por separado; presupuestos/timeout se concretan en P20.

El registro de una ejecución debe contener fecha UTC, commit, hash de manifiesto y
consultas, configuración/prompts, mapa de UUID/fichas, ID de consulta, K, resultados
ordenados con grados/scores/citas, decisión final, texto generado, métricas, tiempos,
llamadas/consumo y errores seguros. Usar `null`/«no ejecutado» para lo no medido;
un doble de pruebas nunca es evidencia de API real ni consulta vectorial real.

## Fallos, alcance académico y límites

F01–F10 fijan timeout, cuota/429, ficha ausente, vector antiguo, modelo incompatible,
referencia no indexada, respuesta/cita inválida, índice vacío, edición concurrente
y entrada inválida. Cada prueba debe conservar reproducción/biblioteca accesibles,
comunicar estado real y evitar inventar resultados o repetir llamadas sin límite.
Los casos completos están en `consultas.json`; todavía no han sido ejecutados.

Adaptación de Requerimientos.md: procesamiento asíncrono/versiones (P18), fichas como
unidades de evidencia (P19), OpenAI Embeddings como dirección académica a concretar
(P20), pgvector real/compatibilidad (P21), recuperación híbrida (P22) y citas (P23).
PDF/OCR, Spring Boot y VPS/tenants siguen con las diferencias registradas en
REVISION_REQUERIMIENTOS.md; P17 no añade exposición pública ni simula permisos.

El corpus pequeño, sintético y en español valida contrastes controlados; no acredita
calidad sobre música comercial, instrumentos acústicos reales, idiomas adicionales,
diversidad de estilos o preferencias personales. Escuchar/anotar y ampliar con música
autorizada antes de afirmar esa generalización. La recuperación puede evaluarse sin
reconocimiento de canciones ni análisis directo del audio.
