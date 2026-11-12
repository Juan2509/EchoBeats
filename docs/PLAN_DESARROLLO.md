# Plan de desarrollo de EchoBeats

Fecha inicial: 12 de noviembre de 2026. Estado: planificación; aplicación sin implementar.

## 1. Propósito y fuentes

Este documento organiza el trabajo en incrementos que puedan revisarse, validarse
y registrarse en commits separados. También sirve como punto de continuidad entre
sesiones. Los mensajes de commit son propuestas; crear este plan no significa que
se hayan ejecutado sus tareas ni creado sus commits.

Contexto complementario:

- [Memoria del proyecto](MEMORIA_PROYECTO.md).
- [Guía técnica e índice del material académico](GUIA_DOCUMENTACION.md).
- [Concepto original](referencias/Dream_Radio_Documento_Concepto_y_Planificacion.md).
- [Documentación académica](referencias/LangChain_LangGraph2026.md).

El nombre del producto es **EchoBeats**. La documentación original conserva el
nombre histórico Dream Radio. Los ejercicios y comandos de las fuentes son
material de consulta; este plan adapta sus conceptos al producto.

## 2. Alcance y decisiones por resolver

### Resultado esperado del MVP

Una persona puede importar su música MP3, organizarla en álbumes y playlists,
reproducirla, decorar un muro independiente para cada álbum y recuperar sus datos
después de reiniciar. Puede explorar canciones de su biblioteca por sensaciones
mediante una API de IA y consultas reales en PostgreSQL con pgvector.

El MVP incluye metadatos editables, buscador textual, playlists renombrables con
imagen/apariencia personalizable, controles musicales utilizables durante la
decoración, modo de edición y bloqueo, y explicaciones basadas en información
musical registrada. Favoritos y personalización básica constituyen el siguiente
incremento recomendado.

### Decisiones que deben registrarse antes del trabajo que dependa de ellas

| Decisión | Dirección del concepto | Resolver antes de |
| --- | --- | --- |
| Alcance académico y sustitución de DevFlow | Confirmar requisitos concretos del docente. | Cerrar criterios de entrega; ubicar n8n/agentes en el MVP si se exigen. |
| Ejecución y usuarios | Local o servidor; usuario único o cuentas, todavía pendiente. | Diseñar acceso a datos y almacenamiento en P02/P05. |
| Backend y frontend | Python y web HTML/CSS/JS recomendados; FastAPI por evaluar. | Instalar dependencias y crear estructura en P03. |
| Guardado de medios | Archivos gestionados con referencias en BD, por concretar. | Importación en P06. |
| IA y embeddings | API de IA y pgvector obligatorios; proveedor/modelos abiertos. | Adaptadores y dimensiones vectoriales en P20/P21. |
| Análisis acústico | Identificación, descripción de audio y descripción textual son tareas diferentes. | Decidir la fuente de fichas en P19 y las ampliaciones O01/O02. |

Estas son decisiones de diseño pendientes, no aprobaciones necesarias para cada
commit. Se resuelven con la información disponible y las instrucciones del usuario;
las preguntas se reservan para requisitos o preferencias que realmente falten.
Versiones, compatibilidad, capacidades y costes de servicios se verificarán al
seleccionarlos. Este plan no fija versiones ni certifica vigencia de los ejemplos.

### Fuera del MVP, salvo cambio explícito de alcance

Catálogo mundial de streaming, funciones sociales, sincronización multidispositivo,
muros independientes por playlist, varios diseños por álbum, locutor de IA,
soporte garantizado de todos los formatos y reconocimiento universal de canciones.
LangGraph y n8n quedan sujetos a utilidad y exigencia docente; no reemplazan el
trabajo básico de biblioteca, persistencia y recuperación vectorial.

## 3. Cómo trabajar y retomar sesiones

1. Leer `AGENTS.md`, esta planificación y la memoria; revisar el estado de Git.
2. Consultar el registro de continuidad al final y elegir el primer bloque pendiente
   cuyas dependencias estén satisfechas.
3. Marcar el bloque como «En curso» en el registro, implementar su alcance y
   comprobar su criterio de cierre. Añadir pruebas de lógica, persistencia o
   integración cuando aporten evidencia; registrar las comprobaciones visuales.
