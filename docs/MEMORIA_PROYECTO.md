# Memoria de EchoBeats

16 noviembre: vista de álbum ajustada al viewport desde651px. Muro máximo que cabe
manteniendo10:7, sin scroll de página ni estirar fondo/decoraciones. Alto de room y
sidebar calculado entre toolbar y player; sidebar llena hasta un margen de7–10px.
Editar pared movido mediante portal junto a Mi biblioteca. Ampliar muro oculta
temporalmente sidebar y ofrece Ver panel del álbum para recuperarlo. En móvil
angosto se conserva distribución vertical con scroll natural. Sin geometría/BD
modificadas.97 tests/build y Chrome con24 pistas simuladas a1920x1080,1440x900,
1280x720,768x900 sin scroll exterior, ratio intacto, controles arriba, player libre;
360 sin overflow horizontal. Ver APARIENCIA.md. Sin escrituras personales ni IA.

16 noviembre, directriz posterior: vuelve scroll interno del panel izquierdo del
álbum, alto pero limitado al hueco entre navegación y reproductor. useAlbumPanelSpace
mide ambos y compensa escala75%, resize y scroll; panel sticky en escritorio/tablet,
estático en móvil para mantener flujo del muro. Barra superior sticky en todas las
secciones con z-index40; herramientas de pared permanecen encima y diálogos en top
layer. Muro no crece con número de canciones y no cambia al recorrer lista interna.
Corregido ancho de workspace escalado a100% para evitar overflow de álbum a1280.
Build y Chrome aislado con24 pistas a1440/1280/768/360 aprobados: scroll interno no
mueve muro/página, panel por encima del player, barra visible al bajar. Sin escrituras
personales ni IA. Capturas sticky-sidebar/header y reporte en data/validation.

## Configuración como sección — 16 de noviembre de 2026

Ruta /configuracion con Fondo principal/Álbumes/Colores y estilo/Conexión y estado,
en lugar de modal. Selector de todos los álbumes con portada/presentación/fondo
actual, URL conserva apartado y álbum; fondos independientes y herencia intactos.
Color/transparencia/imagen/ampliación del muro solo Editar pared → Fondo.
Autosave/CAS del color conservado; preferencias visuales locales. Guardia de
navegación con Aplicar/Descartar para borradores de fondo. AppearanceDialog retirado.
97 pruebas/build y Chrome aislado con dos álbumes y color del muro simulado,
360/768/desktop aprobados; sin escrituras personales ni IA real. Ver APARIENCIA.md.

16 noviembre: usuario pide paneles ligeramente difuminados para ver el fondo.
Superficies de información con84% opacidad y backdrop-filter blur18px/saturate110%,
conservando base oscura y texto nítido. Aplicado a secciones, tarjetas, sidebar,
reproductor y diálogos; navegación, botones y campos mantienen superficies legibles.
Fallback opaco si navegador no admite backdrop-filter. Sin cambios en preferencias,
medios, geometría ni datos. Sustituye opacidad total anterior de esos paneles.

16 noviembre, corrección posterior: usuario consideró insuficiente la compactación
y pidió alejar más. Escritorio >1000px usa zoom CSS .75 solo en workspace, ancho
máximo1520px (álbum1760) y altura compensada133.333svh para mantener reproductor
abajo. Escena y zoom del navegador intactos; móvil/tablet hasta1000px sin escala.
Esto sustituye la decisión anterior de evitar zoom CSS; no modifica preferencias.

16 noviembre: distribución compacta solicitada para que zoom100% se parezca a la
referencia75%. Sin CSS zoom/transform ni modificar zoom del navegador: workspace
máximo1440px (álbum1640), más margen visible, títulos generales hasta48px e Inicio
hasta64px, texto introductorio16px, botones14px, márgenes y rellenos reducidos.
Desplegables conservan16px/44px mínimo y portadas/reproductor no se reducen.
Build y Chrome aislado a1920/1440/1280/768/360 aprobados, zoom/escala1 medidos,
sin desbordamiento horizontal. Inicio/biblioteca/explorar revisados y capturas
density-*.png en data/validation. Solo lecturas; sin medios/BD/IA modificados.

16 noviembre: panel izquierdo del álbum sin max-height ni scroll interno; crece
con pistas/herramientas y ocupa al menos la altura útil de pantalla en escritorio.
Listado sin límite móvil de280px. En móvil sin altura mínima artificial. Modo
Ampliar muro conserva su disposición especial. Sin cambios de geometría/datos.

16 noviembre, directriz posterior: confirmaciones de eliminación en dialog HTML
de EchoBeats, nunca window.confirm. Botón Eliminar pistas debajo de Fichas y opciones
abre selector con todas las páginas del álbum, casillas/seleccionar todas y acción
Eliminar seleccionadas. Quitados botones individuales de las filas y de ficha
centralizada; en listado general se mantiene eliminación individual con modal interno.
Operación secuencial con If-Match/revisión, progreso y resultado parcial; detiene ante
fallo, consulta respuesta incierta sin repetir DELETE. Eventos de retirada actualizan
audio/favoritos inmediatamente y catálogo al cerrar, evitando desmontar selector
durante el lote. Play de filas y corazones iconOnly sin marcos; foco accesible intacto.
97 pruebas frontend y build; Chrome aislado con catálogo simulado verificó cancelar,
dos de tres pistas, fallo incierto/consulta, álbum, ausencia de alertas nativas y
diálogo360/768. No hubo eliminaciones personales ni cambios backend/migraciones.

16 noviembre: icono de repetir sin1 y centrado con flex/SVG. Eliminación de pista
ahora accesible directamente en filas del álbum y con confirmación nativa; botón
Eliminar álbum al final de su panel con confirmación que incluye pistas y muro.
DELETE /albums/{id} exige If-Match, bloquea contenedor/pistas, retira pistas
lógicamente y las reasigna al álbum técnico, invalida trabajos y revisiones de
playlists; borra álbum/muro/créditos del contenedor, conserva originales/fichas/
historial/favoritos y asociaciones históricas. Protege álbum técnico. Eventos
actualizan biblioteca y detienen audio del álbum incluso al verificar un404 tras
respuesta incierta. Sin reintentos DELETE automáticos. Cinco pruebas backend
de carpetas aprobadas en BD/medios temporales, incluidas dos nuevas; build aprobado.
Sin migración ni borrados en biblioteca personal durante esta implementación.

16 noviembre: reproductor ampliado hasta1160px con portadas88px (72px móvil),
tipografía mayor y distribución responsiva. Añadidos bucle de pista y aleatorio
con SVG, nombres accesibles y aria-pressed; estados solo de sesión. Bucle al acabar
respeta pausa, siguiente manual continúa la cola. Aleatorio mezcla Fisher-Yates
manteniendo pista actual al frente sin reiniciar audio, conserva orden original
para desactivar y no modifica playlists guardadas. Cola finita sin repetir salvo
bucle explícito. 97 pruebas frontend/build aprobados; dos pruebas nuevas usan
doble de audio, no acreditan escucha real. Sin cambios BD/medios ni llamadas IA.

16 noviembre: retirado a petición el pie de página global con EchoBeats y
«Tu colección personal · Tu música, tu espacio». El reproductor y los pies de
acciones de los diálogos permanecen intactos.

16 noviembre: corregido texto dañado «? Crear ?lbum» mediante edición UTF-8; botón
ahora Crear álbum. Favoritos integrado en la fila de Álbumes/Canciones/Playlists,
inmediatamente después de Playlists, con ajuste de línea en móvil. Desplegables
globales con mínimo 44px y fuente 16px; Explorar con textarea, número, etiquetas y
notas más legibles y espaciados. Mensaje sin destino indica Biblioteca. Build
aprobado y Chrome aislado a 1280/768/360, sin búsquedas IA ni escrituras en catálogo.

