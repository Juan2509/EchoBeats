# P24 — Favoritos persistentes

Corrección posterior P26: la regresión incluía helpers de búsqueda/indexación que
podían escribir medios en la raíz personal al recrear Settings. El aislamiento de
BD sí se conserva, pero no afirmar medios sin cambios de esas ejecuciones. Ver
HALLAZGO_AISLAMIENTO_P26.md; corregido el fixture global y conservados 506 MP3 sin fila.

14 de noviembre de 2026. **Implementación y verificación automatizada listas;
recorrido visual pendiente.** Sin llamadas a OpenAI ni cambios del índice personal.

## Entrega

- Corazones compartidos entre biblioteca/álbum, playlists, reproductor y Explorar.
- Biblioteca → Favoritos, búsqueda literal, paginación y cola solo de favoritos.
- Estado explícito e idempotente, sin éxito optimista ni reintentos de escritura.
  Un fallo de respuesta obliga a consultar antes de otra modificación.
- Tabla favorite con una fila por pista, fecha y FK protegida; cambios serializados
  mediante bloqueo de la pista. No cambia revisión de metadatos, fichas ni vectores.
- Usuario local único. Sin historial de escucha, cuentas ni cambios de ranking.

Uso, contrato y concurrencia en [FAVORITOS.md](FAVORITOS.md).

## Evidencias

- **222 pruebas backend aprobadas** con avisos como errores, PostgreSQL/pgvector
  reales en bases aisladas. Nueve casos nuevos de favoritos: idempotencia, consulta
  y retirada al reabrir aplicación, búsqueda/páginas, audio servido, texto literal,
  entradas estrictas, 404, origen ajeno, límites y downgrade protegido.
  El caso de persistencia se reforzó y volvió a pasar (9/9): procesos Python/API
  nuevos confirmaron tanto true como false desde PostgreSQL de la base aislada.
  No se confunde reabrir un componente con reiniciar un proceso.
- **57 pruebas frontend aprobadas**. Seis casos nuevos cubren estado compartido,
  bloqueo durante guardado, incertidumbre sin reintentos, respuestas antiguas,
  invalidación al enfocar, consulta posterior y cola filtrada solo de favoritos.
  Son pruebas de controlador/gateway, no acreditan interacción visual ni escucha.
- TypeScript y build de producción aprobados tras colocar los controles finales.
- Docker estaba en `%LOCALAPPDATA%/Programs/DockerDesktop/resources/bin/docker.exe`,
  fuera del PATH de esta sesión; no se instaló ni cambió configuración del equipo.

## Operación local

Respaldo privado previo: `backups/echobeats_pre_p24_b4bb939c.dump`, con manifiesto
JSON/SHA-256 y listado pg_restore comprobado. Revisión previa 0008 confirmada;
AI_ENABLED=false confirmado sin exponer claves. El respaldo no incluye medios,
que se conservaron junto con el volumen y los respaldos anteriores.

Aplicada `0009_favorites` después del respaldo y la regresión. Backend reiniciado
y healthy; ready, rutas OpenAPI, GET favorites por proxy y HTML de Biblioteca
comprobados. Cero favoritos iniciales; no se marcaron pistas personales para probar.
No se hicieron downgrades ni pruebas de escritura en la principal.

## Pendientes y continuidad

Recorrido visual/teclado 360/768/1280 y coherencia visible entre controles pendientes.
El runtime node_repl requerido por la habilidad Computer Use no está disponible en
esta sesión; no se acredita un recorrido de navegador a partir de HTTP o tests de
controlador. Por ello P24 conserva su casilla de cierre abierta.
La habilidad [Computer Use](C:/Users/lickn/.codex/plugins/cache/openai-bundled/computer-use/26.1111.21308/skills/computer-use/SKILL.md)
indica en su guía: «Use node_repl JavaScript for all Computer Use actions.»
La limitación es de herramienta disponible, no una solicitud de aprobación.

Conservar revisiones visuales/audio previas y el cierre real/evaluación P20–P23.
No cambiar ranking ni afirmar aprendizaje por guardar favoritos: siguiente P25
cuando el usuario lo solicite. No se creó commit.
