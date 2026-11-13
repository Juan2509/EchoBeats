# Importación de MP3 — P06

Actualización O06: también se admiten WAV PCM, FLAC nativo y Ogg Vorbis/Opus
(.ogg/.opus), con los mismos límites y conservación de originales. Ver
[audio multiformato](AUDIO_MULTIFORMATO.md). Los apartados históricos siguientes
describen la entrega inicial de P06.

12 de noviembre de 2026. P06 incluye la base de P05, que todavía no existía al
solicitar este paso. P07 amplió esta importación con etiquetas y portadas;
la biblioteca visual y reproducción siguen pendientes de P08–P10.

## Uso

Seguir el [README](../README.md) para iniciar el entorno. En la página inicial,
seleccionar uno o varios MP3 y pulsar «Importar a mi biblioteca». El resultado
distingue archivos guardados, ya existentes y rechazados. Un fallo en un archivo
no impide importar los demás. Reintentar un lote no duplica lo ya confirmado.

Límites iniciales: 20 archivos por solicitud; 50 MiB por MP3; 200 MiB por solicitud
multipart completa, incluido su encabezado y delimitadores. La validación del
servidor no depende del tipo MIME ni del tamaño que declare el navegador.
Se cuenta el cuerpo real incluso sin Content-Length. No se procesan archivos
de un formulario que supere el límite total o el número máximo permitido.

El archivo original se copia a MEDIA_ROOT. Su nombre no se usa como ruta.
Primero se confirma el original con datos provisionales. P07 completa después
sus etiquetas y portada; si falla ese enriquecimiento el audio sigue guardado
y el resultado añade metadata_warnings para reintentar. Campos ausentes usan
el nombre del archivo y «Sin álbum». Ver [METADATOS.md](METADATOS.md).
No se envía audio a ningún proveedor de IA.

## API

`POST /api/v1/imports`: multipart con uno o varios campos `files` de tipo archivo.
La interfaz y `/docs` permiten seleccionar archivos. Respuesta HTTP 200 por lote
admitido con `results`, en el mismo orden de selección:

```json
{
  "results": [
    {"index": 0, "file_name": "cancion.mp3", "status": "imported", "track_id": "11111111-1111-4111-8111-111111111111"},
    {"index": 1, "file_name": "copia.mp3", "status": "duplicate", "track_id": "11111111-1111-4111-8111-111111111111"},
    {"index": 2, "file_name": "texto.mp3", "status": "rejected", "error": {"code": "invalid_audio", "message": "El archivo no contiene audio MP3 válido o está incompleto."}}
  ]
}
```

HTTP 413 indica cuerpo excesivo y 422 formulario inválido/demasiados archivos;
415 indica que no se usó multipart. Una respuesta perdida puede ocurrir después
de un guardado exitoso: reintentar y comprobar duplicados. La interfaz espera
como máximo dos minutos; un timeout del cliente no implica rollback del servidor.

Errores por archivo: `unsupported_format`, `invalid_audio`, `file_too_large`,
`storage_unavailable` y `database_unavailable`. Se conservan nombres sanitizados
para presentación; no se exponen rutas de disco ni detalles del controlador SQL.

## Catálogo y almacenamiento incorporados como dependencia P05

La migración `0002_catalog` crea recursos, artistas, álbumes, créditos ordenados,
pistas, playlists y sus posiciones. La base aplica claves foráneas RESTRICT,
hash de pista único, relación pista/audio única y posiciones únicas por lista.
Se siembra un único álbum de sistema «Sin álbum». No hay muros ni tablas de IA.

Los modelos usan SQLAlchemy Core y metadata compartida con Alembic. La migración
está congelada en su archivo; no importa modelos futuros para crear tablas.
`alembic check` permite revisar coherencia entre esquema y modelos.

Claves de almacenamiento: `audio/<uuid>.mp3` e `images/<uuid>.<tipo>`. Los tipos
visuales quedan preparados en el esquema; su importación/validación corresponde
a P11/P14. Las rutas arbitrarias, secuencias de escape y symlinks fuera de la raíz
se rechazan. No hay un endpoint para leer cualquier ruta del sistema.

## Consistencia, duplicados y fallos

1. Recibir formulario limitado y crear staging dentro de MEDIA_ROOT.
2. Copiar por bloques, limitar tamaño, calcular SHA-256 y sincronizar el archivo.
3. Validar estructura MP3 y duración positiva finita.
4. Tomar bloqueo transaccional por hash y buscar pista existente.
5. Si existe, devolver su ID; si se perdió el medio, reponerlo desde los mismos bytes.
6. Si es nueva, insertar recurso, publicar archivo sin sobrescribir otro destino
   e insertar pista; confirmar transacción.
7. Ante fallo de registro, comprobar si la confirmación ocurrió antes de retirar
   el medio recién creado. Si la BD no permite resolver la duda, conservar el
   archivo para revisión; no borrar algo que podría estar referenciado.

El hash compara bytes completos del original. Dos versiones con distinta
codificación o etiquetas pueden representar la misma canción y seguir siendo
archivos distintos. No se hace reconocimiento acústico en P06.

Un cierre abrupto puede dejar temporales o archivos no referenciados, porque BD
y filesystem no comparten transacción. Con las importaciones detenidas:

```bash
docker compose exec backend python -m app.media_audit
```

El informe lista assets sin archivo, archivos sin referencia y staging. Es de
solo lectura y no elimina nada. Antes de una limpieza manual, hacer respaldo,
comprobar que no haya trabajos activos y revisar cada referencia. No se incluye
limpieza automática ni borrado de pistas en este paso.

## Comprobaciones y límites

```bash
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error
docker compose exec backend python -m alembic check
docker compose exec frontend npm run build
```

Las pruebas usan bases aleatorias y carpetas temporales. La colección sintética
de `pruebas/coleccion` se monta en `/app/fixtures` como solo lectura para pruebas
y demostración; no es el almacenamiento de originales importados.

Validar cabeceras, cuadros y duración con Mutagen no equivale a decodificar toda
la grabación. La compatibilidad de escucha se comprobará en P09/P10. CA-01 está
parcialmente cubierto: se importa y conserva, pero todavía no se reproduce.
P07 ya permite etiquetas y portadas estáticas; GIF decorativos, búsquedas y
gestión visual de playlists siguen pendientes de sus pasos.

Ver [VALIDACION_P06.md](VALIDACION_P06.md) para evidencia de esta entrega.
Fuente del lector de MP3: [documentación oficial de Mutagen](https://mutagen.readthedocs.io/en/latest/api/mp3.html).