16 noviembre: Crear álbum trasladado de Inicio a Biblioteca, junto al título,
sin recuadro ni texto promocional adicional. Mismo diálogo y navegación al álbum
creado. Mensaje de importación sin destinos actualizado para indicar Biblioteca.

16 noviembre: retirado por petición el recuadro inicial «Tu colección empieza aquí»
en biblioteca vacía. Se conservan avisos de búsqueda sin coincidencias, favoritos
vacíos y paginación fuera de rango, que ofrecen acciones específicas.

## Catálogo vaciado por solicitud expresa — 16 de noviembre de 2026

Usuario pidió eliminar toda la música y álbumes del programa. Respaldo previo
backups/echobeats_before_empty_catalog_1794836211847.dump (43469 bytes, SHA-256 en
manifiesto adjunto). Transacción retiró 8 pistas y 3 álbumes de usuario, relaciones,
favoritos, fichas/versiones/embeddings/trabajos y muros de esos álbumes. Cero playlists
existentes. Se conserva álbum técnico Sin álbum, oculto estando vacío, y los 19
assets registrados con todos sus archivos, incluidos los MP3 sin fila. Backend
detenido durante respaldo/operación y reiniciado después. Sin cambios de esquema
ni llamadas IA; las preferencias locales de navegador no se borraron.

16 noviembre: reproductor sin etiqueta visible Sonando/En pausa; conserva anuncio
accesible de estado. Favorito pasa a corazón iconOnly a la derecha del título,
reutilizando estado compartido, confirmación y mensajes de error existentes.

16 noviembre, ajuste posterior: se oculta también el recuadro de estado debajo de
Editar pared por petición del usuario. El estado permanece anunciado a lectores
de pantalla y visible en las herramientas de edición; los errores siguen visibles.

## Legibilidad y cabecera compacta del muro — 16 de noviembre de 2026

Usuario pidió impedir que textos/controles se camuflen al cambiar fondos. Nueva
capa readability.css: superficies opacas, encabezado azul grisáceo, colores de
lectura protegidos frente a paletas extremas, corrección del verde oscuro heredado
en selección y controles con estados explícitos. A petición posterior se quitó el
recuadro/título visible «La pared de…», conservando Editar pared y estado compactos.
Título accesible oculto y lienzo transparente intactos. Ver APARIENCIA.md.
95 pruebas frontend/build y flujo simulado de carpetas/fondos aprobados. Auditoría
acotada de contraste 4,5:1 con blanco/negro/magenta y vistas 360/768/1280; sin cambios
backend, datos, llamadas IA ni commits. No declarar certificación WCAG universal.

## Limpieza de temporales — 16 de noviembre de 2026

A petición del usuario se retiraron 27 carpetas regenerables: perfiles cerrados
de Chrome de pruebas, __pycache__ del código backend y frontend/dist. 8732 archivos,
1482,06 MiB. Manifiesto local: data/validation/limpieza_2026-11-16.json.
Se conservaron código (incluidos cambios sin commit), dependencias instaladas,
documentación, capturas/informes/scripts de validación, .env, respaldos, bases y
todos los medios. No se purgaron volúmenes Docker ni los 506 MP3 sin fila.
No hubo cambios funcionales ni nuevas pruebas de aplicación por esta limpieza.

## Álbumes como carpetas, retirada y encuadre — 15 de noviembre de 2026

Implementación y evidencia en [ALBUMES_CARPETA.md](ALBUMES_CARPETA.md).
Inicio permite crear álbum vacío con nombre, imagen y Vinilo/Portada. Importación
UI obliga destino y respeta carpeta frente a etiquetas; duplicados no se mueven.
Retirada lógica de pista con revisión/confirmación, detención del reproductor y
exclusión de catálogo/audio/playlists/búsqueda, conservando originales e historia.
Reimportar mismo hash restaura el ID. Migración 0010 aplicada tras respaldo privado.
X sobre imágenes propias sin borrar presets ni archivos; lienzo interactivo de
fondo con movimiento, giro y zoom no destructivos, preferencias locales.
244 backend/95 frontend/build aprobados; navegador aislado con mutaciones simuladas,
incluidos creación 360/768, destino obligatorio y giro guardado. No borrados de prueba
en principal ni llamadas reales IA. Pendientes anteriores vigentes. Sin commit.

Registro inicial: 12 de noviembre de 2026.

## Fichas centralizadas y corazones en canciones — 15 de noviembre de 2026

Usuario pidió quitar álbum redundante de filas, mover Ficha y opciones al fondo
del panel y corazón junto al nombre. En vista del álbum desaparecen enlaces al
propio álbum y desplegables por canción. Corazón junto a título en TrackList usa
FavoritesController compartido: ♡/♥, aria-pressed, guardado confirmado y consulta
ante fallo sin reintentar PUT. En listado general se conserva enlace al álbum.
Fichas y opciones del álbum al final del sidebar contiene selector de todas las
pistas (páginas de100, no solo24 visibles), carga solo al abrir, cancelación y
rechazo de datos duplicados/ajenos/listado cambiado. Editor original de descripción
con procedencia, versiones, confirmación de descarte e indexación opt-in intactos;
también preparación y similares para pista elegida. Sin llamadas reales IA/audio.
91 pruebas/build; Chrome aislado verificó 125 opciones/edición última pista,
corazón añadir/quitar y móviles768/360, con catálogo/favoritos/fichas simulados.
Paginación ajustada al sidebar. Sin cambios backend/migraciones/datos personales.

## Contorno personalizable por sticker — 15 de noviembre de 2026

Solicitud implementada: seleccionar sticker → Objeto → Editar contorno. Color y
grosor 0–12, paso .5, preview inmediata; 0 oculta. Vista separada mantiene cómodo
el panel móvil. Filtro SVG feMorphology/SourceAlpha sigue silueta transparente,
escala con muro de referencia, sin tocar archivo/geometría. Antes era blanco fijo.
Preferencias por navegador/origen y clave álbumUUID:elementoUUID; no en BD/otros PCs.
Volver a Imagen oculta efecto sin perder ajustes; Sticker los recupera. Valores
hex/numéricos e identificadores estrictamente validados; migración de prefs antiguas
usa blanco/grosor2. 88 pruebas/build y Chrome aislado check-sticker.cjs aprobados:
contorno fino/grueso/cero, color, independencia, cambios de modo, recarga y móvil
360x640 sin scroll. Muro/guardados de tipo simulados, preferencias reales en perfil
aislado; sin backend/migraciones/escritura en principal. Ver APARIENCIA.md.

## Rehacer con Ctrl+Y — 15 de noviembre de 2026

Petición implementada: Ctrl+Y/Cmd+Y y botón Rehacer recuperan pasos de geometría
deshechos por Ctrl+Z. Orden posición/giro/tamaño, conserva atributos y autoguardado
versionado. Cambios geométricos nuevos vacían rehacer; clic/gesto cancelado no.
Bloqueado durante gesto activo, conflicto, carga o fuera de edición. Los mismos
campos editables/diálogos se excluyen del atajo. Recarga/salida/reset exitoso limpian
historial. 86 pruebas frontend/build aprobados, incluyendo guardado en vuelo y
persistencia con gateway simulado. Sin backend/migraciones/datos personales.

## Deshacer geometría y exclusión de tamaño en rotación — 15 de noviembre de 2026

