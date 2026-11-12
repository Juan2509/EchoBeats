# EchoBeats

Reproductor musical con biblioteca propia, muros por álbum y exploración mediante
IA y pgvector. Proyecto académico en desarrollo.

**Estado actual: P03.** Existen el entorno de desarrollo, una pantalla de conexión
y `GET /api/v1/health`. Importación, reproducción, muros, BD e IA siguen pendientes
de sus pasos. La pantalla inicial no contiene un catálogo simulado.

## Inicio con Docker

Requisitos: Docker con daemon activo y Docker Compose **2.24 o superior**.
La primera construcción descarga imágenes y paquetes; requiere acceso a internet.
Ejecutar desde la raíz del repositorio. Copiar `.env.example` solo si todavía
no existe un `.env` local que se deba conservar:

```bash
cp .env.example .env
docker compose up --build
```

Abrir [EchoBeats](http://localhost:5173). Debe aparecer «Servidor conectado».
La comprobación pública del proceso es
[health](http://localhost:8000/api/v1/health) y la documentación de API está en
[docs](http://localhost:8000/docs).

Los puertos del host se publican solo en `127.0.0.1`; el proceso dentro de cada
contenedor escucha en su interfaz interna. No cambiar las publicaciones a
`0.0.0.0` para compartirlo: la arquitectura actual no tiene cuentas/autenticación.
P03 permite arrancar sin `.env` con valores locales predeterminados; el archivo
de ejemplo documenta la configuración y prepara el siguiente paso.

Frontend y backend recargan cambios en `frontend/src` y `backend/app`.
Cambios de dependencias requieren reconstruir la imagen. No montar un
`node_modules` del host sobre el contenedor.

Para detener, pulsar Ctrl+C en la terminal del arranque y después:

```bash
docker compose down
```

No se usan opciones de borrado de volúmenes. P04 incorporará PostgreSQL, pgvector,
su volumen, migraciones y comprobación de disponibilidad; health en P03 confirma
solo el proceso y no anuncia conexión a una base de datos inexistente.

## Configuración

| Variable | Valor de ejemplo / propósito |
| --- | --- |
| `BACKEND_PORT` | 8000: puerto local del backend. |
| `FRONTEND_PORT` | 5173: puerto local de la interfaz. |
| `ALLOWED_HOSTS` | localhost, 127.0.0.1 y backend interno de Compose. |
| `ALLOWED_ORIGINS` | Orígenes de navegador autorizados para escrituras. Al cambiar puertos, ajustar la lista. |
| `MEDIA_ROOT` | `./data/media` en ejecución nativa; Compose utiliza `/app/data/media` montado desde `./data`. |
| `DATABASE_URL` | Reservada para P04; no se necesita en P03. |

No guardar claves en variables `VITE_*`: su contenido puede acabar en el cliente.
El frontend de Compose solo recibe la dirección interna del proxy. No se necesitan
credenciales de IA ni saldo para instalar o comprobar este paso.

## Comprobaciones

Con servicios iniciados:

```bash
docker compose exec backend python -m pytest
docker compose exec backend python -m pip check
docker compose exec frontend npm run build
docker compose config --quiet
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:5173/api/v1/health
```

El último comando verifica el proxy que usa la interfaz. Los tests comprueban
health sin BD, rechazo de Host y origen de escritura no autorizados, y que rutas
no implementadas no devuelvan un éxito falso. El build comprueba TypeScript y
genera los archivos del frontend. La verificación visual en navegador es adicional.

Si los servicios están detenidos, las comprobaciones sin iniciarlos permanentemente
pueden ejecutarse con `docker compose run --rm --no-deps backend python -m pytest`
y `docker compose run --rm --no-deps frontend npm run build`, después del build.

## Ejecución nativa opcional

Backend: Python **3.12**, con entorno virtual; no instalar sobre Python del sistema.
La versión 3.10 del equipo donde se preparó P03 no es el entorno de referencia.

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install --require-hashes -r backend/requirements.lock
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

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
