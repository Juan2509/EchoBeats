# DREAM RADIO

## Documento de concepto, alcance y planificación del proyecto

**Estado:** Propuesta conceptual y planificación inicial  
**Tipo de proyecto:** Académico / prototipo funcional  
**Fecha de elaboración:** 12 de noviembre de 2026  
**Propósito de este documento:** Registrar de manera clara lo acordado sobre Dream Radio y servir de referencia para decisiones de diseño, desarrollo, pruebas y sustentación. **No constituye todavía una especificación técnica cerrada.**

---

## 1. Resumen ejecutivo

**Dream Radio** será un reproductor musical inteligente con una biblioteca de audio propia y una interfaz altamente personalizable, orientado a recuperar la conexión entre las personas y la música.

En lugar de intentar competir con Spotify u ofrecer un catálogo mundial, Dream Radio permitirá que cada usuario **importe y reproduzca su propia colección de canciones**, la organice en álbumes y listas, y cree espacios visuales personales como si decorara una habitación o una pared musical.

Cada álbum tendrá un **muro independiente**, con fondos, imágenes, pósteres, stickers y GIFs que el usuario podrá colocar, mover, redimensionar y rotar. Los cambios deberán **guardarse de forma persistente**, para que sigan allí al cerrar y volver a abrir la aplicación.

Un módulo aparte de **inteligencia artificial** analizará la colección musical, permitirá buscar por características y sensaciones, y ofrecerá recomendaciones progresivamente adaptadas a los gustos del usuario. La solución deberá integrar, como requisitos académicos, **una base de datos vectorial y el consumo de APIs de IA**.

**Idea central:** Dream Radio no solo reproduce música: crea un espacio personal para vivirla.

**Frase para presentar el concepto:** «No necesitas saber qué canción buscas. También puedes describir cómo quieres sentirla».

> **Nota de alcance:** se trata de un proyecto académico con demostración funcional; **no se plantea como un lanzamiento comercial ni como un reemplazo completo de plataformas de streaming**.

---

## 2. Problema y oportunidad

### 2.1 Problema que se desea abordar

La percepción que motiva Dream Radio es que los servicios musicales convencionales pueden sentirse impersonales, incluso cuando permiten crear playlists: la experiencia suele tener interfaces poco modificables, posibles interrupciones publicitarias según el servicio y el plan, y una organización centrada en catálogos, títulos, géneros y artistas.

La experiencia que se busca recuperar es más parecida a **tener un reproductor MP3 propio, una colección física de discos o una pared decorada con recuerdos musicales**: un entorno al que el usuario pueda dar identidad.

Esta es la **hipótesis de problema** del proyecto y no una afirmación de que todas las plataformas actuales carezcan de personalización o recomendaciones inteligentes.

### 2.2 Necesidades que se intentan satisfacer

- Reproducir música de una colección propia sin introducir publicidad dentro de Dream Radio.
- Conservar control sobre los archivos y la organización de la biblioteca.
- Personalizar de verdad el espacio visual sin necesidad de diseñar una interfaz desde cero.
- Relacionar álbumes y canciones con recuerdos, colores, imágenes y ambientes.
- Descubrir música a través de descripciones naturales: «algo espacial, tranquilo y nostálgico».
- Recibir recomendaciones explicables que tengan en cuenta la colección y, cuando se implemente, preferencias registradas.

### 2.3 Público objetivo inicial

Personas que coleccionan archivos musicales, disfrutan organizar álbumes, valoran la personalización visual y quieren encontrar nuevas conexiones en su propia biblioteca. El proyecto puede probarse con un conjunto reducido de usuarios y canciones; no necesita alcanzar escala comercial.

---

## 3. Objetivos

### 3.1 Objetivo general

**Desarrollar un prototipo funcional de reproductor musical inteligente y personalizable** que permita importar y reproducir una biblioteca de audio propia, crear muros visuales persistentes para álbumes y obtener recomendaciones y búsquedas semánticas mediante APIs de inteligencia artificial y PostgreSQL con pgvector.

### 3.2 Objetivos específicos

1. Permitir la importación, almacenamiento, consulta, organización y reproducción de archivos musicales del usuario.
2. Extraer metadatos disponibles y gestionar audios sin título, artista, álbum o portada identificables.
3. Incorporar análisis de contenido de audio y, si es viable, reconocimiento de canciones mediante servicios específicos.
4. Implementar una interfaz de biblioteca musical estilo pared, con tarjetas de álbumes, playlists y elementos visuales personalizables.
5. Crear un editor limitado de muros por álbum con movimiento, rotación, tamaño y fondos configurables.
6. Persistir el diseño individual de cada muro para reconstruirlo al volver a abrir la aplicación.
7. Generar y almacenar embeddings de descripciones/características musicales y consultar similitudes mediante pgvector.
8. Integrar una API de IA para interpretar búsquedas, apoyar la descripción de canciones y explicar recomendaciones.
9. Registrar señales explícitas o simples de preferencia —como favoritos— y utilizarlas en una versión de recomendaciones personalizadas.
10. Documentar y verificar el funcionamiento de los componentes para una sustentación académica.

---

## 4. Propuesta de valor y diferenciación

**Propuesta de valor:**