Ctrl+Z/Cmd+Z y botón Deshacer revierten posición/giro/tamaño por pasos en edición.
Un arrastre completo produce una entrada (máximo 50 por controlador); conserva
asset/estilo/capas actuales, no deshace archivos ni elimina/restaura imágenes.
Puede revertir después de autoguardado o mientras una escritura está en vuelo:
se conserva borrador nuevo y se guarda con siguiente revisión. Si está arrastrando,
cancela ese gesto sin consumir entrada anterior. No intercepta campos editables ni
diálogos modales. Recarga/salida/reset exitoso limpian historial, no se guarda en BD.
Rotación oculta ocho tiradores y bloquea handlers de redimensionado; contorno/icono
se mantienen. Otro doble clic los recupera. 83 pruebas y build aprobados; Chrome
aislado check-undo.cjs verificó cursor/atajo, undo de geometría, cancelación, foco de
input y rotación sin cambio de tamaño, con muro/guardados simulados. Ver APARIENCIA.md.

## Tiradores de tamaño y Shift — 15 de noviembre de 2026

Usuario autorizó redimensionar directamente con ocho tiradores sobre selección:
cuatro esquinas y cuatro lados, libres o proporcionales manteniendo Shift. Esta
petición sustituye el tamaño fijo anterior; sin campos numéricos. Imagen usa fill
para estirar sus píxeles, no añadir espacio de lienzo; original intacto. Ancla
opuesta/ejes locales respetan giro, límites existentes 3–60% y encaje dentro del
muro. Snapshot por gesto, guardado al soltar, Escape/cancelación restaura. Handles
accesibles con flechas y Shift, desaparecen al deseleccionar. Overlay mantiene ocho
tiradores visibles sobre objetos superpuestos sin cambiar sus capas guardadas.
78 pruebas frontend/build aprobados. Chrome aislado check-resize.cjs verificó
cursor real por lado/esquina, Shift, ancla, borde superior, no guardado durante
gesto, Escape y deselección; muro/guardados simulados sin tocar la principal.
Ver APARIENCIA.md. Sin backend/migración/dependencias/API IA; pendientes previos.

## Selección directa y límites temporales — 15 de noviembre de 2026

El usuario pidió retirar por completo el desplegable Seleccionar objeto y elegir
mediante clic en las imágenes. Implementado sin selector/lista; el panel refleja
el objeto pulsado, conserva acceso por foco de teclado. Contorno temporal de la
caja real (incluye transparencia del archivo) sigue posición/giro solo mientras
está seleccionado en edición. Clic en vacío o terminar edición lo oculta; no altera
tamaño ni marcos del recurso. 74 pruebas y build aprobados. check-floating.cjs
Chrome aislado verificó un único contorno al seleccionar, cambio a otra imagen,
ausencia de selector y desaparición al pulsar vacío, con guardados simulados.
Sin backend/migraciones/escrituras en muros principales. Ver APARIENCIA.md.

## Panel flotante movible — 15 de noviembre de 2026

El usuario pidió editar sin que la ventana opaque/bloquee el muro. Herramientas
convertidas a panel no modal a derecha: sin backdrop/desenfoque/bloqueo de página,
movible por cabecera con ratón/táctil o flechas; restringido a área visible y resize.
Minimizar/Expandir, cerrar conserva edición, terminar guarda/bloquea. Al seleccionar
imagen en muro se muestra Objeto automáticamente; se puede arrastrar mientras panel
está abierto. Ubicación solo durante esta apertura, no BD. 74 pruebas/build y
check-floating.cjs Chrome aislado aprobados (muro y guardados simulados), con
arrastre de panel/imagen, selección/cambio de apariencia, teclado y páginas 768/360.
Ver APARIENCIA.md. Sin backend/migraciones/cambios de datos personales ni commit.

## Herramientas emergentes del muro — 15 de noviembre de 2026

Usuario pidió retirar configuración inferior que exige scroll. Editar pared abre
diálogo con Añadir/Objeto/Capas/Guardar; no hay herramientas desplegadas bajo muro.
Volver al muro/Escape conserva edición, Terminar edición guarda y bloquea; fallo
mantiene ventana. GIF en Añadir, recuperación/reset en Guardar. Estado visible,
foco restaurado y scroll de página bloqueado temporalmente. Las cuatro secciones
caben sin scroll en Chrome aislado 1280x800, 768x800 y 360x640; fallback de scroll
para pantallas menores/zoom/errores largos. check-popup.cjs usó muro/guardado
simulados, verificó selección, cambio Imagen/Sticker, cierre/reapertura y bloqueo.
74 pruebas y build aprobados; sin backend/migraciones/escrituras en principal.
Ver APARIENCIA.md; pendientes previos conservados. Sin commit creado.

## Cambiar apariencia del objeto seleccionado — 15 de noviembre de 2026

En Editar pared, seleccionar PNG/JPEG permite alternar Imagen sin marco o Sticker
con contorno sin volver a subirlo. Conserva ID, recurso, posición, tamaño, giro y
capas; se usa el autoguardado versionado existente. Bloqueado durante gesto/fallo
que exige recarga. Póster heredado se puede convertir; GIF conserva modo animado,
según compatibilidad actual del backend. 74 pruebas y build aprobados; persistencia
probada con gateway simulado. Sin cambios backend ni escrituras en principal.

## Configuración por vista y rotación directa — 14 de noviembre de 2026

Solicitud implementada: quitar fondos personalizados por ámbito (selección local,
sin purgar archivos compartidos), predeterminados protegidos. Inicio/Biblioteca
solo fondo principal; álbum solo su fondo/muro. Transparente/color/imagen/ampliación
en Configuración, cabecera del muro solo Editar pared/Bloquear diseño.
Decoraciones nuevas Imagen sin marco o Sticker con contorno alfa; Póster retirado
del selector, heredados mostrados como imagen. Sin ajustes independientes ancho/alto
ni campo Giro. Doble clic activa ↻ y arrastre gira; otro doble clic vuelve a mover.
R/flechas/Escape como alternativa teclado. Gesto con snapshot, cancelación y guardado
solo al soltar. No cambian geometría/contrato/migraciones/medios existentes.
73 pruebas frontend y build aprobados; check-rotation.cjs en Chrome aislado verificó
flujos, transparencia/contorno y cursor real, con datos/guardados simulados; diálogos
360/768 correctos. Corregida consulta de estado actual al recibir doble clic.
Ver APARIENCIA.md. Persistencia de preferencias sigue por navegador/origen;
pendientes de audio, aceptación y API real continúan. Sin commit creado.

## Tarjetas de fondos, muro y vinilos — 14 de noviembre de 2026

Nueva solicitud implementada: todos los controles con marco/superficie opaca,
incluidos Inicio/Biblioteca/Explorar; selector de fondos en dos columnas con
miniaturas y marca de selección como captura adjunta. Imagen del muro separada
del fondo del álbum, ajustable y reversible con Transparente/Color del muro.
Lienzo sin tope de altura de ventana, mayor anchura y botón Ampliar muro; conserva
10:7 y datos BD. Presentación Vinilos/Portadas en biblioteca, con elección por
álbum en detalle y herencia de la predeterminada; preferencias por navegador/origen.
La apariencia de playlists en BD permanece disponible, sin cambio de API.
71 pruebas y build aprobados. Chrome aislado verificó galería, controles sobre
blanco, imagen del muro, ampliación y vinilos/portadas/recarga; Canvas real,
upload/lectura del asset simulados para evitar datos de prueba en principal.
Capturas escritorio y 360/768 revisadas. Ver APARIENCIA.md. Sin cambios backend,
migraciones, audio automático o API IA; pendientes anteriores conservados.

## Fondos y transparencia — ampliación del 14 de noviembre de 2026

