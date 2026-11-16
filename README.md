# EchoBeats

Explorar ahora ofrece una conversación musical sencilla con sugerencias y tarjetas
para escuchar. Usa favoritos y pistas iniciadas en esta sesión; mantiene búsqueda
avanzada en Opciones. La IA es opt-in y su prueba real sigue pendiente por créditos;
la alternativa local queda identificada. [Alcance y validación](docs/CONVERSACION_MUSICAL.md).

Ampliación del 15 de noviembre: **Inicio → Crear álbum**, con nombre, portada
opcional y apariencia Vinilo/Portada. Para importar música hay que elegir su álbum;
desde el álbum el destino queda fijado. Fichas y opciones permite retirar canciones
con confirmación, conservando originales e historial. Los fondos propios tienen X
y un lienzo para mover, girar y ajustar el recorte. Ver [guía y validación](docs/ALBUMES_CARPETA.md).
Head actual `0011_wall_full_size`. La validación actual de capacidad del muro está
en [APARIENCIA.md](docs/APARIENCIA.md); las cifras de esta ampliación inicial son históricas.

Biblioteca y reproductor de música propia, playlists, muros personalizables por álbum
y exploración de fichas mediante OpenAI/pgvector. Aplicación académica **local de un
usuario**, sin autenticación ni exposición pública.

**P28: documentación y demostración preparadas; aceptación global pendiente.**
Última regresión P27: 241 pruebas backend, 62 frontend y build aprobados. Siguen
pendientes navegador/escucha/seek y éxito/evaluación con API real. El usuario dejó
OpenAI pendiente por créditos: instalar o demostrar no autoriza reanudar llamadas.
Evidencia en [VALIDACION_P28.md](docs/VALIDACION_P28.md).

## Arranque

Docker activo con contenedores Linux y Compose 2.24 o posterior; internet para la
primera descarga de imágenes/paquetes. El preparador usa Node 24 o Python 3;
no necesitas instalar el backend en el host para usar Docker.

```bash
node scripts/preparar_entorno.mjs
docker compose config --quiet
docker compose up --build -d --wait
```

Alternativa al primer comando: `python3 scripts/preparar_entorno.py` o, en Windows
con Python instalado, `py -3 scripts/preparar_entorno.py`. Ambos conservan `.env`
si existe y no imprimen contraseñas. No compartir `docker compose config` expandido.

Si Docker no está en PATH, en este equipo PowerShell permite:

```powershell
$dockerExe = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'
& $dockerExe compose config --quiet
& $dockerExe compose up --build -d --wait
```

