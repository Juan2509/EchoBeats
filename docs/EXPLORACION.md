# Explorar, fuentes y reproducción — P23

P25 añade selector de preferencias off/favorites/discovery. El ajuste intercambia
pares de candidatos, sin variar scores ni fuentes; descubrir excluye favoritos
antes del límite. Razones de orden separadas de las citas musicales y comparación
local sin otra petición. No se reordena al cambiar un corazón. Ver PREFERENCIAS.md.

## Recorrido disponible

En «Explorar», escribir una consulta, escoger modo/filtros y pulsar «Buscar en mi
música». La vista arranca en **Textual** y sin selección de citas con IA. Abrirla,
cambiar filtros o abrir una referencia no inicia búsqueda, reproducción ni llamadas
de proveedor. Solo carga opciones y, cuando procede, el nombre de referencia local.

Textual usa el índice vigente sin API; semántica/híbrida envían la consulta de
texto a OpenAI. «Seleccionar citas con IA» es una opción aparte, desmarcada por
defecto: puede enviar extractos de hasta cinco fichas y consumir créditos. No envía
audio. IA desactivada o sin cuota no impide acceder a biblioteca/reproductor.
La prueba real sigue pendiente por instrucción del usuario; P23 no la reanuda.

Los filtros admiten álbum y playlist conjuntamente, con 1–20 resultados. Los
selectores muestran hasta las primeras 100 colecciones e informan si hay más;
la API permite filtrar por cualquier UUID válido del catálogo. La búsqueda
ordinaria de Biblioteca continúa disponible para pistas sin ficha/vector.

«Buscar similares» desde una pista abre /explorar?similar=<UUID>, carga solo el
nombre y espera el botón del usuario. La recuperación usa su vector vigente,
excluye la referencia y no necesita embedding nuevo. Las citas opcionales siguen
siendo una operación de generación explícita. Referencia sin índice o cambiada
durante la espera se comunica como error, no como ausencia de canciones parecidas.

## Resultados y estados

Se distinguen sin biblioteca, sin índice vigente, sin candidatos y fallo de red,
proveedor o validación. La consulta permanece en el formulario para corregirla o
repetirla conscientemente. No se reintenta ni cambia de modo automáticamente.
No se muestran resultados antiguos bajo una consulta fallida. Una respuesta tardía
de otra consulta/pantalla se ignora y las peticiones se abortan al salir.

Cancelar detiene la espera del cliente; una solicitud ya enviada puede completarse
y consumir créditos. El cliente tiene un límite de espera de 55 segundos para el
recorrido de recuperación y selección de citas; el adaptador conserva sus límites
por operación de P20. No se supone que abortar garantiza que el proveedor no facture.

Sin umbral calibrado los resultados siguen siendo **candidatos**, no coincidencias
garantizadas. No se muestran distancias o RRF como porcentaje de confianza. Los
scores/modelo siguen en la API para evaluación, sin convertirlos en una afirmación
de calidad. Las métricas reales P17/CA-10/CA-11 continúan pendientes.

## Explicaciones y procedencia

Cada tarjeta muestra pista/álbum, citas literales, versión de ficha y si proceden
de descripción registrada o de selección por IA. «Ver ficha, atributos y
procedencia» conserva la instantánea recuperada y distingue datos registrados de
interpretaciones subjetivas. Verificada significa fuente declarada por el editor,
no veracidad certificada automáticamente. Se puede abrir el editor actual de ficha;
su versión puede ser posterior a la instantánea de resultados.

La política de P23 es **literal_quotes_only**:

- Siempre hay alternativa registrada, construida con texto existente de la ficha.
- Si el usuario solicita IA y hay candidatos, se prepara contexto de hasta cinco
  fichas, con ID, versión y prefijo de texto (hasta 1600 bytes UTF-8 cada uno).
  Se respeta el presupuesto combinado de 12000 bytes, incluyendo consulta/JSON.
- Se hace como máximo una operación de generación por búsqueda, no una por tarjeta.
  Se validan salida estructurada, modelo, usage, ID, versión, cita literal y duplicados.
- **La prosa libre del modelo no se publica.** Solo se presentan los fragmentos
  comprobados que seleccionó. No se intenta certificar automáticamente entailment
  de frases nuevas o transformar una emoción manual en hecho acústico.
- Si falla cuota/timeout/rechazo/formato/citas, se conservan candidatos y citas
  registradas con un aviso. No se inventa una razón ni se repite la generación.
  Resultados no citados por el modelo o fuera del contexto mantienen alternativa.

Esta decisión implementa explicaciones conservadoras de evidencia, en vez de
presentar narrativa no comprobada como recomendación. Que una cita sea literal no
prueba pertinencia musical ni la veracidad original del editor; el usuario ve su
fuente completa y P17/P23 deberán evaluar utilidad/calidad con la colección real.
[Structured Outputs: límites y validación](https://developers.openai.com/api/docs/guides/structured-outputs).

No hay conexión ni transacción de BD abierta durante generación. Al terminar se
abre una nueva instantánea y se comprueban de nuevo modelo/receta, ID/versión/hash,
elegibilidad y filtros. Se descarta el candidato que cambió o salió de la playlist;
no se cita su versión nueva como si hubiera generado la explicación anterior.
Si cambió la referencia, 409 reference_changed. Títulos y metadatos de las pistas
válidas se refrescan en esa misma instantánea. No hay reintento de red por cambios.

## Música compartida

«Escuchar» es la única acción que inicia audio desde un resultado. El reproductor
único recibe la **cola exacta de resultados recuperados**, en el mismo orden; no
repite la búsqueda, no consulta un álbum entero y no puede generar otro cargo por
preparar la cola. Una cola de una solicitud anterior no sustituye a esa instantánea.
Consultar, cancelar, editar fichas o navegar no reinicia el audio que ya sonaba.
Escuchar es una intención explícita que puede reemplazar la cola anterior.

El backend no acredita escucha real por servir bytes. Las pruebas de controlador
usan un doble de audio; continuidad/seek/teclado/ancho visual siguen con revisión
manual pendiente. Conservar los originales y los recursos gestionados existentes.

## Contrato añadido

POST /explore/search conserva P22 y añade explain (booleano estricto, false).
POST /explore/similar admite track_id, limit, album_id, playlist_id y explain;
permite recuperación por referencia con generación optativa sin dar efectos
facturables a GET. GET /tracks/{id}/similar mantiene solo recuperación sin generación.

Respuesta de exploración añade explanations_requested, explanation_policy,
generation_usage (null si no se validó), generation_model cuando procede y
explanation/evidence por resultado. explanation_source es recorded o
generated_selection. Los campos de contexto no contienen herramientas, audio ni
rutas privadas; no se ejecutan instrucciones incluidas en una ficha.

El flujo técnico se prueba con embedding y generación simulados sobre pgvector
real en bases aisladas. No constituye uso satisfactorio de API real: se mantienen
P20–P23 sin cierre real hasta resolver créditos, reanudar prueba y evaluar P17.
No hay migraciones ni dependencias nuevas en P23. Próximo bloque previsto P24
(favoritos), conservando los pendientes del núcleo del MVP.