Petición vigente: quitar recuadro de personalización, recuperar transparencia,
volver a estilos predeterminados y ajustar imágenes como wallpaper, con fondo
principal y otro opcional por álbum. Implementado diálogo desde Configuración o
Fondo del álbum; eliminado marcador vacío/marco de edición. Transparente y Color
del muro son reversibles por álbum sin borrar el color/composición en BD.
Principal y overrides con herencia; estilos synthwave/vaporwave/imagen recuerdan
imagen guardada al cambiar de modo. Ajustar/rellenar, zoom/posición y preview con
proporción de ventana. Preparación Canvas de copia JPEG <=2560px/5MiB desde
PNG/JPEG/WebP <=25MiB/48MP/16384 por lado; original intacto. Almacenamiento de
preferencias por navegador/origen, no sincronización en BD ni otros equipos.
69 pruebas frontend/build aprobados. Chrome aislado comprobó transparencia,
herencia/estilos, copia 4000x2000 a 2560x1280, encuadre y recarga. Subida/respuesta
de imagen simuladas explícitamente para evitar recursos de prueba en principal;
no acreditan upload HTTP real. Capturas 1280 y diálogo 360/768 inspeccionadas.
Ver APARIENCIA.md. Sin backend/migración/llamadas IA; pendientes previos vigentes.

## Solicitud visual posterior a P28 — 14 de noviembre de 2026

Ahora el usuario pide aproximar apariencia a Refrencia.png: vaporwave/synthwave,
paleta/degradados/fondo editables y muro abierto como referencia. Reemplaza la
restricción anterior de referencia solo estructural; mantener nombre EchoBeats.
Implementados paneles neón azul/morado/rosa/cian, rejilla estática en perspectiva,
sidebar compacta con vinilo, portada provisional SVG original, muro integrado con
escena y reproductor compacto. No se insertaron objetos ni se tocaron diseños BD.

Configuración → Tu atmósfera: seis colores, ángulo, presets, rejilla, PNG/JPEG y
modo muro escena/color de álbum. Preferencias localStorage por navegador/origen,
no BD ni otros PCs; imagen gestionada por backend y selección local. Fallo de
persistencia informa sesión; quitar/reset no borra archivos. Elegir color desde
editor activa modo álbum sin perder valores previos. Validación CSS/URLs estricta.
65 pruebas frontend y build aprobados. Capturas headless de escritorio y marcos
360/768 inspeccionados; no teclado/escucha/recorrido de configuración completo.
Ver APARIENCIA.md. Vite polling corrige módulos obsoletos en Docker/Windows.
Sin backend/migración/dependencias/API real; pendientes anteriores y 506 MP3 sin
fila conservados. Página temporal de revisión retirada. Sin commit creado.

## Avance vigente: P28 — 14 de noviembre de 2026

Entrega documental preparada: README práctico y guías INSTALACION, CONFIGURACION,
ARQUITECTURA y GUIA_DEMOSTRACION; respaldo/restauración actualizado. Ver
VALIDACION_P28.md. Preparador Node conserva .env existente; verificador crea
proyectos únicos sin clave OpenAI ni copia del .env personal. Frontend Dockerfile
incluye script de auditoría importado por tests. Helper restore acepta UTF-8 BOM,
con rechazo de hash inválido previo a operaciones verificado mediante mocks.

Arranque final echobeats_p28_83f7845a aprobado: base/medios vacíos, Dockerfiles/locks
(caché posible), migración 0009, pip/alembic check, build y 62 pruebas frontend
dentro del contenedor; importación/rangos/proxy y audio íntegro tras recrearlo.
Dump real pg_dump/pg_restore hacia echobeats_restore_p28 en ese PostgreSQL aislado:
fuente/restaurada una pista y 0009. Copia de un medio aparte con hash coincidente.
Demo detenida, datos/credenciales/volúmenes conservados en data/<proyecto>; informe
resultado.json y backup.json. Intentos previos guardados: fallo HTTP/harness y
limitación MEDIA_ROOT relativo que no acreditaba persistencia fuera del contenedor.
Ruta absoluta/recreación verificadas en el intento final; principal ya las fijaba.

No nueva corrida backend: conservar última P27 241/62 y sus límites. Sin API real,
--live ni corpus indexado personalmente. No escucha/navegador/máquina externa
validados; instalación nativa queda opcional no verificada como limpia. Conservar
506 MP3 sin fila y todos los datos privados. P28 no cierra el MVP; siguen
pendientes P08/P15/P16/audio/P20–P27, API/evaluación y definición docente.
Siguiente trabajo: cerrar esos pendientes cuando herramientas/créditos lo permitan
y el usuario lo solicite; no activar Oxx ni inventar P29. Sin commits creados.

## Avance vigente: P27 — 14 de noviembre de 2026

Revisión automática/correcciones listas: páginas de pistas 98→4 sentencias SQL y
álbumes 74→4 en fixture de 24, conservando contrato/créditos/portadas manuales e
heredadas; metadatos solo se montan al abrir el editor por primera vez y después
conservan borrador; imágenes verifican regularidad/tamaño/apertura con 404/503
seguros; lazy/async de imágenes; nombre de diálogo de álbum y cierre nativo de
ficha, foco visible frente al reproductor y sobre fondos personalizados.
241 pruebas backend/62 frontend y build aprobados. Sin migración, paquetes ni
regla nueva de ranking. Auditoría acotada de árbol/build/valores privados y últimas
2000 líneas de logs sin coincidencias; no imprime claves ni certifica historia
completa o seguridad comercial. scripts/revisar_secretos.mjs; ver
REVISION_CALIDAD_P27.md y VALIDACION_P27.md para mediciones y límites.

Sin llamadas reales OpenAI, solo proveedor simulado (1 embedding + 1 selección,
5 fuentes/599 bytes en fixture). Conservar clave privada, 506 MP3 sin fila,
medios, volúmenes y respaldos. Visual/lector de pantalla/teclado/densos/360–1280,
escucha/seek y API real siguen pendientes; no declarar WCAG, latencia real ni
MVP completo. P26 y pendientes anteriores vigentes, P27 abierto para revisión
visual. Próximo P28 cuando lo solicite el usuario; no se creó commit.

## Avance vigente: P26 — 14 de noviembre de 2026

Integración verificada con servidor HTTP real en BD/medios aislados, tres procesos
sucesivos: importación/duplicados, edición manual, playlist/imagen, muros A/B con
PNG/GIF/preview/transformaciones, recursos, rangos y reset persistentes. Fallos
simulados de cuota/timeout/respuesta inválida y recuperación conservan catálogo,
playlist, favoritos y audio por bytes. Controladores integrados frontend también
verificados con doble de audio. 237 pruebas backend/61 frontend y build aprobados.
Informes en data/validation; matriz CA-01–CA-13 en MATRIZ_ACEPTACION_P26.md y
protocolo RECORRIDOS_P26.md. No declarar escucha, navegador ni API real aprobados.

Hallazgo corregido: al recrear Settings, helpers de P21–P25 podían heredar MEDIA_ROOT
personal aunque usaban BD aislada. Se rectificaron validaciones anteriores y el
fixture autouse ahora fija medios temporales, clave vacía e IA/worker desactivados.
Ver HALLAZGO_AISLAMIENTO_P26.md. Principal: diez assets con hash/tamaño correctos,
cero faltantes/staging; 506 MP3 sin fila (49.487.414 bytes) conservados, sin atribuir
origen individual ni borrar. Huella antes/después de regresión corregida: 516
archivos, 83.797.981 bytes, mismos hashes, sin modificaciones. No limpiar por defecto.

