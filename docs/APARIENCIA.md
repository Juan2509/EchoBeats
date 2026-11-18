# Apariencia vaporwave/synthwave

## Objetos del tamaño del muro — 16 de noviembre de 2026

Se amplía límite de ancho/alto normalizado de0.60 a1.0 en editor, API y BD mediante
0011_wall_full_size. Conserva límites del rectángulo girado, mínimo0.03, lienzo
1000x700 y proporción visible10:7. No se mueve ni redimensiona ningún objeto existente.
Objeto → Ajustar al muro centra y amplía al máximo conservando proporción y giro;
es una acción explícita con undo/redo y autoguardado. Imagen cuadrada puede ocupar
todo el alto; sobrante lateral corresponde a su proporción, sin estirar el original.
Tiradores libres permiten modificarla sin Shift; Shift conserva proporciones.
Contorno del lienzo visible solo al editar distingue su área del fondo general.

Migración aplicada tras backup privado45820 bytes:
backups/echobeats_before_wall_full_size_1794854472866.dump y manifiesto SHA-256.
Huellas de wall/wall_element idénticas antes/después. Downgrade rechaza objetos
mayores a0.60 en lugar de recortarlos, probado únicamente en BD aislada.
27 pruebas backend de muros y102 frontend/build aprobados. Chrome con imagen y
guardados simulados verificó imagen al100% del alto (657.48px), proporción intacta,
centrado y undo/redo; sin scroll exterior900px. Capturas wall-full-before/after.
No se modificaron diseños personales para la prueba ni se llamaron proveedores IA.

16 noviembre, ajuste posterior del álbum: Editar pared ahora comparte toolbar con
Mi biblioteca, sobre el vinilo. La zona álbum usa la altura restante entre toolbar
y player (observa resize, alturas y escala). Desde651px, sidebar y wall-panel ocupan
esa zona; el lienzo se limita por ancho y alto conservando10:7. No se cambia modelo
1000x700, posiciones, encuadre ni imágenes. Se elimina margen superior heredado del
player que producía6px de scroll. Sidebar conserva scroll interno y llega hasta
7–10px antes del reproductor. Ampliar muro oculta temporalmente sidebar y Ver panel
del álbum lo restaura, siempre con navegación/player visibles. En móvil angosto,
panel y muro siguen apilados y requieren scroll vertical, sin overflow horizontal.

97 pruebas frontend/build aprobados. Chrome aislado con24 pistas simuladas verificó
1920x1080,1440x900,1280x720,768x900 sin scroll exterior ni recorte de muro; proporción
10:7, botón junto al enlace, scroll de lista sin mover muro y ampliar/restaurar.
360x800 revisado con flujo vertical. Capturas fitted-wall-*.png y reporte local en
data/validation. Sin cambios en diseños personales ni llamadas IA.

16 noviembre: se restaura scroll interno del panel izquierdo aprovechando toda la
altura útil medida entre cabecera y reproductor; sustituye crecimiento sin límite.
ResizeObserver/resize/scroll recalculan altura compensando zoom CSS. Panel sticky
en escritorio/tablet, en flujo normal móvil, con scroll contenido y margen inferior.
Barra superior sticky en todas las rutas (altura observada, offset superior12px,
z-index40). El muro y su encuadre siguen independientes del número de pistas.
Workspace al75% usa width100%, no133%, corrigiendo overflow de álbum a1280.
Build y revisión Chrome1440/1280/768/360 con24 pistas simuladas aprobados: muro y
scroll de página inmóviles al desplazar el panel; player sin cubrir panel, menú
visible al bajar y cero overflow horizontal. Datos y medios sin cambios.

## Configuración como sección — 16 de noviembre de 2026

La navegación superior abre `/configuracion`, con Fondo principal, Álbumes,
Colores y estilo, Conexión y estado. Sustituye AppearanceDialog y la restricción
anterior de editar solo el álbum de la vista. URL conserva apartado y álbum:
`/configuracion?seccion=albumes&album=<uuid>`, con atrás/adelante.

Álbumes carga todas las páginas, excluye el técnico y permite elegir el álbum,
ver portada/vinilo y fondo actual, cambiar presentación y fondo propio/heredado.
Mantiene X solo para imágenes propias, lienzo y enlace para abrir el álbum.
Estados vacío/error/álbum inexistente visibles. Menú lateral pasa a tarjetas móvil.

