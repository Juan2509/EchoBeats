# P28 — Documentación, arranque y demostración

14 de noviembre de 2026. **Entrega documental y comprobación técnica preparadas;
aceptación global/visual y proveedor real pendientes.** No se llamó a OpenAI.

## Entrega

README reorganizado para otra persona; INSTALACION.md, CONFIGURACION.md,
ARQUITECTURA.md y GUIA_DEMOSTRACION.md explican arranque, almacenamiento/modelos,
fuentes, funcionamiento y exposición, sin inventar cierre académico.
BASE_DATOS.md y la matriz de aceptación conservan límites reales.

Preparador Node alternativo al Python, sin sobrescritura ni claves en salida.
Verificador validar_arranque_limpio.mjs genera proyecto único con credenciales
nuevas, clave vacía, puertos locales distintos, PostgreSQL/medios separados y
Dockerfiles/locks existentes. Nunca copia la configuración personal. Verifica
arranque, migraciones, pip/alembic check, frontend build/tests, fixture de audio,
proxy, recreación del backend y bytes persistidos. Detiene solo su proyecto y
conserva datos/configuración/informe; no borra volúmenes.

## Ajustes encontrados durante la comprobación

- La prueba frontend P27 importaba scripts/revisar_secretos.mjs fuera del árbol
  copiado por frontend/Dockerfile. Se incluye ese archivo para que npm test también
  sea repetible dentro del contenedor, sin Git/credenciales en la imagen.
- El helper Python de restore admite manifiestos UTF-8 con BOM de Windows;
  mantiene validación de nombre/hash y rechazo previo a crear destino. Comprobación
  unitaria con operaciones simuladas para BOM/hash inválido; no acredita pg_restore.
- Primer verificador falló una conexión tras etapas Docker bloqueantes. Se evita
  reutilizar keep-alive al comprobar HTTP. El informe inicial se conserva como fallido.
- Otro intento solo reiniciaba contenedor y heredaba MEDIA_ROOT relativo. La copia
  de medios reveló la limitación del harness; se fija /app/data/media y se exige
  recreación más descarga completa. Esa prueba previa no acredita medios persistentes
  fuera del contenedor. No afecta compose.yaml principal, que ya fijaba ruta absoluta.

## Evidencia final

Proyecto **echobeats_p28_83f7845a**, informe local
data/echobeats_p28_83f7845a/resultado.json, resultado passed:

- Credenciales nuevas; preservación al repetir preparador. El preparador Node
  sobre el .env personal existente confirmó conservación byte a byte sin mostrarlo.
- BD/medios vacíos; head 0009_favorites y ready BD/pgvector/migraciones ok.
- pip check y alembic check, construcción desde locks, build frontend y **62 tests
  frontend dentro de la imagen** aprobados. No nueva regresión backend en P28.
- Importación con Origin de la UI de demo, Range exacto, proxy y descarga completa
  tras recrear el contenedor. MEDIA_ROOT=/app/data/media en bind independiente.
- pg_dump custom real, restauración en echobeats_restore_p28 sin reemplazar
  echobeats_demo: ambas con una pista/revisión 0009. Backend/UI detenidos durante
  copia; un archivo de medios aparte con hash coincidente, conservado en media_snapshot.
- Comparación posterior de las 16 tablas públicas: datos lógicos fuente/restaurada
  idénticos, SHA-256 `1dbf7a917ab296afddf11128c5f35b4db54b0737e2035966462e27ad916243c0`.
- Manifiesto local backup.json: SHA-256 del dump
  `fbfc19b645550b69e16377cffeadb1878420ce6d8617231ea049dbd5ce6f3680`;
  includes_media=false: la copia de medios es separada. Volumen/archivos preservados.
- Proyectos P28 detenidos, no borrados. El primero d85662c2 quedó fallido; el
  017ae270 solo demostró reinicio sin recreación y no acredita medios en volumen.
  El resultado final anterior es el que acredita persistencia de archivo tras recrear.
- Seis guías/README revisadas: 23 enlaces locales, ninguno ausente; sintaxis de los
  dos scripts Node comprobada. Auditoría acotada de 230 archivos/build y últimas
  2000 líneas del backend sin coincidencias de valores privados/patrones; no es
  auditoría de todo el historial, dependencias o logs no examinados.
- Instalación principal: ready BD/pgvector/migraciones ok, IA desactivada. Huella
  idéntica a P27: 516 archivos/83.797.981 bytes; .env existente conservado byte a
  byte por el preparador. Informe local data/validation/p28_main_check.json.

## Límites de la comprobación

Almacenamiento vacío/contenedores nuevos no significa descarga sin cachés o máquina
externa: las capas Docker pueden reutilizarse. No se instaló Python en el host ni
se validó todo el flujo nativo. No se ejecutó navegador/escucha/lector de pantalla.
241 backend/62 frontend es la última regresión P27; P28 vuelve a comprobar los
tests/build frontend en la nueva imagen, no presenta el conteo viejo como otra
regresión backend. pip check y alembic check validan dependencias/esquema, no proveedor.

La demostración real de sensaciones/vector/API está aplazada por falta de créditos
y petición del usuario. Sin --live, sin importación/indexación de prueba en la
principal, sin calibración con reservadas o vectores ficticios. Protocolo no equivale
a ejecución ni a permiso para reanudar. Mantener pendientes P08/P15/P16/audio,
P20–P27, CA-10/CA-11 y los acuerdos docentes sobre stack/tenant/PDF.

Se conserva la biblioteca principal, .env, medios, volumen y backups, incluidos
los 506 MP3 sin fila. Entornos P28 detenidos, conservados para diagnóstico/demostración.
P28 no se marca como cierre total del MVP. No se creó commit; después corresponde
cerrar las validaciones pendientes, no activar ampliaciones Oxx automáticamente.
