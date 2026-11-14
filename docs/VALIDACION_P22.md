# P22 — Recuperación semántica, textual e híbrida

13 de noviembre de 2026. **API implementada; cierre real y calibración pendientes.**
Se conserva la petición del usuario de dejar pendiente la prueba real por créditos.
No se consultó OpenAI ni se ejecutaron las reservadas para ajustar resultados.

## Entregables

- POST /explore/search: semantic/lexical/hybrid, límites y filtros de álbum/playlist.
- GET /tracks/{id}/similar: vector de referencia almacenado, exclusión de sí misma,
  sin embedding de consulta nuevo. 409 si la referencia no tiene índice vigente.
- SQL parametrizado, coseno exacto, FTS simple y RRF(60); sin ANN ni LLM generador.
- Elegibilidad por ficha/versión/hash/receta/modelo y metadatos derivados actuales;
  nueva instantánea después de red, sin mantener conexión abierta durante proveedor.
- Estados vacíos diferenciados y errores seguros; no llamar al proveedor si no
  hay biblioteca/candidatos indexados. Resultados con evidencias registradas y
  aviso de candidatos, sin presentar distancia como confianza.
- Evaluador de informes P17 sin red, que exige todas las consultas de partición,
  conserva errores/negativos y no certifica origen de vectores ni API real.

Uso/contrato/fórmulas en [RECUPERACION_SEMANTICA.md](RECUPERACION_SEMANTICA.md).
La interfaz Explorar y generación de explicaciones corresponden a P23.

## Verificación automatizada

- Regresión backend: **197 pruebas aprobadas** con PostgreSQL/pgvector reales en
  bases aisladas y proveedores simulados. Ninguna consumió saldo.
- Nuevos casos: **18 de recuperación** y **4 de métricas**, 22 aprobados.
  Cubren estados vacíos sin consumo, coseno ordenado y límite, FTS y fusión híbrida,
  filtros/playlist/álbum, referencia excluida y sin API, referencia obsoleta, ficha
  modificada durante espera, modelo/dimensión incompatibles, entrada inválida,
  umbral opcional, texto con sintaxis SQL como dato, cuota sin falso éxito,
  modo textual con IA desactivada y metadatos derivados obsoletos excluidos.
- Se comprueba coherencia ficha/versión/evidencia y acceso al audio. El proveedor
  simulado no se presenta como embedding real ni sus rankings como calidad musical.
- Métricas: ideal nDCG/Hit/precisión, error contado como cero, ranking parcial,
  candidatos que no equivalen a abstención y rechazo de consultas omitidas,
  duplicados/referencia excluida. real_api_verified=false incluso en informe ideal.
- `npm.cmd test`: **45 pruebas aprobadas**. `npm.cmd run build`: TypeScript/Vite
  aprobados. El cambio frontend solo actualiza el texto de estado de Configuración;
  no se implementó todavía el formulario/resultados de Explorar.
- Ayuda de `python -m app.evaluate_retrieval` verificada sin red/consumo.
- `git diff --check`: sin errores.

El primer ensayo de ranking textual detectó que PostgreSQL exige JSONPATH explícito
para la ruta de valores de atributos; se añadió el cast y se repitieron las pruebas.

## Verificación local

P22 no requiere migración ni dependencias adicionales. Se reinició backend después
de terminar pruebas y se esperó a healthy; no se modificaron volumen/medios/.env
ni se crearon trabajos o vectores en la biblioteca personal.

GET /ready respondió BD/pgvector/migraciones ok. OpenAPI publicó las rutas nuevas.
POST local de modo lexical y K=3 respondió no_indexed_tracks con cero resultados,
sin llamar al proveedor. Esta comprobación es de disponibilidad y estados, no
de recuperación musical real.

## Pendientes de cierre

Conservar P20/P21 pendientes hasta resolver créditos y reanudar de forma explícita
la prueba real. P22 requiere consulta compatible con vectores reales persistidos,
evaluación de desarrollo P17, selección/congelación de umbral/configuración y
ejecución reservada sin ajustar. No se cambió consultas.json ni se inventaron
resultados favorables. No hay un umbral musical elegido por los tests sintéticos.

Con corte sin definir, vecinos son candidatos, no evidencia automática de pertinencia.
Los negativos de P17 aún requieren validación/abstención real; CA-10/CA-11 no se
declaran superados. La generación/claridad factual/citas se evaluarán en P23.
Mantener revisiones visuales/audio anteriores; esta etapa no las cierra y la nueva
interfaz de exploración todavía no se ha implementado. Próxima implementación P23.
