# Alcance y aceptación del MVP de EchoBeats

Fecha: 12 de noviembre de 2026. Entregable de P01.
Estado: alcance de trabajo definido a partir del concepto; validación docente pendiente.
La aplicación todavía no está implementada y las pruebas funcionales no se han ejecutado.

## 1. Objetivo de la primera entrega

Demostrar un recorrido completo: importar música MP3 propia, organizarla y
reproducirla; personalizar un muro independiente por álbum y recuperarlo al
reiniciar; buscar canciones de la biblioteca por sensaciones utilizando una API
de IA y consultas reales en PostgreSQL con pgvector.

Referencias: [concepto original](referencias/Dream_Radio_Documento_Concepto_y_Planificacion.md),
[memoria](MEMORIA_PROYECTO.md) y [plan de desarrollo](PLAN_DESARROLLO.md).
Este documento concreta el alcance funcional. P02 resolvió stack, despliegue
y modelo de usuarios en [DECISIONES.md](DECISIONES.md): aplicación local de
un usuario, sin autenticación ni publicación en internet.

## 2. Recorridos incluidos

1. **Primera importación:** seleccionar uno o varios MP3, conocer el resultado
   por archivo y ver las pistas válidas en la biblioteca. Las que no tienen
   etiquetas muestran datos provisionales editables y se pueden escuchar.
2. **Organización y escucha:** buscar por título, artista o álbum, abrir un álbum,
   seleccionar una pista y utilizar reproducir/pausar, anterior/siguiente, avance
   temporal y volumen. La información y el progreso corresponden a la pista activa.
3. **Playlists:** crear, renombrar, añadir/quitar/reordenar pistas y personalizar
   imagen/apariencia. Los cambios se conservan al reiniciar y no modifican álbumes.
4. **Espacio del álbum:** activar edición, cambiar color de fondo, añadir imágenes
   y GIFs locales, mover, rotar, redimensionar, ordenar y eliminar elementos.
   Bloquear, guardar, restablecer y recuperar cada composición de forma independiente.
5. **Exploración:** entrar en una sección separada, describir un ambiente o sensación,
   recuperar canciones reales con pgvector, leer explicaciones basadas en sus fichas
   y seleccionar un resultado para reproducirlo.
6. **Fallos:** si falla la IA, se informa lo sucedido y se puede seguir escuchando
   y organizando música. Si falla un guardado, no se anuncia éxito y se permite
   recuperar/reintentar la operación sin aplicar cambios a otro álbum.

## 3. Matriz de requisitos funcionales

«Incluido» identifica un compromiso de esta primera entrega. «Posterior» es
trabajo previsto que no condiciona su aceptación. Los IDs conservan los del concepto.