4. Revisar el diff y preparar únicamente los archivos relacionados con ese cambio.
   Respetar modificaciones y eliminaciones del usuario ajenas al bloque.
5. Al registrar el commit, anotar su hash, validaciones y pendientes en el registro.
   Marcar la casilla del bloque solo cuando se haya cumplido su criterio de cierre.
6. Dejar el siguiente paso y las decisiones nuevas por escrito. Si una tarea queda
   incompleta, registrar exactamente qué funciona y qué falta.

Cada bloque propone un commit con un objetivo coherente. Si el cambio crece,
dividirlo en commits menores que mantengan un estado comprensible y verificable.
Los ajustes pequeños de documentación y pruebas del bloque pueden acompañar al
mismo commit. Evitar juntar distintas fases en un único commit.

Formato sugerido: `tipo(ambito): descripción`, por ejemplo
`feat(player): permitir avanzar dentro de una pista`. Tipos habituales: `docs`,
`chore`, `feat`, `fix`, `refactor` y `test`. No se impone una herramienta de ramas.

## 4. Fase 0 — Alcance, experiencia y arquitectura

**Entrega de fase:** especificación inicial revisable y decisiones suficientes
para comenzar, manteniendo identificados los puntos aún abiertos.

### [x] P00 — Conservar el contexto y este plan

**Commit:** `docs(project): registrar concepto, referencias y plan de EchoBeats`

- Organizar memoria, índice técnico, fuentes originales y planificación.
- Identificar requisitos obligatorios, propuestas y ampliaciones.
- Enlazar los documentos desde las instrucciones de contexto del repositorio.

**Cierre:** documentos accesibles y coherentes con el nombre EchoBeats.
Registrado en el commit `0ee2b43`.

### [x] P01 — Delimitar MVP y criterios de aceptación

**Depende de:** P00. **Commit:** `docs(scope): definir alcance y aceptación del MVP`

- Crear `docs/ALCANCE_MVP.md` con las funciones incluidas y aplazadas.
- Vincular RF-01 a RF-20 y CA-01 a CA-13 del concepto al alcance elegido.
- Registrar requisitos docentes conocidos y los que falten por confirmar;
  preparar una colección de prueba con procedencia y permisos documentados.

**Cierre:** cada función incluida tiene un resultado observable; lo desconocido
no figura como confirmado. La parte académica pendiente queda identificada.

**Resultado:** [alcance del MVP](ALCANCE_MVP.md) con RF-01 a RF-20, CA-01 a
CA-13 y siete comprobaciones complementarias. Colección técnica sintética real
en `pruebas/coleccion/`, con generador y manifiesto de procedencia/hashes.
MP3, metadatos, duplicado y enlaces comprobados. La colección musical autorizada
para evaluación semántica se preparará en P17. Registrado en `bb10254`.

### [x] P02 — Diseñar pantallas, datos y decisiones técnicas

**Depende de:** P01. **Commit:** `docs(design): definir flujos, arquitectura y modelo inicial`

- Dibujar inicio, biblioteca, álbum/reproductor/muro y exploración con IA,
  incluyendo estados vacíos, carga, error y ventanas de distintos tamaños.
- Registrar elección de stack, modo de ejecución, usuarios y gestión de archivos
  en `docs/DECISIONES.md`; justificar opciones sin convertir recomendaciones en hechos.
- Definir entidades, relaciones y contratos iniciales de API; delimitar área
  decorable y estrategia de coordenadas, tamaño, rotación y guardado.

**Cierre:** se puede recorrer importación → reproducción → decoración → búsqueda
en los diseños; álbumes y playlists se distinguen y los controles quedan accesibles.

**Resultado:** [decisiones](DECISIONES.md), [wireframes y flujos](DISENO_PANTALLAS.md),
[modelo de datos](MODELO_DATOS.md) y [contrato de API](CONTRATO_API.md).
Definidos ejecución local de un usuario, stack, archivos gestionados, duplicados,
continuidad del reproductor, lienzo proporcional y guardado con revisión.
Diseño revisado; sin interfaz ejecutable ni endpoints todavía. Implementado sin commit.

