# Audio multiformato — O06

12 de noviembre de 2026. Ampliación solicitada expresamente por el usuario
después de P10; no depende de implementar playlists ni funciones de IA.

## Formatos habilitados

| Extensión | Contenido admitido | MIME servido | Etiquetas y portada |
| --- | --- | --- | --- |
| .mp3 | MPEG Layer III | audio/mpeg | ID3v1/v2 y APIC; se conserva el comportamiento previo. |
| .wav | WAV RIFF con PCM entero de 8/16/24/32 bits | audio/wav | ID3 incrustado y APIC. RIFF INFO no se interpreta; se pueden completar datos manualmente. |
| .flac | FLAC nativo | audio/flac | Vorbis Comments y bloques Picture. |
| .ogg | Ogg Vorbis u Ogg Opus | audio/ogg | Vorbis Comments y METADATA_BLOCK_PICTURE. |
| .opus | Ogg Opus | audio/ogg | Vorbis Comments y METADATA_BLOCK_PICTURE. |

La extensión debe corresponder al contenido real. No se confía en el MIME
de la subida. Vorbis con extensión .opus, MP3 renombrado a .wav y contenedores
no admitidos se rechazan por archivo, sin impedir otros válidos del lote.
Opus bajo .ogg usa extensión interna canónica .opus, sin conversión de bytes.
Dos nombres/extensiones aceptados con los mismos bytes siguen siendo un duplicado.

M4A/AAC, ALAC, AIFF, WMA, WAV comprimido o de punto flotante y Ogg con otros
códecs no se anuncian como soportados. La lista se amplía con validaciones
concretas, no aceptando cualquier archivo que empiece por audio/.

## Uso y reproducción

En Biblioteca → Añade tu música, seleccionar uno o varios archivos admitidos.
Se mantienen 50 MiB por archivo, 20 archivos y 200 MiB por solicitud completa.
WAV sin compresión puede alcanzar ese límite antes que MP3/FLAC/Ogg.

El reproductor utiliza el audio original y la capacidad del navegador. Comprueba
canPlayType con audio_mime_type e informa si el navegador no anuncia soporte.
Un resultado positivo no garantiza todos los perfiles/códecs posibles; los fallos
de decodificación también muestran un aviso. No hay transcodificación ni subida
de audio a servicios externos. [Referencia de códecs web](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Audio_codecs).

## Implementación y conservación

- Mutagen, ya instalado, identifica contenedores, duración y etiquetas.
  Validación básica de estructura/duración; WAV además verifica la cantidad real
  de muestras PCM. No se incorpora un decodificador completo al importador.
- Medios gestionados con UUID y extensión canónica; SHA-256 sobre bytes originales.
  Se conserva el formato y la política de deduplicación/compensación existente.
- GET/HEAD y rangos usan el MIME del archivo validado. Las fichas/listados añaden
  audio_mime_type; el cliente no puede editarlo por PATCH.
- Etiquetas y portadas usan los campos existentes y mantienen la procedencia;
  releer o reimportar no sobrescribe correcciones manuales ni modifica originales.
- Migración 0004_audio_formats amplía únicamente la restricción de storage_key.
  No reescribe pistas, archivos ni IDs. Modelo y auditoría admiten las nuevas claves.
- El downgrade se niega si existen medios con las extensiones nuevas: nunca borra
  datos para forzar la vuelta a MP3. Downgrades de prueba solo en bases aisladas.
- Sin dependencias nuevas del programa ni cambios en los locks. FFmpeg se usó
  en un contenedor temporal exclusivamente para generar/decodificar fixtures.

Lectores y estructuras consultados en el código instalado y la
[documentación oficial de Mutagen](https://mutagen.readthedocs.io/en/latest/api/index.html).

## Evidencias

**72 pruebas backend superadas** en bases PostgreSQL aleatorias aisladas, con
avisos como errores. Incluyen las 57 anteriores y quince casos/variantes nuevos:
importación de los cuatro formatos, etiquetas/portada/duración, MIME, bytes
completos, HEAD/rangos, relectura manual protegida, duplicados, extensión falsa,
lotes mixtos, WAV truncado/float rechazado, FLAC sin etiquetas, portada Ogg inválida
y downgrade protegido sin pérdida del audio.
WAV PCM de 8, 24 y 32 bits se comprueba con señales generadas en memoria;
la fixture con portada/etiquetas cubre PCM de 16 bits.

**14 pruebas frontend superadas**, en Windows y Docker. La nueva prueba simula
un navegador sin soporte de FLAC y comprueba que no se solicite audio y que se
pueda elegir después una pista compatible. Son dobles de audio; no equivalen
a una prueba de decodificación del navegador. TypeScript y build correctos en
ambos entornos; pip check y alembic check correctos, sin diferencias de esquema.

Fixtures originales en `pruebas/coleccion/multiformato/`, con manifiesto de hashes:
señal de 440 Hz, estéreo, 2,5 segundos y portada propia. Generador en
`scripts/generar_audio_multiformato.py`; FFmpeg 7.1.5 decodificó los cuatro archivos
sin errores. Regenerar requiere FFmpeg, Mutagen y Pillow; ejecutar las pruebas
o la aplicación no requiere FFmpeg. La regeneración puede cambiar bytes de
codificación/seriales de Ogg; el manifiesto se genera junto a los archivos.

Por el proxy real del frontend se importaron cuatro pistas sintéticas como
«Prueba WAV», «Prueba FLAC», «Prueba Vorbis» y «Prueba Opus», en el álbum
«Colección multiformato». Las cuatro respondieron 206 para bytes=1000-1999,
con longitud 1000 y sus MIME/tamaños correctos. Se conservan como demostración;
no se modificaron canciones existentes del usuario.
Después de recrear backend/frontend se conservaron los IDs, MIME y rangos de
las cuatro pistas nuevas y del MP3 previo. Auditoría de solo lectura sin medios
faltantes, huérfanos o staging. Servicios detenidos conservando volumen, .env y audios.

La comprobación en Brave no se completó: la herramienta se detuvo al no poder
identificar la URL de Windows con confianza suficiente para aplicar su política.
No se afirma escucha/seek reales en navegador para estos formatos. Siguen
pendientes ese recorrido y los cierres manuales anteriores de P08/P09/P10.

Para probarlos: iniciar con `docker compose up -d --build --wait`, abrir Biblioteca,
buscar «Prueba», reproducir cada señal y mover la barra. También se pueden importar
archivos propios compatibles. Sin commit automático; O06 queda implementado con
validación de navegador pendiente. Siguiente implementación principal: P11.
