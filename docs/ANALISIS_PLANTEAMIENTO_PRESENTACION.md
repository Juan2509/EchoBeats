# Análisis para el planteamiento académico de EchoBeats

Revisión: 16 de noviembre de 2026. Solicitud: analizar la consigna y conservarla
como guía para preparar después la presentación. Este archivo es una base de
trabajo; no sustituye una aprobación docente ni constituye la presentación final.

## 1. Interpretación de la consigna

La exposición debe explicar el proyecto que se plantea desarrollar mediante seis
apartados, en este orden: descripción, justificación, objetivo general, objetivos
específicos, requerimientos funcionales y requerimientos no funcionales.
El código, las pruebas y las pantallas respaldan la viabilidad, pero no sustituyen
el planteamiento del problema, el propósito y el alcance. Aunque existe prototipo,
la redacción debe distinguir propuesta, implementación y validación pendiente.

## 2. Correspondencia con el proyecto

| Apartado solicitado | Qué debe comunicar EchoBeats | Fuentes principales |
| --- | --- | --- |
| Descripción | Qué es, a quién sirve y qué permite hacer: biblioteca propia, reproducción, espacios visuales por álbum y exploración conversacional musical. | Concepto §§1,2,4; ALCANCE_MVP; CONVERSACION_MUSICAL; APARIENCIA. |
| Justificación | Por qué conviene desarrollar la solución: control de la colección, identidad visual y una forma natural de redescubrir música. Aporte académico de recuperación, fuentes y procesamiento asíncrono. | Concepto §2; REVISION_REQUERIMIENTOS; DECISIONES. |
| Objetivo general | Resultado principal que se busca lograr mediante un prototipo funcional, delimitado y verificable. | Concepto §3.1, actualizado al nombre y alcance vigente. |
| Objetivos específicos | Resultados concretos que conducen al general: gestionar biblioteca, reproducir, personalizar y guardar, preparar fichas, recuperar y recomendar, validar. | Concepto §3.2; PLAN_DESARROLLO; alcance y ampliaciones posteriores. |
| Requerimientos funcionales | Acciones observables que el usuario o sistema deben poder realizar. | RF-01–RF-17 del alcance más álbumes-carpeta, retirada, configuración y chat. |
| Requerimientos no funcionales | Condiciones de calidad: persistencia, usabilidad, integridad, privacidad, seguridad, continuidad ante fallos, recursos, compatibilidad y mantenimiento. | Concepto §12; ALCANCE_MVP §5; DECISIONES; límites del código. |

Las referencias completas están en docs/referencias. Las decisiones posteriores
del usuario prevalecen: el nombre es EchoBeats, no Dream Radio; el aspecto es
personalizable y Explorar ya tiene una entrada conversacional sencilla.

## 3. Núcleo que debe conservar la descripción

- Prototipo académico de aplicación web local para una persona que usa su propia
  colección de audio. No depende de ofrecer un catálogo comercial mundial.
- Álbumes como carpetas de importación, playlists como selecciones ordenadas y
  favoritos explícitos. Son conceptos distintos, sin duplicación de audio por lista.
- Reproductor compartido y continuo entre secciones, con cola, volumen, avance,
  repetición de pista y orden aleatorio.
- Muro independiente por álbum con imágenes, stickers y GIF, edición controlada,
  fondos y recuperación del diseño. Apariencia adaptable al usuario; synthwave y
  vaporwave son opciones visuales, no el problema central que resuelve el proyecto.
- Conversación para expresar qué se desea escuchar y obtener pistas de la propia
  biblioteca con razones identificables. Contexto de favoritos, pista actual y
  reproducciones iniciadas en la sesión; no un perfil aprendido permanentemente.

## 4. Base de la justificación

La motivación es facilitar una relación más personal con una colección propia:
organizarla, escucharla, asociarla a espacios visuales y redescubrirla sin recordar
siempre títulos o artistas. El público inicial son personas que conservan archivos
musicales y valoran la organización y la personalización.