Editar pared → Fondo reúne transparencia, color, imagen del muro y ampliación;
no aparecen en Configuración. Color conserva autosave/CAS backend, superficies e
imágenes siguen locales. No modifica archivos, geometría ni preferencias existentes.
El editor de fondo impide navegar con un borrador/carga pendiente y ofrece Aplicar
o Descartar ajustes; no sube imágenes pendientes automáticamente.

97 pruebas frontend/build aprobados. Chrome aislado con dos álbumes simulados:
navegación como sección, independencia de fondos principal/álbum, colores, estado,
controles de pared trasladados y autosave de color simulado;360/768 sin overflow.
Capturas settings-principal/album/colores/sistema/wall-controls y settings-section-
360/768 inspeccionadas. Sin diálogos nativos ni escrituras personales en esta prueba.
No se hicieron migraciones ni llamadas reales a IA; pendientes previos vigentes.

16 noviembre, efecto cristal: paneles de información con84% de superficie oscura
y16% transparente, desenfoque del fondo18px y saturación110%. Afecta contenedores
de Inicio/Biblioteca/Explorar, sidebar, tarjetas, reproductor y diálogos; el texto
no se desenfoca, controles y cabecera conservan fondo estable. Preserva colores
personalizados mediante mezcla oscura. Fallback opaco con @supports para navegadores
sin backdrop-filter. Build aprobado; no es nueva certificación de contraste para
todos los wallpapers. Preferencias e imágenes originales intactas.

Corrección posterior16 noviembre: el usuario pidió alejar más porque el primer
ajuste fue insuficiente. Ahora workspace de escritorio (>1000px) usa escala CSS
0.75, máximo1520px (álbum1760px) y altura compensada133.333svh. La escena queda
sin escalar y el zoom del navegador sigue100%; móvil/tablet sin este alejamiento.
Se sustituye la decisión previa de no usar zoom CSS. Las medidas anteriores de
controles son previas a esta escala:44px se muestran como33px en escritorio.
Build y revisión Chrome1920/1440/1280/768/360 aprobados: zoom de workspace0.75
en escritorio/1 en móvil, body/visualViewport1, sin overflow; reproductor dentro
de pantalla. Capturas density-*.png actualizadas. Sin cambios BD ni preferencias.

16 noviembre: densidad normal compacta para aproximar al100% la distribución que
el usuario prefería al75%. Workspace1440px/álbum1640px centrados, márgenes visibles;
h1 de colección hasta48px, hero64px, intro16px y botones14px; menor espacio entre
secciones, formularios y tarjetas. No se fuerza zoom ni escala CSS, se mantiene la
accesibilidad de zoom del navegador, select16px/min44px y portadas grandes.
Verificación Chrome de Inicio/Biblioteca/Explorar a1920/1440/1280/768/360 con zoom1
y escala visual1, sin overflow horizontal; capturas1440/360 inspeccionadas.
Build aprobado; sin interacciones de escritura, IA ni prueba de escucha.

16 noviembre: reproductor hasta1160px y portada88px/72px móvil; textos y tiempo
ampliados. Controles SVG de aleatorio y repetir canción con estado seleccionado
legible. Aleatorio usa la cola actual y no cambia la pista al activarse; desactivar
restaura orden. Bucle solo de pista, no de álbum. Ambos son de sesión, no persistidos.
97 pruebas frontend y build aprobados; comportamiento con doble de audio, escucha
y revisión visual de esta ampliación aún pendientes.

16 noviembre, controles de formulario: select global en workspace/diálogos con
fuente 1rem, altura mínima44px, padding y borde. Explorar usa textarea y número
con tipografía heredada, etiquetas de16px y notas espaciadas; filtros responsivos.
Favoritos comparte fila después de Playlists. Crear álbum corregido a UTF-8 sin
signos de interrogación dañados. Build y revisión Chrome1280/768/360 aprobados:
cuatro select de Explorar miden45px/16px, sin desbordamiento horizontal. Sin
llamadas IA, importación ni cambios del catálogo en esta revisión.

Ajuste posterior del 16 de noviembre: retirado el recuadro visible de estado
debajo de Editar pared (Sin cambios/Pared guardada). Se conserva como región
accesible oculta y dentro de herramientas; los avisos de error siguen visibles.

## Legibilidad sobre fondos personalizados — 16 de noviembre de 2026