Sin migración, nuevas dependencias ni llamadas reales. .env/volumen/respaldos
conservados. CA-13 no aplica por reconocimiento aplazado. Pendientes de teclado,
360/768/1280, escucha/seek y CA-10/CA-11 reales siguen vigentes; P26 queda abierto.
Falta node_repl para Computer Use; no fingir revisión visual con tests/HTTP.
Próximo bloque P27 a petición del usuario; no se creó commit.

## Avance vigente: P25 — 14 de noviembre de 2026

Preferencias optativas en Explorar y consulta/similares: off por defecto,
favorites intercambia pares contiguos del top K si el segundo es favorito y el
primero no (máximo una posición), discovery excluye favoritos antes de recuperar.
Sin favoritos se conserva orden; no añadir favoritos ajenos, alterar scores,
aprender gustos ni registrar escuchas. No se usan decoraciones. Comparación
local de orden base/mostrado y razón por pista sin repetir proveedor. Al terminar
generación se revalidan fichas/filtros/referencia/favoritos y se reconstruye orden.
No se envían flags de preferencia a generación. 232 pruebas backend/60 frontend y build
aprobados. Sin migración, escrituras personales, medios/vectores/.env ni llamadas
reales. Leer PREFERENCIAS.md y VALIDACION_P25.md. Evaluación musical y recorrido
visual/teclado pendientes; P20–P23 y audio/visuales previos conservados. Próximo
P26 a petición del usuario; no se creó commit.

## Avance vigente: P24 — 14 de noviembre de 2026

Favoritos locales implementados, con botones compartidos en biblioteca/álbum,
playlists, reproductor y Explorar. Listado Biblioteca → Favoritos con búsqueda,
páginas y cola filtrada. Sin cambios de ranking ni historial de escucha. Estado
confirmado, PUT idempotente, sin reintentos automáticos ni éxito optimista; ante
respuesta incierta consultar antes de otro cambio. Al reenfocar se revalida estado.
0009_favorites aplicada tras respaldo privado pre_p24_b4bb939c. 222 pruebas backend,
57 frontend y build aprobados. No se alteraron favoritos personales durante las
pruebas, medios, vectores ni .env; IA desactivada y sin llamadas reales.
Docker encontrado en Programs/DockerDesktop del usuario; no se instaló software.
Leer FAVORITOS.md y VALIDACION_P24.md. Revisión visual/teclado pendiente por falta
de node_repl; conservar pendientes anteriores y P20–P23 reales. Próximo P25,
cuando el usuario lo solicite. Sin commit creado.

## Avance vigente: P23 — 14 de noviembre de 2026

Explorar implementado con modos, filtros, similares, fuentes versionadas y cola
exacta en reproductor compartido. Textual y sin generación por defecto; ninguna
llamada ni reproducción automática. Selección de citas con IA explícita, máximo
cinco fichas, sin audio. Solo citas literales verificadas; no se publica prosa
libre. Fallos conservan descripciones registradas. Nueva instantánea tras red
revalida fichas, referencia y filtros. Sin umbral calibrado son candidatos.
213 pruebas backend/51 frontend y build aprobados. Sin llamadas reales por solicitud previa,
sin migraciones/dependencias ni cambios en .env/índice/medios personales. Leer
EXPLORACION.md y VALIDACION_P23.md. P20–P23 conservan cierre real/evaluación;
revisión visual bloqueada por host de navegador y ventana minimizada. No cerrar
criterios reales con proveedores simulados. Pendientes visuales/audio previos
vigentes. Próxima implementación prevista P24; no se creó commit.

## Avance vigente: P22 — 13 de noviembre de 2026

El usuario autorizó P22. API de recuperación exacta por coseno, textual/híbrida
RRF(60), filtros álbum/playlist y similares por referencia implementadas. Datos
vigentes por versión/hash/modelo/receta y metadatos; nueva instantánea tras red.
Sin transacción abierta durante proveedor ni explicaciones LLM. Sin umbral
calibrado se devuelven candidatos, nunca confianza o pertinencia garantizada.
Evaluador P17 de informes guardados sin red, sin certificar API/origen de vectores.
197 pruebas backend, 45 frontend y build aprobados; pruebas aisladas y proveedor
simulado. Sin llamadas OpenAI ni cambios de vectores/medios/.env personales.
P22 no requiere migración. Ready/rutas y búsqueda lexical local verificados.
Leer RECUPERACION_SEMANTICA.md y VALIDACION_P22.md. P20/P21/P22 conservan cierre
real y evaluación pendientes por créditos/petición del usuario; no repetir llamadas.
Interfaz Explorar y explicaciones siguen en P23, próximo paso de implementación.

## Avance vigente: P21 — 13 de noviembre de 2026

El usuario autorizó P21 aunque P20 conservara prueba real pendiente, y confirmó
después: «Aún no; deja la prueba real pendiente» respecto a créditos API. No repetir
llamadas mientras no se resuelva y se reanude esa prueba. P21 implementa pgvector
1536, index_description en cola durable, versión/hash/modelo/receta description-v1,
publicación atómica y controles/API de índice. Vectores viejos se conservan y no
se presentan vigentes. 175 pruebas backend (ocho P21), 45 frontend y build aprobados,
con proveedor simulado solo en bases aisladas. 0008 aplicada tras respaldo; ready
y columna 1536 verificados. Cero vectores en principal; sin nuevas llamadas OpenAI.
Leer EMBEDDINGS.md y VALIDACION_P21.md. P20/P21 no cerrados por falta de prueba real;
UI pendiente por host no disponible. Próxima implementación prevista P22.

## Avance vigente: P20 — 13 de noviembre de 2026

El usuario autorizó P20 y configuró OPENAI_API_KEY en .env privado; no registrar
valor. Adaptadores OpenAI REST con httpx existente: text-embedding-3-small/1536
y gpt-6-luna/Responses/JSON Schema, sin herramientas ni audio. Timeout/límites,
validación de citas, errores seguros y estado de configuración sin consumo.
Integración permanece desactivada por defecto. Dos intentos reales de embedding
con texto sintético fijo devolvieron 429; el segundo identificó
credit_balance_exhausted. No hubo llamadas validadas ni generación; no repetir
hasta resolver créditos API, no marcar P20 cerrado. Recibos privados en data/ai_checks.
Ver INTEGRACION_IA.md y VALIDACION_P20.md. Pruebas simuladas separadas de consumo
real; 167 pruebas backend (32 IA), 45 frontend y build aprobados. UI pendiente por host no disponible.
P21 previsto, pero depende de cerrar prueba real de P20. Preservar pendientes previos.

## Avance vigente: P19 — 13 de noviembre de 2026

El usuario autorizó P19. Fichas actuales/historial, editor por pista, ETag de
creación/edición, evidencia por atributo y fuentes manual/verified/metadata.
Emoción/energía/contexto son interpretaciones manuales; no source=model público.
Ficha incompleta no impide audio. Si deriva de metadatos, cambios de revisión
la señalan metadata_stale sin sobrescribirla. Versión/hash preparan reindexación,
pero no hay embeddings. P18 nunca sobrescribe fichas. Leer FICHAS_MUSICALES.md
y VALIDACION_P19.md. Cinco propuestas P17 verificables por generador, sin emociones
provisionales; cargador por hash simula por defecto y conserva fichas existentes.
135 pruebas backend y 45 frontend aprobadas; build aprobado. 0007 aplicada tras
respaldo privado; API lista. Corpus probado solo en bases aisladas, sin importarlo
a biblioteca personal. UI pendiente por host de navegador no disponible; mantener
pendientes anteriores. Próxima implementación P20, proveedor/configuración de IA.

## Avance vigente: P18 — 13 de noviembre de 2026

