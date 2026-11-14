# EchoBeats

Reproductor musical con biblioteca propia, muros por álbum y exploración mediante
IA y pgvector. Proyecto académico en desarrollo.

P17 prepara [casos y criterios de evaluación musical](docs/EVALUACION_BUSQUEDA.md)
con cinco fragmentos sintéticos originales y 18 consultas. Aún no hay búsqueda
semántica. P20 prepara el adaptador de API; su prueba real está pendiente por
créditos API agotados. Ver [validación P17](docs/VALIDACION_P17.md).

**Estado actual: API P22 implementada; pruebas reales y calibración P20–P22 pendientes por créditos, por acuerdo del usuario.** Inicio, navegación,
biblioteca visual de álbumes/canciones, búsqueda textual y detalle de álbum.
Importación real de MP3, WAV PCM, FLAC, Ogg Vorbis y Ogg Opus, extracción de etiquetas/portadas
y editor de metadatos con agrupación de álbumes, procedencia y control de revisión.
Las correcciones manuales se conservan al releer el original.
Entrega de audio con su MIME real, GET/HEAD y rangos; reproductor compartido con selección,
pausa, anterior/siguiente, avance y volumen. Playlists permiten crear, renombrar, añadir/quitar/ordenar pistas y guardar imagen
con apariencia de vinilo o tarjeta. P12 incorpora persistencia y API de muros independientes por álbum. P13 muestra la pared y permite cambiar su fondo con modos de edición/bloqueo.
P14 permite añadir PNG/JPEG/GIF, seleccionar, mover y quitar objetos.
P15 añade ancho/alto, giro, capas y selección de objetos tapados; su revisión visual
de cierre sigue pendiente. La IA sigue pendiente. Ver [validación P15](docs/VALIDACION_P15.md).
`health` y `ready` comprueban proceso y BD.

P16 guarda la pared automáticamente tras una pausa al editar, conserva cambios
nuevos durante un guardado y permite restaurar lo guardado o restablecer el diseño
con confirmación. Ver [validación P16](docs/VALIDACION_P16.md).

## Inicio con Docker

P22 añade API semántica/textual/híbrida y similares por pista con filtros. La
pantalla de exploración y las explicaciones se completan en P23. Sin umbral
calibrado, resultados son candidatos. Ver
[recuperación](docs/RECUPERACION_SEMANTICA.md) y [validación P22](docs/VALIDACION_P22.md).

P21 añade indexación versionada y almacenamiento pgvector desde «Ficha musical».
No se ha acreditado aún un embedding de API real; las pruebas usan proveedor
simulado solo en bases aisladas. Ver [EMBEDDINGS.md](docs/EMBEDDINGS.md) y
[VALIDACION_P21.md](docs/VALIDACION_P21.md). La búsqueda semántica corresponde a P22.

Configuración muestra el estado privado de IA sin revelar claves ni consumir API.
El proveedor está desactivado por defecto. Preparación/prueba controlada y pendientes
en [INTEGRACION_IA.md](docs/INTEGRACION_IA.md) y [VALIDACION_P20.md](docs/VALIDACION_P20.md).

P19 permite crear y corregir la «Ficha musical» de cada pista, con fuentes,
evidencias, interpretaciones y versiones conservadas. Una ficha incompleta no
impide escuchar. Editar fichas no llama al proveedor ni genera embeddings. Ver
[fichas musicales](docs/FICHAS_MUSICALES.md) y [validación P19](docs/VALIDACION_P19.md).

P18 permite preparar metadatos en segundo plano desde «Preparación de información»
en cada canción, consultar estado e historial y reintentar errores sin reimportar.
Todavía no analiza el sonido ni genera fichas o embeddings. Ver
[procesamiento](docs/PROCESAMIENTO.md) y [validación P18](docs/VALIDACION_P18.md).