readability.css se carga después de los estilos anteriores para corregir estados
seleccionados que heredaban texto verde oscuro. Navegación en azul grisáceo opaco;
inicio, tarjetas informativas, formularios, importación, playlists, avisos y pie
tienen superficies de lectura. Paneles y diálogos mezclan 88% de base oscura con
12% del color elegido: conservan el matiz sin volver blanco el fondo del texto.
Acentos de texto con luminancia acotada, campos opacos, botones con borde y estados
seleccionado/hover/foco explícitos. Los colores del wallpaper y las imágenes del
muro siguen editables. No se alteran archivos, diseños ni preferencias guardadas.

Corrección posterior pedida por el usuario: se quitó el recuadro grande «La pared
de…». El título sigue solo para lectores de pantalla; Editar pared y el estado de
guardado permanecen compactos y con superficie propia. No se añadió fondo al lienzo.

95 pruebas frontend y build aprobados; recorrido de carpetas/fondos con datos
simulados aprobado. Chrome aislado revisó inicio/biblioteca/explorar/álbum, diálogos
de apariencia/creación y móvil 360/768. Auditoría local de texto renderizado con
paletas blanca/negra/magenta y patrón de alto contraste: mínimo 4,5:1 sin hallazgos
en los estados examinados ni desbordamiento horizontal. Se consideran los colores
del degradado de lectura, no el borde decorativo; se excluye texto oculto accesible.
Capturas readability-*.png y reporte readability-report.json en data/validation.
Esto no certifica accesibilidad universal ni cubre todos los resultados posibles de
IA/errores/medios personales. Pendientes de audio/API real/aceptación siguen abiertos.

15 de noviembre: [ALBUMES_CARPETA.md](ALBUMES_CARPETA.md) registra la creación con
vista previa y Vinilo/Portada sin opción redundante, X sobre miniaturas propias
(presets e herencia protegidos) y encuadre mediante lienzo con arrastre, giro y zoom.
Los campos nuevos panX/panY/rotation son preferencias locales; los ajustes antiguos
se leen con valores neutros. Los originales y recursos compartidos se conservan.

Solicitud posterior a P28, 14 de noviembre de 2026. El usuario ahora pide acercar
la apariencia a Refrencia.png: esta petición sustituye la directriz anterior de
usar la imagen únicamente como orientación estructural. El nombre sigue EchoBeats.

Ampliación posterior: controles distinguibles sobre fondos personalizados,
selector en tarjetas como la captura adjunta, imagen propia del muro, mayor área
de decoración y recuperación de vinilos en álbumes.

## Ajuste vigente: configuración por vista y editor simplificado

### Canciones, fichas y favoritos (15 de noviembre)

Las filas dentro del álbum muestran reproducción, título/número, artista, duración
y corazón ♡/♥. Se retiran enlace redundante al álbum y Ficha y opciones individual.
En listados generales se conserva el enlace al álbum. El corazón junto al título
añade/quita favorito con el controlador existente: no inventa éxito optimista ni
repite PUT; fallo permite consultar el estado antes de volver a modificarlo. Tiene
nombre accesible, aria-pressed y estados ocupado/deshabilitado.

Al final del panel, **Fichas y opciones del álbum** → **Pista que quieres editar**
→ **Editar descripción musical**. Incluye todas las pistas, leyendo páginas de100
solo al abrir; no se limita a las24 visibles de la cola. Hay cancelación al cerrar,
rechazo de duplicados/pistas ajenas/listado cambiado y recarga ante error.
Preparación de información y Buscar similares operan sobre la selección. Reutiliza
el editor modal con procedencia, atributos/versiones, protección de borrador y
precondiciones existentes. No genera descripciones ni indexa automáticamente.

91 pruebas frontend/build aprobados; tres pruebas de lector paginado (205 pistas,
cancelación, listado vacío/cambiado/ajeno/duplicado). Chrome aislado,
check-album-tools.cjs: filas sin enlaces/desplegables redundantes, corazones con
dos PUT deseados, carga perezosa de125 opciones en dos páginas efectivas, selección
y edición/guardado de pista125, tamaños768/360. Catálogo/favoritos/ficha simulados,
sin audio ni IA ni escrituras reales. Capturas album-hearts-desktop.png,
album-track-selector.png y album-hearts-360.png inspeccionadas. En StrictMode puede
iniciarse y abortarse una lectura repetida; no hay escritura automática al abrir.

