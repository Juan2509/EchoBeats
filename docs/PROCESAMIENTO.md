# Procesamiento durable — P18

Operación disponible: **preparar metadatos existentes**. No extrae emociones,
instrumentos ni géneros del sonido, no crea fichas P19, no genera embeddings ni
consume APIs. No reescribe originales ni modifica campos manuales.

## Uso

En Biblioteca → Canciones o en pistas de un álbum, desplegar «Preparación de
información» y pulsar «Preparar información». Consultar estado/historial y, si
falla, «Reintentar preparación». «Actualizar estado» relee tras un fallo de red.
La consulta periódica solo permanece activa con el panel abierto y trabajo activo;
cerrar el panel/página cancela consultas del cliente, no elimina la tarea durable.
Preparar de nuevo la misma versión reutiliza su trabajo, sin duplicar ejecución.

Estados: pendiente, procesando, completado, error y desactualizado. Completado
significa que se preparó un resumen verificable de título, artistas, duración,
hash y revisión actuales. No equivale a una canción analizada por IA.
Versiones anteriores permanecen en el historial con indicador de antigüedad.
Cambiar metadatos permite solicitar una preparación nueva para la revisión nueva.

## Persistencia, exclusión y versiones

`processing_job` se crea en PostgreSQL por `0006_processing_jobs`. La solicitud
bloquea brevemente la pista, captura su revisión y reutiliza/crea una fila única
por pista/operación/versión. Adquisición y finalización usan transacciones cortas;
la tarea se ejecuta en otro hilo y lee mediante su propia conexión.

El trabajador usa una sesión dedicada en autocommit con advisory lock
PostgreSQL `(180018, 1)`, de alcance de la base. Solo el dueño recupera/interpreta
la cola; otro proceso espera sin marcar como interrumpidas tareas del dueño vivo.
No hay llamadas de red ni una transacción abierta durante el trabajo. Esto es un
trabajador local de prototipo, no un servicio distribuido ni una cola en memoria.

Adquirir cambia pending → processing y aumenta attempts. Finalizar comprueba
estado, número de intento y revisión de entrada bajo bloqueo. Un resultado de
otra versión pasa a stale sin publicar result; una finalización duplicada o de
un intento anterior se ignora. Un error publica código/mensaje fijo seguro, sin
excepción original. No se modifica la pista ni se condiciona servir audio.

## Interrupción y reintentos

Al detener backend se solicita parar el hilo y se espera hasta cinco segundos.
Si una tarea queda processing tras una terminación abrupta, el siguiente dueño
del bloqueo la marca error/interrupted. No se repite automáticamente. Las tareas
pending siguen persistidas y se ejecutan cuando el trabajador esté disponible.
La pérdida de conexión causa espera y recuperación al recuperar la sesión dueña.

Reintentar es explícito, solo para error/stale con la misma revisión vigente y
menos de tres intentos adquiridos. Limpia resultado/error/fechas del intento y
vuelve a pending; conserva ID, creación y contador. Al llegar al límite, devuelve
409; no se resetea el contador recargando página ni repitiendo POST de creación.
Resolver el problema antes de continuar; una revisión nueva inicia otro trabajo.
Una versión antigua exige solicitar una preparación actual, no repetir entrada vieja.

`PROCESSING_WORKER_ENABLED=false` pausa la ejecución sin borrar cola. Reiniciar
backend al cambiarlo. La API puede aceptar pendientes durante la pausa; no los
anuncia completados. Por defecto true. No es un control de autorización ni se
habilita acceso público. Desplegar varios procesos sigue limitado por el bloqueo,
pero no convierte esta implementación en arquitectura multiusuario/distribuida.

## Operación y siguientes pasos

Aplicar `docker compose exec backend python -m alembic upgrade head` con respaldo
previo; reiniciar backend para cargar código. No borrar volúmenes. No usar la base
principal para downgrades: la migración rechaza retirar una tabla con trabajos.
Respaldar BD y medios según BASE_DATOS.md; el historial forma parte del dump.

Contrato de rutas en CONTRATO_API.md. P19 añadirá fichas con procedencia; P20–P21
integrarán proveedor/modelo y tareas de indexación con su versión/model_key,
timeouts y política de coste propios. No habilitar index_description por el nombre
de un ejemplo. Esta etapa incorpora procesamiento asíncrono y trazabilidad de
Requerimientos.md; no acredita todavía RAG, búsquedas híbridas ni API real.
