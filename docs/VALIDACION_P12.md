# P12 — Muros persistentes independientes por álbum

Fecha: 13 de noviembre de 2026. Implementado sin commit.

## Resultado

La migración `0005_album_walls` crea `wall` y `wall_element` y asigna un muro
inicial a cada álbum existente, incluido «Sin álbum». Los álbumes nuevos, tanto
manuales como derivados de etiquetas, crean su muro en la misma transacción.
Cada muro empieza con fondo `#242038`, formato 1, revisión 1 y elementos vacíos.

Esta entrega incorpora persistencia y API. El editor visual, la carga de nuevos
recursos decorativos y las interacciones se implementan en P13–P16. No se declara
verificado el recorrido visual de decoración CA-06/CA-07 ni se cierran los
pendientes de P08/P09/P10/O06.

## API disponible

- `GET /api/v1/albums/{id}/wall`: composición completa y ETag; lectura consistente
  sin crear recursos ni modificar fechas/revisión.
- `PUT /api/v1/albums/{id}/wall`: sustituye fondo y todos los elementos en una
  transacción con `If-Match`. Devuelve composición, nueva revisión y ETag.
- `POST /api/v1/albums/{id}/wall/reset`: restablece fondo y elementos solo del
  álbum indicado, con revisión obligatoria. Base para la interfaz de P16.

Sin `If-Match`: 428; revisión obsoleta o `*`: 412 `revision_conflict`, con
`current_revision`, `current_etag` y cabecera ETag. Los recursos versionados de
metadatos y playlists comparten ahora esa información adicional de conflicto.
Álbum inexistente: 404. Si falta su muro por una inconsistencia del catálogo:
503, sin crearlo silenciosamente durante GET.

## Validación y conservación

Formato 1, color hexadecimal normalizado a mayúsculas, hasta 30 elementos y UUID
sin repeticiones. Cada elemento guarda recurso, tipo, centro, tamaño, rotación
y orden. Centro entre 0 y 1; dimensiones entre 0.03 y 0.60; z_index entero 0–29.
Números finitos, sin coerción de booleanos o cadenas numéricas; ángulos
normalizados a [−180,180). Se comprueba el rectángulo girado completo sobre
1000 × 700, con tolerancia de `1e-7` unidades de ese lienzo. Empates de orden se
resuelven por UUID, sin modificar z_index.

Se rechazan datos adicionales, IDs pertenecientes a otro muro, referencias
inexistentes, audios y recursos visuales incompatibles. Se verifican tamaño,
dimensiones y presencia del archivo gestionado antes de reemplazar filas.
PNG/JPEG existentes se pueden reutilizar como póster/sticker/imagen. El tipo GIF
requiere un recurso gestionado GIF de hasta 200 fotogramas; su referencia y
contenido se probaron con una fixture temporal. La subida de GIF sigue pendiente
para P14: `/assets` continúa aceptando únicamente PNG/JPEG.

Un bloqueo por muro serializa escrituras; la restricción global de ID impide que
dos álbumes publiquen simultáneamente un mismo elemento nuevo. Las inserciones
se ordenan por UUID para evitar adquirir esos IDs en órdenes opuestos. Cualquier
fallo revierte la composición completa. Quitar/restablecer elementos elimina
solo filas del muro, conservando recursos y referencias de otros álbumes.

La BD restringe unicidad de muro por álbum, referencias y valores escalares;
la geometría rotada, el máximo de elementos y compatibilidad de recursos se
validan en la API. No escribir composiciones directamente en tablas.

## Evidencias ejecutadas

- **102 pruebas backend superadas**, con PostgreSQL real y avisos como errores;
  incluyen las 76 previas y 26 de P12. Bases aleatorias aisladas, sin tests ni
  downgrades sobre la principal.
- Creación de muro manual/importado/de sistema; reimportación conserva ID;
  rollback de álbum y muro juntos ante fallo de creación.
- Guardar/leer/quitar/restablecer A mantiene B y sus recursos intactos. Revisión
  concurrente: una escritura gana y otra recibe 412. ID nuevo compartido por
  dos muros: una escritura gana y otra recibe 422, con rollback del muro perdedor.
- Límites de geometría rotada y versión; 30/31 elementos, duplicados, tipo de
  recurso incorrecto, archivo ausente, GIF y números NaN/Infinity en JSON real.
- Migración desde 0004 con álbumes preexistentes, upgrade repetido, downgrade de
  muros iniciales y rechazo del downgrade si existen personalizaciones guardadas.
  La regresión también cubre upgrade/downgrade hasta base en BD aislada.
- `alembic check`: sin operaciones nuevas; `pip check`: correcto; OpenAPI generado
  con las rutas de muro. Auditoría: sin archivos faltantes, huérfanos ni staging.
  No se añadieron dependencias ni se modificó frontend en P12.

## Verificación HTTP y reinicio reales

Antes de migrar se creó el respaldo local
`backups/echobeats_20261113T132123Z_cce71cbe.dump`, con manifiesto y hash;
no incluye medios. Se conservan todos los respaldos, `.env`, volumen y MEDIA_ROOT.
Una instantánea HTTP del catálogo confirmó que migrar no cambió álbumes, canciones
ni playlists existentes, y que todos los álbumes previos recibieron su muro vacío.

Se crearon solo dos álbumes de demostración vacíos, «Demostración P12 A» y
«Demostración P12 B», reutilizando una imagen sintética. Por el proxy de Vite
se guardaron fondos, tipos, posiciones, dimensiones, ángulos y orden diferentes.
Intentar guardar en B el ID de un elemento de A devolvió 422, sin cambiar B.

Después de reiniciar el backend, las respuestas de ambos muros coincidieron
exactamente con las guardadas: ID, álbum, fondo, elementos, recursos, geometría,
orden, fecha, revisión y ETag. El contenido de la imagen siguió respondiendo 200.
La comparación del catálogo previo verificó pistas y playlists intactas y todos
los álbumes anteriores conservados. La nueva comprobación de readiness fue sana.
Los servicios quedan activos para revisión local. No se modificaron canciones
del usuario ni se sobrescribieron archivos originales.

## Repetir

Arrancar según README; Compose aplica 0005 antes del backend. Consultar las rutas
en `http://localhost:8000/docs`. Obtener el muro por GET y enviar la composición
del ejemplo de CONTRATO_API.md con su ETag exacto en `If-Match`; usar un asset
visual existente y UUID nuevo por elemento. Repetir GET tras reiniciar backend y
comprobar A/B. Una respuesta GET contiene campos de solo lectura: no reenviarla
completa en PUT. No reintentar una escritura de resultado incierto sin releer.

El downgrade de 0005 se niega si hay elementos, fondo distinto del inicial o
revisión > 1; evita perder diseños, incluso tras un restablecimiento. Probar
reversión exclusivamente en bases aisladas. Siguiente: **P13**, mostrar el muro
y sus modos de edición y bloqueo.