### Color y grosor del sticker (15 de noviembre)

Seleccionar un sticker → Objeto → **Editar contorno**. Elegir color y mover Grosor
entre 0 y 12 (paso .5); 0 oculta el efecto. Se muestra al instante en el muro,
independiente para cada imagen. Volver a Objeto recupera los controles normales.
Los valores se guardan automáticamente en las preferencias de este navegador y
origen, clave álbumUUID:elementoUUID; no viajan en el PUT del muro ni en respaldos
de BD y no se sincronizan entre equipos. Si falla localStorage se informa sesión.

Imagen sin marco oculta el efecto y Sticker recupera los valores. No cambia el
recurso, tamaño, posición, giro ni capas; Ctrl+Z/Y continúa limitado a geometría.
El contorno es un filtro SVG de dilatación de SourceAlpha y relleno con color,
fusionado bajo SourceGraphic. En PNG sigue el alfa; JPEG opaco tiene contorno del
rectángulo completo. Radio expresado respecto a 1000x700 para escalar con el muro,
sin aumentar grosor al estirar el objeto. Predeterminado blanco/nivel2. Los niveles
son del efecto visual, no una medida física de pantalla. Color hexadecimal, nivel
finito en rango y claves UUID se validan al recuperar preferencias manipuladas.

88 pruebas frontend y build aprobados: persistencia serializada/aislamiento por
sticker/álbum, compatibilidad con preferencias antiguas y rechazo de CSS/grosores
inválidos. Chrome aislado check-sticker.cjs verificó color, grosor10 frente a1 y0,
independencia, Imagen→Sticker conservando ajustes, recarga y 360x640 sin scroll.
Capturas sticker-thick.png, sticker-thin.png y sticker-controls-360.png inspeccionadas.
Muro y escrituras de tipo simulados; preferencias reales en perfil aislado. No se
añadieron assets ni se modificó BD/media principal, backend o dependencias.

### Deshacer y rotación sin tiradores (15 de noviembre)

Ampliación: Ctrl+Y/Cmd+Y y botón Rehacer recuperan pasos de posición/giro/tamaño
deshechos. Un nuevo cambio geométrico descarta los pasos pendientes de rehacer;
selección, clic sin movimiento o cancelación no los descartan. No rehace mientras
hay un gesto activo. Se aplican los mismos límites de sesión, exclusión de campos
editables/diálogos y autoguardado CAS que al deshacer. 86 pruebas/build aprobados:
secuencia múltiple de undo/redo, invalidación por nuevo cambio, recarga y rehacer
durante escritura en vuelo verificados con gateway simulado.

Ctrl+Z (Cmd+Z) deshace posición, giro y tamaño durante edición. También hay botón
Deshacer en Objeto. Cada arrastre es una sola entrada; las flechas generan pasos
individuales. Se conservan hasta 50 entradas en esta instancia del álbum; recargar,
salir o reset exitoso las elimina. No revierte altas/bajas, archivos, color, estilo
o capas. Con imágenes quitadas no se resucitan recursos.

El undo restaura geometría sobre el mismo objeto, conservando sus otros atributos.
Funciona después del autoguardado; si hay una escritura en curso se mantiene el
borrador restaurado y se persiste después con revisión nueva. Conflictos/resultados
inciertos siguen exigiendo recarga; no hay reintentos ciegos. Ctrl+Z en mitad de un
gesto cancela y no consume la historia anterior. No intercepta escritura en campos
editables o diálogos modales. El historial no se guarda ni comparte entre PCs.

En modo ↻ no hay tiradores y sus handlers no admiten redimensionar. El contorno y
el icono de rotación permanecen; segundo doble clic devuelve los tiradores. Las
flechas en rotación solo cambian el giro, no tamaño.

83 pruebas frontend y build aprobados. Nuevas pruebas cubren agrupación por gesto,
cancelación, secuencia posición/giro/tamaño, preservación de estilo/recurso/capa,
límite de historial, bloqueo/recarga/conflicto y undo durante guardado en vuelo.
Chrome aislado check-undo.cjs verificó Ctrl+Z nativo tras autoguardados simulados,
cancelación activa, campo de texto ignorado, rotación con cero tiradores/tamaño
intacto y vuelta a ocho tiradores al salir. Captura undo-rotation.png inspeccionada.
No se modificaron muros principales ni backend; los guardados se simularon.

