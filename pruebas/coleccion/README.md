# Colección técnica de EchoBeats

Generada para P01. Consultar [alcance del MVP](../../docs/ALCANCE_MVP.md).

## Procedencia y uso

Los audios son señales sinusoidales originales generadas matemáticamente para
las pruebas de EchoBeats. No proceden de canciones, voces, samples o grabaciones
de terceros. Se preparan para uso, modificación y demostración dentro del proyecto.
El nombre de los álbumes y el artista son etiquetas ficticias de prueba.
No se atribuye ningún permiso sobre música externa ni se ha descargado un catálogo.

[manifiesto.json](manifiesto.json) conserva tamaño y SHA-256 de cada archivo,
parámetros de las señales y metadatos esperados. Las descripciones reflejan el
generador, no una evaluación de IA ni una clasificación emocional.

## Contenido y recorrido

| ID | Archivo | Características y uso |
| --- | --- | --- |
| T01 | `tono_grave.mp3` | 12 segundos, tono de 220 Hz, álbum técnico A, con etiquetas. Importación y reproducción. |
| T02 | `pulsos_medios.mp3` | 12 segundos, tono de 440 Hz con amplitud pulsante, álbum técnico A. Cambiar pista y avanzar. |
| T03 | `tono_agudo.mp3` | 12 segundos, tono de 880 Hz, álbum técnico B. Aislar muros A/B. |
| T04 | `sin_etiquetas.mp3` | 12 segundos, tono de 330 Hz con amplitud pulsante, sin título/artista/álbum/portada. Editar metadatos y asignar álbum manualmente. |
| T05 | `tono_grave_duplicado.mp3` | Copia byte a byte de T01. Verificar política de duplicados. |
| T06 | `invalido.mp3` | Texto con extensión MP3. Debe rechazarse. |
| T07 | `vacio.mp3` | Archivo de cero bytes. Debe rechazarse. |

Ninguno incluye portada. Todos los MP3 válidos son mono, 44,1 kHz, 64 kbps.
La duración codificada puede incluir un pequeño relleno respecto a los 12 segundos
de señal. No comprobar igualdad exacta de duración flotante.

Importar primero T01–T03, luego T04 y corregirlo manualmente. Repetir con T05 y
probar importación mixta de válidos, T06 y T07. Reiniciar para verificar persistencia.
Los recursos visuales de las paredes se prepararán durante su implementación.

## Regeneración

Desde la raíz del proyecto:

```bash
python3 scripts/generar_coleccion_prueba.py
```

Requiere Python y `libmp3lame` disponible en el sistema. No instala paquetes,
accede a internet ni consume APIs. Sobrescribe los siete archivos indicados y
el manifiesto dentro de esta carpeta. La versión del codificador puede cambiar
los bytes resultantes; el manifiesto se actualiza con los nuevos hashes.
Los MP3 ya generados permiten usar la colección sin ejecutar el script.

## Límites de validación

P17 añadió una [colección musical sintética independiente](../semantica/README.md)
con notas/timbres y expectativas controladas. Los tonos de esta carpeta conservan
su uso técnico; no se les asignan géneros ni emociones. Ver
[protocolo P17](../../docs/EVALUACION_BUSQUEDA.md) para evidencia y límites actuales.

Esta colección permite comprobar mecánica de importación, etiquetas, reproducción,
duplicados y archivos inválidos. No demuestra la pertinencia de recomendaciones
por nostalgia, lluvia, género o instrumentos musicales.

En P17 se preparará una colección musical autorizada para evaluar recuperación.
Cada incorporación deberá registrar archivo/hash, autor, origen, permiso o licencia,
álbum, descripción verificada y consultas pertinentes esperadas. No marcar esa
colección como disponible hasta contar con los archivos y su procedencia.

## Comprobación al preparar P01

El 12 de noviembre de 2026 se generaron los siete archivos y se verificaron
tamaños y SHA-256 contra el manifiesto. Los cuatro MP3 originales se decodificaron
con el decodificador de `libmp3lame`: aproximadamente 12,07 segundos por archivo
con señal distinta de silencio. Se comprobaron las etiquetas ID3v1 de T01–T03,
su ausencia en T04 y la igualdad byte a byte entre T01 y T05.
La herramienta `file` reconoció los MP3 válidos, el texto T06 y el archivo vacío T07.
Estas comprobaciones no equivalen a escuchar en un navegador ni a ejecutar la
importación de EchoBeats, que aún no está implementada.
