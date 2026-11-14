# Hallazgo P26 — Medios temporales al recrear Settings

14 de noviembre de 2026. **Defecto del entorno de pruebas corregido; archivos
preexistentes conservados.** No se cambió el comportamiento de la aplicación.

## Causa y alcance

El cliente de test_metadata creaba Settings con media_root temporal, pero algunos
helpers de indexación/búsqueda sustituían app.state.settings por otra instancia de
Settings. `_env_file=None` no desactiva variables de entorno: esa nueva instancia
heredaba MEDIA_ROOT=/app/data/media del contenedor. Las importaciones posteriores
podían escribir allí mientras su base de datos seguía siendo echobeats_test_<uuid>.
Al retirar la base de prueba, los archivos quedaban sin filas en la principal.

Esto afecta la confianza en las afirmaciones de «medios personales sin cambios»
de ejecuciones previas P21–P25 que usaron estos helpers. No implica que se hayan
insertado vectores ficticios en la principal ni que se consumiera OpenAI real.
El origen exacto de cada archivo no registrado no quedó registrado históricamente;
no se atribuye automáticamente todo el conjunto a una sola ejecución o causa.

## Observación de solo lectura

- 10 medios registrados, 34.310.567 bytes; los diez coinciden en tamaño/SHA-256.
- Ningún medio registrado faltante ni staging pendiente.
- 506 MP3 sin fila actual, 49.487.414 bytes, conservados íntegramente.
- Total de archivos bajo la raíz: 516; 83.797.981 bytes.

No se consideran basura ni se borran por el hecho de no tener fila. No se
reimportan automáticamente ni se les inventa procedencia. Revisar inventario,
respaldos y decisión de conservación aparte, dentro de P27 o por indicación expresa.

## Corrección y regresión

Fixture autouse en backend/tests/conftest.py fija MEDIA_ROOT dentro de tmp_path para
cualquier nueva instancia de Settings durante cada caso, aunque cambie un helper.
También vacía OPENAI_API_KEY y desactiva IA/worker por omisión. Los tests de proveedor
con fake explícito conservan su configuración intencional. test_metadata comparte
esa raíz temporal; el nuevo servidor HTTP usa exclusivamente BD/medios aislados.

Un caso nuevo comprueba que Settings recreado, config de índice y enable de búsqueda
conservan la raíz temporal y que la importación se escribe allí. El informe final y
la comparación de huellas antes/después están en VALIDACION_P26.md. La huella de
control incluye rutas relativas gestionadas, tamaño y hash, guardados solo en
data/validation, sin publicar contenido ni claves. No se eliminaron archivos para
hacer pasar la comprobación.