## 5. Fase 1 — Base técnica reproducible

**Entrega de fase:** interfaz, backend, base de datos y almacenamiento inicial
arrancan con instrucciones documentadas.

### [ ] P03 — Crear estructura y configuración de desarrollo

**Depende de:** P02. **Commit:** `chore(setup): preparar estructura y entorno de desarrollo`

- Crear estructura de frontend, backend, pruebas y documentación según el stack elegido.
- Declarar dependencias compatibles y estrategia para reproducir su instalación.
- Añadir `.gitignore`, `.env.example` sin secretos y un README de arranque;
  excluir medios privados, entornos, datos generados y credenciales.

**Cierre:** el entorno se puede instalar siguiendo el README y no se versionan
claves ni archivos personales de prueba. No instalar siguiendo ciegamente ejemplos.

### [ ] P04 — Preparar PostgreSQL y extensión vectorial

**Depende de:** P03. **Commit:** `chore(database): preparar PostgreSQL con pgvector`

- Configurar un servidor que disponga de la extensión y almacenamiento duradero.
- Añadir mecanismo de migraciones y configuración de conexión.
- Comprobar conexión y activación de `vector`; documentar arranque, parada y
  respaldo/restauración sin borrar datos durante el arranque normal.

**Cierre:** conexión real, extensión comprobada y persistencia tras reiniciar.
La tabla de embeddings espera a la elección de modelo en P20/P21.

### [ ] P05 — Crear esquema de biblioteca y almacenamiento

**Depende de:** P04. **Commit:** `feat(catalog): crear modelo persistente de biblioteca y recursos`

- Crear migraciones para artistas, álbumes, pistas, playlists, su orden y recursos.
- Definir integridad de relaciones, álbum desconocido, procedencia de metadatos,
  identificación de archivos y política de duplicados.
- Preparar almacenamiento de audio/imágenes y acceso seguro a referencias;
  si se eligieron cuentas, aplicar propiedad y aislamiento desde este bloque.

**Cierre:** migraciones funcionan en una BD vacía y las relaciones conservan
integridad. La aplicación no acepta rutas arbitrarias del sistema como recursos.

## 6. Fase 2 — Biblioteca, reproductor y playlists

**Entrega de fase:** colección musical utilizable sin depender de la IA.

### [ ] P06 — Importar y almacenar MP3

**Depende de:** P05. **Commit:** `feat(import): importar archivos MP3 a la biblioteca`

- Implementar selección/carga individual y múltiple con resultados por archivo.
- Validar tipo real, tamaño y lectura básica; aplicar la política de duplicados.
- Coordinar registro en BD y guardado del archivo; tratar fallos parciales y
  evitar registros que apunten a archivos que nunca se guardaron.

**Cierre:** MP3 válido se conserva tras reiniciar; archivo inválido se rechaza
con un mensaje útil y no impide importar otros válidos. Cubre CA-01 parcialmente.

### [ ] P07 — Extraer y editar metadatos

**Depende de:** P06. **Commit:** `feat(metadata): extraer etiquetas y permitir edición manual`

- Leer título, artista, álbum, duración y portada cuando estén disponibles.
- Mostrar valores provisionales y portada predeterminada cuando falten datos.
- Permitir corregir datos y agrupación de álbum, guardando su procedencia;
  proteger correcciones manuales frente a enriquecimientos posteriores.

**Cierre:** un MP3 sin etiquetas no rompe la biblioteca y sus cambios manuales
persisten. Cubrir CA-02 y RF-11.

### [ ] P08 — Construir navegación y biblioteca visual

**Depende de:** P07. **Commit:** `feat(library): mostrar biblioteca visual y búsqueda textual`

- Implementar inicio, navegación y dashboard a partir de P02.
- Mostrar álbumes y pistas con imágenes reales o predeterminadas; resolver
  estados vacíos, carga y error sin datos ficticios presentados como importados.
- Buscar por título, álbum y artista; abrir un álbum y mostrar sus pistas.

**Cierre:** lo importado aparece correctamente y una búsqueda localiza el álbum
esperado. Cubrir RF-02, RF-04 y CA-09.