El usuario autorizó P18. Implementados trabajos PostgreSQL y trabajador local
exclusivo, estados/versiones, adquisición/CAS, recuperación tras interrupción,
reintentos explícitos hasta tres intentos, API y controles por canción. Operación
prepare_metadata prepara datos existentes con procedencia; no es análisis acústico,
ficha ni embedding. Leer PROCESAMIENTO.md y VALIDACION_P18.md antes de P19–P21.
120 pruebas backend aprobadas; ocho P18 repetidas tras ajuste final; 42 frontend
y build aprobados. Respaldo privado previo; 0006_processing_jobs aplicada y backend
reiniciado. Ready y rutas comprobados por HTTP; bloqueo exclusivo confirmado.
UI pendiente por host de navegador no disponible. Mantener pendientes anteriores.
Próxima implementación P19: fichas musicales estructuradas y trazables.

## Avance vigente: P17 — 13 de noviembre de 2026

El usuario autorizó P17. Completada preparación de evaluación: cinco fragmentos
musicales originales de síntesis en pruebas/semantica, manifiesto/hash/procedencia,
18 consultas y diez casos de fallo. Protocolo en EVALUACION_BUSQUEDA.md; evidencia
en VALIDACION_P17.md. Se verificaron WAV, hashes y coherencia de casos sin APIs.
No confundir anotaciones emocionales editoriales pendientes de escucha con hechos
verificados del generador. Las reservadas no se usan para ajustar prompts/modelos.
No se importó corpus ni se crearon fichas/embeddings. P19 vinculará Mxx con UUID
por hash; siguiente implementación P18. No hay evidencia de IA ni CA-10/CA-11
superados todavía. P08/P15/P16/audio conservan sus recorridos manuales pendientes.

## Avance vigente: P16 — 13 de noviembre de 2026

El usuario autorizó P16. Implementado autoguardado a 700 ms, cola de composición
reciente sin sobrescribirla con respuestas anteriores, restaurar guardado y reset
persistente con confirmación y ETag. Mantener borrador al fallar, sin reintentos
inciertos. Navegación advierte que una escritura enviada podría completarse.
42 pruebas frontend aprobadas. Ver VALIDACION_P16.md. Revisión visual pendiente:
Computer Use informó que el host de acceso al navegador no está disponible.
CA-06/CA-07 con cierre/reinicio siguen pendientes; P15/P08/audio no se dan por
cerrados. P15 registrado por el usuario en 97f797a. Próxima implementación P17.

## Avance vigente: P15 — 13 de noviembre de 2026

El usuario autorizó P15. Implementados ancho/alto 3–60 %, giro normalizado,
orden de capas y selector para recuperar objetos tapados. El ajuste geométrico
conserva el rectángulo girado dentro del lienzo 1000 × 700; guardado con la API
existente, sin migración. 33 pruebas frontend y build aprobados. Ver VALIDACION_P15.md.
Revisión visual pendiente: Computer Use no pudo determinar la URL de Brave y
detuvo el control. No cerrar P15 hasta revisar teclado y 360/768/1280. Próxima
implementación P16. La imagen sigue siendo referencia estructural opcional.

## Referencia visual del usuario — 13 de noviembre de 2026

El usuario agregó `Refrencia.png` en la raíz (la llamó «Referencia») y pidió
verla y conservar su estilo/concepto para el desarrollo futuro, sin implementar
cambios visuales ahora. Se inspeccionó la imagen. El plan continúa: próximo P15.

**Aclaración posterior del usuario (prioritaria):** es solo una referencia de
estructura y posibilidades de personalización. EchoBeats no debe venir por
defecto con esa estética ni reproducir esa composición. Centrarse en la relación
entre panel musical, pared editable y reproductor, y en la libertad del usuario
para construir su propio espacio. El collage/neón es un resultado posible si
el usuario lo elige, no un tema obligatorio ni una pared precargada. La apariencia
predeterminada queda por definir y no se deduce de esta imagen.

Estilo particular de la composición mostrada, opcional para el usuario:
ambiente musical inmersivo, oscuro y retrofuturista,
con estética synthwave/neón, tonos azul noche/negro y acentos cian, magenta y
violeta. Fondo cuadriculado con una zona inferior de rejilla en perspectiva;
brillos y bordes luminosos como acentos, sin convertirlos aún en valores CSS.

La música permanece accesible: cabecera compacta, panel izquierdo de portada,
vinilo y pistas, y reproductor compacto en la parte inferior. El área principal
es una pared/collage personal con pósteres, ilustraciones y stickers de bordes
recortados, tamaños y giros distintos, superpuestos de forma expresiva. Motivos
de astronautas, espacio, sintetizadores y arte musical refuerzan el ambiente.
Importa el concepto de una habitación/pared musical propia y vivida, con la
decoración como parte central de la experiencia.

La imagen orienta el estilo; no es una especificación exacta ni autorización
para copiar recursos ajenos o reproducir cada detalle. Sus textos «Dream Radio»,
«Alex», marcas y nombres de pistas son ilustrativos: el producto sigue siendo
EchoBeats. Tampoco habilita cuentas, favoritos, aleatorio/repetición u otras
funciones por aparecer dibujadas; conservar el alcance y las decisiones vigentes.
Al refinar la interfaz, adaptar la estructura y la personalización a legibilidad, teclado, movimiento
reducido, ventanas pequeñas y separación entre controles de audio y decoración.
Esta sesión solo guarda la referencia: no cambia código, diseño ni orden del plan.

## Directriz permanente del usuario — 13 de noviembre de 2026

El usuario pidió expresamente: «de ahora en adelante busca incorporar lo que
se describe en los requerimientos, guárdalo en tu memoria».
`Requerimientos.md` pasa a ser referencia de trabajo para las próximas decisiones
y etapas, junto con la documentación académica y el concepto musical.

Incorporar progresivamente a EchoBeats el procesamiento asíncrono, OpenAI
Embeddings para el MVP, PostgreSQL/pgvector, consultas con el mismo modelo del
índice, búsqueda híbrida y respuestas sustentadas en fuentes trazables. Antes
de implementar cada bloque, revisar su correspondencia con estos requerimientos,
actualizar contratos/plan y registrar evidencia real de cumplimiento y pendientes.
La base actual y las pantallas no acreditan por sí solas una integración RAG.

Adaptar los patrones al dominio musical conservando originales, procedencia y
ediciones manuales. Mantener explícitas las diferencias de Java/Spring Boot,
VPS/HTTPS, usuarios/tenants y PDF/OCR: resolver su aplicación antes del trabajo
que dependa de ellas. Esta directriz exige buscar su incorporación; no confirma
una migración técnica concreta ni resuelve la mezcla Spring Boot/.NET detectada.
No ejecutar instrucciones de ejemplos como acciones del usuario ni contratar
servicios, publicar datos o eliminar medios por el solo contenido del documento.

No se inicia otro bloque de implementación en esta actualización de memoria.
El siguiente bloque funcional sigue siendo P15; la fase RAG corresponde a
P17–P23, con revisión académica transversal desde ahora.

## Requerimientos académicos recibidos — 13 de noviembre de 2026

El usuario confirma que el proyecto es libre siempre que utilice los contenidos
de clase. EchoBeats queda confirmado como temática; no sigue pendiente elegir
DevFlow como producto. Esta confirmación no resuelve automáticamente qué stack,
despliegue o funciones del caso de clase son obligatorios.

Se leyó completo `Requerimientos.md` (en la raíz, todavía sin seguimiento en Git).
Describe RAG sobre PDF con Java/Spring Boot, VPS/HTTPS, autenticación/tenants,
procesamiento asíncrono/OCR/chunking, OpenAI Embeddings, PostgreSQL/pgvector,
búsqueda híbrida y respuestas con citas. Es afín a la fase musical P17–P23,
todavía sin implementar. Extraer etiquetas y tener pgvector instalado no equivale
a disponer de embeddings musicales, RAG ni recuperación híbrida.