| ID | Decisión de alcance | Resultado observable de aceptación | Trabajo / pruebas |
| --- | --- | --- | --- |
| RF-01 | Incluido: MP3 individual y múltiple. | Se almacenan pistas válidas con resultados por archivo; inválidos se rechazan sin perder las otras importaciones. Copias de bytes idénticos devuelven la pista existente, según D05. | P06; CA-01, AC-01. |
| RF-02 | Incluido: biblioteca visual. | Álbumes, pistas y playlists reflejan datos persistidos; hay estados de vacío, carga y error. | P08, P11; CA-01, AC-02. |
| RF-03 | Incluido: reproducción básica. | Play/pausa, avance, volumen y anterior/siguiente funcionan con audio real y mantienen coherente la pista activa. | P09–P10; CA-03. |
| RF-04 | Incluido: buscador textual. | Encontrar por título, artista y álbum; consulta sin coincidencias muestra estado vacío útil. | P08; CA-09. |
| RF-05 | Incluido: gestión de playlists. | Crear/renombrar y editar pistas/orden e imagen; reabrir conserva los cambios. | P11; CA-04, CA-05. |
| RF-06 | Incluido: presentación visual de colecciones. | Playlists muestran vinilo con imagen central o tarjeta personalizada, según el diseño, con alternativa predeterminada. | P08, P11; CA-05, AC-02. |
| RF-07 | Incluido: un muro por álbum. | A y B tienen composiciones distintas; álbum sin cambios recibe diseño inicial. | P12–P13; CA-07. |
| RF-08 | Incluido: fondo de color y editor de objetos. | Añadir/mover/rotar/redimensionar/ordenar/eliminar imágenes y GIFs locales dentro de la zona decorable. Fondo de imagen e importación desde servicios externos quedan posteriores. | P13–P15; CA-06, AC-03. |
| RF-09 | Incluido y obligatorio: persistencia. | Fondo, recursos y transformaciones reaparecen al reiniciar; restablecer también se conserva. Un fallo de escritura se comunica. | P12, P16; CA-06, CA-07, AC-04. |
| RF-10 | Incluido: editar y bloquear. | En modo bloqueado no se mueven objetos; el reproductor y la navegación permanecen utilizables en ambos modos. | P13; CA-08. |
| RF-11 | Incluido: metadatos editables. | Datos ausentes usan valores provisionales; edición persiste con procedencia y no se sobrescribe silenciosamente. | P07; CA-02. |
| RF-12 | Incluido: ficha musical para indexar. | Cada pista de demostración semántica tiene descripción verificable, fuente y versión; puede ser manual. Análisis directo de audio queda posterior. | P18–P19; AC-05. |
| RF-13 | Incluido y obligatorio: pgvector. | Embeddings reales se guardan y consultan en PostgreSQL; modelo/dimensiones/configuración son compatibles y quedan registrados. | P21–P22; CA-10. |
| RF-14 | Incluido y obligatorio: API de IA real. | Una llamada real forma parte del recorrido demostrado, con evidencia sin secretos; simulaciones no cuentan como cumplimiento. | P20–P23; CA-10, CA-11, AC-06. |
| RF-15 | Incluido: búsqueda por sensaciones. | Consulta en lenguaje natural devuelve pistas existentes de la biblioteca, estado vacío o explicación de datos insuficientes. | P17, P22–P23; CA-11. |
| RF-16 | Incluido: explicación con evidencia. | Las razones se apoyan en fichas recuperadas; no se inventan pistas ni atributos. La explicación alternativa ante fallo también se basa en datos. | P23; CA-11, CA-12. |
| RF-17 | Posterior recomendado: favoritos y personalización. | Cuando se active, los favoritos persisten y producen un cambio explicable en recomendaciones, con alternativa para usuarios sin favoritos. | P24–P25; fuera del cierre del MVP. |
| RF-18 | Posterior: huella acústica. | Cuando se active, servicio comprobado e identificación trazable; fallo sin título/artista inventados. | O01; CA-13 condicional. |
| RF-19 | Posterior: estaciones automáticas. | Cuando se active, listas temáticas reproducibles que contienen solo pistas existentes. | O03. |
| RF-20 | Futuro: reconocimiento enriquecido, locutor y herramientas multiagente. | Delimitar y evaluar cada función por separado antes de desarrollarla. | O01, O02, O05, O09. |

P02 incorpora reproducción continua al navegar dentro de la aplicación;
cerrar/reabrir no inicia audio automáticamente. Se comprobará en P10.
Aleatorio, repetición y cola avanzada corresponden a O08. Las cuentas múltiples,
compartir muros y sincronizar dispositivos no se incluyen sin una decisión posterior.

## 4. Matriz de aceptación del concepto

Estado inicial de todos los casos incluidos: **Pendiente de implementación y ejecución**.
El cierre de este documento no significa que la aplicación haya superado estas pruebas.

