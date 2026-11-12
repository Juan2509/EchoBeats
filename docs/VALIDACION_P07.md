# Validación P07 — Etiquetas, edición y portadas

Fecha: 12 de noviembre de 2026. Implementación funcional de RF-11 y del
recorrido de metadatos de CA-02; reproducción sigue pendiente de P09/P10.

## Entregado

- Lectura ID3v1/ID3v2 con Mutagen al importar y al releer originales existentes.
- Editor de título, créditos, número de pista, portada y asignación de álbum.
- Creación de álbumes y edición compartida de nombre/créditos con aviso en diálogo.
- Procedencia por campo y protección de correcciones manuales, incluso valores vacíos/nulos permitidos.
- Control ETag/If-Match para evitar sobrescrituras entre pestañas.
- Portadas incrustadas y manuales PNG/JPEG verificadas, normalizadas y compartibles.
- Portada predeterminada propia en SVG, sin consultas a servicios externos.
- Migración 0003_metadata; Pillow 13.0.0 añadido con hashes al lock.

## Pruebas ejecutadas

| Comprobación | Resultado |
| --- | --- |
| Suite PostgreSQL aislada con `pytest -W error` | **32 pruebas superadas**, sin avisos. |
| ID3v1 y v2 | Título, artistas ordenados, álbum, número `2/10` y duración correctos. |
| Archivo sin etiquetas | Valores provisionales, artista vacío, álbum desconocido y portada predeterminada, sin fallo de importación. |
| Edición/relectura | Cambios manuales sobreviven a releer y reimportar un duplicado con etiquetas reales. |
| Limpieza explícita de campos | Artistas vacíos, número nulo y portada predeterminada manual no se restauran desde el archivo. |
| Concurrencia de edición | Falta de If-Match devuelve 428; revisión vieja 412; corrección vigente conservada. |
| Agrupación | Mismo título/créditos agrupa pistas; título igual con artista diferente no se mezcla. |
| Corrección compartida de álbum | Renombrar afecta sus pistas; releer y añadir otra pista del grupo original conserva el nombre corregido y el ID. |
| Portada manual del álbum | No se sobrescribe con APIC posterior ni altera la agrupación. |
| Portada inválida | SVG/texto disfrazado de imagen se ignora al importar o se rechaza en subida manual; audio sigue guardado. |
| Aislamiento del álbum desconocido | Portada de una pista sin identificar no aparece en otras de «Sin álbum». |
| Contenido servido | PNG válido y nosniff; un asset de audio no se puede leer por la ruta de portadas. |
| Integridad del original | Bytes y hash MP3 iguales antes y después de extracción. |
| Validación de edición | Títulos vacíos, null no permitido, artistas repetidos, número inválido, duración editable y referencias de portada incorrectas rechazados. |
| Migraciones / modelos | `alembic check` sin diferencias; roundtrip y BD vacía cubiertos en suite aislada. |
| Dependencias | `pip check` sin incompatibilidades. |
| Frontend | TypeScript y build Vite correctos. |

## Prueba HTTP y persistencia reales

Se generó un MP3 técnico específico para P07 con título, artista, álbum y una
portada original de color. Se importó por el proxy de frontend, se comprobó
la extracción y después se corrigieron título, artista, álbum y número por PATCH.
La portada normalizada respondió como PNG. No se editaron canciones del usuario.

Se recrearon contenedores, conservando volumen y MEDIA_ROOT: mismos ID,
revisión, valores manuales y portada recuperados. Una nueva lectura de etiquetas
mantuvo las correcciones. La demostración sintética queda en la biblioteca local
como «Título corregido P07», en «Demostración P07 manual».

Informe de medios al terminar: sin archivos faltantes, huérfanos o staging.
No se reescribió el MP3 ni se enviaron audios a proveedores de IA.

## Límites y continuidad

No hubo inspección visual automatizada en navegador. Los tests HTTP/build no
acreditan por sí solos el diálogo, foco, avisos de cierre o todos los gestos del
editor; se mantienen como comprobaciones visuales para P08/P26.

Los artistas reutilizan la grafía canónica del nombre normalizado; no existe
todavía una herramienta para renombrar globalmente artistas. Las imágenes se
normalizan estáticamente; GIF decorativos se implementan en sus pasos posteriores.
Recursos de portada subidos y no asignados se conservan, sin borrado automático.

La búsqueda textual, dashboard de biblioteca, reproductor, muros y módulos de IA
siguen pendientes. Las revisiones quedan preparadas para futuras invalidaciones
de fichas/embeddings, sin afirmar que esos módulos ya existen.

Documentación de uso en [METADATOS.md](METADATOS.md). Al finalizar se detienen los
servicios conservando datos y configuración. Sin commit automático.
Siguiente: **P08 — navegación y biblioteca visual**.
