# Guía de demostración — EchoBeats

## Condiciones y material

Usar una instalación dedicada según INSTALACION.md; no alterar la biblioteca
personal para una exposición ni simular pérdidas sobre sus archivos. El verificador
P28 conserva un proyecto bajo data/echobeats_p28_<id>, con URLs/configuración en
resultado.json. Reabrir con su compose.json/.env/proyecto exactos; al terminar stop,
sin borrar volumen. Su biblioteca empieza vacía y queda con una pista sintética
tras la validación. Para otra demostración desde cero, generar otro proyecto.

Material del repositorio:

- pruebas/coleccion: tonos sinusoidales originales T01–T04 y variantes para
  importación/errores. manifiesto.json y README registran hashes y construcción.
- pruebas/coleccion/multiformato: WAV PCM, FLAC, Ogg Vorbis/Opus y MP3 de prueba,
  con manifest de hashes/metadatos. No son grabaciones de terceros.
- pruebas/semantica: M01–M05, fragmentos musicales de síntesis sin samples/voces,
  fichas, consultas, grados y particiones P17. Las emociones provisionales no se
  convierten en hechos ni se usan reservadas para ajustar prompts/umbrales.
- PNG/JPEG/GIF propio autorizado para el muro/playlist. Las pruebas generan
  imágenes temporales, no un tema visual predeterminado. La imagen Referencia
  orienta estructura/personalización y no debe imponerse como apariencia inicial.

La procedencia autoriza el uso indicado dentro del proyecto; no atribuir licencias
o permisos sobre música externa ni artistas reales. No se descargó un catálogo.

## A. Recorrido local sin proveedor

1. Mostrar ready: BD, pgvector y migraciones ok. Configuración con IA desactivada;
   explicar que este panel no consume ni acredita API real. No mostrar .env ni claves.
2. Biblioteca: importar tono_grave.mp3, pulsos_medios.mp3, tono_agudo.mp3 y
   sin_etiquetas.mp3. Añadir un duplicado y un archivo inválido: resultados por
   archivo, sin duplicar la pista válida ni perder las otras.
3. Buscar título/artista/álbum y término ausente. Abrir sin_etiquetas, mostrar
   provisionales/portada predeterminada, corregir título/artista/álbum y guardar.
   Confirmar procedencia manual y que releer/importar no pisa esos cambios.
4. Reproducir de forma explícita: escuchar play/pausa, avance intermedio y final,
   volumen, anterior/siguiente, límites y avance natural. Abrir otro álbum y
   continuar el mismo audio. Recargar: no comienza reproducción automáticamente.
   Repetir formatos autorizados con soporte del navegador, registrando fallos reales.
5. Crear playlist, renombrar, añadir pistas y guardar orden; elegir PNG/JPEG y
   vinilo/tarjeta. Escuchar orden guardado. Intentar imagen inválida sin perder anterior.
6. En álbum A: activar edición, fondo, PNG/GIF, arrastre/flechas, tamaño, giro,
   capas y selector de tapados. Pausar/animar GIF. Esperar guardado y bloquear;
   intentar arrastrar bloqueado mientras se usa audio. En B: otro diseño.
7. Reiniciar backend del proyecto de revisión. Reabrir A/B, playlist y canción
   corregida: comparar posiciones, tamaño, giro, capas, recursos, imagen/orden y
   metadatos. Reset A con confirmación: B y recursos compartidos siguen intactos.
8. Marcar/desmarcar favoritos desde varias vistas, reabrir y ver Biblioteca →
   Favoritos. Explicar preferencia explícita, sin historial de escucha ni inferencia
   desde decoraciones. No afirmar que se entrenó un modelo.
9. Guardar ficha musical con fuente y evidencia. Describir solo lo respaldado;
   emociones/energía/contexto son interpretaciones manuales. No pulsar Indexar en
   esta parte. Mostrar Explorar sin índice: estado declarado, no éxito inventado.

Registrar navegador/versión, 360/768/1280, teclado/foco, pista/hash, acciones,
esperado/observado y evidencia. Estos pasos son protocolo pendiente de ejecución
visual/escucha; los informes HTTP no acreditan que ya se haya completado.

## B. Evidencia técnica simulada, declarada como tal

Presentar pruebas P26/P27, no hacer pasar sus respuestas por llamadas reales.
Bases echobeats_test_<uuid>, medios temporales y proveedores falsos. Explicar
persistencia HTTP entre procesos/contenedores, CAS, versionado y fallos simulados.
La matriz MATRIZ_ACEPTACION_P26.md separa aprobado técnico de pendiente real.

P27 compara páginas de 24 pistas/álbumes: 98/74 → 4 sentencias SQL; serialización
igual al detalle y preservación de portadas. Tiempos locales no son SLA. Muros de
30 objetos reutilizan recursos; GIF grandes/memoria/red de navegador no medidos.

En simulaciones: cuota/timeout/respuesta inválida conservan biblioteca/audio;
citas fuera de ficha se rechazan, prosa libre no se publica; sin transacción de BD
durante proveedor y revalidación posterior de versiones/filtros/preferencias.
No manipular proveedor o archivos personales para representar el fallo en vivo.

## C. API/vector real y sensaciones — aplazado

**No ejecutar hasta resolver créditos y reanudar explícitamente con el usuario.**
La petición de P28 no revoca la restricción. Tampoco es autorización para --live,
importar/indexar corpus en la principal o activar AI_ENABLED.

Cuando se autorice, usar corpus/datos dedicados y seguir INTEGRACION_IA.md,
EMBEDDINGS.md y EVALUACION_BUSQUEDA.md: recibir éxito real, conservar recibo sin
secretos, indexar fichas elegibles y comprobar modelo/dimensiones/receta en
PostgreSQL. Ejecutar consulta compatible, registrar resultado/fuentes y escuchar.
No representar coseno/RRF como confianza ni calibrar con vectores ficticios.

En Explorar: comparar textual/semántica/híbrida, filtros y similares sin repetir
referencia. Selección de citas es optativa y con consumo separado. Mostrar tabla
P25 y razón de orden, con/sin favoritos sobre los mismos candidatos; descubrir
excluye favoritos antes de K. Cambiar un corazón no repite API ni reordena solo.

CA-10/CA-11 y RF-13/RF-14 quedan pendientes mientras no exista esta evidencia.
CA-13: **No aplica: reconocimiento no incluido**. No cerrar el MVP por tener tests verdes.

## Respaldo, entrega y explicación

Detener escrituras, copiar BD en formato custom + manifiesto/hash y también medios;
conservar configuración privada aparte. Restaurar a una base nueva, nunca sobre
la activa. BASE_DATOS.md detalla comando y requisitos. P28 verifica un roundtrip
en datos sintéticos aislados; no restaura ni limpia la principal.
Para esta demo usar siempre su prefijo Compose específico: el helper Python de
la raíz apunta al proyecto principal y no debe emplearse como si siguiera esta demo.

Explicar el flujo con ARQUITECTURA.md: interfaz/proxy/API, medios por ID, SQL/cola,
worker y API solo cuando se habilite. Presentar locks/migraciones/fuentes y límites,
no claves, logs privados, archivos personales ni builds como prueba de API real.
Confirmar con la rúbrica las diferencias Java/Spring, VPS/tenants y PDF/OCR aún
abiertas en REVISION_REQUERIMIENTOS.md. No migrar ni contratar por inferencia.
