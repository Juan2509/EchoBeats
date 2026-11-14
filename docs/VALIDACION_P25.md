# P25 — Personalización mediante favoritos

14 de noviembre de 2026. **Regla e interfaz implementadas; evaluación musical real
y recorrido visual pendientes.** Sin llamadas reales a OpenAI, por acuerdo previo.

## Entrega y decisión

Preferencias off/favorites/discovery en Explorar y API de consulta/similares.
Regla versionada adjacent_pairs_v1: intercambio de pares contiguos dentro del top K
con desplazamiento máximo de uno. Descubrir excluye favoritos antes del límite.
Tabla de comparación sin segunda consulta y razón de orden explícita por pista.
Se conservan consulta, filtros, elegibilidad P22, citas P23 y reproductor único.
No hay aprendizaje automático, gustos derivados del muro ni historial de escucha.
Especificación, ejemplo y límites en [PREFERENCIAS.md](PREFERENCIAS.md).

## Evidencia técnica

- **232 pruebas backend aprobadas** en la regresión completa con avisos tratados
  como errores. La primera ejecución detectó un test que asumía orden vectorial
  usando modo híbrido con empates textuales; se fijó modo semántico para aislar esa
  comprobación y la regresión final pasó. No se alteró RRF para satisfacer el caso.

- Diez casos nuevos de backend, SQL/pgvector reales en bases aisladas y proveedores
  simulados: comparación off/favorites en lexical/semantic/hybrid; mismos candidatos
  y scores; desplazamiento acotado y no acumulativo; usuario sin favoritos;
  favorita ajena y fuera del top K excluida; descubrimiento antes del límite;
  filtros, similares sin referencia repetida, ausencia de candidatos sin consumo;
  cambios de favoritos durante embedding/generación y revalidación de comparación;
  contexto sin flags de gustos y entradas inválidas.
- 34 casos P22/P23 aprobados después de integrar la regla.
- **60 pruebas frontend aprobadas**, incluidas tres nuevas: comparación con la
  misma respuesta, rechazo de posiciones/IDs/señales incoherentes y envío explícito
  de opciones para consulta/referencia, desactivadas por defecto.
- TypeScript y build de producción aprobados. La cola continúa usando el orden
  exacto devuelto; la comparación no inicia audio ni pide otra búsqueda.
- Backend reiniciado y healthy, ready correcto y revisión 0009_favorites conservada.
  Comprobación HTTP por proxy de off/favorites/discovery en modo lexical, explain=false:
  las tres devolvieron no_indexed_tracks, cero resultados y la política correcta.
  IA desactivada confirmada sin mostrar claves; esta prueba vacía no acredita
  personalización musical con índice real ni reemplaza las pruebas aisladas.

No se tocaron consultas, grados o particiones reservadas P17 para escoger la regla.
Los vectores artificiales comprueban orden/concurrencia, no pertinencia musical ni
calibración. La tabla es un contrafactual del mismo conjunto, no una nueva búsqueda.

## Conservación y pendientes

Sin migraciones ni dependencias nuevas; se mantiene 0009_favorites. Sin escrituras
de prueba en la principal ni cambios a .env, favoritos personales, medios, volumen
o vectores. Mantener respaldos previos y la petición de no repetir llamadas reales.

P25 conserva casilla abierta para revisión visual/teclado 360/768/1280 y valoración
con colección real cuando se resuelva/reanude proveedor. La automatización visual
requiere node_repl, no disponible en esta sesión; no se acredita navegador a partir
de tests de controlador/HTTP. Ver la instrucción y habilidad en VALIDACION_P24.md.
No declarar mejora de nDCG, Recall, gustos o pertinencia por estos tests.

RF-17 tiene persistencia y efecto técnico explicable cubiertos por P24/P25; la
calidad musical y recorrido completo siguen pendientes. P20–P23 y pendientes
visuales/audio previos conservan su estado. Siguiente bloque previsto P26,
integración y recuperación, cuando lo solicite el usuario. No se creó commit.
