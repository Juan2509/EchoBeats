# Explorar como conversación musical

Ampliación solicitada el 16 de noviembre de 2026. Sustituye el formulario técnico
como entrada principal, sin eliminar la búsqueda avanzada ni sus fuentes.

## OpenAI en Explorar

Explorar usa OpenAI directamente cuando el backend tiene `AI_ENABLED=true`
y `OPENAI_API_KEY` configurados. Al abrir la vista se comprueba la configuración
local. Al enviar el mensaje se comparten hasta cuatro intercambios previos y el
contexto musical. La respuesta puede consumir créditos. Si OpenAI no está
configurado o devuelve un error, EchoBeats ofrece una respuesta básica.

## Experiencia

Enter envía el mensaje y Shift+Enter añade una línea. Puedes cancelar la espera
o empezar una conversación nueva. Las tarjetas permiten escuchar, marcar favoritos,
abrir un álbum y consultar citas cuando existen. Opciones reúne la búsqueda avanzada
y el control para olvidar reproducciones recientes. GPT-6 Luna usa esfuerzo de
razonamiento bajo para el chat.

## Contexto y gustos

- Favoritos explícitos: hasta ocho recientes como contexto; las razones y filtros
  consultan favoritos guardados. No se modifican corazones por lo que diga el chat.
- Pista actual y hasta doce reproducciones iniciadas durante esta sesión. Se añaden
  solo al evento `playing`, no por abrir una ficha o seleccionar un audio que no
  empieza. Son señales débiles de reproducción, no escuchas completas verificadas.
- Este contexto reciente vive en memoria del reproductor; no hay tabla de historial,
  localStorage, telemetría externa ni perfil aprendido. Puede olvidarse en Opciones.
- La conversación vive en la vista (máximo20 turnos); al servidor van como máximo
  los cuatro turnos respondidos anteriores y la pregunta actual. No se persiste.
- «Otras opciones» puede excluir hasta20 IDs de la última respuesta. Se validan
  entradas, roles, UUID, longitudes y estado vigente de pistas; no acepta rol system.

La API resuelve títulos/autores/fichas desde la base; no confía en metadatos enviados
por el navegador. Pistas retiradas o inexistentes no se usan como contexto. No recibe
audio ni solicita acceso a servicios externos de escucha.

## IA y alternativa local

`POST /api/v1/explore/chat`: messages, current_track_id, recent_track_ids,
previous_track_ids, reference_track_id y use_ai (false por omisión).
Responde reply, mode, recommendations, suggestions, warnings y resumen de contexto.

Con OpenAI habilitado se solicita un plan estructurado de intención, consulta,
referencia permitida y descubrimiento. No hay herramientas ni escrituras; store=false.
El plan se valida dos veces y solo puede referenciar pistas del contexto. Después
se usa recuperación híbrida o similares existente: como máximo dos operaciones
lógicas externas (plan y embedding de consulta), con límites del adaptador existente.
No se mantiene transacción SQL durante red. Un fallo de plan/cuota activa alternativa
local explícita; no se repite esa operación. Un fallo de recuperación conserva una
alternativa de catálogo, con aviso. Para descubrir música, el plan puede devolver hasta cuatro sugerencias acotadas
con canción, artista cuando se conoce, obra de origen si es relevante y razón
concreta. Cada opción indica afinidad directa o aproximada. Una opción aproximada
explica qué aspecto encaja y cuál difiere. Esta rama usa una llamada de generación y
no requiere embeddings. Deduplica las sugerencias y omite coincidencias de título
y artista con pistas activas. La interfaz ofrece búsquedas en YouTube construidas
a partir del título y artista. La disponibilidad y los datos de las sugerencias
dependen de la verificación del usuario.