### [ ] P09 — Entregar audio y permitir avance temporal

**Depende de:** P07. **Commit:** `feat(audio): servir pistas con soporte de avance temporal`

- Implementar acceso a archivos según la estrategia elegida y servir tipo/duración adecuados.
- Resolver solicitudes parciales de audio cuando el mecanismo de entrega lo requiera.
- Tratar pista inexistente, recurso inaccesible y archivo perdido sin exponer rutas internas.

**Cierre:** el navegador reproduce una pista real y puede solicitar un punto
intermedio sin cargar toda la biblioteca. Verificar una respuesta parcial si aplica.

### [ ] P10 — Integrar reproductor y estado musical

**Depende de:** P08, P09. **Commit:** `feat(player): integrar controles y selección de pistas`

- Implementar reproducir/pausar, anterior/siguiente, avance y volumen.
- Sincronizar pista activa, portada, título, duración y progreso, incluido fin de pista.
- Definir comportamiento al navegar y ante errores de audio; añadir estados
  accesibles de controles y comprobar reproducción continua si se incluyó en P01.

**Cierre:** los controles responden con audio real y no muestran datos de otra
pista. Completar CA-01 y CA-03; comprobar límites de inicio/final de la lista.

### [ ] P11 — Gestionar playlists y su apariencia

**Depende de:** P08, P10. **Commit:** `feat(playlists): gestionar listas e imagen de vinilo`

- Crear y renombrar playlists; añadir, quitar y ordenar canciones.
- Permitir imagen central de vinilo o apariencia de imagen según el diseño;
  validar archivos visuales y ofrecer recursos predeterminados.
- Guardar nombre, pistas, orden y apariencia; reproducir la selección de la lista.

**Cierre:** cerrar/reabrir conserva los cambios; editar playlists no cambia la
pertenencia de pistas a álbumes. Cubrir CA-04, CA-05, RF-05 y RF-06.

## 7. Fase 3 — Muros por álbum y personalización persistente

**Entrega de fase:** cada álbum recupera su composición después de reiniciar.

### [ ] P12 — Persistir un muro independiente por álbum

**Depende de:** P05, P08. **Commit:** `feat(walls): crear muros persistentes por álbum`

- Crear migraciones y contratos de muro/fondo/elementos con relación al álbum.
- Guardar IDs, referencias visuales, posición, dimensiones, rotación y orden;
  validar valores, recursos y versión del formato de composición.
- Cargar un diseño inicial para álbumes sin personalización y guardar cambios
  mediante una operación consistente.

**Cierre:** guardar y recuperar A no altera B, incluso al reiniciar el backend.
Añadir comprobación de integración de aislamiento y persistencia.

### [ ] P13 — Mostrar el muro y sus modos de edición

**Depende de:** P10, P12. **Commit:** `feat(wall-editor): mostrar composición y modos de edición`

- Componer panel de información, reproductor y área decorable del álbum.
- Implementar «Editar pared», «Bloquear diseño» y cambio de fondo de color.
- Renderizar recursos guardados y asegurar que las decoraciones no bloqueen
  navegación, pistas ni controles musicales.

**Cierre:** abrir álbumes muestra el fondo correcto y en modo bloqueado los
objetos no se desplazan. Cubrir CA-08.

### [ ] P14 — Añadir, mover y eliminar recursos visuales

**Depende de:** P13. **Commit:** `feat(wall-editor): añadir y mover elementos decorativos`

- Importar imágenes, stickers, pósteres y GIFs locales compatibles con límites definidos.
- Seleccionar, arrastrar y eliminar objetos dentro del área permitida.
- Conservar referencias estables y definir límites de peso, cantidad y dimensiones.

**Cierre:** los objetos se manipulan solo durante la edición y un recurso inválido
no rompe el muro. Comprobar GIF local y alternativa de manejo por teclado.

### [ ] P15 — Rotar, redimensionar y ordenar elementos

**Depende de:** P14. **Commit:** `feat(wall-editor): transformar y ordenar elementos del muro`

- Añadir rotación y redimensionamiento con mínimos/máximos y controles utilizables.
- Gestionar superposición sin permitir cubrir la estructura protegida.
- Aplicar el sistema de coordenadas de P02 y comprobar cambios de ventana.

