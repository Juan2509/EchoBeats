# Protocolo de integración y recuperación — P26

## Ejecución automática reproducible

Usar los contenedores del proyecto y locks existentes, sin instalar paquetes.
Conservar .env privado, medios, respaldos y volumen. No borrar volúmenes ni ejecutar
downgrade sobre la principal. RUN_DB_TESTS=1 crea bases echobeats_test_<uuid> que
se migran y retiran al terminar; los medios funcionales usan tmp_path de pytest.

PowerShell, desde la raíz (ruta de Docker de este equipo):

```powershell
$p26Docker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
& $p26Docker compose exec -T backend python -c "from pathlib import Path; Path('/app/data/validation').mkdir(parents=True,exist_ok=True)"
& $p26Docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error --tb=short --junitxml=/app/data/validation/p26_backend.xml
Push-Location frontend
node --experimental-strip-types --test --test-reporter=spec --test-reporter-destination=../data/validation/p26_frontend.txt tests/*.test.ts
npm.cmd run build
Pop-Location
```

Si Docker está en PATH, también se puede usar docker compose. PostgreSQL requiere
permiso de crear bases aisladas, según BASE_DATOS.md; no cambiar permisos del equipo
por omisión. Para repetir solo el recorrido nuevo: pytest tests/test_runtime_integration.py.

El servidor de pruebas runtime_server.py rechaza cualquier nombre distinto de
echobeats_test_<32 hex>. Escucha en 127.0.0.1 y puerto efímero dentro del contenedor,
con worker e IA desactivados y clave vacía. Cada arranque es un proceso nuevo y
su propio almacenamiento temporal; los tres arranques del caso comparten solo la
misma BD/medios aislados para comprobar persistencia. El fixture conserva medios
entre esos reinicios y cierra exclusivamente sus procesos. No expone un navegador
de revisión ni representa la API de OpenAI.

## Recorrido visual y escucha pendientes

Precondición: una instalación de revisión con BD y medios dedicados, sin datos
personales, y herramientas de navegador disponibles. No usar pérdidas, corrupción,
downgrades ni escrituras de ensayo sobre la biblioteca principal. Los tests HTTP
anteriores son automáticos y efímeros; no dejan un servidor de revisión abierto.

Registrar navegador/versión, sistema, ancho, pista/hash autorizada, acción,
resultado esperado/observado, fecha y evidencia. No anotar claves ni rutas privadas.

1. En 360/768/1280, recorrer Inicio/Biblioteca/álbum/playlist/Explorar con Tab,
   Shift+Tab, Enter, Espacio y flechas. Verificar foco visible, ausencia de controles
   ocultos, nombres accesibles y vacío/carga/error. No declarar accesibilidad total.
2. Importar lote válido/incorrecto y MP3 sin etiquetas; confirmar provisionales,
   portada predeterminada y edición persistente. Reabrir tras reiniciar el backend.
3. Escuchar una pista completa o segmentos verificables: play/pausa, seek intermedio,
   cerca del final, volumen, anterior/siguiente y fin de lista. Abrir otro álbum y
   conservar el único audio activo. Recargar sin reproducción automática. Repetir
   con MP3, WAV PCM, FLAC, Ogg Vorbis/Opus según soporte real del navegador.
4. Crear/renombrar playlist, guardar orden y PNG/JPEG, alternar vinilo/tarjeta;
   rechazar imagen inválida conservando lo anterior. Reabrir y escuchar orden guardado.
5. En A, añadir PNG/GIF, mover/rotar/redimensionar y cambiar capas, también con
   teclado y objetos tapados. En B, otra composición. Esperar autoguardado, alternar
   A/B y reiniciar backend: comparar todos los campos, recursos y previews.
6. Bloquear e intentar arrastrar; objetos inmóviles con reproductor utilizable.
   Desbloquear, modificar durante guardado, provocar conflicto solo en revisión,
   conservar borrador y consultar estado antes de reintentar un resultado incierto.
   Restablecer A con confirmación y comprobar persistencia sin cambiar B ni audio.
7. Marcar/desmarcar favorito entre vistas y reiniciar. En Explorar revisar cada
   opción P25 y su comparación: ningún cambio automático por pulsar corazón,
   favoritos ajenos no aparecen y descubrir excluye guardados. Escuchar la cola
   que se muestra. La razón de orden no es una descripción musical.
8. Fallo de proveedor simulado exclusivamente en revisión: error/fallback explícito,
   sin reintentos ocultos ni explicaciones inventadas, biblioteca y audio utilizables.

## Flujo real de IA aplazado

No ejecutarlo hasta resolver créditos y reanudarlo explícitamente con el usuario.
Entonces conservar recibos sin secretos, espacio/modelo/receta/dimensiones y fuentes,
indexar corpus autorizado y evaluar consultas P17 según partición congelada.
CA-10/CA-11 requieren proveedor/vector reales y escucha; el evaluador local y los
tests artificiales no los acreditan. CA-13 no aplica mientras O01 esté aplazado.