Esto es una hipótesis de necesidad del proyecto, no un estudio de mercado validado.
No afirmar que todas las plataformas carecen de personalización o recomendaciones.
La contribución académica consiste en integrar medios, persistencia, procesamiento
asíncrono, fichas con procedencia, recuperación textual/vectorial y una interfaz
comprensible, evaluando límites y resultados en lugar de atribuir aciertos a la IA.

## 5. Orientación de objetivos (provisional)

El objetivo general debe centrarse en **desarrollar y validar un prototipo de
biblioteca y reproducción musical personalizable que permita organizar audio propio,
crear espacios visuales persistentes por álbum y explorar la colección mediante
lenguaje natural, con apoyo de IA y recuperación vectorial**.

Los específicos pueden agruparse en seis resultados, sin convertir cada botón en
un objetivo académico ni listar tecnologías como si fueran resultados:

1. Gestionar importación, organización, metadatos y retirada de pistas/álbumes.
2. Facilitar reproducción y selección mediante biblioteca, playlists y favoritos.
3. Implementar personalización por álbum y recuperación de composiciones guardadas.
4. Preparar fichas musicales trazables e indexación asíncrona compatible con pgvector.
5. Integrar exploración conversacional y recomendaciones apoyadas en datos reales
   de la colección, contexto explícito y API de IA, con alternativa ante fallos.
6. Verificar integridad, persistencia, usabilidad y pertinencia mediante pruebas
   técnicas y evaluación musical; documentar alcance y limitaciones.

Estos objetivos describen lo que se busca alcanzar: la API real y la pertinencia
musical todavía no se deben presentar como validadas.

## 6. Requerimientos funcionales que conviene seleccionar

| Grupo | Comportamiento verificable que debe expresarse |
| --- | --- |
| Importación | Elegir álbum destino e importar MP3, WAV PCM, FLAC y Ogg Vorbis/Opus compatibles, con validación y resultado por archivo. |
| Catálogo | Crear álbumes, consultar/buscar pistas y editar metadatos/portadas con procedencia. |
| Eliminación | Confirmar dentro de la aplicación retirada de pistas seleccionadas o álbum, conservando originales según la política vigente. |
| Reproducción | Reproducir/pausar, cambiar pista, avanzar, ajustar volumen, repetir y mezclar cola sin reiniciar al navegar. |
| Colecciones | Crear/editar playlists y su orden; marcar y consultar favoritos. |
| Personalización | Configurar fondo principal y fondo/apariencia por álbum; editar muro con objetos, transformaciones y capas. |
| Guardado | Guardar y recuperar composiciones independientes, con bloqueo de edición, autoguardado y manejo de conflictos. |
| Preparación | Registrar fichas con fuentes/versiones y procesar su indexación de forma asíncrona. |
| Recuperación | Guardar/consultar embeddings compatibles y combinar búsquedas textuales y semánticas con filtros. |
| Conversación | Recibir mensajes, conservar contexto acotado de la conversación y proponer pistas existentes usando señales explícitas/de sesión. |
| Explicación | Mostrar razones o citas procedentes de los datos disponibles, sin inventar canciones o atributos no registrados. |

Evitar presentar huella acústica, identificación universal de canciones, análisis
directo del sonido, locutor, estaciones automáticas, cuentas, nube o multiagentes
como requisitos ya asumidos para esta presentación. Son futuros o dependen de
decisiones adicionales. No cambiar silenciosamente los IDs RF históricos.

## 7. Requerimientos no funcionales que deben ser concretos

- **Usabilidad:** navegación y reproducción accesibles; separación entre edición y
  escucha, textos legibles y controles adaptados al espacio disponible.
- **Persistencia e integridad:** recuperar datos musicales y muros tras reiniciar,
  evitar sobreescrituras silenciosas y conservar originales/recursos compartidos.