**Cierre:** posición, tamaño, ángulo y orden se serializan y reconstruyen sin
saltos inesperados; los elementos siguen siendo recuperables en ventanas pequeñas.

### [ ] P16 — Completar guardado, restauración y restablecimiento

**Depende de:** P12–P15. **Commit:** `feat(walls): guardar y restaurar diseños completos`

- Guardar al finalizar acciones significativas y mostrar pendiente/guardando/guardado/error.
- Evitar que una respuesta atrasada sobrescriba cambios recientes o el muro de otro álbum.
- Resolver navegación con cambios sin guardar, fallo de guardado y restablecimiento
  persistente del diseño, con recuperación o confirmación de pérdida cuando corresponda.

**Cierre:** decorar A, guardar, cerrar/reabrir y abrir B cumple CA-06 y CA-07.
Probar respuesta de red tardía y fallo de escritura; completar RF-07 a RF-10.

## 8. Fase 4 — Fichas musicales, API de IA y pgvector

**Entrega de fase:** búsqueda musical semántica completa con evidencia de API real
y consultas vectoriales sobre canciones existentes.

### [ ] P17 — Definir casos de búsqueda y evaluación

**Depende de:** P01, P07. **Commit:** `docs(ai): definir consultas y criterios de recuperación musical`

- Preparar consultas por ambiente, instrumentos, energía y similitud con una pista.
- Asociar resultados pertinentes esperados y casos sin evidencia suficiente.
- Fijar cómo evaluar relevancia, calidad de explicaciones y comportamiento ante fallos;
  no presentar distancias como porcentajes de confianza.

**Cierre:** existe un conjunto reproducible de consultas sobre la biblioteca de
prueba, antes de ajustar los prompts o elegir resultados favorables.

### [ ] P18 — Incorporar estados de procesamiento musical

**Depende de:** P07. **Commit:** `feat(analysis): registrar estados y reintentos de procesamiento`

- Registrar pendiente, procesando, completado y error, además de versión de entrada.
- Elegir ejecución desacoplada apropiada al prototipo; evitar bloquear la reproducción.
- Permitir reintento y proteger frente a resultados duplicados o antiguos;
  definir qué sucede si la app se cierra durante el procesamiento.

**Cierre:** una tarea interrumpida o fallida no deja la canción inaccesible ni
requiere volver a importar el archivo para reintentar.

### [ ] P19 — Crear fichas musicales estructuradas y trazables

**Depende de:** P17, P18. **Commit:** `feat(descriptions): guardar fichas musicales con procedencia`

- Definir campos, validación y fuente de cada descripción: manual/verificada,
  metadatos o análisis de audio cuando exista un servicio seleccionado.
- Permitir preparar/corregir fichas de la colección de prueba sin inventar rasgos.
- Versionar la descripción y señalar si un cambio exige regenerar el embedding.

**Cierre:** las fichas diferencian información disponible e inferencias; una
ficha incompleta no impide reproducir y no se anuncia análisis acústico inexistente.

### [ ] P20 — Integrar proveedor de IA y configuración

**Depende de:** P19. **Commit:** `feat(ai): integrar API con respuestas validadas y manejo de fallos`

- Seleccionar y documentar proveedor/modelos, capacidades, credenciales y límites
  verificados; definir adaptadores para generación y embeddings según lo elegido.
- Incorporar validación estructurada, tiempos máximos, tratamiento de cuotas y
  reintentos acotados; mantener claves en backend y diagnósticos sin secretos.
- Probar una llamada real controlada y documentar qué datos salen de la aplicación;
  separar uso normal de pruebas automáticas que no deben consumir saldo.

**Cierre:** existe evidencia de consumo real de API y de respuesta inválida/fallo
gestionados. Los dobles de prueba no se presentan como integración real.

### [ ] P21 — Generar y almacenar embeddings reales

**Depende de:** P04, P19, P20. **Commit:** `feat(embeddings): indexar fichas musicales en pgvector`