> Dream Radio es un reproductor musical inteligente y personalizable que transforma una colección de archivos de audio en una biblioteca visual propia. Permite escuchar música, decorar un espacio diferente para cada álbum y descubrir canciones a través de búsquedas y recomendaciones por sensaciones, apoyadas en inteligencia artificial y tecnología vectorial.

### 4.1 Tres pilares del producto

**Pilar A — Mi biblioteca, mi música.** El usuario importa y reproduce sus archivos; no depende de que el proyecto obtenga derechos para transmitir un catálogo global.

**Pilar B — Mi música, mi espacio.** La pared musical no es un tema visual genérico: cada álbum puede verse y sentirse diferente, y la personalización permanece guardada.

**Pilar C — Mi música, nuevas conexiones.** La IA permite explorar semejanzas musicales y describir preferencias en lenguaje cotidiano, no solo buscar por nombres o géneros.

### 4.2 Qué NO pretende ser

- No pretende replicar Spotify ni ofrecer todas las canciones disponibles en internet.
- No pretende ser una red social musical en su primera versión.
- No pretende ser un editor gráfico profesional ni ofrecer control píxel por píxel.
- No pretende garantizar que una IA identifique cualquier canción desconocida.
- No pretende que la IA «aprenda gustos» mágicamente: hacen falta datos de preferencias y una lógica de recomendación comprobable.

---

## 5. Experiencia general y mapa de pantallas

Se recomienda diferenciar **la entrada/navegación del sistema**, **la biblioteca**, **el reproductor y muro por álbum** y **la sección de IA**. La separación entre estas experiencias es parte del enfoque acordado.

### 5.1 Pantalla de inicio / navegación principal

Será el punto de entrada a Dream Radio, con identidad visual propia y accesos claros a:

- **Biblioteca / Dashboard principal:** álbumes, playlists, búsqueda y organización.
- **Explorar con IA:** recomendaciones, consultas por sensaciones y estaciones temáticas.
- **Configuración:** preferencias, gestión de archivos, opciones básicas de visualización.
- **Funciones futuras:** se pueden reservar espacios de navegación, pero no es necesario construirlas en el MVP.

**Principio de interfaz:** el módulo de IA es una sección aparte y **no debe invadir constantemente el espacio de escucha**.

### 5.2 Dashboard: mini biblioteca tipo pared

La biblioteca principal se imaginará como una **pared o estantería musical visual**, no como una tabla fría de archivos.

Elementos previstos:

- Tarjetas de álbumes y colecciones.
- Elementos visuales cuadrados y **círculos con apariencia de vinilo** para representar playlists/colecciones.
- Playlists iniciales predeterminadas, si se decide sembrarlas, pero **renombrables y editables**.
- Imagen central de los vinilos personalizable; posibilidad de cambiar su apariencia o sustituir el recuadro visual por una imagen propia.
- Búsqueda visible para localizar álbumes en bibliotecas grandes y, idealmente, canciones, artistas y playlists.
- Zonas decorativas adicionales: imágenes, pósteres o stickers en espacios disponibles, dentro de límites definidos.
- Posibilidad de ordenar/reorganizar tarjetas si la implementación lo permite.

**Distinción funcional:** los álbumes describen una colección musical y sus pistas; las playlists son selecciones editables de canciones. Aunque puedan tener apariencias similares, no deben confundirse en el modelo de datos.

### 5.3 Reproductor y pared de un álbum

Al abrir un álbum, se mostrará su espacio individual:

**Panel izquierdo:** portada del álbum, nombre, artista(s), información disponible, lista de canciones y selección de pista.

**Zona central/inferior:** controles del reproductor: reproducir/pausar, anterior/siguiente, tiempo transcurrido, duración, barra de progreso y volumen. Repetición y reproducción aleatoria son deseables.

**Zona principal:** pared del álbum, con fondo y objetos decorativos. El usuario construye la atmósfera visual asociada al álbum.

**Separación esencial:** los controles musicales deben seguir siendo utilizables aunque existan stickers, pósteres o GIFs decorativos.

### 5.4 Sección «Explorar con IA»

Separada del dashboard de escucha. Incluirá, según alcance:

- Campo de búsqueda por descripción: «quiero música cálida, electrónica y relajante».
- Canciones sugeridas desde la biblioteca disponible.
- Explicación breve de por qué cada resultado coincide con la petición.
- «Canciones similares a esta».
- Estaciones temáticas o listas generadas a partir de una idea.
- Recomendaciones apoyadas en preferencias cuando haya señales suficientes.

**Ejemplos de estaciones:** Nostalgia digital, Mundos acuáticos, Música de videojuegos, Sonidos futuristas, Recuerdos de la infancia, Lluvia nocturna y Pixel Dreams. Son nombres ilustrativos, no categorías obligatorias.

---

## 6. Personalización visual: libertad controlada

### 6.1 Filosofía de edición

El usuario tendrá libertad para **decorar el espacio**, pero no para modificar cada detalle de la arquitectura de la interfaz.

**Elementos estructurales protegidos:** controles de reproducción, organización básica del panel informativo, funcionamiento de los vinilos y componentes de navegación.

