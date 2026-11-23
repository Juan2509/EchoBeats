# EchoBeats

EchoBeats es un proyecto académico para organizar, reproducir y explorar una colección de música propia. Reúne una biblioteca local, un reproductor compartido, playlists, muros personalizables por álbum y herramientas para descubrir canciones de la colección. El modo local está pensado para un usuario.

## Instalación y arranque

Necesitas una copia del repositorio, Python 3 para preparar el entorno, Docker con contenedores Linux, Docker Compose 2.24 o posterior y conexión a internet para la primera construcción. Docker instala las dependencias de la aplicación dentro de sus imágenes.

### Windows

Inicia Docker Desktop en modo de contenedores Linux. Abre PowerShell en la carpeta del proyecto, junto a `compose.yaml`.

```powershell
py -3 scripts/preparar_entorno.py
docker compose config --quiet
docker compose up --build -d --wait
```

Si Python está disponible como `python`, usa `python scripts/preparar_entorno.py` en la primera línea.

### Linux

Asegúrate de que Docker Engine esté iniciado. Si tu instalación usa systemd y el motor está detenido, ejecuta `sudo systemctl start docker`. Abre una terminal en la carpeta del proyecto.

```bash
python3 scripts/preparar_entorno.py
docker compose config --quiet
docker compose up --build -d --wait
```

El preparador crea un `.env` privado con una contraseña aleatoria cuando el archivo no existe. Si ya tienes una biblioteca, conserva ese archivo junto con el volumen de PostgreSQL. La contraseña registrada en la base permanece aunque edites el archivo.

### Abrir, detener y reiniciar

Cuando termine el arranque, copia la dirección en el navegador.

| Servicio | Dirección predeterminada |
| --- | --- |
| EchoBeats | `http://localhost:5173` |
| Estado de la API | `http://localhost:8000/api/v1/ready` |
| Documentación interactiva de la API | `http://localhost:8000/docs` |
| Estado a través del frontend | `http://localhost:5173/api/v1/health` |
| PostgreSQL local | `127.0.0.1:5433` |

Compose inicia PostgreSQL, aplica las migraciones y levanta FastAPI, Spring Boot, el gateway y el frontend. Es normal que `migrate` termine con código `0`. El endpoint `/api/v1/ready` verifica la base de datos, pgvector, la revisión del esquema y la disponibilidad de FastAPI.

Para detener EchoBeats, ejecuta `docker compose stop`. Para usarlo de nuevo, ejecuta `docker compose up -d --wait`. Usa el comando de instalación con `--build` al actualizar el código o las imágenes.

## Usar EchoBeats

1. **Biblioteca.** Abre **Biblioteca → Crear álbum**, elige un nombre y, si quieres, sube una portada. Importa MP3, WAV PCM, FLAC nativo u Ogg Vorbis/Opus y selecciona el álbum de destino. Al importar desde un álbum, el destino queda fijado. EchoBeats lee las etiquetas compatibles, conserva el archivo original y detecta duplicados por contenido.
2. **Reproductor y playlists.** Reproduce desde un álbum, una búsqueda o una playlist. La cola se mantiene al navegar. Puedes pausar, cambiar de pista, avanzar, ajustar volumen, usar repetición u orden aleatorio y marcar favoritos. La reproducción de cada formato depende de los decodificadores del navegador.
3. **Portada y muro.** En **Editar álbum y portada**, elige una imagen o la portada de una canción. En **Editar pared**, añade imágenes o GIF y ajusta su posición, tamaño, giro y capas. Los cambios del muro se autoguardan. **Configuración** reúne fondos, colores y estilo. Los fondos del muro se ajustan en **Editar pared → Fondo**.
4. **Fichas musicales.** En **Fichas y opciones**, elige una pista para editar su descripción y conservar la procedencia de sus datos. Una ficha puede prepararse para búsqueda semántica mediante su indexación.
5. **Explorar.** El chat tiene un modo básico que usa metadatos, favoritos y, cuando corresponde, la pista actual y las reproducciones recientes de la sesión. Ese contexto se mantiene en memoria y se puede olvidar desde **Opciones**. En **Opciones → Búsqueda avanzada** puedes consultar fichas por texto, por similitud semántica o mediante búsqueda híbrida cuando haya índices vigentes y el proveedor esté habilitado.

### Buscar canciones por sonido

Importa al menos dos canciones. El trabajador prepara el índice acústico en segundo plano. Desde una pista de la biblioteca o de un álbum, abre **Buscar similares → Buscar canciones por sonido**. En **Explorar** puedes ver el estado del análisis y reintentarlo si falla.