- Crear migración vectorial con dimensiones coherentes con el modelo/configuración.
- Generar embeddings de fichas y almacenar pista, modelo, versión y estado.
- Evitar regeneración de entradas sin cambios y definir reindexación al cambiar
  modelo/configuración; no comparar espacios vectoriales incompatibles.

**Cierre:** vectores reales persisten en PostgreSQL y la indexación repetida no
duplica registros. Editar una ficha deja claro cuándo su vector está desactualizado.

### [ ] P22 — Implementar recuperación semántica

**Depende de:** P17, P21. **Commit:** `feat(search): buscar canciones por similitud con pgvector`

- Generar embedding de consulta compatible y ejecutar búsqueda parametrizada.
- Recuperar pistas existentes, limitar resultados y aplicar filtros de biblioteca;
  calibrar tratamiento de coincidencias débiles con las consultas de P17.
- Añadir similitud desde una canción si se incluyó en P01 y evaluar primero la
  búsqueda exacta; incorporar ANN únicamente si volumen/medición lo justifican.

**Cierre:** consultas reales de pgvector devuelven resultados pertinentes y
tratan catálogo vacío/no indexado o falta de coincidencias útiles. Cubrir CA-10.

### [ ] P23 — Integrar exploración con IA y explicaciones fundamentadas

**Depende de:** P10, P20, P22. **Commit:** `feat(explore): buscar por sensaciones y explicar recomendaciones`

- Construir la sección separada con consulta, estados, resultados y reproducción.
- Usar las fichas recuperadas como contexto para explicaciones; validar que cada
  resultado y afirmación se vinculen a datos disponibles, con alternativa basada
  en esos datos si falla la generación.
- Ejecutar el flujo completo: petición → API/embedding → pgvector → fichas →
  explicación → reproducción; mantener operativos biblioteca y audio ante fallos.

**Cierre:** cubrir CA-11 y CA-12 y completar RF-12 a RF-16 según P01.
Guardar evidencia de ejecución real; declarar la fuente de las descripciones.

## 9. Fase 5 — Preferencias y recomendación progresiva

**Prioridad:** incremento recomendado después del núcleo del MVP, o parte de este
si así se cerró en P01.

### [ ] P24 — Guardar favoritos

**Depende de:** P10, P05. **Commit:** `feat(favorites): guardar y consultar canciones favoritas`

- Crear persistencia y controles para marcar/desmarcar favoritos.
- Mostrar estado coherente entre biblioteca, reproductor y exploración.
- Aplicar propiedad por usuario si existen cuentas y conservar el cambio tras reiniciar.

**Cierre:** favorito y desmarcado sobreviven al reinicio y se reflejan en todas
las vistas. No se registra historial de escucha sin haber definido ese alcance.

### [ ] P25 — Personalizar recomendaciones con señales explícitas

**Depende de:** P22–P24. **Commit:** `feat(recommendations): incorporar favoritos al orden de resultados`

- Definir una regla sencilla y documentada para usar favoritos en la recuperación
  u ordenación; conservar relación con la intención actual de búsqueda.
- Resolver usuario sin favoritos y evitar que siempre se recomienden las mismas pistas.
- Comparar consultas con/sin preferencias y explicar qué señal cambió los resultados.

**Cierre:** hay efecto comprobable y justificable; no se afirma entrenamiento
automático ni se usan decoraciones como evidencia de gusto. Cubrir RF-17.

## 10. Fase 6 — Integración, calidad y entrega académica

Las validaciones de cada bloque se ejecutan durante su implementación. Esta fase
comprueba que los recorridos completos funcionan juntos y prepara la entrega.

### [ ] P26 — Verificar recorridos completos y recuperación ante fallos

**Depende de:** P11, P16, P23; P25 si forma parte de la entrega.
**Commit:** `test(integration): verificar recorridos y persistencia del MVP`

- Ejecutar CA-01 a CA-12 en un entorno reproducible, con énfasis en reinicio
  real, aislamiento de muros, seek de audio y errores de proveedor.
- Registrar CA-13 como aplazado si no se implementó identificación; si existe,
  comprobar que el fallo no produce metadatos inventados.
- Automatizar los recorridos críticos que aporten valor; documentar verificaciones
  manuales de audio, arrastre, rotación y distintos tamaños de ventana.

