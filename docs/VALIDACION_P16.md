# P16 — Guardado, restauración y restablecimiento

13 de noviembre de 2026. Implementación completada; recorrido visual de cierre pendiente.

## Comportamiento

El editor programa guardado después de 700 ms sin nuevas acciones. No guarda
durante un arrastre o subida: al terminar, se programa la composición final.
Se conserva «Guardar ahora» y bloquear espera a que se confirmen todos los cambios.
El estado distingue cambios pendientes, guardando, guardado y error.

Una sola escritura por muro. Durante un guardado se puede seguir cambiando fondo,
posición, tamaño, giro y capas; añadir archivos espera a que termine la escritura.
La respuesta confirma únicamente la revisión enviada y conserva el borrador más
reciente. La siguiente escritura usa el ETag confirmado. La comparación canónica
por ID evita falsos cambios por el orden de elementos devuelto por PostgreSQL.
Al salir se cancelan temporizadores y se ignoran respuestas del controlador anterior.

«Restaurar pared guardada» relee la composición del servidor, con confirmación
si se descarta un borrador. «Restablecer diseño» confirma la sustitución del diseño
del álbum, usa POST /albums/{id}/wall/reset con If-Match y recupera fondo inicial
y lista vacía. No elimina recursos importados, audio ni composiciones de otros álbumes.
Si falla, se conserva el borrador anterior y se comunica el error; un resultado
incierto o conflicto requiere releer antes de volver a escribir. No hay reintentos
automáticos en bucle ni almacenamiento adicional del borrador en disco del navegador.

Salir mediante navegación o Atrás/Adelante advierte sobre cambios pendientes u
operaciones activas: cancelar permite esperar o guardar; confirmar descarta lo aún
no enviado. Una petición enviada puede completarse aunque se abandone la pantalla.
Cerrar/recargar pestaña conserva el aviso nativo; no se confía en escribir al cerrar.
Después de un guardado confirmado, reabrir carga la composición y comienza bloqueado.

## Comprobaciones

- `npm.cmd test`: 42 pruebas aprobadas. Nueve pruebas nuevas cubren agrupación de
  cambios, respuesta atrasada con edición nueva, ETag de la siguiente escritura,
  fallo sin bucle, reset persistente/fallido, cancelación al salir, gateway POST,
  arrastre sin escrituras intermedias, reconstrucción de transformaciones y preview
  GIF, y cambios mientras se bloquea el diseño.
- Pruebas del controlador con gateway simulado: no equivalen a un recorrido visual.
- El backend existente prueba composiciones completas A/B, lectura por nueva
  conexión PostgreSQL, reset sin borrar recursos compartidos, conflictos y rollback
  con bases de prueba aisladas (`backend/tests/test_walls.py`).
- `docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error`:
  112 pruebas aprobadas. No se usó la base principal para las pruebas.
- `npm.cmd run build`: comprobación TypeScript y compilación de producción Vite
  aprobadas. `git diff --check`: sin errores.

## Cierre manual pendiente

Se consultó el inventario de Computer Use: no había navegadores conectados y devolvió
`The browser access host is unavailable`. No se hicieron cambios mediante la UI.
Pendiente demostrar CA-06/CA-07 de extremo a extremo: decorar A y B, esperar
«Pared guardada», cerrar/reabrir, reiniciar backend y comprobar objetos, fondo,
giro/tamaño/capas y aislamiento; probar cancelar/aceptar salida y restablecimiento.
Completar teclado y anchos 360/768/1280 junto con el pendiente de P15; comprobar
que las herramientas y el reproductor siguen accesibles. No declarar cerrada la
fase visual con solo las pruebas automatizadas. P08 y audio mantienen sus pendientes.

## Alcance y continuidad

RF-07–RF-10 conservan el alcance local de un usuario y los contratos existentes,
sin dependencias ni migraciones nuevas. La referencia visual orienta estructura y
personalización, sin imponer tema ni objetos iniciales. Requerimientos.md sigue
orientando la futura integración RAG; P16 no acredita embeddings ni IA.
Próxima implementación: P17 (casos de búsqueda y evaluación).
