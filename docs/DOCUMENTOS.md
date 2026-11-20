# Documentos en EchoBeats

La sección **Documentos** recibe un PDF de hasta 10 MiB y 12 páginas.
ClamAV escanea el archivo antes de que Poppler extraiga el texto. Las páginas
sin texto legible pasan por Tesseract en español e inglés. El trabajador guarda
hasta 40 fragmentos, preserva su orden y las páginas de origen, registra encabezados de sección reconocibles y usa OpenAI
para generar los embeddings. PostgreSQL conserva los fragmentos y vectores en
pgvector, junto con el nombre, hash y modelo. El original en tu equipo sigue
siendo la fuente para verificar imágenes, tablas, sellos o firmas.

La carga queda en una cola persistente y privada, con hasta cinco PDF en curso
por instancia. Al publicar el índice o registrar un fallo se retira el PDF
temporal de la base en la misma transacción. Ante un reinicio, el trabajador
retoma las cargas interrumpidas. Si ya se habían solicitado embeddings, el
reinicio puede volver a consumir créditos para esos fragmentos. Si falla el procesamiento, vuelve a cargar el
archivo para reintentarlo. En el modo remoto cada cuenta consulta solo su propia
base. El PDF temporal no tiene una URL de descarga.

## Activación

En el entorno privado de la instancia, configura una clave de OpenAI con
créditos, `AI_ENABLED=true`, `DOCUMENTS_ENABLED=true`,
`AI_EMBEDDING_DIMENSIONS=1536` y `PROCESSING_WORKER_ENABLED=true`.
La carga envía texto extraído a OpenAI y consume el saldo de la cuenta.
La consulta también puede consumir créditos. No se envía el PDF ni imágenes.

Reconstruye los servicios para aplicar la migración `0014_document_index` y
poner en marcha el trabajador. Ejecuta la actualización de firmas desde la
instancia correspondiente. En modo remoto, añade las mismas opciones de
proyecto y archivo de entorno que usaste al levantar la cuenta.

```sh
docker compose up --build -d --wait
docker compose exec -T backend freshclam
```

El volumen `document_signatures` conserva las firmas entre recreaciones.
Actualízalas periódicamente. La carga queda deshabilitada sin firmas y el
procesamiento falla si el escáner no puede completar el análisis.

## Consultar un documento

1. Abre **Documentos**, selecciona un PDF y pulsa **Procesar PDF**.
2. Espera el estado **Listo** y pulsa **Consultar**.
3. Escribe una pregunta. Se combinan coincidencias textuales y vectoriales
   dentro de ese documento. La respuesta se apoya en fragmentos recuperados y
   muestra citas con documento y página. Si no se verifican las citas de la
   respuesta generada, se muestran los fragmentos recuperados.
4. **Eliminar** retira el documento y su índice de la instancia.

La aplicación elimina la copia PDF del conjunto activo de datos. Una copia
de seguridad tomada durante una carga pendiente, los registros de PostgreSQL
y el almacenamiento físico pueden conservar rastros según su retención.
Para respaldar el índice sin incluir originales en cola, excluye los datos
de `document_upload` y respalda cuando la cola esté vacía.