### Tiradores de tamaño (15 de noviembre)

Última solicitud: ocho tiradores en esquinas y centros de lados, solo al seleccionar.
Arrastrar estira la imagen en el eje indicado; esquinas admiten ancho/alto libres.
Shift mantiene la relación de aspecto inicial del gesto, también desde laterales.
Se transforman los píxeles visualmente (`object-fit: fill`), conservando el archivo
original: no se añade lienzo vacío. Esto sustituye la restricción de tamaño fijo
anterior sin devolver los campos numéricos. GIF/sticker comparten los tiradores.

Se ancla la esquina/lado opuesto y se usan los ejes de la imagen aunque esté girada.
Se mantienen tamaños entre 3 y 60 % por dimensión y la imagen completa dentro del
muro; se detiene el gesto al alcanzar un límite, sin invertir ni sacar el ancla.
Las proporciones consideran 1000x700, no un lienzo cuadrado. Shift se evalúa en cada
movimiento. Foco sobre tirador + flechas ajusta; Shift conserva proporciones.
Escape, pointercancel o pérdida de captura restaura el snapshot. No autoguarda
durante el gesto; soltar vuelve al autoguardado serializado/CAS existente.

El contorno/tiradores usan overlay sobre objetos superpuestos para que sean visibles,
sin elevar permanentemente la imagen ni alterar su z_index. Desaparecen al
deseleccionar/bloquear. Panel flotante/rotación siguen disponibles.

78 pruebas frontend y build aprobados: geometría de ocho tiradores para varios giros,
ancla, Shift con relaciones no cuadradas, límites, cancelación y persistencia con
gateway simulado. Chrome aislado check-resize.cjs: cursor real en lateral/esquina,
Shift, ancla, borde superior, fill, ocho tiradores solo en selección, sin guardado
hasta soltar, Escape y deselección. Captura resize-handles.png inspeccionada.
Guardados/muro simulados en navegador, sin escribir en datos personales. TypeScript
admite extensiones .ts entre helpers sin emisión para ejecutar los mismos cálculos
en pruebas Node; sin dependencias nuevas.

Selección directa (15 de noviembre): eliminado el desplegable Seleccionar objeto
de Objeto y Capas. Clic sobre imagen/sticker elige el objeto y actualiza el panel;
clic en vacío deselecciona. La selección tiene contorno discontinuo y tinte leve
de su caja exacta (también píxeles transparentes), que sigue posición y giro. No
añade espacio ni cambia geometría; desaparece al deseleccionar/bloquear. Foco de
teclado selecciona y usa el mismo indicador. El borde permanente solo corresponde
al estilo sticker, nunca a este indicador de edición.
74 pruebas y build aprobados; check-floating.cjs comprobó ausencia del desplegable,
selección única, cambio a segunda imagen y clic real en zona vacía, retirando
contorno. Capturas floating-editing.png y selection-cleared.png. Escenario/guardados
simulados en Chrome aislado; no modifica muros personales.

Último ajuste del 15 de noviembre: las herramientas son ahora un panel flotante
no modal, situado inicialmente a la derecha, sin fondo oscuro ni desenfoque ni
bloqueo de scroll/foco del muro. Arrastrar la cabecera permite ubicarlo libremente;
queda limitado al área visible (incluida barra de scroll) y se reajusta al cambiar
tamaño/contenido. Minimizar conserva una cabecera compacta; Expandir recupera las
herramientas. La X y Terminar edición guardan lo pendiente, bloquean el muro y
retiran el contorno del lienzo. Escape oculta las herramientas y conserva la edición.
Cabecera enfocada: flechas desplazan (Mayús amplía paso), Inicio vuelve a derecha.
Seleccionar una imagen en el muro muestra automáticamente Objeto sin abrir/cerrar
el panel ni impedir arrastre/doble clic. Las preferencias de ubicación/minimización
son de esta apertura; no se guardan en BD ni se modifican decoraciones al moverlo.

check-floating.cjs verificó en Chrome aislado: panel no modal/sin backdrop/scroll
libre, arrastre real de cabecera, selección y movimiento de imagen con panel abierto,
cambio Imagen/Sticker con guardado simulado, navegación automática a Objeto,
desplazamiento por teclado, minimizar/expandir, Escape y ajuste de las cuatro páginas
a 768x800 y 360x640 sin desbordamiento. Capturas floating-right.png,
floating-editing.png, floating-minimized.png y floating-360.png inspeccionadas.
74 pruebas frontend y build aprobados. Sin escrituras en muros principales.
Esta ampliación sustituye el comportamiento modal/bloqueo de scroll descrito abajo.

