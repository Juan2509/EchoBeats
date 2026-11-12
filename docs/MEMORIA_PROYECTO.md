# Memoria de EchoBeats

Registro inicial: 12 de noviembre de 2026.

## Solicitud y estado

El usuario pidió revisar y comprender los dos documentos aportados y guardar el
contexto antes de comenzar el desarrollo. Confirmó expresamente **EchoBeats** como
nombre definitivo. Toda mención a Dream Radio en la fuente conceptual corresponde
a este mismo proyecto con su nombre anterior.

Se revisó el texto de ambos archivos. Se conservaron copias completas y sin
modificaciones en `referencias/`; esta memoria las sintetiza, no las sustituye.
El material técnico referencia imágenes externas en `images/` que no acompañan
a los dos Markdown recibidos; su contenido visual no se pudo revisar.
En la revisión inicial no se ejecutaron los ejemplos ni se verificaron en línea
versiones, precios, disponibilidad de modelos o servicios. En ese momento todavía
no había implementación; el avance posterior se registra a continuación.

Después de la revisión, el usuario solicitó un plan por secciones que permita
organizar los futuros commits y retomar el trabajo entre sesiones. Se preparó
`PLAN_DESARROLLO.md` con tareas, dependencias, criterios de cierre y bitácora.
La planificación no implica que sus tareas estén ejecutadas ni sus commits creados.

## Avance posterior: P01

El usuario solicitó desarrollar el paso 1 y recibir al terminar una sugerencia de
commit en español, preferencia que se mantiene para los siguientes pasos.
P00 ya estaba registrado en `0ee2b43`. Se completó P01 con `ALCANCE_MVP.md`:
RF-01 a RF-16 incluidos, RF-17 posterior recomendado y RF-18 a RF-20 aplazados.
CA-01 a CA-12 aplican al MVP; CA-13 queda condicional al reconocimiento.

Se creó una colección técnica original en `pruebas/coleccion/`, con cuatro señales
MP3, un duplicado y dos archivos inválidos, manifiesto y generador reproducible.
Se verificaron hashes, tamaños, decodificación y etiquetas. La evaluación de
pertinencia musical sigue requiriendo una colección musical autorizada en P17.
No se implementó la aplicación ni se creó un commit en este paso.
P01 quedó posteriormente registrado en `bb10254`.

## Avance posterior: P02

El usuario pidió continuar con P02. Se crearon `DECISIONES.md`,
`DISENO_PANTALLAS.md`, `MODELO_DATOS.md` y `CONTRATO_API.md`.
Las elecciones actuales de trabajo son una aplicación local de un usuario,
React/TypeScript/Vite, Python 3.12/FastAPI, SQLAlchemy/Psycopg/Alembic y
PostgreSQL con pgvector. Docker permitirá usar Python compatible sin modificar
el Python 3.10 del sistema. Las versiones exactas se comprobarán en P03.

Medios copiados a MEDIA_ROOT, deduplicación por bytes SHA-256, un reproductor
compartido que continúa durante navegación, un lienzo de 1000 × 700 escalable,
coordenadas relativas y guardado completo por revisión. Contratos de API y datos
definen manejo de errores, archivos parciales y conflictos de edición.

Se consultaron fuentes oficiales para orientar capacidades técnicas; no se
instalaron paquetes ni se construyó aún interfaz/API ejecutable. Proveedor de
IA y requisitos docentes siguen pendientes. Los apartados históricos siguientes
reflejan el concepto inicial; las decisiones vigentes se consultan en DECISIONES.md.
P02 se entregó sin crear commit y el usuario lo registró después en `6c0163a`.

## Avance posterior: P03

Se prepararon frontend React/TypeScript/Vite, backend FastAPI con health real,
configuración por entorno, Docker Compose local, exclusiones de archivos privados
y README de instalación. Locks npm y Python (versiones/hashes) e imágenes por digest.
No se implementaron todavía biblioteca, reproducción, muros, IA ni base de datos.

Se construyeron ambas imágenes y se comprobó arranque local, seis pruebas HTTP
sin avisos, compatibilidad de paquetes, build de frontend en host/Node 24 y
respuesta HTTP directa y por proxy. Sin verificación visual en navegador.
Detalles y versiones en `VALIDACION_P03.md`. Los servicios de comprobación se
detienen al finalizar; no se publica ni se crea commit. P03 se registró después
en `4d87180`.

## Avance posterior: P04

