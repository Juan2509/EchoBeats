# P18 — Estados y reintentos de procesamiento

13 de noviembre de 2026. Implementación y verificación automatizada completadas;
interacción visual pendiente. Próxima implementación P19.

## Resultado

Cola durable PostgreSQL, estados pending/processing/completed/error/stale,
versión de entrada y hasta tres intentos explícitos. Ejecución en hilo local,
adquisición atómica, exclusión entre trabajadores mediante bloqueo PostgreSQL,
recuperación de trabajos interrumpidos y rechazo de resultados duplicados/antiguos.
La operación real P18 prepara metadatos existentes con procedencia; no modifica
canciones ni originales, no analiza sonido, no genera fichas/embeddings ni usa APIs.

Rutas nuevas y controles desplegables por canción permiten crear, consultar,
actualizar estado y reintentar. Ver [PROCESAMIENTO.md](PROCESAMIENTO.md) y
[contrato](CONTRATO_API.md). El cierre de panel o página no borra el trabajo.

## Pruebas ejecutadas

- `docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error`:
  **120 pruebas aprobadas** con bases aisladas; nunca downgrades/tests sobre la principal.
- Después del ajuste final de procedencia e indicador histórico, se repitió
  `pytest tests/test_processing.py -W error`: **8 pruebas aprobadas**.
- P18 cubre deduplicación de seis solicitudes concurrentes, adquisición única,
  trabajador real, fallo seguro sin filtrar excepción, tres intentos, recuperación
  tras interrupción y reintento sin importar otra vez, stale antes/durante la tarea,
  CAS frente a intento tardío, segundo trabajador sin recuperar al dueño vivo,
  resultado histórico identificado y downgrade protegido. Se comprueba GET de
  pista/audio y respuesta parcial 206 después de solicitar procesamiento.
- `npm.cmd test`: **42 pruebas aprobadas**. El panel nuevo no tiene prueba DOM;
  estas pruebas no acreditan interacción visual.
- `npm.cmd run build`: TypeScript y compilación Vite aprobados.
- `python -m compileall -q app migrations`: sin errores.
- `git diff --check`: sin errores.

La primera regresión completa se interrumpió al reiniciar backend para cargar
P18; se repitió después del reinicio y terminó con los 120 éxitos citados.
No se presenta esa ejecución interrumpida como aprobada.

## Migración local y comprobaciones reales

Se conservó `backups/echobeats_pre_p18_a7b92.dump`, formato pg_dump custom,
antes de migrar desde `0005_album_walls`; manifiesto compatible con el script de
restauración en `backups/echobeats_pre_p18_a7b92.json`. Cabecera PGDMP y SHA-256
verificados. Copia inicial de metadatos también en `.dump.json`; el manifiesto
canónico para restaurar es `.json`. El dump no incluye medios: se conservaron
MEDIA_ROOT y volumen existentes. Los respaldos privados permanecen fuera de Git.

Se aplicó `0006_processing_jobs`, que solo añade tabla/índice de trabajos, y se
reinició backend para cargar el código. `/api/v1/ready` respondió ready con BD,
pgvector y migraciones ok; OpenAPI expuso las rutas nuevas. Una consulta de lectura
en pg_locks confirmó un único dueño del bloqueo del trabajador en la base local.
Las tareas de prueba se crearon en bases aisladas, no en la biblioteca personal.
El downgrade rechaza retirar historial; no se ejecutó en la base principal.

## Revisión pendiente

Computer Use no expuso navegadores y devolvió `The browser access host is unavailable`.
No se realizaron acciones UI ni se declara escucha real. Revisar manualmente:

1. Abrir Biblioteca → Canciones → «Preparación de información».
2. Preparar una pista; comprobar pendiente/procesando/completado o su estado final
   (una tarea rápida puede acabar antes del primer refresco), sin impedir reproducir.
3. Cerrar/reabrir el panel/página y comprobar historial persistido.
4. Editar metadatos y comprobar que el trabajo anterior se identifica como histórico
   y se puede iniciar el de la versión nueva.
5. Revisar teclado y panel a 360/768/1280 px. Fallos/reinicio/concurrencia ya se
   probaron de forma automatizada y aislada; no provocar fallos en datos personales.

Se mantienen pendientes visuales de P08/P15/P16 y audio. P18 incorpora
asincronía/versiones de Requerimientos.md, pero no acredita RAG ni CA-10/CA-11.