15 de noviembre, herramientas emergentes: Editar pared abre un diálogo en lugar
de desplegar controles debajo del lienzo. Navegación por Añadir, Objeto, Capas y
Guardar, con estado de guardado visible. Volver al muro o Escape cierra conservando
edición/selección; Terminar edición guarda lo pendiente y bloquea, conservando la
ventana si falla. Recuperar/restablecer siguen disponibles en Guardar y mantienen
confirmaciones/protecciones. GIF se controla en Añadir. No se abren ventanas al
arrastrar o hacer doble clic; el gesto de rotación se conserva sobre el muro.

Chrome aislado, check-popup.cjs: las cuatro secciones caben sin desplazamiento a
1280x800, 768x800 y 360x640, con selección de objeto y guardado simulado Imagen →
Sticker. Verificados retorno al muro, reapertura en Objeto, Escape y cierre con
bloqueo. Capturas popup-1280-Objeto.png y popup-360-Objeto.png inspeccionadas.
El diálogo permite desplazamiento de seguridad para ventanas más bajas, zoom o
mensajes de error extensos: no se recortan controles. Se bloquea el scroll de la
página mientras está abierto y se restaura el foco al cerrar. 74 pruebas frontend
y build/TypeScript aprobados. Sin escrituras de prueba en BD/medios principales.

15 de noviembre: al seleccionar un PNG/JPEG en Editar pared, **Apariencia del objeto
seleccionado** permite alternar Imagen sin marco / Sticker con contorno. Conserva
recurso y geometría y se autoguarda con las precondiciones existentes. GIF conserva
modo animado por compatibilidad del contrato actual. 74 pruebas y build aprobados;
prueba de persistencia/guardas con gateway simulado, sin escritura en principal.

Configuración desde Inicio/Biblioteca solo ofrece el fondo principal; desde un
álbum solo ofrece su fondo y los controles de su muro. Heredar el principal sigue
disponible sin permitir modificarlo desde el álbum. Los controles de transparencia,
color, imagen y ampliación se reúnen en Configuración: la cabecera del muro conserva
únicamente Editar pared/Bloquear diseño. Para editar el color guardado, activar
Editar pared antes de abrir Configuración. No se cambia el protocolo de guardado.

Eliminar fondo personalizado quita la imagen de la selección del ámbito actual;
se puede cambiar por otra imagen. Los estilos predeterminados no tienen eliminación.
Quitar imagen del muro vuelve a Transparente si estaba activa. Quitar la imagen
general/de álbum vuelve a Synthwave si estaba activa, conservando otros estilos
seleccionados. Se puede descartar una imagen pendiente antes de subirla. Los recursos
gestionados se conservan para no romper referencias compartidas de álbumes/objetos
u otros navegadores: esta acción no es una purga de archivos del backend.

Nuevas decoraciones: Imagen sin marco o Sticker con contorno. Póster ya no aparece
en el selector; registros anteriores se muestran como imagen sin marco, sin migrar
ni reescribir composiciones. Se retiran ancho/alto independientes y el campo Giro.
Imagen conserva transparencia, sin superficie opaca, sombra, borde ni marco; sticker
aplica drop-shadow blanco a la silueta alfa, también en PNG. El indicador de foco
es temporal y no se guarda como marco. GIF conserva reproducción/pausa existentes.

En edición, doble clic sobre la imagen activa ↻: arrastrar alrededor de su centro
gira, otro doble clic elimina el icono y vuelve a movimiento. R alterna por teclado;
flechas mueven o giran según el modo; Escape cancela el gesto o sale del modo.
Se conserva una instantánea al iniciar el gesto: no hay autoguardado durante el
arrastre; soltar confirma y cancelar restaura. Se mantienen límites/encaje 10:7,
CAS, capas y protección de conflictos; girar puede recolocar/reducir proporcionalmente
para mantener una composición heredada grande dentro del muro.