| ID | Alcance y procedimiento | Resultado exigido / evidencia |
| --- | --- | --- |
| CA-01 | Incluido. Importar un MP3 válido desde una biblioteca vacía, reiniciar y abrirlo. | Pista visible, archivo recuperable y reproducción audible; anotar archivo e importación. |
| CA-02 | Incluido. Importar MP3 sin etiquetas, reproducirlo y editar título/artista/álbum; reiniciar. | Valores provisionales, portada predeterminada y cambios editados persistentes, sin inferir identidad. |
| CA-03 | Incluido. Reproducir/pausar, cambiar pista, mover progreso y volumen. | El audio responde, el tiempo/progreso coincide y la información sigue la pista activa; verificar inicio/final de la lista. |
| CA-04 | Incluido. Crear/renombrar playlist, editar pistas y orden, reiniciar. | Nombre, pertenencia y orden conservados; álbumes originales intactos. |
| CA-05 | Incluido. Cambiar imagen/apariencia de playlist, reiniciar. | Imagen elegida recuperada; recurso inválido rechazado sin perder la imagen anterior. |
| CA-06 | Incluido. Decorar A con fondo y varios objetos, guardar, cerrar interfaz y reiniciar backend. | Fondo, referencias, posiciones, tamaños, rotaciones y orden se reconstruyen; registrar antes/después. |
| CA-07 | Incluido. Decorar A y B de forma distinta y alternar entre ellos, incluido tras reinicio. | Ningún objeto o respuesta tardía de A se aplica a B. |
| CA-08 | Incluido. Bloquear diseño e intentar arrastrar mientras se usan controles de audio. | Objetos inmóviles, reproducción y navegación utilizables; desbloquear permite edición. |
| CA-09 | Incluido. Buscar álbum existente y términos de canción/artista; probar término ausente. | Resultados correctos y estado sin coincidencias sin error. |
| CA-10 | Incluido. Indexar fichas, generar consulta compatible y buscar en pgvector. | Registrar dimensiones/modelo/configuración, consulta y pistas recuperadas desde PostgreSQL real; no vectores de muestra. |
| CA-11 | Incluido. Ejecutar consultas de referencia por sensaciones y reproducir un resultado. | Pistas existentes y explicaciones respaldadas por fichas; conservar consulta, resultados y fuente. La pertinencia musical se evalúa con música autorizada, no solo tonos de prueba. |
| CA-12 | Incluido. Simular indisponibilidad, cuota o respuesta inválida de la API. | Estado de error útil o alternativa declarada; la biblioteca y el reproductor siguen funcionando. Una simulación valida el fallo, no RF-14. |
| CA-13 | Condicional, aplazado con RF-18. Ejecutar identificación sin coincidencia cuando exista O01. | No se presenta identidad inventada. Mientras O01 no exista, informar «No aplica: reconocimiento no incluido», nunca «Superado». |

### Comprobaciones adicionales

| ID | Verificación complementaria | Resultado exigido |
| --- | --- | --- |
| AC-01 | Importación con duplicado, archivo vacío y contenido inválido con extensión MP3. | Política de duplicados aplicada, errores por archivo y biblioteca sin referencias rotas. |
| AC-02 | Biblioteca vacía y con datos, con imágenes ausentes. | Navegación y acciones comprensibles; recursos predeterminados sin afirmar datos inexistentes. |
| AC-03 | Editor con GIF, límites de tamaño/peso y ventana más pequeña. | Límites comunicados, objetos recuperables y controles fijos accesibles; alternativa de manipulación por teclado. |
| AC-04 | Fallar un guardado, recuperar conexión, restablecer y reiniciar. | No anunciar guardado falso; permitir reintento; restablecimiento persistente solo en el álbum objetivo. |
| AC-05 | Editar ficha después de indexar y reiniciar durante procesamiento. | Vector desactualizado identificable, reprocesamiento posible y audio disponible. |
| AC-06 | Revisar evidencia de API, configuración y cliente. | Sin claves en frontend, repositorio o registros; indicar qué datos se envían y acotar llamadas. |
| AC-07 | Ejecutar la demostración desde instrucciones de instalación. | Arranque y migraciones reproducibles; persistencia de medios y BD; límites conocidos documentados. |

## 5. Condiciones de calidad y límites

- **Persistencia:** demostrar reinicio de la aplicación, no solo cambio de vista.
  Los archivos asociados también deben seguir accesibles.
- **Resiliencia:** fallos de análisis, vectores o explicación no bloquean música
  ya importada. Biblioteca vacía o aún no indexada tienen estados explícitos.
- **Transparencia:** diferenciar etiquetas, edición manual, descripción sintética
  y análisis real. No anunciar que la IA escucha o aprende gustos sin implementarlo.
- **Uso de recursos:** no precargar todos los audios. Límites de archivo, objetos,
  tamaño de biblioteca de demostración y llamadas se fijan en P02/P06/P14/P20
  y se comprueban después; no hay métricas de rendimiento medidas todavía.
- **Usabilidad:** controles de audio accesibles durante edición/bloqueo,
  foco visible y comprobación de composición en distintos tamaños de ventana.
