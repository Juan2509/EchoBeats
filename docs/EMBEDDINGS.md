# Indexación musical — P21

## Qué hace

Una ficha guardada puede indexarse como texto mediante el proveedor OpenAI de
P20. El resultado se almacena en PostgreSQL/pgvector vinculado a la ficha, su
versión/hash y configuración de modelo. No se analiza ni se envía el audio.
Guardar una ficha no inicia indexación automáticamente.

En «Ficha musical» aparece «Índice semántico». Guardar los cambios antes de pulsar
«Indexar ficha guardada». La interfaz indica que envía texto, atributos y evidencias
a OpenAI y puede consumir créditos. La API rechaza solicitudes nuevas si la IA
está desactivada/sin clave; completar fichas o audio no depende de activarla.
Si la última prueba del proveedor falló por créditos, resolver ese estado antes
de habilitarlo o reintentar; no repetir llamadas por el solo hecho de instalar P21.

Estados: sin ficha, incompleta, sin indexar, pendiente, indexando, vigente,
desactualizado y error. Un resultado ready significa que hay un vector guardado
de la versión/hash/modelo actuales y que la ficha sigue siendo elegible. Un registro
histórico no se presenta como vigente. Consultar estado no consume API.

## Identidad de entrada y almacenamiento

Modelo: text-embedding-3-small, 1536 dimensiones, float. Se conserva el adaptador
P20 y se añade a la clave de aplicación la receta de preparación:

`openai:text-embedding-3-small:dimensions=1536:float:v1:description-v1`

description-v1 es JSON canónico UTF-8 con text/features/source/source_details,
claves ordenadas y sin UUID, fechas ni versión dentro del texto semántico. Mantiene
las etiquetas de fuente e interpretación; no convierte una opinión en hecho.
El hash de contenido de P19 identifica esa entrada. Hasta 6000 bytes: una ficha
que excede el presupuesto se rechaza antes de encolar/enviar, sin truncado silencioso
ni perder evidencias guardadas. Cambiar la receta cambia la clave y exige reindexar.

`track_embedding` conserva UUID, description_id/version, content_hash, model_key,
input_format, embedding vector(1536), usage y fecha. La pista se deriva de la FK
a su ficha única. Unicidad ficha/versión/modelo; FK RESTRICT y conservación de
vectores históricos. No se añade ANN: P22 partirá de recuperación exacta para el
corpus pequeño, sin asumir una mejora de un índice aproximado.

Vector1536 usa un tipo SQLAlchemy y CAST de parámetros enlazados, sin concatenar
valores en SQL. Valida dimensión, valores numéricos finitos/no booleanos, rango
float32 y vector no nulo. PostgreSQL comprueba además su tipo/dimensión. No se
añadieron dependencias: pgvector ya está instalado, SQLAlchemy/psycopg ya bloqueados.
Referencias de implementación: [pgvector](https://github.com/pgvector/pgvector),
[tipos personalizados SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/custom_types.html).

## Cola, concurrencia y fallos

0008 amplía processing_job con model_key e input_hash y operación index_description.
input_version es versión de ficha para indexación y revisión de pista para
prepare_metadata. La unicidad incluye modelo. Los trabajos antiguos reciben
model_key vacío; su ejecución de metadatos y contador no se alteran.

El trabajador P18 conserva el único dueño de bloqueo PostgreSQL; atiende las dos
operaciones. Cada adquisición/finalización bloquea pista y trabajo en ese orden.
Prepara una instantánea, libera conexión/transacción antes de la llamada externa
y comprueba otra vez versión/hash/elegibilidad/modelo antes de publicar.
La inserción de vector y finalización del trabajo son una sola transacción.
Un intento antiguo/duplicado no publica; una ficha cambiada en vuelo pasa a stale.

Repetir la solicitud de la misma entrada devuelve el trabajo existente, incluso
si terminó o falló; no crea un nuevo intento ni regenera. Un error requiere retry
explícito, hasta tres adquisiciones, con entrada vigente y proveedor habilitado.
Cuota/timeout no crean bucles de reintentos. Cambiar ficha/modelo exige solicitar
la entrada nueva. Un resultado incierto puede haber consumido API: consultar
estado antes de reintentar. Error/cierre no impiden reproducir.

Al reiniciar, processing se convierte en error/interrupted y no se repite solo.
pending se conserva; indexación espera mientras AI_ENABLED=false. Habilitar la IA
puede reanudar pendientes existentes: revisarlos antes de habilitarla si se dejó
una cola intencionalmente pausada. Los trabajos de metadatos siguen funcionando
sin IA. El entorno/modelo se carga al recrear el backend, no con cambios de UI.

## API efectiva

- POST /tracks/{id}/index-jobs: sin cuerpo o JSON vacío. 202 con trabajo completo.
  Modelo/versión/hash se eligen en servidor; campos adicionales 422. Ficha
  ausente 404, incompleta/obsoleta 409, entrada extensa 422, IA no habilitada 503.
- GET /tracks/{id}/index-status: status, model_key, description_version/hash y job
  cuando existan. Nunca devuelve el vector ni hace llamadas externas.
- GET /jobs/{id} y POST /jobs/{id}/retry atienden ambas operaciones. is_current
  de indexación usa versión/hash/elegibilidad/modelo, no revisión de pista sin más.
- GET/PUT description actualizan index_status/needs_indexing/index_notice según
  lo realmente almacenado. Historial de descripción conserva su carácter histórico.
- El listado processing-jobs de P18 conserva solo prepare_metadata para no mezclar
  contadores/versiones en su panel. El índice tiene su propio estado.

Conservar la clave privada y límites de P20. No existe endpoint público de cambiar
modelo, claves, cuotas ni facturación. El esquema P21 exige 1536 dimensiones;
otra dimensión configurada rechaza encolar (409) y no usa los vectores existentes.
Cambiar ese espacio requerirá migración/configuración y reindexación deliberadas.

## Comprobación real pendiente

La prueba local usa pgvector real y proveedor simulado únicamente en bases aisladas;
esos vectores no se insertaron en la biblioteca personal ni acreditan API real.
La última prueba de P20 devolvió credit_balance_exhausted. No se hicieron nuevas
llamadas de proveedor durante el desarrollo P21 sin confirmar su resolución.

Para cerrar: resolver créditos y comprobar P20; importar corpus P17 autorizado y
guardar sus fichas; habilitar IA de forma consciente; indexar una ficha y verificar
en nueva conexión que persisten modelo, versión, hash, vector_dims=1536 y usage.
Repetir solicitud y comprobar mismo trabajo/vector sin otra llamada; editar ficha,
comprobar stale e indexar nueva versión. Conservar evidencia segura, sin claves ni
audio enviado. La búsqueda semántica y evaluación de pertinencia siguen en P22/P23.