Validación vigente: 73 pruebas frontend y build/TypeScript aprobados. Chrome
aislado, check-rotation.cjs, comprobó menús por vista, eliminación por ámbito y
predeterminados, PNG transparente, contorno alfa de sticker, ausencia de Póster y
campos de tamaño/giro, doble clic real por protocolo Input, giro ~90°, salida del
modo, movimiento posterior, guardado y diálogos 360/768 sin desbordamiento.
Datos/guardados del muro simulados en navegador, sin modificar la principal.
Capturas rotation-album-settings.png, rotation-active.png y rotation-move.png en
data/validation. Se corrigió consulta del estado del gesto al recibir doble clic.
Los recorridos de scripts anteriores documentados más abajo son históricos;
sus selectores corresponden al menú anterior. Pendientes de audio/API real vigentes.

## Uso

Abrir http://localhost:5173 y recargar con Ctrl+F5 si hay recursos antiguos.
Configuración abre **Fondos y apariencia**, sin panel de personalización permanente.
**Fondo principal** se usa en toda la aplicación. Dentro de un álbum, **Fondo del
álbum** permite elegir otro exclusivo o **Usar fondo principal** para volver a
heredarlo. Cada ámbito permite Synthwave, Vaporwave o imagen; cambiar a un estilo
predeterminado conserva la última imagen guardada para volver a seleccionarla.
Colores de paneles y degradados agrupa los seis colores, ángulo, rejilla y presets.
Las opciones se presentan en una galería de dos columnas con miniaturas de los
estilos, imagen propia y fondo heredado, borde y marca de selección. Las miniaturas
de estilos son ilustraciones CSS representativas de paleta/rejilla. La imagen
propia tiene miniatura del encuadre y vista previa ampliada antes de aplicar.

**Imagen del muro** abre un selector independiente: su imagen queda detrás de los
objetos y no cambia el fondo de la página/álbum. Comparte preparación, encuadre y
validación; su preview tiene proporción 10:7. Transparente/Color del muro conservan
la imagen para recuperarla abriendo el selector y pulsando Aplicar fondo.
El lienzo usa toda la anchura disponible, sin límite basado en altura de ventana;
**Ampliar muro** coloca el panel musical arriba y permite decorar a todo el ancho.
Se conserva geometría proporcional 1000x700 y datos existentes; no hay migración.

Biblioteca → Álbumes → **Apariencia predeterminada de álbumes** permite Vinilos o
Portadas. En cada álbum, **Apariencia del álbum** ofrece una elección propia o
heredada. Se guarda en las mismas preferencias de navegador, sin alterar portadas,
metadatos ni la apariencia de playlists que ya se guardaba en BD desde P11.
Botones, navegación Inicio/Biblioteca/Explorar, enlaces de acción y desplegables
tienen bordes y superficies opacas para distinguirlos sobre imágenes/colores;
se conservan indicadores de foco/selección y estados deshabilitados.

Seleccionar PNG/JPEG/WebP → vista previa → Ajustar (imagen completa) o Rellenar
(recorte de bordes) → zoom y posición horizontal/vertical → **Aplicar fondo**.
El encuadre se conserva como metadatos reversibles, sin cortar definitivamente
el recurso. La vista previa usa la proporción actual de ventana; al cambiar de
pantalla se recalcula la imagen con el mismo modo/zoom/posición. No se estira.
La entrada admite hasta 25 MiB, 48 MP y 16384 px por lado; el navegador crea una
copia JPEG de hasta 2560 px en el lado mayor y 5 MiB, sin ampliar imágenes pequeñas.
Se respeta orientación de la imagen y la transparencia se compone sobre azul noche.
El archivo original no cambia; imágenes corruptas o que excedan esos límites se
rechazan conservando el fondo anterior. GIF/SVG no son fondos compatibles.
La copia se registra usando la validación existente del backend, purpose=wall.

Las preferencias se guardan en localStorage, clave echobeats.appearance.v1,
**por navegador y origen**. No se sincronizan entre PCs/perfiles ni se exportan
con la BD. Si el navegador impide guardar, se informa que solo se aplican en sesión.
La imagen sí usa almacenamiento gestionado del backend; solo su selección es local.

El muro dispone de **Transparente** y **Color del muro**, reversibles por álbum.
Cambiar el color desde Editar pared selecciona automáticamente la segunda opción;
Transparente recupera la escena sin borrar ese color. Se quitaron el recuadro
vacío, el contorno de edición y la caja de herramientas enmarcada. Los valores,
objetos, capas y transformaciones guardados en BD no
se sustituyen al cambiar la apariencia. La geometría sigue siendo proporcional 10:7.
Reset de apariencia requiere confirmación y no restablece diseños de álbumes.