**Elementos personalizables:** fondos, imágenes centrales o tarjetas visuales, pósteres, stickers, GIFs e imágenes decorativas, con reglas para evitar que bloqueen el reproductor.

### 6.2 Capacidades del editor

- Cambiar el color del fondo.
- Utilizar una imagen como fondo, si se implementa.
- Importar imágenes o GIFs decorativos desde fuentes permitidas.
- Colocar elementos con el cursor libremente dentro del área decorable.
- Arrastrar elementos para cambiar su posición.
- Rotarlos.
- Redimensionarlos dentro de límites razonables.
- Eliminar elementos añadidos.
- Guardar y recuperar el diseño.
- Restablecer el diseño predeterminado.

**Interacción recomendada:** controles «Editar pared» y «Bloquear diseño». Al estar bloqueada, una pared se puede disfrutar sin mover objetos accidentalmente.

### 6.3 Un muro diferente para cada álbum

**Requisito acordado:** cada álbum podrá tener un diseño independiente. Abrir el álbum A nunca debe mostrar accidentalmente el diseño del álbum B.

Ejemplo:

- Álbum A: tonos rosa, pósteres y stickers.
- Álbum B: fondo azul, estética futurista y vinilos.
- Álbum C: tonos cálidos y recuerdos visuales.

Se puede proporcionar un diseño inicial común para álbumes aún no personalizados, sin imponerlo una vez que el usuario modifique su muro.

### 6.4 Persistencia obligatoria

**Requisito acordado:** las personalizaciones deben permanecer después de salir o cerrar el programa. No basta con mantener el estado mientras la pestaña o aplicación está abierta.

Se recomienda guardar **la descripción del diseño**, no una captura de pantalla. Para cada objeto, se necesitan como mínimo:

- Álbum al que pertenece.
- Identificador del objeto.
- Tipo (póster, sticker, GIF, etc.).
- Referencia a su imagen/archivo.
- Posición horizontal y vertical.
- Tamaño.
- Ángulo de rotación.
- Orden de superposición, si corresponde.
- Información del fondo del muro.

**Ejemplo ilustrativo, no esquema definitivo:**

```json
{
  "album_id": 12,
  "background_color": "#242038",
  "objects": [
    {
      "id": "poster-01",
      "type": "poster",
      "asset": "poster1.png",
      "x_percent": 25,
      "y_percent": 18,
      "width_percent": 20,
      "rotation_degrees": 15,
      "z_index": 2
    }
  ]
}
```

El uso de **coordenadas relativas al área decorable** puede ayudar a que el diseño se adapte a distintos tamaños de ventana. La representación exacta y límites de desplazamiento deben probarse.

**Guardado recomendado:** registrar los cambios al terminar una acción de arrastre/rotación/redimensionamiento y en eventos significativos, evitando escrituras innecesarias por cada píxel recorrido. También es conveniente guardar antes de salir y proporcionar retroalimentación de guardado.

**Almacenamiento recomendado:** conservar imágenes y audios como archivos en un almacenamiento gestionado por la aplicación y guardar en PostgreSQL sus referencias y propiedades. No es obligatorio meter archivos completos ni imágenes en pgvector.

### 6.5 Personalización del dashboard y playlists

Además de muros por álbum, la pantalla de biblioteca podría aceptar decoración de espacios laterales, como pósteres de pared. La edición de esas zonas debe respetar buscador, navegación y tarjetas.

Para las playlists:

- Renombrar.
- Modificar canciones que contienen.
- Conservar la presentación de vinilo, con imagen personalizable en su centro; o mostrar una imagen personalizada completa.
- Usar imágenes por defecto cuando no se adjunte una propia.

**No está acordado** que cada playlist tenga también una pared totalmente independiente: ese cambio puede evaluarse después de implementar los muros por álbum.

---

## 7. Biblioteca de audio y reproducción

### 7.1 Decisión principal

**El audio se reproducirá a partir de archivos aportados por el usuario**. No se diseñará como buscador y reproductor universal de cualquier canción de internet.

Formato prioritario recomendado para demostrar el MVP: **MP3**. WAV puede evaluarse pronto; FLAC y Ogg dependen de compatibilidad con el reproductor elegido y se tratarán como ampliaciones posibles, no como promesa de soporte inmediato.

### 7.2 Flujo de importación propuesto

1. El usuario selecciona uno o varios archivos compatibles.
2. El sistema comprueba formato, tamaño, integridad básica y posibles duplicados.
3. Se almacenan los archivos o se gestiona una referencia válida a ellos.
4. Se leen los metadatos que ya contiene el archivo: título, artista, álbum, duración, portada, etc.
5. Si faltan datos, se muestran campos provisionales y se habilita la edición manual.
6. Se solicita, de manera controlada, identificación o análisis musical mediante las capacidades disponibles.
7. Se genera una descripción de la canción y su representación vectorial.
8. La canción queda disponible en la biblioteca y en el reproductor.

**Aclaración:** el orden exacto puede cambiar: la reproducción no debería bloquearse indefinidamente mientras termina el análisis por IA.

### 7.3 Audios sin nombre, artista ni portada

Ejemplo: se importa `audio1.mp3`.

Se deben diferenciar **dos tareas distintas**:

**Identificación de grabación:** utilizar un servicio de reconocimiento por huella acústica para intentar conocer título, artista, álbum y, mediante un servicio de metadatos, portada. Herramientas a evaluar: **AcoustID/MusicBrainz** o **ACRCloud**, según disponibilidad, condiciones de uso y facilidad de integración. La coincidencia debe considerarse tentativa hasta validarla; si falla, el sistema no inventa datos.

**Análisis del sonido:** utilizar un modelo o servicio compatible con audio para obtener o estimar información sobre estilo, instrumentos, presencia de voz, ritmo, energía y atmósfera musical. **No debe asumirse que cualquier API de LLM puede identificar canciones por audio o que sus juicios emocionales son hechos objetivos.**

**Comportamiento esperado:** incluso si no se identifica la grabación, se puede reproducir, renombrar manualmente y describir musicalmente cuando el analizador lo permita. No debe presentarse una descripción inferida como metadato verificado.

### 7.4 Controles mínimos del reproductor

- Reproducir y pausar.
- Cambiar de canción.
- Ver título, artista, álbum y portada disponibles.
- Mostrar tiempo transcurrido, duración y barra de avance.
- Controlar volumen.
- Mantener coherencia entre la canción actual y el panel informativo.

Funciones deseables: aleatorio, repetición, cola de reproducción y reproducción continua al navegar entre vistas.

### 7.5 Derechos y uso de archivos

El prototipo debe utilizar audios que el usuario pueda usar legítimamente (propios, autorizados o con licencia apropiada). **Permitir subir un archivo no equivale a adquirir derechos de distribución pública**. Dream Radio no debe redistribuir bibliotecas ajenas ni prometer reproducción global sin licencias.

Si se envían audios a APIs externas, habrá que informar qué se envía, revisar sus condiciones de privacidad y permitir una política adecuada de consentimiento/activación. Se recomienda comenzar con un conjunto de audios de prueba controlados.

---

## 8. Inteligencia artificial y base de datos vectorial

### 8.1 Requisitos académicos no negociables

El proyecto **debe integrar una base de datos vectorial real** y **consumir al menos una API de inteligencia artificial**. La IA y los vectores deben cumplir funciones verificables y no aparecer solo como elementos decorativos en la presentación.

### 8.2 ¿Qué es un embedding en Dream Radio?

Una descripción de una canción, por ejemplo:

> «Electrónica ambiental, sintetizadores suaves, tempo moderado y sensación nostálgica».

Se convierte con un modelo de embeddings en una lista de números (**vector**). Las búsquedas del usuario pueden representarse de forma compatible y compararse para encontrar canciones cercanas semánticamente.

**Importante:** un embedding de una descripción textual **no es lo mismo que una representación obtenida directamente del sonido**. En el MVP se propone empezar por embeddings de descripciones enriquecidas. La precisión de la búsqueda depende de la calidad de esas descripciones y del modelo empleado.

### 8.3 Funciones previstas de la IA

**Función A — Interpretar peticiones:** comprender textos como «quiero música para una tarde lluviosa, pero electrónica y alegre».

**Función B — Describir y clasificar:** ayudar a producir descripciones estructuradas de canciones con base en metadatos y, cuando sea factible, análisis real de audio.

**Función C — Recomendar desde la biblioteca:** recuperar canciones relacionadas por similitud y mostrarlas al usuario.

**Función D — Explicar resultados:** mostrar una justificación basada en datos recuperados y no inventar rasgos musicales no registrados.

**Función E — Crear estaciones:** organizar grupos temáticos a partir de la intención del usuario.

**Función F — Aprender preferencias (progresivo):** utilizar favoritos, reproducciones, saltos o valoraciones para ajustar resultados. Es necesario implementar almacenamiento de eventos y reglas de recomendación antes de afirmar que Dream Radio aprende automáticamente.

**Función futura — Locutor de IA:** presentar canciones y comentar conexiones; la voz generada puede aplazarse para no ampliar demasiado el MVP.

### 8.4 Flujo sugerido de búsqueda semántica

```text
Usuario escribe una sensación
            ↓
Validación de la petición
            ↓
Interpretación mediante API de IA (si es útil)
            ↓
Generación de embedding de consulta
            ↓
Búsqueda de similitud en PostgreSQL + pgvector
            ↓
Filtrado de canciones que existen en la biblioteca
            ↓
Resultados ordenados + explicación fundamentada
            ↓
Reproducir canciones o crear estación
```

### 8.5 Persistencia de preferencias

Para personalizar recomendaciones de manera verificable, registrar según el alcance:

- Canciones marcadas como favoritas.
- Playlists creadas o editadas.
- Valoraciones explícitas opcionales.
- Historial de reproducción (si se decide almacenar).
- Saltos/omisiones, interpretados con cautela.

No se debe inferir una preferencia fuerte a partir de una sola escucha o utilizar colores/decoración del muro como evidencia automática de gusto musical sin diseñar y validar esa regla.

### 8.6 ¿RAG o agente?

La documentación del curso aborda **RAG, agentes y memoria**. Para Dream Radio:

- **Recuperación semántica:** es imprescindible y usa pgvector.
- **RAG:** es apropiado si una IA obtiene primero fichas o descripciones de la base y luego responde usando ese contexto; puede utilizarse en explicaciones musicales con evidencia recuperada.
- **Agente / LangGraph:** sería útil si se requiere elegir dinámicamente herramientas (identificar una canción, buscar en la biblioteca, consultar metadatos, generar estación); **no es obligatorio para que funcione la primera búsqueda vectorial**, salvo que el docente lo exija específicamente.

---

## 9. Arquitectura tecnológica propuesta

**Diferenciar requisitos confirmados y elecciones técnicas recomendadas.** Las tecnologías que aparecen como «propuestas» pueden cambiar tras comprobar las condiciones de clase, despliegue y compatibilidad.

| Componente | Tecnología o enfoque | Estado | Papel |
|---|---|---|---|
| Base de datos principal | PostgreSQL | Propuesta fuerte | Álbumes, canciones, playlists, usuarios locales si aplica, diseños y preferencias. |
| Búsqueda vectorial | PostgreSQL + extensión **pgvector** | **Requisito funcional a cumplir** | Guardar embeddings y consultar similitudes. |
| Inteligencia artificial | Al menos una **API de IA** | **Requisito obligatorio** | Analizar/interpretar y generar explicaciones estructuradas. |
| Backend | Python | Recomendado | Importación, API, procesamiento y conexión con BD. |
| Frontend visual | HTML, CSS y JavaScript | Recomendado | Biblioteca tipo pared, reproductor y editor de objetos. |
| Comunicación frontend/backend | API REST con JSON; backend como FastAPI por evaluar | Propuesto | Acceder a catálogo, preferencias, muros y consultas. |
| Orquestación LLM | LangChain | Opcional recomendado | Conectar IA, prompts y herramientas de recuperación. |
| Agentes | LangGraph | Ampliación posible | Flujos de decisión multi-herramienta. |
| Automatizaciones | n8n | Según exigencia curricular | Enriquecimiento de metadatos, importaciones u otros procesos repetibles. |
| Reconocimiento musical | AcoustID/MusicBrainz o ACRCloud | Por evaluar | Identificar grabaciones sin etiquetas. |
| Análisis directo de audio | API/modelo con capacidades de audio verificadas | Por seleccionar | Describir características acústicas. |
| Interfaz rápida alternativa | Streamlit | Alternativa, no decisión cerrada | Prototipo sencillo; evaluar limitaciones para arrastrar/rotar libremente objetos. |

**Decisión técnica recomendada:** si la experiencia de «pared editable» es central, **HTML/CSS/JavaScript ofrece mayor control de interacción** que una interfaz puramente basada en componentes estándar de Streamlit. Streamlit puede servir para experimentar la IA, pero no debe imponerse sin evaluar la experiencia de edición deseada.

### 9.1 Arquitectura lógica simplificada

```text
┌─────────────────────────────────────────────────────────┐
│ FRONTEND: Dream Radio                                  │
│ Inicio | Biblioteca | Reproductor/Muros | Explorar IA   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / JSON
                        ▼
┌─────────────────────────────────────────────────────────┐
│ BACKEND PYTHON                                          │
│ Catálogo | Archivos | Reproducción | Muros | Preferencias│
│ Búsqueda semántica | Integraciones con APIs de IA       │
└───────────────┬───────────────────────────┬─────────────┘
                │                           │
                ▼                           ▼
┌───────────────────────────┐    ┌────────────────────────┐
│ PostgreSQL + pgvector     │    │ APIs / modelos externos │
│ Música, muros, favoritos, │    │ IA, identificación y    │
│ descripciones, embeddings │    │ metadatos (si aplica)   │
└───────────────────────────┘    └────────────────────────┘
                │
                ▼
        Almacenamiento de
        audios e imágenes
```

**Nota:** la entrega de audio al navegador debe diseñarse de forma que permita reproducción y desplazamiento por la pista. La ubicación definitiva de almacenamiento de archivos y la estrategia para reproducirlos dependerán de si la aplicación corre localmente o en un servidor académico.

---

## 10. Modelo inicial de información (conceptual, no SQL definitivo)

Entidades o grupos de datos previsibles:

| Entidad | Información relevante |
|---|---|
| **Track / Canción** | ID, archivo, duración, título editable, artista/álbum, fuente de metadatos, descripción, estado de análisis. |
| **Artist / Artista** | ID, nombre e información opcional. |
| **Album / Álbum** | ID, título, artista(s), portada y colección de pistas. |
| **Playlist** | ID, nombre editable, apariencia (vinilo/imagen), conjunto ordenado de canciones. |
| **Wall / Muro** | ID, álbum asociado, configuración de fondo y datos de diseño. |
| **WallElement / Elemento decorativo** | ID, muro, archivo/imagen, tipo, posición, tamaño, rotación y orden. |
| **MediaAsset / Recurso visual** | Ruta o referencia a portada, póster, sticker, GIF o imagen propia. |
| **TrackEmbedding** | ID de canción, vector, modelo y versión/fuente de la descripción. |
| **Preference / Preferencia** | Favoritos, valoraciones y señales usadas para personalización. |
| **PlaybackEvent / Evento de escucha** | Pista, momento y tipo de evento, si se implementa seguimiento. |
| **AIRequest / Solicitud de IA** | Petición, resultados e información básica de diagnóstico, si se decide registrar. |

