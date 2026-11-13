# Fichas musicales estructuradas — P19

Una ficha es información aportada con procedencia, no un análisis automático del
audio. Puede estar incompleta sin impedir escuchar, editar metadatos o importar.
P19 no consume APIs, no reconoce instrumentos por sonido y no genera embeddings.

## Editar una pista

En Biblioteca → Canciones o en pistas de un álbum, pulsar «Ficha musical».
El diálogo permite guardar descripción, fuente, procedencia y atributos. Cada
atributo indica nombre, valor, fuente, evidencia y si es interpretación subjetiva.
No rellenar lo desconocido. `verified` es una declaración del editor acompañada
de fuente; no una certificación automática de la veracidad del contenido.

Fuentes admitidas: manual, verified y metadata. No se admite source=model en esta
API: requiere una integración futura que valide y registre su procedencia.
Emoción, energía y contexto siempre son interpretaciones manuales. Un dato de
tempo puede proceder de un generador, una fuente documentada o una medición
realmente realizada; no se deduce del título ni de una preferencia del usuario.

La procedencia general es obligatoria; el texto puede quedar vacío para conservar
una ficha incompleta. Para ser candidata a indexación debe tener descripción no
vacía y, si deriva de metadatos, no estar desactualizada. Los atributos son opcionales,
pero cada uno exige valor y evidencia. Límites: texto 6000 caracteres, procedencia
2000, hasta 20 atributos, valor 255 y evidencia 1000; BPM entre 1 y 400. No duplicar
el mismo atributo: reunir valores/evidencias en su campo.

Guardar bloquea temporalmente la edición y conserva el borrador ante error.
Conflicto o respuesta incierta exige recargar antes de escribir otra vez;
recargar pide confirmar el descarte si hay cambios. Cerrar, Escape y navegación
advierten de cambios sin guardar; durante una escritura se evita salir del editor
mediante sus controles. Cerrar el navegador muestra el aviso nativo; una petición
ya enviada podría completarse. La ficha no modifica el reproductor ni el original.

## Versiones y preparación para indexación

Creación: If-None-Match: *. Actualización: If-Match de la ficha. Se bloquea la pista
durante una transacción corta para evitar dos creaciones o ediciones simultáneas.
Una modificación crea versión nueva; guardar contenido idéntico es una operación
sin cambios de versión. Se conserva un historial de snapshots con ID, versión,
contenido, evidencias, hash y revisión de pista de entrada.

Los cambios de metadatos no reescriben fichas manuales/verificadas ni sus atributos.
Si la fuente general o un atributo es metadata, se compara la revisión de pista
de entrada con la actual: `metadata_stale=true` conserva la ficha pero requiere
revisión/corrección antes de indexarla. Guardar sin cambios no certifica información
vieja; corregir el contenido/evidencia crea la versión actualizada.
Los trabajos prepare_metadata de P18 nunca publican sobre una ficha.

P19 devuelve `index_status=not_indexed`, `can_index`, `needs_indexing` e indicación
de que aún no hay embedding. Esto es elegibilidad, no indexación ejecutada. Cambiar
la ficha/version/content_hash requerirá generar el vector de la nueva entrada en
P21; no se marca ready ni se inventa un vector stale que aún no existe. En P21 se
añadirá el vínculo explícito con modelo/configuración y versión indexada.

La versión histórica puede consultarse mediante
GET /api/v1/tracks/{id}/description/versions/{version}; devuelve historical=true,
sin presentar el estado histórico como elegibilidad actual. El editor muestra la
versión actual; todavía no incluye un explorador visual del historial.

## Corpus P17 preparado

`node scripts/preparar_fichas_p17.mjs` genera
`pruebas/semantica/fichas.json`: cinco propuestas derivadas del manifiesto,
identificadas por Mxx y SHA-256. Regenera ese archivo de propuestas; no modifica
audios ni fichas guardadas. Solo contiene rasgos verificables por construcción:
BPM, timbre, modo, percusión, voz ausente y notas/pulso. Excluye annotation y sus
emociones/energía/contexto pendientes de escucha humana. Preservar consultas
reservadas de P17; no cambiar expectativas para favorecer resultados futuros.

Para aplicarlas a una biblioteca local, importar primero los WAV con el importador
existente. Ejecutar `node scripts/cargar_fichas_p17.mjs` para simular: identifica
pistas por content_sha256 expuesto en la API, nunca por título solamente.
Solo `--apply` escribe fichas ausentes con precondición de creación; conserva
cualquier ficha ya existente, incluidas correcciones manuales. Una coincidencia
ausente o ambigua se omite. Un fallo puede dejar un lote parcial; repetir es seguro
para las fichas ya creadas porque se omiten, sin sobrescribir. No importa audios,
no cambia títulos/álbumes y solo admite API HTTP local. `--help` detalla opciones.

La creación de las cinco fichas se probó con WAV reales en una base aislada y
medios temporales; no se cargaron en la biblioteca personal durante este paso.
Para música externa, anotar solo información con procedencia disponible; el
material sintético no acredita evaluación emocional ni reconocimiento acústico.

## Conservación y alcance

Migración `0007_track_descriptions`: ficha actual e historial, FK RESTRICT. No
modifica canciones/medios. Downgrade se rechaza si hay fichas; nunca probarlo en
la principal. Respaldar BD y MEDIA_ROOT; el dump conserva fichas e historial.

Las fichas/evidencias constituyen datos de entrada para el RAG futuro, no órdenes
para ejecutar herramientas o cambiar instrucciones. Esta etapa concreta trazabilidad
de Requerimientos.md; API/modelos, embeddings, búsqueda híbrida y citas generadas
se implementan en P20–P23, con las decisiones académicas pendientes registradas.
