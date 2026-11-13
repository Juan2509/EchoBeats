# P17 — Preparación de la evaluación musical

13 de noviembre de 2026. Paso completado como preparación del conjunto y protocolo,
no como integración ni validación de búsqueda semántica.

## Entregables

- [EVALUACION_BUSQUEDA.md](EVALUACION_BUSQUEDA.md): relevancia, particiones,
  métricas/objetivos previos, explicaciones con evidencias, fallos y registro de ejecuciones.
- [Colección original](../pruebas/semantica/README.md): cinco WAV musicales sintéticos,
  manifiesto con SHA-256, parámetros y procedencia; descripciones verificables por
  construcción y anotaciones subjetivas pendientes de revisión humana separadas.
- [consultas.json](../pruebas/semantica/consultas.json): 18 consultas por ambiente,
  timbre/instrumento sintético, energía, similitud y búsqueda híbrida; negativos y
  controles exploratorios. Diez escenarios de fallo para P18–P23.
- Generador y verificador locales sin dependencias ni acceso externo.

## Evidencia ejecutada

`node scripts/generar_coleccion_semantica.mjs` generó cinco WAV de 12 segundos
(PCM 16 bits, mono, 22050 Hz), 529244 bytes cada uno, y su manifiesto. No se
importaron a la aplicación ni se modificaron medios personales o la base de datos.

`node scripts/validar_coleccion_semantica.mjs` aprobó integridad/hash, cabeceras,
duración, señal no silenciosa y sin saturación, IDs únicos, correspondencia de
corpus, referencias/exclusiones, grados de relevancia y campos de evidencia.
Resultado: 5 WAV, 18 consultas y 10 escenarios coherentes. No evalúa calidad de IA.

Se repitió el generador sin `--overwrite`: rechazó la sustitución y se verificó
que el hash del manifiesto no cambió. No se regeneró sobre archivos existentes.
`node --check` comprueba sintaxis de ambos scripts; `git diff --check` comprueba
formato. No se repitieron pruebas de aplicación porque no cambió código del producto,
dependencias, esquema ni contratos en ejecución.

## Cierre y límites

P17 deja un conjunto reproducible fijado antes de elegir prompts/resultados.
P18 es la siguiente implementación. En P19 habrá que vincular Mxx con UUID reales
por hash y guardar fichas; P20–P23 deben aportar API real, vectores y consultas
PostgreSQL, comparación textual/vectorial/híbrida y explicaciones con citas.

Las consultas reservadas no deben usarse para ajustar configuración. Emociones
exploratorias pendientes de escucha humana no puntúan aún. Esta colección no
acredita pertinencia sobre música externa o preferencias generales, ni CA-10/CA-11.
No hubo descargas, servicios contratados ni llamadas con coste. Los pendientes
visuales de P08/P15/P16 y audio siguen registrados; P17 no los cierra.
