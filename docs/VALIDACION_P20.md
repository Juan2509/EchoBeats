# P20 — Proveedor, configuración y validación

13 de noviembre de 2026 (recibos en UTC del 14 de noviembre).
**Implementación lista; cierre pendiente por créditos API agotados.**

## Implementado

- Adaptador OpenAI REST para embeddings y generación JSON Schema estricta,
  validación de dimensiones/modelo/números/usage y de citas ID-versión-fragmento.
- Configuración privada con SecretStr, integración desactivada por defecto,
  modelo/configuración explícitos y sin claves en frontend o diagnósticos.
- Timeout total, tamaño máximo de respuesta, una operación simultánea por
  instancia y reintentos temporales acotados. No repetir resultados inciertos,
  cuota, falta de créditos o límites de gasto/uso.
- Estado de configuración GET /ai/status y panel de Configuración sin consumo.
- Comando voluntario de prueba real con texto sintético fijo y recibo privado.
- Sin dependencias nuevas: usa httpx bloqueado ya instalado. Sin migración,
  escritura de fichas, embeddings en BD ni análisis de audio.

Modelos, límites, datos enviados, fuentes oficiales y operación en
[INTEGRACION_IA.md](INTEGRACION_IA.md). La documentación se verificó con la habilidad
OpenAI Docs; no se eligieron modelos a partir de ejemplos antiguos del curso.

## Pruebas locales

La regresión final aprobó **167 pruebas backend**, incluidos **32 casos de IA**.
Todas las pruebas de IA usan MockTransport, claves falsas y ningún consumo del
proveedor. No se confunden con los dos intentos --live registrados más abajo.

Cobertura: vectores finitos/no booleanos/no nulos, dimensión/modelo incompatibles,
JSON inválido, rechazo e incompletitud, versiones/IDs/citas ajenos, 401/403/429/5xx,
cuota y códigos actuales de crédito/gasto/uso sin reintento, timeout de lectura y
total, concurrencia, entradas/respuestas excesivas, ausencia de clave/activación,
estado sin secretos y comando sin clave que no inventa recibo exitoso.
El esquema/citas no prueba por sí solo corrección semántica de una explicación.

Frontend: `npm.cmd test`, **45 pruebas aprobadas**; `npm.cmd run build`, TypeScript
y Vite aprobados. No hay prueba DOM nueva del panel de estado; no equivale a revisión
visual. `git diff --check` sin errores. Las pruebas no ejecutan app.ai_check --live.

## Prueba real ejecutada y límite externo

El usuario indicó que configuraría la clave en `.env`; se comprobó solo su
presencia, sin mostrarla. Se recreó backend para cargar el entorno privado.
La activación permanente sigue false; --live habilita únicamente su ejecución.

Se hicieron dos intentos manuales controlados, sin reintentos automáticos y con
la entrada fija descrita en INTEGRACION_IA.md. En ambos falló la primera solicitud
(embedding) con HTTP 429; no se envió la generación. Recibos privados:

- `data/ai_checks/p20_20261114T000526Z_76195372.json`: fallo 429 inicialmente
  clasificado como ai_rate_limit, sin llamadas validadas.
- `data/ai_checks/p20_20261114T000709Z_b3f4afe4.json`: tras actualizar clasificación
  de errores actuales, ai_quota / **credit_balance_exhausted**, cero llamadas validadas.

La segunda comprobación permitió identificar la causa concreta. Se detuvieron
las llamadas: no hay respuesta válida de embeddings ni generación ni evidencia
de consumo exitoso. No presentar el rechazo real de proveedor como integración
real satisfactoria, ni asumir que se facturó cero por carecer de respuesta válida.
No se enviaron canciones, fichas personales ni biblioteca; solo texto artificial.
Los recibos no contienen clave ni vector/respuesta completos y no se versionan.

OpenAI documenta ese código como créditos prepago agotados y distingue cuota de
límite temporal. Resolver disponibilidad de créditos en la cuenta API antes de
repetir la prueba; no automatizar cambios de facturación ni repetir el error en
bucle. [Referencia oficial](https://developers.openai.com/api/docs/guides/error-codes).

## Estado local y pendientes

GET /ready confirmó BD/pgvector/migraciones ok. GET /ai/status respondió
enabled=false, configured=true, available=false y verification=not_checked;
su consulta no hace llamadas externas ni asegura acceso/saldo. Biblioteca/audio
siguen independientes del proveedor. No se modificaron DB/medios ni .env desde
el código de integración; el usuario guardó su clave privadamente.

Computer Use volvió a informar `The browser access host is unavailable`, sin
navegadores conectados. Pendiente revisar el panel Configuración/IA con teclado
y tamaños de ventana; conservar pendientes visuales y de audio anteriores.

P20 permanece sin marcar cerrado: requiere repetir de forma controlada cuando
haya créditos y conservar una respuesta real válida de API, con dimensiones,
usage y generación validada. No consumir más ni marcarlo completado por las pruebas
simuladas. Próxima implementación prevista P21, dependiente del cierre real P20.