Requisitos: Docker con daemon activo y Docker Compose **2.24 o superior**.
La primera construcción descarga imágenes y paquetes; requiere acceso a internet.
Ejecutar desde la raíz del repositorio:

```bash
python3 scripts/preparar_entorno.py
docker compose up --build
```

Abrir [EchoBeats](http://localhost:5173) y entrar en «Biblioteca».
«Configuración» permite comprobar la conexión con el servidor.
Seleccionar archivos `.mp3`, `.wav`, `.flac`, `.ogg` o `.opus` en «Añade tu música»
para importar: hasta 20 archivos, 50 MiB
por archivo y 200 MiB por solicitud completa. Los originales quedan copiados en
MEDIA_ROOT. Se leen las etiquetas disponibles; si faltan, se usan datos provisionales
y álbum «Sin álbum». El editor permite corregirlos sin reescribir el audio original.
Ver [importación y consistencia](docs/IMPORTACION_MP3.md).
Ver [metadatos y portadas](docs/METADATOS.md) para edición y relectura segura.
Buscar por título, artista o álbum y alternar «Álbumes» / «Canciones».
La búsqueda ignora mayúsculas y conserva tildes; el texto y la página quedan en
la URL para recargar o usar Atrás/Adelante. Abrir una tarjeta muestra las pistas
del álbum en orden. El panel «Editar canciones, álbumes y portadas» conserva el
editor de P07 y sus borradores durante la navegación dentro de la aplicación.
Ver [validación P08](docs/VALIDACION_P08.md) y sus comprobaciones visuales pendientes.
P09 permite abrir la `audio_url` de una pista directamente en el reproductor
nativo del navegador. GET admite rangos y HEAD consulta tamaño/tipo sin descargar
el audio. Uso, evidencias y límites en [validación P09](docs/VALIDACION_P09.md).
P10 añade botones para reproducir en «Canciones» y dentro de cada álbum. La barra
compartida conserva pista, posición y volumen al navegar dentro de la aplicación.
La lista sigue el álbum o la búsqueda seleccionados, incluso entre páginas.
Al terminar avanza a la siguiente pista y se detiene al final; cerrar/recargar
la página no restaura ni inicia audio automáticamente. Ver
[validación P10](docs/VALIDACION_P10.md) para pruebas y revisión manual pendiente.
P11 añade la pestaña «Playlists» y su editor. Guarda nombre, canciones y orden;
Subir/Bajar también funcionan con teclado. Puedes elegir vinilo o tarjeta y una
imagen PNG/JPEG de hasta 5 MiB. Elegir imagen guarda los cambios actuales.
Guarda el borrador antes de reproducir la lista en su nuevo orden. Si otra pestaña
modificó la playlist, recarga los datos guardados para revisar el conflicto.
Ver [validación P11](docs/VALIDACION_P11.md).
P12 crea un muro inicial por álbum y permite leer/guardar/restablecer su composición
mediante la API con revisión. La migración conserva el catálogo y los recursos;
P13 muestra la vista y los controles de fondo del muro. Ver
[validación P12](docs/VALIDACION_P12.md). No ejecutar downgrade sobre la biblioteca
principal: la reversión rechaza muros guardados para conservar los diseños.
Al abrir un álbum, la pared aparece bloqueada. Pulsa «Editar pared» para elegir
color y «Guardar pared», o «Bloquear diseño» para guardar y bloquear. En edición puedes añadir recursos PNG/JPEG/GIF de hasta 5 MiB, elegir un objeto
y arrastrarlo, usar flechas o botones para moverlo, o quitarlo. Escape cancela
el arrastre. Guarda o bloquea para conservar la composición.
Si aparece un conflicto o el resultado es incierto, recarga la pared guardada
antes de volver a editar. Ver [validación P13](docs/VALIDACION_P13.md) y [P14](docs/VALIDACION_P14.md).
La ampliación O06 admite WAV PCM entero, FLAC nativo y Ogg con Vorbis/Opus.
El navegador debe poder decodificar el códec; se muestra un aviso si no anuncia
compatibilidad. No hay conversión automática. Límites, formatos exactos y
evidencias en [audio multiformato](docs/AUDIO_MULTIFORMATO.md).
La comprobación pública del proceso es
[health](http://localhost:8000/api/v1/health) y la documentación de API está en
[docs](http://localhost:8000/docs).
La comprobación de dependencias está en [ready](http://localhost:8000/api/v1/ready).

Los puertos del host se publican solo en `127.0.0.1`; el proceso dentro de cada
contenedor escucha en su interfaz interna. No cambiar las publicaciones a
`0.0.0.0` para compartirlo: la arquitectura actual no tiene cuentas/autenticación.
El script crea `.env` con contraseña aleatoria, sin imprimirla ni versionarla.
Si ya existe, lo conserva; completar los campos POSTGRES_* siguiendo `.env.example`
al actualizar desde P03. La contraseña vacía impide iniciar PostgreSQL.

Frontend y backend recargan cambios en `frontend/src` y `backend/app`.
Cambios de dependencias requieren reconstruir la imagen. No montar un
`node_modules` del host sobre el contenedor.

Para detener, pulsar Ctrl+C en la terminal del arranque y después:

```bash
docker compose down
```

No se usan opciones de borrado de volúmenes. El volumen `echobeats_postgres_data`
conserva la BD al recrear contenedores. Compose aplica migraciones pendientes
antes del backend; el servicio `migrate` finaliza correctamente, no queda corriendo.

## Configuración

| Variable | Valor de ejemplo / propósito |
| --- | --- |
| `BACKEND_PORT` | 8000: puerto local del backend. |
| `FRONTEND_PORT` | 5173: puerto local de la interfaz. |
| `ALLOWED_HOSTS` | localhost, 127.0.0.1 y backend interno de Compose. |
| `ALLOWED_ORIGINS` | Orígenes de navegador autorizados para escrituras. Al cambiar puertos, ajustar la lista. |
| `MEDIA_ROOT` | `./data/media` en ejecución nativa; Compose utiliza `/app/data/media` montado desde `./data`. |
| `POSTGRES_DB` / `POSTGRES_USER` | Base y usuario locales; por defecto echobeats. |
| `POSTGRES_PASSWORD` | Contraseña aleatoria del .env; nunca versionada. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | 127.0.0.1:5433 para clientes nativos; Compose usa postgres:5432 internamente. |
| `DATABASE_URL` | Opcional para ejecución nativa con esquema postgresql+psycopg. Vacía usa POSTGRES_*. Compose no usa la URL nativa. |

No guardar claves en variables `VITE_*`: su contenido puede acabar en el cliente.
El frontend de Compose solo recibe la dirección interna del proxy. No se necesitan
credenciales de IA ni saldo para instalar o comprobar este paso.

## Comprobaciones

Con servicios iniciados:

```bash
docker compose exec backend python -m pytest
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error
docker compose exec backend python -m pip check
docker compose exec backend python -m alembic check
docker compose exec backend python -m app.media_audit
docker compose exec frontend npm run build
docker compose exec frontend npm test
docker compose config --quiet
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:5173/api/v1/health
curl --fail http://localhost:8000/api/v1/ready
```

La petición al puerto 5173 verifica el proxy. Las pruebas básicas comprueban
health, readiness sin configuración y restricciones HTTP locales. Las pruebas
con RUN_DB_TESTS crean/eliminan únicamente una base aleatoria aislada y verifican
migraciones, pgvector y estados de readiness; no alteran el esquema principal.
El build comprueba TypeScript. La verificación visual en navegador es adicional.

Si los servicios están detenidos, las comprobaciones sin iniciarlos permanentemente
pueden ejecutarse con `docker compose run --rm --no-deps backend python -m pytest`
y `docker compose run --rm --no-deps frontend npm run build`, después del build.

## Base de datos, respaldo y restauración

PostgreSQL se publica en `127.0.0.1:5433` para evitar el servicio ya existente
en 5432. Migraciones, conexión, persistencia y recuperación se explican en
[BASE_DATOS.md](docs/BASE_DATOS.md).

```bash
docker compose exec backend python -m alembic current
python3 scripts/base_datos.py respaldar
```

El respaldo va a `backups/` con manifiesto y hash. Restaurar siempre crea una
base nueva `echobeats_restore_<nombre>` y nunca reemplaza la activa. El dump
no incluye medios: para una biblioteca futura conservar también MEDIA_ROOT.

## Ejecución nativa opcional

Backend: Python **3.12**, con entorno virtual; no instalar sobre Python del sistema.
La versión 3.10 del equipo donde se preparó P03 no es el entorno de referencia.

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install --require-hashes -r backend/requirements.lock
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Antes de migrar nativamente, preparar `.env` e iniciar PostgreSQL con
`docker compose up --detach --wait postgres`. Se usa el puerto 5433 del host.

Frontend: Node **24** como versión de referencia del contenedor, npm y una segunda
terminal. El rango mínimo del proyecto está en package.json; se comprobó también
la construcción con el Node del host indicado en el registro de validación.

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

El proxy nativo apunta a `http://127.0.0.1:8000`. Para otro destino, configurar
`API_PROXY_TARGET` en el proceso de Vite; no incluir credenciales en esa dirección.
El script dev usa `0.0.0.0` para funcionar dentro de Docker, por eso la ejecución
nativa debe conservar el argumento final `--host 127.0.0.1`.

## Dependencias reproducibles

- Frontend: `package.json` declara dependencias directas y `package-lock.json`
  fija el árbol exacto. Instalar con `npm ci`.
- Backend: `requirements.in` declara dependencias directas; `requirements.lock`
  fija versiones transitivas y hashes para Python 3.12. Instalar con
  `pip install --require-hashes -r backend/requirements.lock`.
- Imágenes de Python y Node fijadas por digest en sus Dockerfiles. Actualizarlas
  deliberadamente y repetir las comprobaciones cuando se cambien.
- Imagen de PostgreSQL/pgvector fijada por digest en Compose; sus cambios requieren
  comprobar compatibilidad y persistencia de la BD.

Para actualizar Python: resolver `requirements.in` con pip-tools en Python 3.12
usando `pip-compile --generate-hashes --strip-extras --output-file requirements.lock
requirements.in`, revisar el diff y reconstruir. Registrar el entorno de resolución
como en el [registro de P03](docs/VALIDACION_P03.md). Para actualizar frontend,
modificar package.json, regenerar el lock con npm y repetir instalación limpia/build.
No modificar manualmente los locks ni actualizar paquetes durante el arranque.

## Estructura y continuidad

```text
backend/         API FastAPI, configuración, módulos y pruebas
frontend/        React/TypeScript/Vite y pantalla inicial
docs/            alcance, decisiones, diseños y bitácora
pruebas/         colección técnica sintética y procedencia
scripts/         generación de los audios de prueba
data/            medios y temporales locales, excluidos de Git
compose.yaml     entorno local de desarrollo
```

No se versionan `.env`, claves, node_modules, entornos Python, builds, datos
privados ni bases locales. La colección sintética de `pruebas/coleccion` sí está
versionada y tiene manifiesto de procedencia y hashes.

Continuar desde [PLAN_DESARROLLO.md](docs/PLAN_DESARROLLO.md).
Consultar [DECISIONES.md](docs/DECISIONES.md), [alcance](docs/ALCANCE_MVP.md),
[pantallas](docs/DISENO_PANTALLAS.md), [modelo](docs/MODELO_DATOS.md) y
[API](docs/CONTRATO_API.md) antes de añadir funcionalidades.