El usuario autorizó continuar con PostgreSQL y pgvector. Se incorporó la imagen
por digest (PostgreSQL 17.11/pgvector 0.8.7), volumen nombrado, Alembic con
`0001_enable_vector`, motor SQLAlchemy/Psycopg y endpoint /api/v1/ready.
El arranque aplica migraciones antes del backend. Puerto de host 5433 porque
5432 ya tenía otro servicio, que se dejó intacto. Backend usa postgres:5432.

`scripts/preparar_entorno.py` genera .env privado sin sobrescribir uno existente.
`scripts/base_datos.py` respalda con manifiesto/hash y restaura solo a una base
nueva. Nueve pruebas, caída/recuperación, distancias de vectores de prueba,
respaldo real y persistencia tras recrear contenedores comprobados.
Datos conservados en volumen, .env y backups locales, excluidos de Git;
base restaurada de comprobación aislada de la principal. Detalles en
BASE_DATOS.md y VALIDACION_P04.md. Aún sin catálogo ni embeddings musicales.
P04 se registró posteriormente en `cb6575b`.

## Avance posterior: P06 y dependencia P05

El usuario solicitó P06. P05 aún no existía y se completó como dependencia:
catálogo SQLAlchemy Core, migración 0002_catalog, integridad de relaciones,
álbum «Sin álbum» y almacenamiento gestionado.

P06 añade selección/carga múltiple y POST /api/v1/imports: valida MP3 mediante
Mutagen 1.48.1, aplica límites, calcula SHA-256 y evita duplicados concurrentes.
Transacción por archivo con staging y compensación; un commit ambiguo se comprueba
antes de retirar medios. `python -m app.media_audit` solo informa inconsistencias.

Se recuperó la configuración .env ausente sincronizando solo el rol local con
la contraseña generada, sin borrar volumen/datos. Se comprobaron 24 pruebas,
build, alembic check y persistencia real después de recrear contenedores.
Cuatro audios sintéticos quedan importados en la biblioteca local. Títulos de
archivo y álbum desconocido son provisionales; lectura de etiquetas en P07.
Sin biblioteca visual ni reproducción aún. Detalles en IMPORTACION_MP3.md y
VALIDACION_P06.md. Sin commit automático. Siguiente: P07.

## Avance posterior: P07

P05/P06 quedaron registrados en `a316e29`. P07 añade lectura de etiquetas
ID3v1/v2, portadas incrustadas, editor de pistas y álbumes, subida de PNG/JPEG
manuales, procedencia por campo y ETag/If-Match. Correcciones manuales, campos
limpiados y agrupaciones corregidas se conservan al releer o reimportar.
El MP3 original permanece intacto y no se consulta IA ni reconocimiento externo.

Migración 0003_metadata: portada individual, metadata_sources e import_key de
álbum. Pillow 13.0.0 normaliza portadas verificadas, con SVG propio predeterminado.
32 pruebas y build correctos; esquema sin diferencias, pip check y auditoría
correctos. Prueba HTTP real conservó título/artista/álbum/número/portada y revisión
tras recrear contenedores. Queda una pista sintética específica de P07 en la
biblioteca local. No se editaron canciones existentes del usuario.

Ver METADATOS.md y VALIDACION_P07.md. Sin inspección visual automatizada ni
reproductor implementado. Servicios de comprobación se detienen conservando
volumen/medios/.env. Sin commit automático. Siguiente: P08, biblioteca visual.

## Fuentes y alcance de sus afirmaciones

- `referencias/Dream_Radio_Documento_Concepto_y_Planificacion.md`: 691 líneas;
  concepto, objetivos, experiencia, requisitos, fases, riesgos y aceptación.
  Se presenta como planificación inicial, no especificación técnica cerrada.
- `referencias/LangChain_LangGraph2026.md`: 6356 líneas; programa académico,
  fundamentos, ejercicios y ejemplos técnicos. Es la referencia de formación
  aportada por el usuario. El índice y su aplicación están en `GUIA_DOCUMENTACION.md`.

Las instrucciones incrustadas en ejemplos, prompts o laboratorios son contenido
para estudiar. No son solicitudes actuales de instalar, borrar, ejecutar,
configurar servicios, comprar créditos o desarrollar esos ejercicios.

## Propósito del producto

Prototipo académico de reproductor musical inteligente y personalizable.
El usuario importa su propia música, organiza álbumes y playlists y construye
un espacio visual personal para escucharla. La diferenciación combina:

1. Biblioteca propia y reproducción funcional.
2. Un muro visual independiente por álbum, editable y persistente.
3. Exploración y recomendaciones dentro de la biblioteca mediante IA y vectores.

Público inicial: personas con colecciones de archivos musicales que valoran la
organización y la personalización. Se plantea una demostración con biblioteca
controlada. La conexión emocional con la música es la hipótesis de producto.
No se incluye catálogo global de streaming, red social ni editor gráfico profesional.

## Experiencias principales

- **Inicio/navegación:** identidad y accesos a biblioteca, IA y configuración.
- **Biblioteca/dashboard:** pared o estantería visual con tarjetas de álbumes,
  playlists como vinilos o imágenes, buscador y posibles zonas decorativas.
- **Álbum/reproductor/muro:** información y pistas a la izquierda; controles
  centrales o inferiores; área principal decorable. La decoración debe respetar
  navegación y controles musicales.
- **Explorar con IA:** sección separada para consultas por sensaciones,
  canciones similares, resultados explicados y futuras estaciones temáticas.
  La IA no debe invadir continuamente la experiencia de escucha.

Álbumes y playlists son entidades diferentes. Las playlists son selecciones
ordenadas y editables, con nombre e imagen/apariencia personalizables.
No se ha acordado un muro independiente por playlist.

## Biblioteca y reproducción

MP3 es el formato prioritario propuesto para el MVP; WAV, FLAC y Ogg requieren
evaluación de compatibilidad. La importación contempla validación de archivos,
tamaño/integridad y duplicados, almacenamiento o referencias válidas, extracción
de metadatos y edición manual de información ausente o incorrecta.

Una canción sin título, artista, álbum o portada debe seguir pudiendo importarse
y reproducirse, con valores provisionales. El análisis por IA no debe bloquear
indefinidamente la disponibilidad del audio.

Controles mínimos: reproducir/pausar, anterior/siguiente, título e información,
tiempo/duración, avance temporal y volumen. Aleatorio, repetición, cola y
continuidad entre vistas son funciones deseables.

La identificación por huella acústica (AcoustID/MusicBrainz o ACRCloud por evaluar)
es distinta del análisis de características del sonido. Un modelo generativo
no garantiza reconocimiento de canciones. Conservar la procedencia de los datos:
etiquetas del archivo, edición manual, coincidencia identificada e inferencia de IA.
Una identificación fallida no permite inventar título, artista o portada.

## Muros: requisito central

Cada álbum tiene su propio muro. Editar A y abrir B nunca debe mezclar diseños.
El diseño debe sobrevivir al cierre y reinicio de la aplicación.

El editor contempla fondos, imágenes, pósteres, stickers y GIFs; añadir,
arrastrar, rotar, redimensionar, eliminar, guardar/restaurar y restablecer.
La imagen de fondo y algunas integraciones siguen sujetas al alcance.
Se recomiendan modos «Editar pared» y «Bloquear diseño».

Persistir la descripción de la composición: álbum/muro, ID y tipo del elemento,
referencia al recurso, posición, tamaño, ángulo, orden de superposición y fondo.
Las coordenadas relativas son una propuesta para adaptarse a la ventana.
Guardar al terminar operaciones significativas evita escrituras por cada píxel.
Audios e imágenes se proponen como archivos gestionados; la BD conserva referencias.

## IA y búsqueda vectorial

El concepto fija como obligatorios **pgvector y el consumo demostrable de al
menos una API de IA**. Sus funciones deben poder comprobarse de extremo a extremo.

Primera vía propuesta: embeddings de descripciones musicales enriquecidas,
con datos de estilo, instrumentos, voz, ritmo, energía o ambiente cuando exista
evidencia. Un embedding textual de la descripción no equivale a analizar el audio.
El MVP puede usar descripciones manuales/verificadas si el análisis directo aún
no está disponible, declarando esta limitación en la sustentación.

Flujo propuesto:

1. Validar la consulta por sensaciones; interpretarla con IA cuando aporte valor.
2. Generar su embedding compatible con el modelo/configuración de indexación.
3. Consultar similitud en PostgreSQL + pgvector.
4. Recuperar canciones existentes en la biblioteca y ordenar resultados.
5. Explicar coincidencias con evidencia de las fichas recuperadas.
6. Permitir reproducir y, posteriormente, construir una estación.

Registrar modelo y versión/fuente de la descripción junto a cada embedding.
Las explicaciones no deben inventar rasgos musicales ni canciones.
Los favoritos pueden alimentar personalización progresiva; historial, saltos y
valoraciones requieren almacenamiento y reglas antes de afirmar que aprende gustos.
La decoración visual no constituye por sí sola una preferencia musical.

