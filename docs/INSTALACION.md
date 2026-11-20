# Instalación y diagnóstico de EchoBeats

## Referencia reproducible

Docker con motor Linux activo y Compose 2.24 o posterior. Backend Python 3.12,
frontend Node 24 dentro de las imágenes fijadas por digest; PostgreSQL 17/pgvector.
Construcción inicial con internet y espacio para imágenes/volúmenes. Locks:
backend/requirements.lock con hashes y frontend/package-lock.json. No actualizar
dependencias por el hecho de instalar. El Compose es un entorno local de desarrollo
(Vite y recarga de backend), no una configuración de producción pública.

Si ya existe una biblioteca, conservar primero .env, volumen, medios y respaldo.
Preparar una nueva contraseña no modifica un rol PostgreSQL ya inicializado. Si
se perdió .env de un volumen existente, recuperar su configuración antes de arrancar.

## Inicio con Docker

Desde la raíz del repositorio:

```bash
node scripts/preparar_entorno.mjs
docker compose config --quiet
docker compose up --build -d --wait
```

El preparador Node requiere Node 24 de referencia; alternativa Python 3:
`python3 scripts/preparar_entorno.py` o `py -3 scripts/preparar_entorno.py` en Windows.
No requiere instalar el backend en el host. Ambos crean .env solo si no existe,
con contraseña aleatoria y sin imprimirla. Permisos 0600 donde el sistema los
aplique; en Windows revisar los permisos heredados de la carpeta privada.

Si Docker no está en PATH, en este equipo:

```powershell
$dockerExe = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
& $dockerExe compose config --quiet
& $dockerExe compose up --build -d --wait
& $dockerExe compose ps
```

Rutas: http://localhost:5173, API http://localhost:8000/docs y ready
http://localhost:8000/api/v1/ready. El proxy se comprueba con
http://localhost:5173/api/v1/health. Postgres solo publica 127.0.0.1:5433.
Los tres puertos se pueden cambiar según CONFIGURACION.md, con orígenes coherentes.

Orden: PostgreSQL disponible → migraciones completas → FastAPI → Spring Boot → gateway → frontend.
`migrate Exited (0)` es correcto. Ready acredita BD, extensión y revisión de esquema,
no éxito de OpenAI ni calidad de resultados. AI_ENABLED=false no impide biblioteca,
edición, reproducción, muro o fichas manuales.

```bash
docker compose stop
docker compose up -d --wait
```

No quitar volúmenes para reiniciar. `down` sin opciones de volumen conserva BD,
pero para uso cotidiano basta stop. Antes de aplicar migraciones pendientes sobre
una biblioteca existente, respaldar conforme a BASE_DATOS.md. Nunca downgrade en
la principal; las reversiones protegidas se prueban solo en bases aisladas.

## Validar desde almacenamiento vacío

```powershell
node scripts/validar_arranque_limpio.mjs --docker "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
```

Docker en PATH: omitir la opción. El script genera data/echobeats_p28_<id>/ con
.env nuevo sin OpenAI, compose.json de proyecto único y appdata independiente.
Elige puertos libres de localhost, declara sus orígenes y no publica PostgreSQL.
Reutiliza Dockerfiles/locks; puede aprovechar cachés. Nunca copia .env personal.

Comprueba biblioteca vacía, head 0009_favorites, pip check, alembic check, build
y tests frontend en contenedor, importación sintética, rangos exactos, proxy y
recreación de backend y persistencia del audio. Detiene solo su proyecto y conserva resultado/configuración,
medios y volumen. Si falla, el informe muestra la etapa y código, sin volcar secretos.
No es un navegador de revisión ni consume proveedor. Reabrir usando los valores
del informe, no un proyecto de ejemplo distinto:

```powershell
$demo = 'data/echobeats_p28_ID'
$project = 'echobeats_p28_ID'
& $dockerExe compose --project-name $project --env-file "$demo/.env" --file "$demo/compose.json" up -d --wait
```

Abrir frontend_url de resultado.json. Detener con el mismo prefijo y `stop`.
Conservar datos; una limpieza posterior de entornos/volúmenes es una decisión aparte.

## Diagnóstico sin revelar claves

| Síntoma | Comprobación / acción |
| --- | --- |
| docker no reconocido | Localizar el ejecutable; usar ruta completa o PATH de la sesión. |
| Motor/pipe no disponible | Iniciar Docker Desktop/motor Linux y repetir docker compose ps. |
| Puerto ocupado | Identificar servicio existente; cambiar los puertos del proyecto y ALLOWED_ORIGINS. No detener servicios ajenos. |
| migrate falla | Revisar compatibilidad/revisión y respaldo; no borrar BD para ocultar el fallo. |
| ready 503 | BD/pgvector/migraciones; alembic current/heads. No es un fallo del reproductor ni de créditos. |
| Credenciales rechazadas | Conservar .env con su volumen; editar contraseña de plantilla no cambia un rol existente. |
| Navegador 403 al guardar | Origin debe coincidir con ALLOWED_ORIGINS, incluyendo esquema/puerto. |
| Explorar sin índice | Guardar fichas no indexa; se necesita vector vigente. Biblioteca textual sigue disponible. |
| IA desactivada/cuota | Mantener desactivada; no repetir solicitudes hasta resolver y reanudar con autorización. |
| Audio/formato no decodificable | Ver MIME/compatibilidad y archivo; no se transcodifica. Rangos correctos no acreditan escucha. |
| Conflicto/guardado incierto | Conservar borrador y consultar estado antes de reintentar; no repetir escrituras a ciegas. |

No compartir .env, Docker inspect/config expandido ni logs completos. La auditoría
acotada de scripts/revisar_secretos.mjs no imprime valores; límites en VALIDACION_P27.md.

## Ejecución nativa opcional

No se validó como instalación limpia en P28: la referencia comprobada es Docker.
Backend exige Python 3.12 y venv propio, no Python 3.10 del host. Dejar PostgreSQL
disponible y evitar que backend/frontend nativos compitan con sus puertos Docker.
En PowerShell, desde la raíz:

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install --require-hashes -r backend/requirements.lock
$env:MEDIA_ROOT = Join-Path (Get-Location) 'data\media'
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_PORT = '5433'
Push-Location backend
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
Pop-Location
```

Respaldo previo si hay biblioteca. MEDIA_ROOT absoluto evita que cambiar cwd lo
redirija a backend/data; DATABASE_URL privada, si se define, prevalece sobre POSTGRES_*.
En POSIX usar python3.12/venv/bin/python y la misma configuración absoluta.

Otra terminal, frontend: `cd frontend`, `npm ci`, `npm run dev -- --host 127.0.0.1`.
No exponer el dev server a la red por omisión. API_PROXY_TARGET sin credenciales
apunta a http://127.0.0.1:8000; la versión Node de referencia es 24.
