# Colección musical controlada P17

Actualización P19: `fichas.json` contiene cinco entradas API verificables por el
generador, sin anotaciones emocionales provisionales. Preparación/carga por hash
y conservación de fichas existentes en [FICHAS_MUSICALES.md](../../docs/FICHAS_MUSICALES.md).
Estas propuestas no cambian el conjunto de consultas ni acreditan embeddings.

Cinco fragmentos musicales originales, generados sin muestras ni grabaciones de
terceros. Son patrones de notas con timbres de síntesis; no se presentan como
grabaciones de piano, guitarra o artistas reales. Uso previsto: pruebas,
modificación y demostración dentro de EchoBeats. No se atribuyen licencias de
terceros ni derechos sobre música externa.

| ID | Archivo | Evidencia objetiva de construcción |
| --- | --- | --- |
| M01 | orbita_lenta.wav | 60 BPM, seno, arpegio sin tercera, sin percusión. |
| M02 | circuito_rapido.wav | 140 BPM, dos notas/pulso, tres armónicos y percusión sintetizada. |
| M03 | eco_menor.wav | 60 BPM, campanas sintetizadas, tríada menor, sin percusión. |
| M04 | campanas_al_sol.wav | 100 BPM, campanas sintetizadas, tríada mayor, sin percusión. |
| M05 | orbita_gemela.wav | Patrón de M01 una octava arriba, mismo pulso y timbre. |

Todos duran 12 s y usan WAV PCM de 16 bits, mono, 22050 Hz. `manifest.json`
registra archivo, hash, tamaño, secuencia MIDI, generador, autor/procedencia,
permiso de uso, texto descriptivo v1 y campos de construcción. `annotation`
separa energía, ambiente y emoción editoriales: son hipótesis pendientes de
escucha humana; no hechos acústicos ni etiquetas de un modelo.

`consultas.json` fija 18 consultas y 10 escenarios de fallo antes de implementar
prompts o recuperación. Criterios y ejecución en
[EVALUACION_BUSQUEDA.md](../../docs/EVALUACION_BUSQUEDA.md).

Desde la raíz, `node scripts/generar_coleccion_semantica.mjs` genera archivos sin
dependencias ni red; rechaza sustituir archivos existentes. `--overwrite` regenera
solo los cinco WAV y el manifiesto de esta carpeta. No ejecutarlo sobre una colección
con cambios no conservados. `--help` muestra uso. Los hashes fijan estos bytes; cambiar
el generador exige versionar corpus y expectativas antes de volver a medir.

Para P19/P21, importar estos WAV con el importador multiformato y vincular M01–M05
a los UUID reales por SHA-256, nunca por título solamente. Los WAV no contienen
etiquetas: asignar título/álbum del manifiesto con edición manual existente.
Las fichas y los embeddings aún no existen; el manifiesto es entrada de preparación,
no una importación ya ejecutada. T04 del corpus técnico sirve como control sin ficha.
T05 es duplicado, T06/T07 inválidos: no son candidatos musicales adicionales.

Esta colección pequeña permite probar contrastes conocidos y trazabilidad; no
demuestra calidad en géneros, instrumentos reales o diversidad cultural. Ampliarla
con música autorizada y anotaciones humanas antes de generalizar resultados.
