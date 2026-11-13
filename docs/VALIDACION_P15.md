# P15 — Tamaño, giro y superposición

13 de noviembre de 2026. Implementación lista; cierre visual pendiente.

## Funcionalidad

En un álbum, entrar en «Editar pared» y seleccionar un objeto en el lienzo o
en el selector de objetos, que permite recuperar incluso los completamente tapados.
Modificar ancho/alto (3–60 % del lienzo) y giro (-180 a 180 grados). Los campos
aceptan teclado; un campo vacío o fuera de rango no cambia el objeto y recupera
su valor al salir. 180 grados se normaliza a -180.

«Al fondo», «Una capa atrás», «Una capa delante» y «Al frente» ordenan los objetos.
El selector enumera desde atrás hacia delante. Los empates heredados usan el mismo
desempate por ID que el servidor; al ordenar o añadir se asignan capas consecutivas
0–29. Los extremos deshabilitan las acciones sin efecto.

Se conserva el lienzo de referencia 1000 × 700 y su escalado uniforme. Al transformar,
se calcula el rectángulo envolvente girado: si supera el lienzo se reduce
proporcionalmente y se limita el centro para mantenerlo entero dentro. Las capas
permanecen contenidas por el lienzo con aislamiento y recorte; no cubren reproductor,
datos ni herramientas. No se aplica la estética de Refrencia.png como predeterminada.

Solo se transforma en edición, sin subida, arrastre, guardado o conflicto pendientes.
Se conservan IDs, recursos y previews. «Guardar pared» o bloquear confirma el borrador
con el contrato y ETag existentes. P15 no requiere migraciones. El guardado automático,
restablecimiento y coordinación adicional siguen en P16. La fase RAG continúa en
P17–P23 conforme a REVISION_REQUERIMIENTOS.md.

## Evidencia

- `npm.cmd test`: 33 pruebas aprobadas, incluyendo cuatro nuevas pruebas de
  transformaciones, límites, capas, reconstrucción y bloqueos durante operaciones.
- `npm.cmd run build`: TypeScript y compilación Vite aprobados. esbuild requirió
  ejecutar fuera del aislamiento por acceso denegado a directorios superiores.
- La prueba de reconstrucción del controlador usa un gateway simulado; por sí sola
  no acredita escritura real en PostgreSQL ni interacción visual.
- `docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error`:
  112 pruebas aprobadas con bases aisladas, incluyendo la persistencia y validación
  existente del muro. No se modificó la composición del usuario para estas pruebas.
- `git diff --check`: sin errores de espacios.

## Pendientes de cierre

Computer Use detuvo la inspección de Brave porque no pudo determinar con suficiente
confianza su URL actual. No se hicieron acciones de interfaz tras el bloqueo.
Comprobar manualmente a 360/768/1280 px: seleccionar objetos solapados, cambiar
tamaño/giro con teclado, recorrer capas, guardar y recargar sin saltos; cambiar el
ancho de ventana y verificar recuperación de todos los objetos y acceso al reproductor.
No declarar cerrado P15 hasta completar esta revisión. Los pendientes anteriores de
audio y P08 conservan su estado.
