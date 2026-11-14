# P26 — Integración, reinicios y recuperación

14 de noviembre de 2026. **Recorridos automáticos y matriz implementados; cierre
global pendiente de navegador/escucha y API real.** Sin llamadas reales a OpenAI.

## Entregables

- [Matriz CA-01–CA-13](MATRIZ_ACEPTACION_P26.md): resultado, capa, evidencia y límite
  de cada caso. CA-13: no aplica, reconocimiento O01/RF-18 aplazado.
- [Protocolo repetible y recorrido manual](RECORRIDOS_P26.md), sin autorizar llamadas
  reales ni borrar datos por leerlo.
- tests/runtime_server.py: servidor efímero con puerto local, DB de nombre aislado
  validado, medios temporales y proveedor/worker desactivados. No es un servicio
  añadido a la instalación ni expone la principal.
- test_runtime_integration.py: flujo HTTP desde biblioteca vacía, lote mixto,
  duplicados, metadatos manuales, búsqueda, playlist con imagen/orden, dos muros,
  PNG/GIF/preview, conflictos, rangos y reinicios de procesos reales. Dos reinicios
  comprueban persistencia y reset aislado; no equivalen a escucha/gestos visuales.
- Tres variantes de fallo de proveedor simulado y recuperación explícita posterior,
  conservando catálogo, playlist, favoritos y bytes de audio utilizables.
- Flujo integrado de controladores frontend: muro bloqueado/edición/guardado,
  error de Explorar, favorito y controles de audio con doble. Sin acreditar audio real.

## Defecto encontrado y corregido

Al recrear Settings, algunos helpers de prueba heredaban MEDIA_ROOT personal pese
a usar una BD aislada. Se corrigió el aislamiento global de medios/clave/worker y
se añadió una regresión específica. Ver [hallazgo y alcance](HALLAZGO_AISLAMIENTO_P26.md).
Los 506 MP3 ya no registrados se conservan; no se consideran eliminables sin
revisar procedencia. No se oculta el hallazgo con limpieza de archivos.

El primer arranque del nuevo servidor de test falló por ruta de módulos; el harness
fija PYTHONPATH de backend y se verificó después. No requirió cambio de aplicación.

## Comprobaciones y límites

- Regresión final corregida: **237 pruebas backend**, cero fallos/errores/omitidas,
  con avisos tratados como errores. Cinco casos nuevos (reinicios HTTP, tres fallos
  y regresión del aislamiento de Settings).
- **61 pruebas frontend**, cero fallos/omitidas; un flujo integrado nuevo con doble.
- `data/validation/p26_backend.xml`, SHA-256
  `fab69915016a5363482064f712d0605f2e299994a79b170f39cb28ad1e6ef403`.
- `data/validation/p26_frontend.txt`, SHA-256
  `c9d2fb4f8614e181c909dd1f0fc39c7c12db252ccc2e371c68f223850ef1d6eb`.
- `data/validation/p26_media_check.json`: unchanged=true; 516 archivos y
  83.797.981 bytes antes/después; mismas rutas relativas y hashes. SHA-256 de la
  huella `7dfe1a55f1a3aa33b2e124d3fd30fcb5867520eae5697d69037da12c714efe6d`.
  Esto acredita conservación durante la última regresión corregida, no las anteriores.

Build/TypeScript de frontend aprobado. Pruebas con Python 3.12 y PostgreSQL/pgvector
de los contenedores/locks existentes; sin paquetes ni migraciones nuevos. Las pruebas
usan bases aleatorias y medios de pytest, no datos personales para simular fallos.
Informes locales ignorados por Git en data/validation; el resumen versionado es
esta documentación. Conservar .env, medios, volúmenes y respaldos.

Auditoría de solo lectura: BD/pgvector/migraciones ok, IA desactivada, diez assets
registrados verificados por SHA-256/tamaño, cero faltantes y cero staging. Los 506
MP3 no registrados totalizan 49.487.414 bytes y quedan como hallazgo de conservación.
No atribuir su origen exacto ni prometer que son copias seguras para borrar.

## Pendientes de aceptación

No se completó el recorrido visual/teclado 360/768/1280 ni escucha/seek decodificado
de MP3/WAV/FLAC/Ogg. La habilidad
[Computer Use](C:/Users/lickn/.codex/plugins/cache/openai-bundled/computer-use/26.1111.21308/skills/computer-use/SKILL.md)
remite a la guía que exige «Use node_repl JavaScript for all Computer Use actions»;
esa herramienta no está disponible en esta sesión. No se sustituye por capturas
inventadas o resultados de HTTP/controladores.

CA-10/CA-11 y RF-13/RF-14 siguen pendientes de éxito real/evaluación: el usuario
pidió no repetir OpenAI mientras no se resuelvan créditos y se reanude la prueba.
Mocks y pgvector con vectores técnicos no certifican API ni pertinencia musical.
No se usaron reservadas P17 para calibrar. Conservar pendientes P08/P15/P16/audio
y P20–P25. P26 queda abierto; siguiente bloque previsto P27 cuando se solicite,
sin que avanzar borre estos pendientes. No se creó commit.
