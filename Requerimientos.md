# Arquitectura RAG  — Java - Springboot y pgvector

1. ## Objetivo

  Permitir que cada cliente conserve los PDF originales en su computador mientras consulta y analiza su
  contenido desde cualquier lugar. En el VPS se almacenan fragmentos de texto, embeddings y metadatos; no se
  necesita que el computador esté encendido para consultar el texto ya indexado.

2. ## Componentes

  • Cliente web: carga temporal de PDF por HTTPS.
  • SpringBoot: autenticación, autorización, recepción y gestión de expedientes.
  • Procesador asíncrono en Servidor: extracción de texto, OCR cuando sea necesario, segmentación e indexación.
  • OpenAI Embeddings para el MVP; proveedor local en una etapa posterior.
  • PostgreSQL + pgvector en Servidor: datos transaccionales, fragmentos, vectores y trazabilidad.
  • SprignBoot+  Pgvector.EntityFrameworkCore: persistencia y consultas.
  • Motor RAG: búsqueda híbrida, recuperación contextual y generación de respuestas fundamentadas.

  ## Flujo de indexación

3. El cliente selecciona un PDF de su computador y lo envía cifrado por HTTPS.

4. La API lo guarda temporalmente en el Servidor, con límites de tamaño, validación y escaneo de archivos.

5. Un trabajo asíncrono extrae texto y ejecuta OCR para páginas escaneadas.

6. El procesador divide el texto en fragmentos (por ejemplo, 500–1.000 tokens con solapamiento moderado),
  conservando página, sección y orden.

7. Se solicita a OpenAI un embedding para cada fragmento.

8. Se almacenan en PostgreSQL el texto, vector, identificadores, permisos, modelo y metadatos.

9. Se verifica la indexación y se elimina la copia temporal del PDF según la política acordada. El PDF original
  permanece en el equipo del cliente.

10. Flujo de consulta

11. Se genera el embedding de la pregunta con el mismo modelo utilizado para el índice consultado.

12. PostgreSQL recupera fragmentos mediante pgvector, siempre aplicando filtros de tenant y autorización.

13. Se combinan, cuando convenga, resultados vectoriales y búsqueda textual; se reordenan y seleccionan
   evidencias.

6. El modelo recibe fragmentos recuperados y devuelve análisis con citas al documento, página y fuente.

# Limitaciones de no conservar el PDF

La IA puede consultar fragmentos ya indexados con el PC apagado, pero no puede abrir, descargar ni verificar
el PDF original si no está disponible. Las citas por página dependen de metadatos extraídos durante la
indexación. Para valor probatorio, fidelidad de imágenes, tablas, firmas o sellos, el original puede ser
indispensable; guardar hash no reemplaza el archivo. Reindexar por cambio de OCR o extracción puede exigir
que el cliente vuelva a cargar el PDF.