# Revisión de calidad — P27

14 de noviembre de 2026. Instalación local de un usuario, sin autenticación ni
exposición pública. Revisión de código, HTTP/SQL y pruebas; **no certificación de
accesibilidad, seguridad comercial ni rendimiento en cualquier biblioteca**.

## Hallazgos y resolución

| ID | Evidencia | Resolución y límite |
| --- | --- | --- |
| Q01 Lectura N+1 | Página de 24 pistas: 98 sentencias SQL; 24 álbumes: 74. Cada ficha se leía individualmente. | Resuelto: lectura agrupada de filas/créditos y contadores de álbum. Cuatro sentencias por página no vacía; se preservan orden, créditos, procedencia, portada manual y heredada. Regresión con presupuesto SQL y comparación contra detalle. |
| Q02 Editor oculto carga biblioteca | MetadataEditor se montaba dentro de details cerrado y un contenedor hidden incluso en Inicio; su efecto descargaba todas las páginas. | Resuelto por carga al abrir por primera vez. Después permanece montado para conservar borradores al cerrar/ocultar, sin introducir pérdidas por desmontaje. La descarga completa al activar el editor sigue existiendo; no se afirma paginación de sus selectores. |
| Q03 Errores de imagen | Endpoint visual solo comprobaba existencia, a diferencia de audio: truncado/permisos podían transferir un archivo inválido o producir excepción. | Resuelto: archivo regular, apertura y fstat/tamaño antes de cabeceras; 404 para inválido/faltante y 503 genérico para acceso, sin ruta privada. Regresión para truncado, permiso simulado y symlink externo. No hash en cada GET ni garantía frente a un atacante que modifica disco durante la transferencia. |
| Q04 Diálogo de álbum sin nombre | dialog no tenía aria-labelledby. Ficha se desmontaba sin close nativo explícito. | Resuelto en código: ID único/heading y aria-busy del álbum; nombre contextual/aria-haspopup/expanded en botón de ficha y close nativo antes de desmontar. Foco devuelto/lector de pantalla deben comprobarse en navegador. |
| Q05 Foco bajo reproductor | Protección de foco existía solo en muro; controles externos podían quedar bajo la barra sticky. | Mitigado: revelar foco visible fuera de muro/reproductor/diálogo y descartar callbacks de foco antiguo; muro conserva control de arrastre. Foco doble claro/oscuro en objetos para fondos personalizados; main tiene foco visible. No acreditar teclado/oclusiones a tres anchos sin navegador. |
| Q06 Imágenes de muro ansiosas | Objetos tenían src inmediato sin loading lazy. | Mitigado: loading=lazy y decoding=async en objetos y decodificación async en portadas. Son pistas al navegador, no prueba de descargas evitadas. Medición de red/memoria visual pendiente. |
| Q07 Archivos sin fila P26 | 506 MP3 conservados, con origen individual no demostrado. | Limitado explícitamente: no borrar, reimportar, mover ni etiquetar como basura. Conservar inventario/respaldos y evaluar disposición por separado. No bloquean lectura de los diez assets registrados, cuyos hashes se revisaron en P26. |
| Q08 Alcance de secretos/acceso | Se requiere proteger .env/medios y no trasladar clave al cliente; API es local sin cuentas. | Auditoría acotada y repetible de valores privados/patrones, árbol/build y logs, más pruebas Origin/Host/SQL/rutas/recursos. No equivale a escáner universal, revisión de todas las versiones históricas o auditoría de dependencias/CVE. Sin tenant ni autorización para despliegue público. |

## Mediciones reproducibles

Datos sintéticos en BD/medios temporales: 24 pistas con dos créditos cada una y
24 álbumes; muro de 30 objetos que reutiliza PNG/GIF/preview. Proveedor simulado
en seis fichas aparte. No se usa la colección personal para mutaciones de prueba.

| Métrica | Antes (p27_before.xml) | Después (p27_after.xml) |
| --- | --- | --- |
| SQL página 24 pistas | 98 | 4 |
| SQL página 24 álbumes | 74 | 4 |
| Tiempo observado pistas | 147,647 ms | 35,726 ms |
| Tiempo observado álbumes | 99,682 ms | 16,934 ms |
| Respuesta pistas | 18.020 bytes | 18.020 bytes |
| Respuesta álbumes | 8.516 bytes | 8.516 bytes |

Tiempos de una ejecución local por estado, afectados por cachés/carga; no son
percentiles ni compromiso de latencia. Los tests acotan SQL, no milisegundos.
Los datos de página se comparan con el endpoint de detalle en la misma ejecución.

El muro de 30 objetos produjo 9.717 bytes JSON y tres URLs visuales distintas,
366 bytes de recursos en esta diminuta fixture. No representa GIFs grandes ni
uso de memoria real. El rango de audio 100–199 transfirió exactamente 100 bytes;
HEAD/rangos/ausencia de reproducción automática siguen cubiertos por pruebas.
El único audio compartido no recibe src hasta seleccionar pista.

La prueba de presupuesto de Explorar exige como máximo una solicitud simulada de
embedding y una de selección de citas; hasta cinco fichas, solo ID/versión/texto,
sin audio ni conexión DB retenida durante proveedor. Conservar el costo de red
real como no medido: no se reanudó OpenAI por falta de créditos/petición del usuario.

## Accesibilidad revisada en código

Etiquetas de formularios, botones de audio por nombre, aria-pressed de favoritos,
orden/flechas de muro, selector de objetos tapados, Escape/cancelación y estados
status/alert revisados. GIF usa preview al pausar y respeta prefers-reduced-motion
al inicio y cuando cambia a reduce; la opción explícita de animar sigue disponible.

Contraste calculado para pares sólidos del CSS: texto principal 15,78:1,
nota 10,20:1, texto de botón 11,51:1 y foco principal 15,48:1. Solo esos pares:
no todos los estados, imágenes de usuario, transparencias, foco ni legibilidad a
zoom. No afirmar cumplimiento WCAG a partir de estas cuentas o de atributos ARIA.

Pendiente: Tab/Shift+Tab/Enter/Espacio/flechas, lector de pantalla, zoom/reflow,
360/768/1280, muros densos/GIF grandes, acceso al audio, foco de cierre y ausencia
de oclusión. Protocolo manual en RECORRIDOS_P26.md. La herramienta node_repl que
exige Computer Use sigue ausente; no se sustituye por revisión DOM ficticia.

## Protección y conservación

SQL parametrizado/escape literal y UUID validados, recursos por ID, rechazo de
rutas arbitrarias/symlinks y límites de imágenes/GIF/carga de audio se mantienen
en la regresión. Origin y Host limitan el navegador local; no son autenticación.
Medios originales, .env, volúmenes y backups se conservan. Sin migraciones,
paquetes nuevos ni llamadas reales. Validación e informes en VALIDACION_P27.md.