## Diseño

Paleta azul noche/morado/rosa/cian, bordes de neón, paneles degradados, rejilla
estática en perspectiva y muro abierto junto al panel de canciones. Portada con
vinilo decorativo y reproductor compacto. Portada provisional SVG original con
sol/rejilla; no reemplaza portadas registradas ni copia píxeles de la referencia.
Ficha/procesamiento/favorito/similares permanecen en Ficha y opciones para compactar
las filas. No se introducen decoraciones ni se modifican muros personales.

Variables y validación en features/appearance/theme.ts; proveedor/controles en
Appearance.tsx; estilos en app/synthwave.css. Solo hexadecimales, ángulo acotado y
URL de recurso gestionado por ID: no CSS arbitrario, data URLs, rutas de disco ni
fondos remotos desde almacenamiento manipulado. Una carga incierta conserva la
selección anterior, no se reintenta y puede dejar un recurso registrado conservado.
Cerrar controles aborta la espera y evita que una respuesta tardía cambie el tema.

Vite usa polling para detectar cambios en las carpetas compartidas de Docker
Desktop/Windows: durante revisión se detectaron módulos CSS antiguos en caché
por falta de eventos. Reiniciar solo frontend permitió cargar el tema nuevo.

## Verificación y límites

71 pruebas frontend aprobadas: presets/persistencia serializada,
validación de preferencias/CSS/URLs, migración del fondo anterior, herencia y
aislamiento por álbum, transparencia reversible y reducción proporcional. Build y TypeScript
aprobados. No cambios backend, migraciones, dependencias ni llamadas OpenAI.
Se añadieron pruebas de imagen independiente del muro y persistencia/migración
de presentación vinilo/portada con herencia y aislamiento por álbum.

Browser host de Computer Use indisponible. Se inspeccionaron capturas de un Chrome
headless con perfiles aislados: álbum a 1280 px y marcos HTTP de 360/768 px, con
datos leídos y sin iniciar audio ni editar diseños. Los marcos corrigen la limitación
del tamaño mínimo de ventana en una captura nativa estrecha. Evidencia local:
data/validation/appearance-desktop-final.png y appearance-responsive-http.png.
No se presentan capturas previas con estilos antiguos/carga pendiente como válidas.

Ampliación posterior: Chrome headless con perfil aislado y protocolo DevTools
comprobó controles reales de transparencia, vaporwave/synthwave, herencia,
preview, encuadre, persistencia y recarga. Canvas real preparó imagen 4000x2000
como JPEG 2560x1280 de 20442 bytes. Subida y lectura del asset simuladas solamente
en el navegador: no se añadieron imágenes de prueba a la principal ni se acredita
upload HTTP real. Se inspeccionaron wallpaper-dialog.png, wallpaper-scene.png,
wallpaper-360.png y wallpaper-768.png en data/validation. Se corrigió desbordamiento
móvil del encabezado. Prueba reproducible local en check-wallpaper.cjs (requiere
Chrome aislado con depuración 9226 y álbum técnico existente).
Revisión de galería: check-gallery.cjs verificó navegación opaca sobre fondo
blanco, cuatro tarjetas de álbum, preparación Canvas real e imagen de muro
independiente con upload/lectura simulados, transparencia y persistencia tras
recarga de vinilo/portada por álbum y biblioteca. Capturas gallery-backgrounds.png,
gallery-wall-preview.png, gallery-wall-applied.png, gallery-controls-light.png y
gallery-vinyl-library.png. Galería móvil 360/768 y ampliación de anchura verificadas
con check-wallpaper.cjs. No hubo escrituras de prueba en BD/medios principales.
Quedan por recorrer carga real de archivo contra servidor, audio continuo, teclado
completo y edición completa; no se reutiliza la captura en blanco anterior como prueba.
Las capturas de composición no cierran pendientes P15/P16/aceptación P26 ni escucha.
Contrastes de P27 corresponden a la paleta anterior; colores/imágenes personalizados
requieren revisar legibilidad. No se afirma WCAG ni equivalencia exacta de píxeles
con la referencia. Se conserva la restricción de API real y los 506 MP3 sin fila.