**Cierre:** matriz de aceptación con resultado, evidencia y limitaciones reales.
Los defectos detectados se corrigen en commits `fix` concretos antes del cierre.

### [ ] P27 — Revisar accesibilidad, recursos y protección de datos

**Depende de:** P26. **Commit:** `fix(quality): resolver hallazgos de la revisión del MVP`

- Revisar teclado, foco, etiquetas y legibilidad; comprobar controles de audio
  accesibles con muros densos y preferencia de movimiento si se incorporan animaciones.
- Medir con la biblioteca de prueba: carga de imágenes/GIFs, audio bajo demanda,
  consultas, límites de archivos y llamadas de IA; corregir cuellos observados.
- Verificar secretos fuera del cliente/repositorio/logs, validación de recursos,
  consultas parametrizadas y acceso según el modo de usuarios elegido.

**Cierre:** hallazgos registrados y resueltos o limitados explícitamente; no se
declara preparación comercial a partir de una revisión del prototipo.
Si no hay correcciones, registrar únicamente la evidencia en un commit `docs`.

### [ ] P28 — Documentar arranque y preparar demostración

**Depende de:** P26, P27 y requisitos académicos aplicables.
**Commit:** `docs(delivery): documentar instalación, arquitectura y demostración`

- Actualizar README, decisiones, configuración, migraciones, almacenamiento y
  restauración; comprobar instrucciones desde un entorno limpio.
- Crear guía de demostración: importar, reproducir, personalizar A/B, reiniciar,
  buscar por sensaciones y mostrar API/vector real y manejo de fallos.
- Documentar limitaciones, fuentes de audios/recursos, pruebas, arquitectura,
  modelos/configuración y explicación técnica de los componentes implementados.

**Cierre:** otra persona puede iniciar el prototipo y repetir la demostración;
la documentación corresponde al código y la matriz de requisitos está actualizada.

## 11. Ampliaciones condicionadas

Estos bloques no se marcan como pendientes del MVP por defecto. Se habilitan al
acordar su alcance o confirmar que la evaluación los exige. Entonces se detallan
sus dependencias y criterios igual que los bloques principales.

| ID | Trabajo y commit sugerido | Condición de finalización |
| --- | --- | --- |
| O01 | Reconocimiento por huella y metadatos externos. `feat(recognition): identificar grabaciones mediante huella acústica` | Servicio verificado, coincidencias trazables y fallo sin identidad inventada; CA-13. |
| O02 | Análisis directo de audio. `feat(audio-analysis): describir características mediante un modelo de audio` | Capacidad real comprobada, envío controlado, límites de duración/coste y distinción entre inferencia y metadato. |
| O03 | Estaciones temáticas. `feat(stations): crear listas desde una intención musical` | Solo canciones existentes, selección ordenada reproducible y opción de guardado definida. |
| O04 | Automatización con n8n. `feat(automation): automatizar enriquecimiento musical con n8n` | Caso útil definido, webhook validado, tareas idempotentes, reintentos y workflow exportado sin secretos. |
| O05 | Orquestación con LangGraph. `feat(agent): coordinar herramientas musicales mediante un grafo` | Herramientas delimitadas, estado y persistencia definidos, límites de ejecución y evaluación de decisiones/fallos. |
| O06 | Formatos adicionales. `feat(import): admitir formatos de audio adicionales verificados` | Validación, metadatos, reproducción y avance probados por cada formato anunciado. |
| O07 | Fondo de imagen y decoración del dashboard. `feat(customization): ampliar fondos y decoración de biblioteca` | Persistencia y límites visuales sin interferir con navegación; recursos compatibles validados. |
| O08 | Aleatorio, repetición y cola avanzada. `feat(player): ampliar modos y cola de reproducción` | Comportamiento definido en fin de lista, cambios de vista y cambios manuales de canción. |
| O09 | Locutor de IA. `feat(narration): presentar canciones mediante voz generada` | Contenido basado en datos y controles/costes definidos; no bloquea el reproductor. |

Si n8n o LangGraph son obligatorios, reubicar O04/O05 antes de P26, actualizar
P01 y comprobarlos en la entrega. No esperar al final para descubrir esa exigencia.