Con IA, la respuesta de chat usa hasta 900 caracteres para conversar sobre gustos,
artistas, géneros, discos o sonidos, y retoma hasta cuatro turnos previos. Una charla
musical puede continuar sin tarjetas ni consultas de embeddings. El servidor sigue
redactando la respuesta cuando muestra resultados de la biblioteca. Las razones de las tarjetas
de biblioteca proceden de citas literales registradas, con fuente y versión, o de
señales explícitas del catálogo. Los metadatos/títulos
del contexto se tratan como datos no confiables en las instrucciones al modelo.
El modo ai significa que se interpretó la petición con IA, no que todas las tarjetas
sean resultados semánticos ni que su pertinencia esté demostrada.

Sin IA se reconocen saludos con puntuación y fórmulas como «hola que tal»,
agradecimientos y preguntas sobre gustos. Las peticiones reconocibles de charla
general reciben una pregunta breve. El modo local reconoce la música de
videojuegos y retoma ese tema ante una aclaración. Estas respuestas no consultan
el catálogo. Se usa
la recuperación textual/similares local cuando hay índice vigente. Sin resultados,
se examinan hasta500 pistas elegibles, priorizando referencias del contexto antes
de las incorporaciones recientes: coincidencias de palabras, favoritos y álbumes
del contexto. Descubrimiento excluye favoritos; referencia excluye su propia pista.
Se explica la razón real. Se omiten las pistas sin coincidencias ni señales de contexto.
Este orden de catálogo es específico del chat y no cambia scores/política P25.

La alternativa local no equivale a un modelo conversacional general ni a análisis
acústico. No conoce gustos fuera de EchoBeats. No se garantizan recomendaciones
personalizadas de calidad sin las evaluaciones pendientes de P17/CA-10/CA-11.

## Validación

251 pruebas backend de regresión aprobadas con bases/medios aislados; cinco del
chat cubren límites de entrada, catálogo vacío, favoritos/contexto real, descubrimiento,
pistas retiradas, plan simulado, cuota, referencia inventada, adaptador MockTransport
y seguimiento local. Tras añadir exclusión de opciones anteriores, esas cinco se
repitieron y aprobaron. No hubo proveedor real ni cambios en la biblioteca personal.

100 pruebas frontend y build aprobados. Se añaden validaciones de mensajes acotados,
rechazo de audio externo/IDs repetidos y contexto reciente solo mediante playing.
Chrome aislado con respuestas simuladas comprobó apertura sin POST, compositor
simple, saludos/seguimientos, tarjetas, exclusión previa, modo local inicial,
avanzado oculto, cancelación y360/768 sin desbordamiento horizontal. Capturas
music-chat-welcome/results/360/768 inspeccionadas en data/validation.

No hay migraciones, dependencias nuevas ni cambios de configuración privada.
La interpretación y pertinencia con API real y la escucha continúan pendientes.


Las peticiones generales se orientan a charla o descubrimiento. En modo local,
la búsqueda de pistas se reserva para peticiones de biblioteca, favoritos o una
referencia explícita. El modo local incluye ejemplos musicales de
[Smalltown Boy](https://londonrecords.co.uk/artists/bronski-beat/) y
[First Steps](https://radicaldreamland.bandcamp.com/track/first-steps).
Una declaración de identidad por sí sola no genera recomendaciones.

Para una recomendación abierta que menciona Mighty Switch Force, EchoBeats
incluye un enlace directo a la [banda sonora oficial de la secuela](https://virt.bandcamp.com/album/mighty-switch-force-2-ost)
de Jake Kaufman como aproximación documentada. Las sugerencias que genera el
modelo sin una fuente documental siguen identificadas como conocimiento general.

Los saludos y agradecimientos breves se contestan sin consultar el modelo.
Si se excluye la música de videojuegos, los seguimientos de recomendación
mantienen esa restricción dentro del contexto reciente. Para una referencia
electrónica como Mighty Switch Force se ofrecen ejemplos de discos o sencillos
con fuente y se evitan las opciones ya mostradas. Si falta un punto de partida
musical, se pide precisar qué rasgo conservar.