FFmpeg analiza localmente hasta los primeros 30 segundos de cada pista. El sistema guarda un vector de 26 dimensiones y compara las pistas por distancia coseno. Los resultados son candidatos basados en el comienzo del audio. Este índice es independiente del índice de fichas y funciona sin OpenAI.

Los trabajos pendientes se retoman tras reiniciar el servidor. Puedes pausar el análisis automático con `PROCESSING_WORKER_ENABLED=false` o preparar el índice manualmente con `docker compose exec backend python -m app.index_audio`.

## Arquitectura

```text
Navegador → React / TypeScript / Vite → gateway Nginx
                                         ├─ Spring Boot
                                         └─ FastAPI + trabajador local
Spring Boot y FastAPI → PostgreSQL + pgvector y medios gestionados
```

| Componente | Función |
| --- | --- |
| React, TypeScript y Vite | Interfaz, navegación y reproductor compartido. Las preferencias visuales se conservan por navegador y origen. |
| Nginx | Distribuye las peticiones según el método y la ruta bajo una API común. |
| Java 21 y Spring Boot | Lecturas del catálogo y entrega de audio e imágenes. Gestiona operaciones de favoritos, playlists y muros. |
| Python 3.12 y FastAPI | Importación, edición de catálogo, fichas musicales, procesamiento, indexación y exploración. |
| PostgreSQL 17, pgvector y Alembic | Persistencia de catálogo, metadatos, favoritos, playlists, muros y trabajos. Conserva índices separados para fichas y audio. Alembic aplica el esquema. |
| Medios gestionados | Copias de audio e imágenes en `data/media/` para el modo local. El reproductor solicita tramos del audio mediante HTTP Range. |

La cola de procesamiento se guarda en PostgreSQL. El trabajador local reclama y publica trabajos de forma coordinada para recuperar tareas interrumpidas. Las escrituras versionadas, como las de muros y playlists, usan ETags para detectar cambios concurrentes.

### Estructura del repositorio

| Ruta | Contenido |
| --- | --- |
| `frontend/` | Interfaz y pruebas del cliente. |
| `backend/` | API Python, trabajador, migraciones y pruebas. |
| `backend-java/` | API Spring Boot. |
| `gateway/`, `deploy/remote/` | Enrutamiento HTTP y configuración de acceso remoto. |
| `scripts/` | Preparación del entorno, copias de seguridad y validaciones. |
| `pruebas/` | Archivos sintéticos y casos para probar importación, reproducción y búsqueda. |
| `docs/` | Referencias técnicas, registros históricos y evidencias de validación. |

## Configuración

Usa `.env.example` como referencia y conserva los valores privados en `.env`.

| Variable | Para qué sirve |
| --- | --- |
| `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT` | Puertos publicados. Valores iniciales `5173`, `8000` y `5433`. Dentro de Compose, PostgreSQL usa `postgres:5432`. |
| `ALLOWED_ORIGINS` | Orígenes permitidos para escrituras. Si cambias un puerto publicado, incluye el origen del navegador con su esquema y puerto. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Identidad y credenciales de PostgreSQL. |
| `PROCESSING_WORKER_ENABLED` | Activa o pausa el procesamiento automático local. |
| `AI_ENABLED`, `OPENAI_API_KEY` | Habilitan funciones de OpenAI en el backend. Las instalaciones nuevas arrancan con `AI_ENABLED=false`. |

Para usar OpenAI, configura una clave con créditos en el backend, fija `AI_ENABLED=true` y vuelve a levantar Compose para aplicar el entorno. Mantén la clave fuera de Git y de las variables públicas `VITE_*`. El proveedor recibe texto para el chat y los embeddings de fichas. Las consultas e indexaciones pueden consumir créditos. El catálogo, la reproducción, los muros y la búsqueda acústica siguen disponibles con la IA externa desactivada.

La búsqueda textual usa texto de las fichas, la semántica compara sus vectores vigentes y la híbrida combina ambos órdenes. Cuando hay evidencia registrada, la interfaz puede mostrar citas de fichas. La distancia y el orden de los resultados representan criterios de recuperación, sin equivalencia con un porcentaje de confianza.

## Respaldar y restaurar

Guarda tres elementos para poder recuperar una biblioteca: el dump de PostgreSQL con su manifiesto, una copia de `data/media/` y el `.env` privado correspondiente. Antes de respaldar, deja que terminen las importaciones y los guardados. Con PostgreSQL en ejecución, usa estos comandos desde la raíz del proyecto.

```bash
python3 scripts/base_datos.py respaldar
python3 scripts/base_datos.py restaurar backups/echobeats_FECHA_ID.dump --base echobeats_restore_comprobacion
```