## 12. Hitos y dependencias principales

| Hito | Bloques | Evidencia observable |
| --- | --- | --- |
| H0 — Diseño inicial | P00–P02 | Alcance, pantallas, arquitectura y decisiones registradas. |
| H1 — Base reproducible | P03–P05 | Entorno y BD arrancan; extensión vectorial disponible. |
| H2 — Música propia | P06–P11 | Importar, buscar, escuchar y editar playlists con persistencia. |
| H3 — Espacio personal | P12–P16 | Muros A/B independientes recuperados tras reiniciar. |
| H4 — Exploración inteligente | P17–P23 | API real y pgvector sustentan búsqueda y explicaciones. |
| H5 — Preferencias | P24–P25 | Favoritos guardados cambian recomendaciones de forma explicable. |
| H6 — Entrega | P26–P28 | Aceptación revisada, instrucciones reproducidas y demostración preparada. |

El orden de lectura de los bloques es la ruta sugerida. Sus dependencias permiten
ajustes: por ejemplo, P17 puede prepararse después de la biblioteca, y los favoritos
pueden guardarse antes de integrar IA. En cualquier ruta, H2 y H3 deben funcionar
sin servicios de IA disponibles.

## 13. Registro de continuidad entre sesiones

Actualizar este registro al terminar cada sesión. Estados: Pendiente, En curso,
Implementado sin commit, Completado o Bloqueado por una dependencia concreta.
Una casilla marcada significa que se cumplió el criterio de cierre, no solo que
se crearon archivos. Las ampliaciones se habilitan expresamente en el registro.

### Estado actual

- **Última actualización:** 12 de noviembre de 2026.
- **Trabajo actual:** P02 terminado en diseño y arquitectura, sin commit.
- **Aplicación:** sin implementación.
- **Próximo bloque:** P03 — crear estructura y configuración de desarrollo.
- **Decisiones de trabajo:** local de un usuario, React/TypeScript/Vite,
  Python 3.12/FastAPI y PostgreSQL/pgvector; archivos copiados a MEDIA_ROOT.
- **Decisiones pendientes:** proveedores/modelos de IA, versiones exactas,
  selección musical autorizada y requisitos docentes; ver `DECISIONES.md`.
- **Ampliaciones habilitadas:** ninguna por ahora.
- **Estado de Git al iniciar P02:** sin cambios pendientes; P01 registrado en
  `bb10254`. No se creó un commit al terminar P02; se propone su mensaje al usuario.
- **Alcance concretado:** RF-01 a RF-16 incluidos; RF-17 posterior recomendado;
  RF-18 a RF-20 aplazados. CA-13 condicional al reconocimiento.
- **Validación de P01:** cobertura completa de IDs, enlaces locales, hashes y
  tamaños de siete archivos; cuatro MP3 originales decodificados con señal y
  etiquetas esperadas. Sin aplicación todavía para ejecutar aceptación funcional.
- **Validación de P02:** enlaces, ejemplos JSON y geometría ilustrativa del muro;
  revisión de coherencia entre rutas, relaciones y recorridos. Fuentes oficiales
  consultadas para capacidades técnicas; dependencias aún no instaladas/probadas.
- **Preferencia del usuario:** terminar cada paso con una sugerencia de mensaje
  de commit en español; mantener esta práctica en futuras sesiones.

### Bitácora

| Fecha | Bloque | Estado | Commit | Validación y siguiente paso |
| --- | --- | --- | --- | --- |
| 2026-11-12 | P00 | Completado | `0ee2b43` | Fuentes, memoria y plan registrados; continuado en P01. |
| 2026-11-12 | P01 | Completado | `bb10254` | Alcance, matrices y colección sintética registrados. |
| 2026-11-12 | P02 | Implementado sin commit | — | Pantallas, decisiones, datos y API definidos y revisados; siguiente: P03. |

### Plantilla de cierre de sesión

```md
Fecha:
Bloque(s) trabajado(s):
Estado y casillas actualizadas:
Cambios y decisiones:
Validaciones ejecutadas y resultados:
Commit(s), si se crearon:
Pendientes o dependencias:
Siguiente acción concreta:
```