**Relaciones básicas:** un álbum contiene canciones; una playlist contiene varias canciones y una canción puede estar en distintas playlists; cada álbum tiene un muro en el MVP; un muro contiene varios elementos visuales; los embeddings están asociados a canciones y a la versión de datos con la que se generaron.

Las decisiones sobre cuentas de usuario, múltiples perfiles, archivos repetidos, álbumes desconocidos y normalización final **siguen pendientes**.

---

## 11. Requisitos funcionales sugeridos

Los siguientes identificadores sirven para planear y probar; **no equivalen a funcionalidades ya implementadas**.

| ID | Requisito | Prioridad propuesta |
|---|---|---|
| RF-01 | Importar al menos archivos MP3 válidos. | MVP |
| RF-02 | Mostrar biblioteca de álbumes, canciones y playlists. | MVP |
| RF-03 | Reproducir, pausar y desplazar el avance de una canción. | MVP |
| RF-04 | Buscar álbumes y canciones por texto. | MVP |
| RF-05 | Crear/renombrar playlists y cambiar su imagen o apariencia. | MVP |
| RF-06 | Mostrar el vinilo visual o la tarjeta de imagen para colecciones. | MVP |
| RF-07 | Abrir un muro independiente por álbum. | MVP |
| RF-08 | Cambiar fondo y añadir/mover/rotar/redimensionar/eliminar imágenes. | MVP |
| RF-09 | Guardar y recuperar el muro tras reiniciar la aplicación. | MVP obligatorio |
| RF-10 | Activar/desactivar edición de muro. | MVP recomendado |
| RF-11 | Registrar y editar metadatos ausentes o incorrectos. | MVP |
| RF-12 | Producir una descripción musical para indexación semántica. | MVP obligatorio para búsqueda |
| RF-13 | Almacenar embeddings y buscar con pgvector. | MVP obligatorio |
| RF-14 | Consumir API de IA en un flujo demostrable. | MVP obligatorio |
| RF-15 | Buscar canciones por sensaciones y mostrar resultados. | MVP |
| RF-16 | Presentar razones verificables para las recomendaciones. | MVP recomendado |
| RF-17 | Registrar favoritos y usarlos en recomendaciones. | MVP recomendado |
| RF-18 | Intentar reconocer canciones por huella acústica. | Segunda fase o MVP si el tiempo lo permite |
| RF-19 | Generar estaciones temáticas automáticas. | Segunda fase o MVP extendido |
| RF-20 | Incorporar reconocimiento enriquecido, voz del locutor y herramientas multiagente. | Futuro |

**Nota:** el análisis de audio directo tiene valor diferencial, pero su implementación dependerá del coste, acceso y calidad de APIs compatibles. El MVP vectorial puede construirse con un conjunto de descripciones verificadas/manuales si esa parte avanzada todavía no está disponible; debe declararse transparentemente durante la sustentación.

---

## 12. Requisitos no funcionales y límites de personalización

- **Persistencia:** muros, playlists y preferencias guardadas deben sobrevivir al cierre y reinicio de la aplicación.
- **Usabilidad:** controles de audio y buscador siempre accesibles; decoraciones no deben impedir pulsar botones.
- **Rendimiento:** limitar peso/tamaño y número de imágenes/GIFs, y no cargar todos los audios completos de la biblioteca al abrir la página.
- **Resiliencia:** si falla la API de IA o identificación, el reproductor y la biblioteca deben seguir funcionando.
- **Seguridad:** validar formatos y tamaños de archivos; no mostrar claves de API en frontend; utilizar consultas parametrizadas.
- **Privacidad:** proteger audios e información de preferencias y explicar el envío de contenido a proveedores externos.
- **Transparencia:** distinguir metadatos leídos, coincidencias verificadas e inferencias realizadas por IA.
- **Mantenibilidad:** módulos de reproducción, biblioteca, personalización e IA separados, con pruebas básicas.
- **Responsividad:** preservar, dentro de lo razonable, la composición de muros al cambiar el tamaño de ventana.
- **Costes:** acotar número de llamadas a APIs y duración de archivos analizados; revisar cuotas y límites del proveedor elegido.

**Límites explícitos de edición:** no permitir modificación irrestricta de cada píxel de los vinilos ni de la estructura fija de la aplicación; sí permitir libertad de posición, rotación y tamaño de imágenes dentro de áreas editables.

---

## 13. Recorridos de usuario esperados

### Escenario 1: Primera importación de una canción sin metadatos

1. Abro Dream Radio y voy a mi biblioteca.
2. Importo `audio1.mp3` sin título ni portada.
3. Veo un título provisional y una portada predeterminada.
4. La canción se puede reproducir aunque no se haya identificado.
5. El sistema intenta extraer metadatos; opcionalmente consulta reconocimiento acústico.
6. La IA analiza o describe características disponibles y genera material para búsqueda semántica.
7. Si no encuentra el nombre real, no lo inventa; puedo editarlo manualmente.

### Escenario 2: Decoración de un álbum