El primer comando crea el dump y su manifiesto SHA-256. Ejecuta el segundo cuando quieras comprobar una copia, sustituyendo el nombre de ejemplo por el del archivo real. La restauración requiere una base nueva cuyo nombre comience por `echobeats_restore_`. En Windows puedes sustituir `python3` por `py -3`.

## Diagnóstico

```bash
docker compose ps -a
docker compose logs --tail=50 migrate
docker compose logs --tail=50 backend backend-java gateway frontend
```

| Síntoma | Qué revisar |
| --- | --- |
| Docker no responde | Inicia Docker Desktop o Docker Engine y comprueba `docker compose version`. |
| Puerto ocupado | Identifica cuál de los tres puertos está en uso. Cambia la variable correspondiente y actualiza los orígenes permitidos si cambias la URL del navegador. |
| `migrate` rechaza la contraseña | Recupera el `.env` asociado al volumen existente o sincroniza la contraseña del rol PostgreSQL con la configuración actual. Conserva el volumen. |
| `ready` devuelve `503` | Revisa migraciones, conexión a PostgreSQL, pgvector y estado de FastAPI. |
| El navegador recibe `403` al guardar | Comprueba que `ALLOWED_ORIGINS` incluya exactamente el esquema, host y puerto del frontend. |
| Explorar no encuentra vectores | Guarda e indexa fichas con la configuración vigente. Si el proveedor indica cuota agotada, revisa el saldo antes de volver a solicitar embeddings. |
| Una pista no se reproduce | Comprueba el formato y el soporte del navegador. EchoBeats entrega el audio original. |

## Pruebas y demostración

Con los servicios iniciados, puedes ejecutar las pruebas y comprobar la compilación desde la raíz.

```bash
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
docker compose exec -T -e RUN_DB_TESTS=1 backend python -m pytest
docker compose exec -T backend python -m alembic check
```

Las pruebas del backend crean bases de prueba aisladas, usan medios temporales y mantienen desactivada la IA externa por defecto. Las pruebas automáticas cubren el contrato de HTTP, rangos de audio, persistencia y recuperación con proveedores simulados. La validación con OpenAI y la evaluación musical de la búsqueda siguen pendientes.

Para una demostración, usa una biblioteca dedicada y pistas sintéticas de `pruebas/coleccion/`. Crea un álbum, importa dos pistas, comprueba la reproducción y el avance, guarda una playlist, edita el muro y prueba Explorar en modo básico. Reinicia el entorno y vuelve a abrir el álbum para mostrar que se conservaron los cambios.

## Acceso remoto opcional

El modo remoto usa Linux, Docker Engine 28 o posterior, Docker Compose 2.24.4 o posterior y Caddy 2.10 o posterior. Cada cuenta utiliza un subdominio, un proyecto Compose, un puerto de loopback y sus propios volúmenes. Caddy recibe el tráfico público por HTTPS y autentica el acceso a la interfaz y a la API. PostgreSQL y el gateway quedan en la red interna. El despliegue en un VPS público sigue pendiente de validación.

1. Apunta un subdominio DNS al VPS y habilita los puertos 80 y 443 para Caddy. Crea un archivo privado con permisos 0600, por ejemplo `/ruta/privada/echobeats/ana.env`.
2. En ese archivo fija `REMOTE_ENV_FILE` con la ruta absoluta del propio archivo, `REMOTE_DOMAIN` con el subdominio, `REMOTE_HTTP_PORT` con un puerto local libre, `POSTGRES_PASSWORD` con una contraseña exclusiva y `AI_ENABLED=false` para el arranque inicial.
3. Valida y levanta el proyecto desde la raíz del repositorio. Usa un nombre distinto por cuenta.

   ```bash
   docker compose --env-file /ruta/privada/echobeats/ana.env -p echobeats-ana -f compose.yaml -f compose.remote.yaml config --quiet
   docker compose --env-file /ruta/privada/echobeats/ana.env -p echobeats-ana -f compose.yaml -f compose.remote.yaml up --build -d --wait
   ```

4. Copia `deploy/remote/accounts.caddy` a `/etc/caddy/echobeats.caddy`. Genera el hash de la contraseña de acceso con `caddy hash-password`. Añade al Caddyfile los imports, sustituyendo los datos de ejemplo por los de la cuenta.

   ```caddyfile
   import /etc/caddy/echobeats.caddy
   import echobeats_account ana.musica.example.com ana HASH_BCRYPT_ANA 18101
   ```

5. Ejecuta `sudo caddy validate --config /etc/caddy/Caddyfile` y `sudo systemctl reload caddy`. Abre el subdominio por HTTPS y verifica el certificado, el inicio de sesión y la carga y reproducción de una pista de prueba. Para mantener o detener la cuenta, reutiliza los mismos archivos y el mismo nombre de proyecto Compose.