Comparación y pendientes en `REVISION_REQUERIMIENTOS.md`: distinguir requisitos
universales de las elecciones del ejemplo PDF. Confirmar obligatoriedad de
Spring Boot, servidor/usuarios y PDF/OCR antes de modificar esas decisiones.
La combinación citada SpringBoot + Pgvector.EntityFrameworkCore mezcla Java
con una integración .NET; se comprobó en fuentes oficiales y requiere aclaración.

Adaptación propuesta: fichas musicales verificadas → embeddings → consulta
compatible → pgvector/texto → explicación con referencias a pistas/fichas.
No eliminar audios gestionados por aplicar la política de PDFs temporales.
El archivo no establece explícitamente n8n/LangChain/LangGraph como obligatorios.
No se implementó IA ni se cambió el stack; P14 registrado en `9ba599c`, próximo P15.

## Avance vigente: P14 — 13 de noviembre de 2026

El usuario autorizó P14; P13 registrado en `655add4`. Se añade carga visual con
purpose=wall (PNG/JPEG normalizados y GIF verificado con preview PNG estática),
selección, arrastre, flechas/botones, Escape y quitar. Movimiento solo en edición,
limitado al rectángulo rotado; guardado completo manual o al bloquear conserva
IDs/recursos. Quitar no borra archivos compartidos. P15 añadirá giro/tamaño/orden;
P16 completará autosave/restablecimiento/coordinación integral.

Límites: 5 MiB, 4096 por lado/16 millones de píxeles, GIF hasta 200 fotogramas y
32 millones de píxeles decodificados totales. Lectura añade static_preview_url.
Sin dependencias ni migraciones nuevas. Carga y composición son transacciones
separadas: un recurso importado de un borrador descartado puede quedar registrado
sin uso; conservarlo y no limpiar automáticamente.

112 pruebas backend y 29 frontend, build, esquema y dependencias correctos.
Chrome verificó GIF local real, preview/movimiento reducido, carga inválida,
arrastre, Escape, teclado, quitar, bloqueo y anchos 360/768/1280. Reinicio backend
conservó composición y ETag; B y recursos retirados intactos. Audio siguió
avanzando al mover/guardar/bloquear, sin acreditar escucha audible. Auditoría
correcta; 2 originales de audio conservan SHA-256. Ver VALIDACION_P14.md.

Solo álbumes «Demostración P14 A/B» y recursos sintéticos nuevos; no se alteraron
canciones del usuario. Servicios activos, Chrome cerrado, datos/configuración/
respaldos conservados. Pendientes anteriores vigentes. Sin commit automático.
Siguiente implementación: **P15, rotar, redimensionar y ordenar elementos**.

## Avance vigente: P13 — 13 de noviembre de 2026

El usuario autorizó P13; P12 ya estaba registrado en `4c5c0d4`. La vista de álbum
muestra portada/datos/pistas y muro proporcional con fondo/elementos persistidos,
separado del reproductor compartido. Arranca bloqueado; editar permite cambiar
color y guardar, y bloquear guarda el borrador antes de cerrar la edición.
PUT versionado conserva elementos; cargas/respuestas antiguas se descartan.
Conflicto/resultado incierto conserva el color y requiere recargar antes de
reescribir. Advertencia básica al salir con pendientes; P16 ampliará guardados.

25 pruebas frontend, TypeScript/build y recorrido Chrome headless correctos.
Anchos 360/768/1280, teclado, bloqueo de arrastre, persistencia/aislamiento A/B,
foco móvil visible y audio avanzando al navegar/alternar modos. Fallo simulado,
conflicto real y recurso ausente comprobados. GIF/movimiento reducido probado
con fixture de respuesta temporal, sin GIF insertado en la colección real.
No se acredita escucha audible ni se cierran revisiones manuales anteriores.
Auditoría sin faltantes/huérfanos/staging; solo se cambió el color del muro de
«Demostración P12 A». Servicios activos, Chrome temporal cerrado.

Sin cambios de backend, dependencias ni migraciones. No hay manipulación de
objetos todavía: P14 añadirá carga/movimiento/borrado; P15 transformaciones;
P16 guardado integral. Ver VALIDACION_P13.md. Sin commit automático.
Siguiente implementación: **P14, añadir/mover/eliminar recursos visuales**.

## Avance vigente: P12 — 13 de noviembre de 2026

El usuario autorizó P12; P11 ya estaba registrado en `12bd0e5`. Migración
`0005_album_walls`: wall/wall_element, backfill de álbumes existentes y creación
transaccional de muro en álbumes manuales o importados. Fondo inicial #242038,
formato/revisión 1. GET/PUT/reset con ETag/If-Match, validación de geometría
rotada/recursos y reemplazo atómico. No se eliminan archivos al quitar elementos.
Los conflictos versionados informan revisión y ETag actuales. Downgrade de 0005
rechaza diseños guardados para evitar pérdida; solo se probó en bases aisladas.

102 pruebas backend superadas, esquema sin diferencias, dependencias/OpenAPI y
auditoría correctos. Respaldo previo local con hash conservado. Comparación HTTP
antes/después confirma catálogo intacto; dos muros de demostración A/B conservan
composición y ETag tras reiniciar backend. Álbumes de demostración vacíos e imagen
sintética; canciones del usuario intactas. Servicios activos y volumen/medios/.env
conservados. Ver VALIDACION_P12.md para evidencias y límites.

P12 implementa backend y persistencia; no hay editor visual todavía. No cierra
CA-06/CA-07 visuales ni los pendientes P08/P09/P10/O06. Sin commit automático.
Siguiente implementación: **P13, vista del muro y modos de edición/bloqueo**.

## Contexto confirmado y estado vigente — 13 de noviembre de 2026

El usuario pidió revisar nuevamente los dos adjuntos y el plan de desarrollo,
comprenderlos y conservar el contexto. **EchoBeats** es el nombre definitivo;
Dream Radio es el nombre histórico del concepto. Esta solicitud es de revisión
y memoria documental; no inicia P11 ni autoriza ejecutar los laboratorios.

Se revisó el contenido textual de los adjuntos de Descargas y el plan existente.
Ambos adjuntos coinciden byte por byte con las referencias ya conservadas:

- `LangChain_LangGraph2026 (4).md`: 6356 líneas; SHA-256
  `d24a621f44fd9bb100c71f55434bec4780f43ff852932ce53848ea7f3879053f`.
- `Dream_Radio_Documento_Concepto_y_Planificacion.md`: 691 líneas; SHA-256
  `edd4a98148e01df1b75922831277b65b28489fd393e59b7a01bb30c600326416`.

No se duplican ni reemplazan las fuentes. La guía académica es la referencia
técnica aportada: prompts, contexto, HTTP/APIs, embeddings, recuperación/RAG,
LangChain/LCEL, mensajes, validación estructurada y Streamlit, además del marco
curricular de n8n/agentes. Sus ejemplos no sustituyen las decisiones vigentes
del repositorio ni certifican versiones, precios o disponibilidad de servicios.
Las imágenes externas enlazadas no forman parte de esta revisión textual.

La prioridad del producto sigue siendo biblioteca propia y reproducción,
playlists editables, muros independientes por álbum con persistencia real y
exploración semántica explicable sobre canciones existentes. pgvector y una API
de IA real son requisitos; embeddings textuales, análisis acústico e identificación
de grabaciones se mantienen como capacidades distintas. Proveedor/modelos de IA,
colección musical de evaluación y requisitos docentes concretos siguen pendientes.