- **Integridad:** relaciones entre canciones, álbumes, playlists y muros válidas;
  consultas parametrizadas y acceso a archivos mediante referencias gestionadas.

## 6. Colección de prueba y procedencia

Se preparó una [colección técnica sintética](../pruebas/coleccion/README.md), con
manifiesto de archivos, procedencia, uso previsto y huellas SHA-256. Incluye dos
álbumes, cuatro señales originales codificadas como MP3, una copia duplicada,
un archivo vacío y otro inválido con extensión MP3. No utiliza grabaciones ajenas.

Sirve para importación, etiquetas, duración, reproducción, aislamiento y errores.
Las señales no son canciones comerciales ni sustituyen una evaluación musical.
Las descripciones de prueba se limitan a características conocidas del generador;
no se presentan como resultado de una IA ni como evidencia de sensaciones humanas.

Para P17 se incorporará una selección musical propia, autorizada o con licencia
documentada. Por cada pista registrar origen, autor, permiso/licencia, archivo,
álbum y descripción verificada. No hay una selección musical externa recibida ni
permisos de terceros confirmados en esta sesión. Esto queda como dependencia de
la evaluación de pertinencia de CA-11, no como una prueba ya superada.

## 7. Requisitos académicos y decisiones pendientes

| Tema | Lo conocido | Pendiente y momento de resolución |
| --- | --- | --- |
| API de IA y BD vectorial | El concepto los exige y propone pgvector explícitamente. | Seleccionar modelos/proveedores y verificar capacidades en P20; demostrar API y BD reales en P21–P23. |
| DevFlow frente a EchoBeats | El curso nombra DevFlow; el usuario eligió EchoBeats para este proyecto. | Confirmar con el docente si acepta el proyecto alternativo; registrar evidencia antes de cerrar la entrega académica. |
| n8n | Forma parte del currículo, con workflows e integraciones. | Confirmar obligatoriedad para EchoBeats; si se exige, incorporar O04 antes de P26. |
| Agentes y LangGraph | El curso contempla agentes/RAG; el concepto deja LangGraph como ampliación. | Confirmar si exige agente o framework concreto; activar O05 si corresponde antes de P26. |
| RAG | La recuperación de fichas y generación de explicaciones es una aplicación prevista. | Confirmar si la rúbrica exige además una base documental u otra demostración específica. |
| Evidencias y sustentación | El curso pide repositorio, pruebas, documentación y defensa individual. | Obtener rúbrica, fecha de entrega y formatos exactos; exportar workflows si se incorporan. |
| Entorno y cuentas | P02 adopta ejecución local de un usuario, sin cuentas ni publicación. | Cambiar a servidor/multiusuario requiere nueva decisión de autenticación y propiedad. |
| Stack, límites y servicios | P02 define stack y límites iniciales en DECISIONES.md. | Fijar/probar versiones en P03; verificar IA al seleccionar proveedor en P20. |

Las preguntas académicas no impiden preparar alcance, diseño y biblioteca.
No se considera confirmada una exigencia docente solo porque aparezca como
ejercicio en la guía. Si se recibe una respuesta que cambie el alcance, actualizar
este documento y las dependencias del plan antes de la implementación afectada.

## 8. Definición de terminado

### Cierre de P01 (documentación)

- RF-01 a RF-20 tienen decisión, resultado observable y vínculo al plan.
- CA-01 a CA-13 tienen procedimiento, evidencia y estado incluido/condicional.
- Se registraron límites, pendientes docentes y colección técnica reproducible.
- Quedan diferenciadas especificación, implementación y validación funcional.

### Cierre futuro del MVP (producto)

- RF-01 a RF-16 y CA-01 a CA-12 cumplen su aceptación con evidencia real,
  además de las comprobaciones complementarias aplicables.
- CA-13 queda «No aplica» o se ejecuta si se incorpora reconocimiento.
- RF-17 a RF-20 no condicionan el cierre salvo actualización explícita de alcance.
- Se completaron los requisitos académicos específicos que finalmente se confirmen.
- README, configuración, arranque, datos de demostración y limitaciones coinciden
  con la aplicación entregada. Ninguna pantalla simulada sustituye API, audio,
  persistencia o consultas vectoriales reales.