1. Abro un álbum desde la pared de la biblioteca.
2. Elijo «Editar pared».
3. Cambio el fondo, agrego un póster, lo arrastro, lo giro y lo redimensiono.
4. Bloqueo el diseño, escucho una canción y cierro Dream Radio.
5. Vuelvo a abrir el mismo álbum: el muro se reconstruye como lo dejé.
6. Abro otro álbum: aparece **su propia** pared, no la anterior.

### Escenario 3: Exploración por sensaciones

1. Entro en «Explorar con IA».
2. Escribo: «quiero algo que recuerde una tarde lluviosa, electrónico pero alegre».
3. Se transforma la petición en una consulta semántica.
4. pgvector encuentra canciones de mi biblioteca relacionadas.
5. Veo sugerencias y una explicación sustentada en descripciones guardadas.
6. Selecciono una sugerencia para reproducirla o construir una estación.

### Escenario 4: Personalización de una playlist

1. En la biblioteca selecciono una playlist de ejemplo.
2. La renombro.
3. Cambio la imagen central del vinilo o reemplazo la presentación visual por una imagen propia.
4. Guardo; al regresar, conserva su nombre y apariencia.

---

## 14. Etapas recomendadas de desarrollo

El proyecto puede ser grande conceptualmente, pero **debe construirse en incrementos verificables**.

### Fase 0 — Validación y diseño

- Definir el público de prueba y preparar una biblioteca musical de muestra con permisos adecuados.
- Diseñar wireframes de inicio, dashboard, álbum/muro e IA.
- Elegir cómo se almacenan archivos de audio e imágenes.
- Comprobar compatibilidad del reproductor con formatos reales.
- Revisar disponibilidad y condiciones de APIs de análisis/reconocimiento.

**Entregable:** flujo de pantallas, alcance cerrado del MVP y decisiones técnicas registradas.

### Fase 1 — Reproductor y biblioteca

- Importar MP3.
- Leer y editar metadatos.
- Organizar canciones/álbumes/playlists.
- Reproducir con controles básicos.
- Buscar por título, álbum o artista.

**Entregable:** biblioteca musical local funcional, aun sin IA.

### Fase 2 — Paredes y personalización persistente

- Dashboard con tarjetas/vinilos visuales.
- Muro independiente por álbum.
- Editor controlado: fondos, objetos arrastrables, rotación y tamaño.
- Guardado en PostgreSQL y restauración al abrir.
- Renombrar playlists y cambiar su apariencia.

**Entregable:** experiencia visual personalizable que persiste tras reiniciar.

### Fase 3 — IA y búsqueda vectorial

- Crear descripciones estructuradas para canciones.
- Obtener embeddings con un modelo apropiado.
- Configurar pgvector y comprobar consultas de similitud.
- Integrar al menos una API de IA.
- Buscar por sensaciones y explicar resultados.

**Entregable:** caso de uso que demuestre de extremo a extremo IA + búsqueda vectorial.

### Fase 4 — Preferencias y enriquecimiento

- Favoritos y señales básicas de preferencia.
- Mejoras de recomendación.
- Reconocimiento de pistas sin metadatos, cuando sea viable.
- Estaciones temáticas.

**Entregable:** personalización musical mejorada, no solo visual.

### Fase 5 — Ampliaciones opcionales

- Locutor con voz de IA.
- Agente con LangGraph y/o workflows de n8n, si aportan valor o son exigidos por la evaluación.
- Importación avanzada de formatos adicionales.
- Varios diseños por álbum.
- GIFs en línea con integración más elaborada.
- Compartir muros, sincronización multidispositivo y funciones sociales.

**Principio de implementación:** priorizar un prototipo completo y demostrable antes de aumentar el número de funcionalidades.

---

## 15. Pruebas y criterios de aceptación del MVP

| Caso | Prueba | Resultado esperado |
|---|---|---|
| CA-01 | Importar MP3 válido. | Aparece en biblioteca y puede reproducirse. |
| CA-02 | Importar archivo sin metadatos. | No falla; muestra valores provisionales editables. |
| CA-03 | Reproducir, pausar y buscar posición temporal. | El audio responde y la barra de progreso se sincroniza. |
| CA-04 | Crear o renombrar playlist. | El cambio permanece tras reiniciar. |
| CA-05 | Cambiar imagen de una playlist. | Se conserva la apariencia elegida. |
| CA-06 | Decorar álbum A y cerrar programa. | Su fondo y objetos reaparecen en posición y rotación guardadas. |
| CA-07 | Abrir álbum B tras decorar A. | No aparecen objetos de A en B. |
| CA-08 | Bloquear edición. | Los objetos no se mueven por interacciones normales de reproducción. |
| CA-09 | Buscar un álbum por nombre. | Aparece un resultado correcto de la biblioteca. |
| CA-10 | Crear embeddings y consultar pgvector. | Se obtienen canciones comparadas por similitud real. |
| CA-11 | Consultar por sensaciones. | Se devuelven pistas existentes con explicación basada en sus datos. |
| CA-12 | Simular fallo de API externa. | Se informa el error sin impedir reproducir música importada. |
| CA-13 | Probar una identificación fallida. | No se presenta título/artista inventado como información confirmada. |