RAG es pertinente para explicar con fichas recuperadas. LangGraph sería útil
para decisiones entre herramientas, pero no es requisito técnico de una primera
búsqueda vectorial salvo exigencia académica específica. Estaciones, reconocimiento
enriquecido, voz de locutor y herramientas multiagente son ampliaciones.

## Tecnologías: estado de las decisiones

| Componente | Estado según el concepto |
| --- | --- |
| PostgreSQL + pgvector | Dirección de persistencia y requisito vectorial explícito. |
| API de IA | Obligatoria; proveedor y modelo por seleccionar. |
| Python | Recomendación de backend. |
| HTML/CSS/JavaScript | Preferencia preliminar para el editor visual. |
| REST/JSON y FastAPI | API propuesta; framework aún por evaluar. |
| LangChain | Orquestación opcional recomendada. |
| LangGraph | Ampliación posible o exigencia docente por confirmar. |
| n8n | Según exigencia curricular y utilidad real. |
| Streamlit | Alternativa para experimentar; evaluar adecuación al muro editable. |
| Reconocimiento y análisis directo de audio | Servicios/capacidades/costes por verificar. |

Arquitectura lógica propuesta: frontend → backend Python → PostgreSQL/pgvector,
archivos gestionados e integraciones externas. La entrega de audio debe permitir
avance temporal; el mecanismo depende del despliegue finalmente elegido.

## Información conceptual

Entidades previstas: Track, Artist, Album, Playlist, Wall, WallElement,
MediaAsset, TrackEmbedding y Preference. PlaybackEvent y AIRequest son opcionales.
Un álbum contiene canciones y tiene un muro; las playlists contienen canciones
en orden mediante una relación múltiple; cada muro contiene elementos; cada
embedding se vincula a una canción y versión de descripción.
El documento no define todavía SQL ni normalización definitivos.

## Plan y criterios de aceptación

Etapas propuestas: 0) validar alcance, wireframes, archivos y servicios;
1) biblioteca/reproductor; 2) personalización persistente;
3) IA y búsqueda vectorial; 4) preferencias/enriquecimiento;
5) ampliaciones opcionales.

Los RF-01 a RF-20 y CA-01 a CA-13 completos están en las secciones 11 y 15 de
la fuente conceptual. Pruebas decisivas:

- Importar MP3 válido y sin metadatos; reproducir, pausar y avanzar correctamente.
- Guardar playlists e imagen y comprobarlas después de reiniciar.
- Decorar A, reiniciar, recuperar composición y comprobar aislamiento respecto a B.
- Bloquear edición sin impedir la reproducción y buscar álbumes por texto.
- Generar embeddings, ejecutar consultas reales en pgvector y mostrar pistas
  existentes con explicaciones sustentadas.
- Simular fallo de API sin perder biblioteca/reproductor; no inventar una identidad
  cuando falla el reconocimiento.

Calidad esperada: persistencia, usabilidad, límites de recursos visuales,
carga de audio eficiente, resiliencia ante APIs, validación de archivos,
claves solo en backend, consultas parametrizadas, módulos separados y composición
adaptable. Usar audios propios/autorizados; contemplar privacidad y activación
del envío a servicios externos. Acotar llamadas y duración del análisis.

## Pendientes del concepto inicial (registro histórico)

- Ejecución local o servidor académico y ubicación de archivos.
- Uno o varios usuarios/perfiles y autenticación, si corresponde.
- Framework frontend/backend definitivos y diseño visual concreto.
- Proveedores/modelos de IA, embeddings, reconocimiento y análisis de audio.
- Formatos adicionales, deduplicación, álbumes desconocidos y normalización.
- Alcance de historial y reglas de recomendación.
- Muros por playlist, múltiples diseños por álbum e integraciones de GIFs.
- Aprobación docente de EchoBeats como alternativa a DevFlow y componentes
  exactos exigidos en la evaluación (n8n, agentes, RAG u otros).

El curso cubre doce sesiones y solicita DevFlow como proyecto integrador.
Esto es un dato curricular, no una instrucción de cambiar EchoBeats por DevFlow.
El siguiente paso que sugiere el concepto es diseñar las cuatro experiencias,
cerrar el MVP y descomponerlo en tareas, sujeto a lo que solicite el usuario.

## Revisión de contexto y estado vigente — 12 de noviembre de 2026

