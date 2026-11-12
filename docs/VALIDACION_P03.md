# Validación de P03 — Entorno inicial

Fecha: 12 de noviembre de 2026. No es una validación funcional del MVP.

## Entregables

- Estructura de API, configuración, servicios, modelos e integraciones Python.
- React/TypeScript/Vite con pantalla de conexión real y estados de espera/error/reintento.
- Endpoint de proceso `GET /api/v1/health`; rutas funcionales pendientes devuelven 404.
- Dockerfiles, Compose local, configuración de ejemplo y exclusiones de Git/Docker.
- Dependencias Python bloqueadas con hashes y árbol npm bloqueado.
- [README](../README.md) con instalación, arranque, parada y comprobaciones.

## Entornos comprobados

| Componente | Versión observada |
| --- | --- |
| Docker / Compose del host | 25.0.3 / 2.24.5 |
| Python del backend | 3.12.16, imagen fijada por digest en Dockerfile. |
| Node del frontend en Docker | 24.22.3, imagen fijada por digest. |
| Node / npm del host | 25.2.1 / 11.6.2; instalación y build adicionales. |
| React / React DOM | 19.3.1 / 19.3.1 |
| Vite / TypeScript / plugin React | 7.3.8 / 5.9.3 / 5.2.0 |
| FastAPI / Starlette / Uvicorn | 0.162.5 / 1.10.0 / 0.54.0 |
| SQLAlchemy / Psycopg / Alembic | 2.1.8 / 3.3.9 / 1.20.1 |
| Pydantic Settings / pytest | 2.16.2 / 9.2.0 |

Python del host no se modificó. El lock Python se resolvió mediante pip-tools
en un contenedor temporal Python 3.12, ejecutado con el UID/GID del usuario;
las versiones y hashes efectivos se conservan en `backend/requirements.lock`.
El frontend se instaló con el helper de la habilidad Sites y npm; el contenedor
reinstaló desde cero mediante `npm ci`. No se utilizaron credenciales de IA.

## Resultados

| Comprobación | Resultado |
| --- | --- |
| `docker compose config --quiet` | Configuración válida en Compose 2.24.5. |
| `docker compose build` | Ambas imágenes construidas; Python instalado con `--require-hashes`, frontend con `npm ci`. |
| `docker compose up --detach --wait` | Backend listo y frontend iniciado; no se requiere BD en P03. |
| `docker compose exec -T backend python -m pytest -W error` | 6 pruebas superadas sin avisos. |
| `docker compose exec -T backend python -m pip check` | Sin dependencias incompatibles. |
| `npm run build` en host y en contenedor frontend | TypeScript y build correctos en ambos entornos. |
| GET directo a `127.0.0.1:8000/api/v1/health` | HTTP 200, `{"status":"ok"}`. |
| GET por proxy a `127.0.0.1:5173/api/v1/health` | HTTP 200, misma respuesta del backend. |
| GET a `127.0.0.1:5173/` | HTTP 200 y HTML de EchoBeats. |
| Publicaciones de Compose | Solo 127.0.0.1:8000 y 127.0.0.1:5173. |

Las pruebas cubren proceso sin BD/IA, rutas aún inexistentes, rechazo de Host no
permitido, rechazo de escritura con Origin externo y paso al router para origen
local o cliente terminal. Se usa HTTPX con ASGITransport, según su
[documentación oficial](https://www.python-httpx.org/advanced/transports/), para
evitar el cliente de Starlette que mostró una advertencia de obsolescencia.

También se revisan enlaces locales del README, sintaxis/formatos de configuración,
diff y exclusiones: `.env`, datos privados, builds, node_modules y entornos Python
quedan fuera de Git; `.env.example` y la colección sintética permanecen versionables.

## Límites y siguiente paso

No se realizó inspección visual en navegador: build y respuesta HTTP no acreditan
la experiencia visual renderizada. No hay reproductor, biblioteca, muros ni IA
implementados y no se ejecutaron pruebas CA del MVP. Tampoco se anuncia una
conexión real a PostgreSQL: se prepara en P04.

Los servicios levantados para esta comprobación se detienen al terminar sin borrar
datos. Las imágenes quedan disponibles para repetir el arranque del README.
No se publicó ningún sitio, se modificó el Python del sistema ni se creó un commit.

Fuentes de configuración consultadas:
[Vite](https://vite.dev/guide/) y
[bloqueo con pip-tools](https://pip-tools.readthedocs.io/en/stable/).
