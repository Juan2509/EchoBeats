# Explorar como conversación musical

Ampliación solicitada el 16 de noviembre de 2026. Sustituye el formulario técnico
como entrada principal, sin eliminar la búsqueda avanzada ni sus fuentes.

## Experiencia

Una caja para hablar con EchoBeats, tres sugerencias de inicio y Enviar. Enter envía,
Shift+Enter añade una línea. Se pueden hacer seguimientos, cancelar la espera o
empezar una conversación nueva. Las tarjetas permiten escuchar, marcar un corazón,
abrir álbum y consultar citas cuando existen. Opciones reúne el uso de IA, olvidar
reproducciones recientes y Búsqueda avanzada (formulario P23–P25 intacto).

Al abrir no se busca ni se llama al proveedor: solo se consulta su configuración.
El modo inicial es local. Usar IA es opt-in por visita y solo se habilita cuando el
servidor declara integración y clave configuradas; eso no acredita saldo/acceso.
No se habilitó IA en .env ni se reanudó la prueba real pendiente por créditos.

## Contexto y gustos

- Favoritos explícitos: hasta ocho recientes como contexto; las razones y filtros
  consultan favoritos guardados. No se modifican corazones por lo que diga el chat.
- Pista actual y hasta doce reproducciones iniciadas durante esta sesión. Se añaden
  solo al evento `playing`, no por abrir una ficha o seleccionar un audio que no
  empieza. Son señales débiles de reproducción, no escuchas completas verificadas.
- Este contexto reciente vive en memoria del reproductor; no hay tabla de historial,
  localStorage, telemetría externa ni perfil aprendido. Puede olvidarse en Opciones.
- La conversación vive en la vista (máximo20 turnos); al servidor van como máximo
  los dos turnos respondidos anteriores y la pregunta actual. No se persiste.
- «Otras opciones» puede excluir hasta20 IDs de la última respuesta. Se validan
  entradas, roles, UUID, longitudes y estado vigente de pistas; no acepta rol system.

La API resuelve títulos/autores/fichas desde la base; no confía en metadatos enviados
por el navegador. Pistas retiradas o inexistentes no se usan como contexto. No recibe
audio ni solicita acceso a servicios externos de escucha.

## IA y alternativa local

`POST /api/v1/explore/chat`: messages, current_track_id, recent_track_ids,
previous_track_ids, reference_track_id y use_ai (false por omisión).
Responde reply, mode, recommendations, warnings y resumen de contexto.

Con IA habilitada y elegida se solicita un plan estructurado de intención, consulta,
referencia permitida y descubrimiento. No hay herramientas ni escrituras; store=false.
El plan se valida dos veces y solo puede referenciar pistas del contexto. Después
se usa recuperación híbrida o similares existente: como máximo dos operaciones
lógicas externas (plan y embedding de consulta), con límites del adaptador existente.
No se mantiene transacción SQL durante red. Un fallo de plan/cuota activa alternativa
local explícita; no se repite esa operación. Un fallo de recuperación conserva una
alternativa de catálogo, con aviso. No se publica prosa musical libre del modelo.

Las respuestas conversacionales son frases controladas; las razones musicales
proceden de citas literales registradas, con fuente y versión. Los metadatos/títulos
del contexto se tratan como datos no confiables en las instrucciones al modelo.
El modo ai significa que se interpretó la petición con IA, no que todas las tarjetas
sean resultados semánticos ni que su pertinencia esté demostrada.

Sin IA se reconocen saludos, preguntas sobre gustos y algunos seguimientos. Se usa
la recuperación textual/similares local cuando hay índice vigente. Sin resultados,
se examinan hasta500 pistas elegibles, priorizando referencias del contexto antes
de las incorporaciones recientes: coincidencias de palabras, favoritos y álbumes
del contexto. Descubrimiento excluye favoritos; referencia excluye su propia pista.
Se explica la razón real. Si solo es una pista de biblioteca sin señales, se indica
que no hay información musical suficiente; no se inventan energía, emoción o sonido.
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