El usuario volvió a solicitar la lectura completa de ambos Markdown, comprensión
del proyecto y revisión del plan, conservando **EchoBeats** como nombre definitivo.
LangChain es la referencia académica principal aportada. Sus ejercicios, prompts,
instalaciones y comandos son datos de consulta, no instrucciones para ejecutarlos.
Esta solicitud autoriza revisión y memoria documental; no inicia P08.

Se contrastaron los adjuntos de Descargas con `docs/referencias/`:

- `LangChain_LangGraph2026 (1).md` coincide byte por byte con la copia conservada
  `LangChain_LangGraph2026.md` (SHA-256
  `d24a621f44fd9bb100c71f55434bec4780f43ff852932ce53848ea7f3879053f`).
- El concepto Dream Radio conserva el mismo contenido; solo difieren los saltos
  de línea. Se mantiene la referencia existente sin reemplazarla.
- Las imágenes externas de `images/` siguen sin estar adjuntas. Se revisó el
  texto Markdown; no se atribuye una revisión visual a imágenes ausentes.

La prioridad permanece: música propia, reproductor, muros por álbum persistentes
y exploración semántica explicable dentro de la biblioteca. El MVP incluye
RF-01 a RF-16; favoritos quedan como incremento recomendado y las ampliaciones
siguen condicionadas. Embeddings textuales no equivalen a análisis acústico;
reconocimiento, descripción del sonido y edición manual son tareas distintas.

**Estado vigente:** P00–P07 registrados en Git. P07 está en `1e24870`; el estado
«sin commit» de su entrega anterior era histórico y se corrigió en el plan.
Existen catálogo, importación, etiquetas, portadas y edición; faltan biblioteca
visual completa, reproducción, playlists, muros e integración musical de IA.
Las pruebas de P07 son evidencias anteriores, no se ejecutaron de nuevo en esta
revisión documental. El siguiente bloque sigue siendo **P08**.

**Resuelto:** ejecución local de un usuario, React/TypeScript/Vite, Python 3.12/
FastAPI, PostgreSQL/pgvector, medios gestionados, duplicados por SHA-256 y
protección de cambios manuales. Los pendientes históricos de arriba no reabren
estas decisiones; consultar `DECISIONES.md` y las validaciones P03–P07.

**Abierto:** proveedor/modelos de IA, colección musical autorizada para evaluar
relevancia y confirmación docente de EchoBeats como alternativa a DevFlow y de
componentes exigidos. El archivo académico desarrolla especialmente prompts,
embeddings, recuperación, LCEL, salidas estructuradas y Streamlit; menciona
LangGraph y n8n sin un tutorial completo equivalente. Es la base de formación,
pero sus ejemplos no certifican compatibilidad ni vigencia de servicios.

**Revisión del plan:** la secuencia P08–P11 (biblioteca/audio/playlists), P12–P16
(muros), P17–P23 (evaluación/fichas/API/embeddings/recuperación) y P26–P28
(integración/calidad/entrega) cubre los pilares del concepto. Mantener evaluación
antes de ajustar la recuperación, API y vectores reales como evidencias, y escucha
operativa ante fallos de IA. No se modificó el alcance ni se habilitaron ampliaciones.

## Avance posterior: P08

El usuario solicitó continuar con el paso 8. Se implementaron inicio, navegación,
biblioteca visual con tarjetas y lista de canciones, búsqueda literal por título/
álbum/artistas y detalle de álbum con pistas ordenadas y paginadas. Mayúsculas
ignoradas, tildes conservadas; comodines escapados y consultas parametrizadas.
Consulta/vista/página persisten en URL; formularios P07 conservan borradores al
navegar y sus guardados refrescan el catálogo. Sin audio ni simulaciones de IA.

42 pruebas PostgreSQL aisladas, TypeScript/build Windows y Docker, pip check,
esquema y auditoría correctos; importación del MP3 técnico `tono_grave.mp3` y
búsqueda real por proxy verificadas. En este equipo no había .env ni recursos
Docker de EchoBeats: se creó configuración privada y volumen nuevo sin alterar
otros recursos. Los datos históricos anteriores no estaban presentes aquí.

La revisión visual quedó pendiente: la herramienta de navegador se detuvo al no
poder identificar la URL con confianza para aplicar su política. No se declara
cierre de P08 ni verificación visual. Ver `VALIDACION_P08.md`; revisar teclado y
anchos 360/768/1280 antes de cerrar, después P09. No se creó commit.
