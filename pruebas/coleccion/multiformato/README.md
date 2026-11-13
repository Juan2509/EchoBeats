# Señales originales de prueba multiformato

Señal sinusoidal propia de 440 Hz, estéreo, 2,5 segundos; PCM de 16 bits en WAV,
FLAC, Ogg Vorbis y Ogg Opus. No contiene grabaciones musicales de terceros.
Cada archivo incorpora título, artista, álbum, número y portada original de color.

`manifest.json` conserva origen, versión del codificador, duración, tamaños y
SHA-256. Regenerar con `scripts/generar_audio_multiformato.py` requiere FFmpeg,
Mutagen y Pillow; no son instalaciones que deba ejecutar el importador.
FFmpeg también comprueba la decodificación de los resultados al generarlos.
Los bytes pueden variar al regenerar con otra versión o serial de Ogg.

La suite usa estas copias versionadas y no necesita FFmpeg para ejecutarse.
No demuestran pertinencia musical ni sustituyen la colección autorizada de P17.