Abrir [EchoBeats](http://localhost:5173), [ready](http://localhost:8000/api/v1/ready)
y [OpenAPI](http://localhost:8000/docs). `migrate` termina con código 0 antes del
backend; no es un servicio permanente. [INSTALACION.md](docs/INSTALACION.md)
explica diagnóstico y ejecución nativa.

```bash
docker compose stop
docker compose up -d --wait
```

Conservar `.env`, `data/`, `backups/` y volumen `echobeats_postgres_data`. No borrar
volúmenes para arrancar ni cambiar una contraseña inicializada editando solo `.env`.
Si hay biblioteca existente, respaldar antes de aplicar migraciones pendientes.

## Funciones disponibles

Apariencia neón personalizable en **Configuración → Tu atmósfera**: colores y
dirección de degradados, rejilla y fondo propio. Preferencias por navegador;
diseños del muro siguen en BD por álbum. Uso y límites en [APARIENCIA.md](docs/APARIENCIA.md).

- MP3, WAV PCM, FLAC, Ogg Vorbis/Opus: importación, etiquetas/portadas y edición con
  procedencia, búsqueda por título/artista/álbum y provisionales sin identidad inventada.
- Un reproductor compartido: cola, pausa, anterior/siguiente, progreso y volumen;
  recargar no inicia ni restaura reproducción automáticamente.
- Playlists con nombre, orden, PNG/JPEG y apariencia vinilo/tarjeta.
- Muro por álbum: color, PNG/JPEG/GIF, posición/tamaño/giro/capas, bloqueo,
  autoguardado y reset versionado. GIF pausables con preview.
- Fichas con fuente/versión/evidencia, cola de preparación/indexación y favoritos.
  Preferencias explícitas acotan cambios de orden; no entrenan gustos ni registran escuchas.

Biblioteca funciona sin IA. **Explorar textual también exige fichas con índice
vigente**; sin vectores muestra el estado correspondiente. Semántica/híbrida y
selección opcional de citas pueden consumir API al habilitarse explícitamente.
No se envía audio. Guardar fichas no indexa ni llama al proveedor automáticamente.
Citas literales comprobadas, sin prosa libre; scores no son confianza ni pertinencia garantizada.

Límites: 20 audios, 50 MiB por archivo, 200 MiB por solicitud; imágenes 5 MiB y
4096 px por lado; muro 30 objetos; GIF 200 fotogramas/32 MP decodificados totales.
Sin transcodificación, reconocimiento ni análisis acústico.

## Demostración aislada

La [guía de demostración](docs/GUIA_DEMOSTRACION.md) distingue lo local, lo simulado
y lo real pendiente. Para probar otro arranque con base y medios vacíos:

```powershell
node scripts/validar_arranque_limpio.mjs --docker "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
```

Omitir `--docker` si está en PATH. Crea un proyecto único bajo `data/`, credenciales
nuevas sin clave OpenAI y puertos separados. Construye/migra, verifica dependencias,
build/tests, importación/rangos y recreación de backend; detiene solo ese proyecto al terminar,
conservando datos, configuración e informe para reabrirlo. Puede usar caché Docker;
no acredita navegador/escucha, API real o instalación en otra máquina.

## Datos y configuración

Solo `.env` privado; nunca claves en `VITE_*`, frontend o Git. IA desactivada por
defecto; consultar Configuración no consume API ni acredita proveedor válido.
[CONFIGURACION.md](docs/CONFIGURACION.md) detalla puertos, modelo/receta y límites.
PostgreSQL interno `postgres:5432`; host `127.0.0.1:5433`. Compose monta `./data`
en `/app/data`; los originales se conservan.

Hay **506 MP3 sin fila actual**, conservados tras un defecto de aislamiento de tests
corregido en P26. No borrarlos ni reimportarlos automáticamente. Ver [hallazgo](docs/HALLAZGO_AISLAMIENTO_P26.md).

```bash
docker compose exec backend python -m alembic current
python3 scripts/base_datos.py respaldar
python3 scripts/base_datos.py restaurar backups/ARCHIVO.dump --base echobeats_restore_revision
```

El helper de respaldo requiere Python 3 y `docker` en PATH. El dump no contiene
medios; restaurar crea una base nueva y no cambia la activa. [BASE_DATOS.md](docs/BASE_DATOS.md)
explica copia coherente de BD/medios/configuración y alternativa Docker.

## Verificación

```bash
docker compose exec -e RUN_DB_TESTS=1 backend python -m pytest -W error --tb=short
docker compose exec backend python -m pip check
docker compose exec backend python -m alembic check
docker compose exec frontend npm test
docker compose exec frontend npm run build
```

Las pruebas usan BD/medios temporales y clave vacía por defecto. No acreditan API
real ni escucha. No usar la principal para downgrades o pérdidas simuladas. Consultar
[matriz P26](docs/MATRIZ_ACEPTACION_P26.md) y [calidad P27](docs/REVISION_CALIDAD_P27.md).

## Documentación

- [Instalación](docs/INSTALACION.md), [arquitectura](docs/ARQUITECTURA.md),
  [configuración](docs/CONFIGURACION.md), [demostración](docs/GUIA_DEMOSTRACION.md).
- [Alcance](docs/ALCANCE_MVP.md), [API](docs/CONTRATO_API.md), [datos](docs/MODELO_DATOS.md),
  [decisiones](docs/DECISIONES.md) y [requerimientos](docs/REVISION_REQUERIMIENTOS.md).
- [IA](docs/INTEGRACION_IA.md), [embeddings](docs/EMBEDDINGS.md),
  [exploración](docs/EXPLORACION.md), [preferencias](docs/PREFERENCIAS.md).
- [Plan](docs/PLAN_DESARROLLO.md) y [memoria](docs/MEMORIA_PROYECTO.md).

`backend/`: FastAPI/Python 3.12; `frontend/`: React/TypeScript/Vite; `pruebas/`:
señales/música sintética original con hashes; `scripts/`: preparación/operación.
Datos y builds privados ignorados por Git. Dependencias bloqueadas: frontend
`npm ci`; backend `pip install --require-hashes -r backend/requirements.lock` en
Python 3.12. No actualizar locks automáticamente al arrancar.