Recomendación: conservar capturas, pruebas de funcionamiento, consultas reales y registros de errores/correcciones para justificar el proyecto durante su evaluación.

---

## 16. Riesgos y decisiones pendientes

Esta sección evita convertir recomendaciones en supuestos ya aprobados.

| Tema | Riesgo o pregunta | Dirección actual |
|---|---|---|
| Audio local vs. servidor | ¿Los archivos residirán en el PC o se subirán al servidor del prototipo? | **Pendiente.** Priorizar solución académica sencilla. |
| Formatos | ¿Soporte garantizado para WAV/FLAC/Ogg? | **Pendiente de pruebas.** MP3 primero. |
| Reconocimiento musical | Límites y costes de servicios de huella acústica. | **Por evaluar.** No bloquear el MVP. |
| Análisis directo de audio | Las APIs difieren en capacidades reales y coste. | **Por seleccionar y verificar.** |
| Portadas | Puede faltar álbum o no existir imagen disponible. | Usar portada predeterminada o personalizada; no inventar datos. |
| Muro y visualización | Riesgo de decoración excesiva o elementos fuera de pantalla. | Editor limitado, modo bloqueo, restablecimiento. |
| Personalización de playlists | ¿También tendrán muros independientes? | **No acordado;** por ahora el muro propio corresponde al álbum. |
| Usuarios | ¿Un solo usuario local o cuentas múltiples? | **Pendiente.** Para MVP, comenzar simple. |
| Historial | Privacidad y efecto real sobre las recomendaciones. | **Progresivo.** Favoritos primero. |
| Diseño adaptable | Elementos podrían moverse en pantallas distintas. | Preferir dimensiones/posiciones relativas y probar. |
| APIs externas | Dependencias, cuotas, privacidad y errores. | Diseñar fallbacks y proteger claves. |
| Framework frontend | Streamlit reduce trabajo inicial, pero puede limitar edición libre. | Preferencia técnica preliminar: web HTML/CSS/JS. |
| RAG/Agentes/n8n | El curso los estudia, pero su obligatoriedad específica debe confirmarse. | No añadirlos artificialmente; integrar si aportan valor o se exige. |
| Escala del catálogo | La personalización por álbum demanda almacenamiento y rendimiento. | Prototipo con tamaño controlado. |

---

## 17. Relación con la documentación académica

El documento de referencia aportado por el usuario es **`LangChain_LangGraph2026 (4).md`**, titulado *Desarrollo de Software Asistido por Inteligencia Artificial y Automatización Inteligente*.

Entre los contenidos y competencias relevantes se incluyen:

- Prompt Engineering, uso responsable y validación crítica de resultados de IA.
- Consumo de APIs REST, HTTP, JSON y manejo de errores.
- Integración de modelos generativos en aplicaciones y flujos.
- Automatizaciones y webhooks mediante n8n.
- Agentes, memoria, embeddings y recuperación semántica.
- PostgreSQL con **pgvector**, RAG, LangChain y LangGraph.
- Documentación, pruebas funcionales y sustentación técnica.

**Adaptación a Dream Radio:** estos contenidos ofrecen herramientas y criterios para construir el sistema; la propuesta del reproductor y de los muros es la **idea específica del proyecto**, no un requisito literalmente descrito en el material del curso.

En particular, la documentación del curso contempla un proyecto integrador llamado *DevFlow*; **queda pendiente confirmar si el docente autoriza Dream Radio como proyecto integrador alternativo y qué componentes técnicos exige exactamente en la entrega**.

---

## 18. Texto breve para presentar Dream Radio

> Dream Radio nace de una idea sencilla: escuchar música debería sentirse personal. Es un reproductor inteligente que permite importar una colección propia, reproducirla sin anuncios introducidos por la aplicación y convertir cada álbum en una pared visual única con imágenes, pósteres y fondos que permanecen guardados. Además, incorpora inteligencia artificial y una base de datos vectorial para analizar características musicales, buscar canciones por emociones o ambientes y descubrir nuevas conexiones dentro de la biblioteca. No busca reemplazar a los servicios de streaming; busca recuperar la experiencia de tener un espacio musical que realmente se sienta propio.

---

## 19. Definición final del concepto y siguiente paso

**Concepto acordado:**

> **Dream Radio = Biblioteca de música propia + Reproductor funcional + Paredes personalizables y persistentes + Exploración y recomendaciones mediante IA y búsqueda vectorial.**

**Prioridad del proyecto:** primero conseguir una experiencia básica, estable y personal: importar música, reproducirla, verla en una biblioteca estilo pared y conservar la decoración de cada álbum. Después incorporar la inteligencia artificial y comprobar que su función de análisis, búsqueda y recomendación realmente aporta valor.

**Siguiente paso lógico:** diseñar los wireframes de las cuatro experiencias principales (inicio, dashboard, reproductor/muro de álbum, sección de IA), cerrar el alcance del MVP con el docente y convertir estos requisitos en tareas de desarrollo incremental.

---

*Este documento recoge las ideas y acuerdos tratados durante la conversación sobre Dream Radio. Las tecnologías y funciones marcadas como propuestas, opciones o decisiones pendientes deben validarse antes de considerarse definitivas.*