Git confirma O06 en `e53aa4b`, después de P09/P10 en `6e001a0` y P08 en
`ddd5b20`. El próximo bloque de implementación es **P11: playlists**. P08 conserva
la revisión visual de teclado y anchos 360/768/1280; P09/P10/O06 conservan sus
recorridos manuales de reproducción, seek y continuidad según corresponda.
Registrar un commit no acredita esas comprobaciones. Los estados «sin commit»
de entregas anteriores son históricos y quedan supersedidos por este registro.

Solo se actualizó documentación de continuidad; no se instalaron dependencias,
iniciaron servicios ni ejecutaron pruebas funcionales en esta revisión.

## Avance vigente: P11 — 13 de noviembre de 2026

El usuario autorizó iniciar P11. Implementadas API con ETag/If-Match y bloqueo
transaccional, pestaña de playlists, crear/renombrar, añadir/quitar/subir/bajar
pistas, imagen PNG/JPEG y apariencia vinilo/tarjeta. Usa tablas de P05 sin migrar.
El reproductor recupera la lista guardada en orden; editar no cambia álbumes.
Guardados de ficha y secuencia se serializan; se informa un posible éxito parcial
y se conserva el borrador ante error. No hay borrado de listas ni muro por lista.

76 pruebas backend y 16 frontend, build, pip check y esquema correctos. Chrome
headless permitió crear/editar/recargar, subir imagen, revisar anchos 360/768/1280
y comprobar avance del audio sin acreditar escucha audible. Ver VALIDACION_P11.md.
Los pendientes manuales de P08/P09/P10/O06 se conservan. Sin commit automático.
Siguiente implementación: **P12, muros persistentes por álbum**.

Este entorno no tenía .env ni recursos Docker EchoBeats; se generaron sin tocar
otros proyectos. Se conservan dos pistas sintéticas y «Selección P11 verificada» con
imagen sintética. Volumen, medios y configuración privada se mantienen. Recreación real de
PostgreSQL/backend/frontend conservó la respuesta completa y la imagen; servicios
activos al finalizar para revisión local.

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

## Avance posterior: P09

P08 quedó registrado en `ddd5b20`, conservando su revisión visual pendiente.
El usuario autorizó avanzar P09, que depende de P07. Se implementó GET/HEAD
`/api/v1/tracks/{id}/audio`, resolución de MP3 gestionado y `audio_url` en fichas
y listados. FileResponse de Starlette sirve por bloques con rangos, If-Range,
ETag/fecha, MIME audio/mpeg e inline. HEAD devuelve cabeceras completas sin cuerpo.
Comprueba tipo, ruta, archivo regular, tamaño y apertura; errores seguros de
ausencia/permisos no exponen rutas ni eliminan pistas. No cambia originales,
esquema ni dependencias. El reproductor compartido sigue correspondiendo a P10.

57 pruebas PostgreSQL aisladas con avisos como errores, build y OpenAPI correctos.
Proxy real: HEAD 200, 96.675 bytes; GET bytes=1000-1999 responde 206 y 1.000 bytes.
Brave cargó el MP3 técnico de P08 y reconoció duración de unos 12,084 s; no se
confirmó reproducir/seek porque el control UI detectó actividad del usuario en
la ventana e interrumpió las acciones. No se afirma escucha audible.

Ver `VALIDACION_P09.md`. P09 queda implementado sin commit, con su criterio
manual pendiente; P08 conserva revisión de teclado/anchos. Próxima implementación
P10, manteniendo explícitas ambas comprobaciones pendientes. Sin commit automático.

## Avance posterior: P10

El usuario autorizó avanzar al paso 10 con las comprobaciones manuales anteriores
pendientes. Se incorporó un PlayerProvider con único elemento audio fuera de las
vistas, selección desde Canciones/Álbum y barra de reproducción compartida. Play/
pausa, anterior/siguiente, progreso, seek y volumen; fin de pista avanza y fin
de lista se detiene. Abrir otra vista no cambia pista ni cola. Al recargar no
se restaura ni comienza audio automáticamente.

La cola recupera todas las fichas del álbum/búsqueda, sin descargar sus audios;
play se solicita durante el clic antes de esperar a la lista. Fallo de lista
completa usa la página visible con aviso. Errores de audio, autoplay bloqueado,
pausas externas y promesas/eventos/colas antiguos se gestionan explícitamente.
Correcciones de metadata actualizan la pista activa sin reiniciar el audio.

13 pruebas del controlador/colas en Windows y Docker, con dobles de audio/HTTP;
57 pruebas backend aisladas, builds TypeScript/Vite en ambos entornos y Compose
correctos. Sin nuevas dependencias ni migraciones. Tests frontend montados como
solo lectura en Compose y script `npm test` con node:test.

Brave seguía recibiendo actividad del usuario y el control UI no permitió abrir
la prueba. No se acredita escucha real, seek manual, continuidad audible ni
validación de teclado/tamaños. CA-01/CA-03 y los cierres visuales P08/P09/P10
permanecen pendientes de su recorrido manual; ver `VALIDACION_P10.md`.
P09/P10 siguen sin commit. Siguiente implementación P11; no se crean commits.

## Avance posterior: O06 — Audio multiformato

El usuario solicitó admitir WAV, FLAC, Ogg y otros formatos además de MP3.
Esto habilita O06 expresamente, sin esperar a P11. P09/P10 ya habían quedado
registrados por el usuario en `6e001a0`; sus revisiones manuales siguen pendientes.

Se admiten MP3, WAV PCM entero (8/16/24/32 bits), FLAC nativo, Ogg Vorbis y Ogg
Opus (.ogg o .opus). Mutagen identifica contenido y etiquetas; extensión y contenido
deben concordar. Ogg Opus se guarda con extensión interna .opus, sin cambiar
bytes. No se habilitan AAC/M4A, AIFF, WMA ni otros códecs no comprobados.

ID3 en MP3/WAV; Vorbis Comments, Picture y METADATA_BLOCK_PICTURE en FLAC/Ogg.
Persisten correcciones manuales y originales. MIME real en GET/HEAD y rangos;
audio_mime_type en fichas para avisos canPlayType y errores de decodificación.
Sin conversión automática ni nuevas dependencias de la aplicación.

Migración 0004_audio_formats amplía solo la restricción de claves de medios.
El downgrade se niega si existen medios de formatos nuevos, sin borrar datos.
FFmpeg se usó únicamente en un contenedor temporal para generar y decodificar
cuatro señales propias de 440 Hz/2,5 s con portada y etiquetas; manifiesto y
generador conservados. Quedan importadas como demostración en «Colección
multiformato», sin modificar canciones existentes del usuario.

Pruebas backend aisladas de importación, formatos falsos, bytes/MIME/HEAD/rangos,
metadatos, portadas, duplicados y downgrade seguro; frontend cubre aviso de
formato no anunciado. Build y esquema correctos. Ver `AUDIO_MULTIFORMATO.md`
para los resultados finales y tamaños/MIME. La herramienta de control de Brave
se detuvo al no poder identificar la URL con confianza: no se afirma reproducción
ni seek manual de los nuevos formatos. O06 implementado sin commit, con esa
comprobación pendiente; siguiente implementación principal P11.

Cierre técnico O06: 72 pruebas backend y 14 frontend superadas, build correcto
en Windows/Docker y esquema sin diferencias. Tras recrear servicios, las cuatro
pistas multiformato y el MP3 previo conservan ID, MIME y rangos. Auditoría sin
faltantes/huérfanos/staging. Servicios detenidos, con volumen/.env/medios conservados.