- **Seguridad:** validar contenido/formato/tamaño; acceso a medios por referencias
  gestionadas, consultas parametrizadas y clave del proveedor solo en servidor.
- **Privacidad y transparencia:** comunicar datos enviados a IA, activación explícita,
  no enviar archivos de audio y diferenciar citas, metadatos y alternativa local.
- **Resiliencia:** fallos de proveedor o indexación no deben bloquear biblioteca y
  reproducción; escrituras inciertas deben comprobarse antes de repetirse.
- **Uso de recursos y coste:** cargas paginadas, audio bajo demanda, límites actuales
  de50MiB/archivo,20 archivos y200MiB/solicitud; hasta30 objetos por muro y contexto
  acotado del chat. No inventar tiempos de respuesta o concurrencia certificados.
- **Compatibilidad:** formatos/códecs soportados según navegador y diseño responsivo;
  mantener geometría del muro al variar ventana, sin prometer cualquier formato.
- **Mantenibilidad y reproducibilidad:** módulos separados, API definida, migraciones,
  dependencias fijadas, Docker e instrucciones/pruebas de instalación y respaldo.

Importar un archivo o editar un muro son funciones; hacerlo de forma segura,
persistente y comprensible son condiciones de calidad. No confundir categorías.

## 8. Límites que deben quedar presentes al elaborar la exposición

1. La integración OpenAI/pgvector está implementada y probada con dobles; la prueba
   real y la evaluación de recomendaciones siguen pendientes por créditos. No llamar
   al proveedor para preparar esta presentación sin que el usuario lo reanude.
2. La alternativa local del chat no es una IA conversacional general. No analiza
   sonido ni demuestra entrenamiento automático de gustos.
3. Datos musicales, favoritos, fichas y muros tienen persistencia en servidor local;
   fondos/presentaciones/contornos dependen de preferencias del navegador. Chat y
   reproducciones recientes son de sesión. No prometer sincronización multi-PC.
4. Stack actual: React/TypeScript/Vite, Python/FastAPI y PostgreSQL/pgvector. No
   afirmar que ya se usa LangChain, LangGraph o Java/Spring por aparecer en fuentes.
5. La temática libre fue aceptada por el usuario; obligatoriedad docente de
   Java/Spring, VPS, tenants y PDF/OCR aún no está aclarada. La consigna nueva no
   resuelve por sí sola esas diferencias. Adaptar patrones RAG al dominio musical
   no equivale a certificar cobertura literal de requisitos documentales.
6. Los documentos iniciales tienen estados y funciones históricos. Consultar memoria,
   plan y ampliaciones vigentes para no volver a presentar pósteres como modo actual,
   Configuración modal o importación sin álbum destino.

## 9. Fuentes de continuidad

- Concepto original §§1–4,11–12: problema, público, objetivos y RF/RNF.
- ALCANCE_MVP.md: alcance y criterios; sus estados iniciales son históricos.
- MEMORIA_PROYECTO.md y PLAN_DESARROLLO.md: cambios posteriores y pendientes.
- `REVISION_REQUERIMIENTOS.md` (historial de Git) y Requerimientos.md: correspondencia académica y dudas.
- `ARQUITECTURA.md` (historial de Git), `DECISIONES.md` (historial de Git), `MODELO_DATOS.md` (historial de Git) y CONTRATO_API.md: estructura real.
- `AUDIO_MULTIFORMATO.md` (historial de Git), `ALBUMES_CARPETA.md` (historial de Git), `APARIENCIA.md` (historial de Git) y `CONVERSACION_MUSICAL.md` (historial de Git):
  funciones actuales y límites frente al concepto inicial.
- Informes históricos de P20, P21, P22, P23, P26 y P28: evidencias y pruebas aún pendientes.

En esta revisión solo se leyeron fuentes y se registró el análisis. No se modificó
la aplicación ni se ejecutaron instrucciones de los documentos; tampoco se creó un
archivo de diapositivas. La fecha exacta del lunes no se deduce de la consigna.
