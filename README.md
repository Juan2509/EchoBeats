# EchoBeats

EchoBeats es una aplicación académica para organizar, reproducir y explorar una colección de música propia. Funciona en tu equipo y está pensada para un solo usuario.

## Objetivo

Reunir en un mismo espacio la biblioteca, la escucha y la exploración musical. Puedes organizar canciones en álbumes, personalizar cómo se presentan y usar sus fichas para encontrar pistas dentro de tu colección.

## Cómo funciona

1. **Organiza tu biblioteca.** En **Biblioteca → Crear álbum**, elige un nombre y, si quieres, sube una portada. Importa archivos MP3, WAV PCM, FLAC u Ogg Vorbis/Opus y selecciona el álbum de destino. Si importas desde un álbum, el destino ya está fijado. EchoBeats lee las etiquetas compatibles y conserva los archivos originales.
2. **Escucha y prepara playlists.** Reproduce desde un álbum, una búsqueda o una playlist. El reproductor mantiene su cola al navegar y ofrece pausa, anterior, siguiente, progreso, volumen, repetición y orden aleatorio. Puedes marcar canciones como favoritas.
3. **Personaliza los álbumes.** En **Editar álbum y portada** puedes subir una imagen o elegir la portada propia de una canción del álbum. En **Editar pared** puedes decorar el muro con imágenes o GIF, moverlos, cambiar su tamaño y giro, y ordenar sus capas. **Configuración** reúne los ajustes de fondos, colores y estilo.
4. **Explora tu música.** La vista **Explorar** ofrece sugerencias locales a partir de los metadatos y, según la consulta, de tus favoritos, la pista actual y la escucha de la sesión. La búsqueda textual avanzada consulta fichas vigentes; los modos semántico e híbrido requieren un índice vectorial vigente y un proveedor habilitado. OpenAI procesa el chat cuando el servidor tiene `AI_ENABLED=true` y `OPENAI_API_KEY` configurados. La integración con OpenAI trabaja con texto y está desactivada en instalaciones nuevas. Desde una pista también puedes buscar canciones por sonido mediante el índice acústico local.

La interfaz usa React, TypeScript y Vite. En Docker Compose, Spring Boot sirve las consultas del catálogo, audio e imágenes, favoritos, playlists y muros. FastAPI atiende la importación, la edición de pistas y álbumes, la indexación y la exploración. PostgreSQL guarda la biblioteca, las playlists y los muros, y pgvector almacena los índices de búsqueda. Los medios se guardan en `data/media/` y las preferencias visuales se conservan en el navegador.

## Ejecutar EchoBeats

En ambos sistemas necesitas una copia del repositorio, Python 3 para preparar la configuración, Docker con contenedores Linux, Docker Compose 2.24 o posterior e internet para la primera descarga. Docker instala las dependencias del frontend y del backend dentro de sus imágenes.

### Windows

1. Inicia Docker Desktop en modo de contenedores Linux.
2. Abre PowerShell en la carpeta del proyecto, donde está `compose.yaml`.
3. Ejecuta:

```powershell
py -3 scripts/preparar_entorno.py
docker compose config --quiet
docker compose up --build -d --wait
```

Si Python está disponible como `python`, puedes usar `python scripts/preparar_entorno.py`.

### Linux

1. Inicia Docker Engine. Si tu instalación usa systemd y el motor está detenido, ejecuta `sudo systemctl start docker`.
2. Abre una terminal en la carpeta del proyecto, donde está `compose.yaml`.
3. Ejecuta:

```bash
python3 scripts/preparar_entorno.py
docker compose config --quiet
docker compose up --build -d --wait
```

### Abrir la aplicación

Cuando termine el arranque, copia en el navegador la dirección que quieras abrir.

- EchoBeats (`http://localhost:5173`)
- Estado del backend (`http://localhost:8000/api/v1/ready`)
- Referencia del contrato HTTP (`http://localhost:8000/docs`)

Docker inicia PostgreSQL, aplica las migraciones y levanta Spring Boot, FastAPI y el frontend. El puerto de la API conserva las URLs existentes y distribuye por método y ruta. `/api/v1/ready` verifica PostgreSQL, pgvector, el esquema y la disponibilidad de FastAPI desde Spring Boot. El servicio `migrate` termina con código `0` después de actualizar el esquema.

### Acceso remoto

Para publicar EchoBeats por HTTPS en un VPS Linux, usa el modo remoto
con Caddy y un proyecto aislado por cuenta. [Guía de acceso remoto](docs/ACCESO_REMOTO.md).

### Consultar documentos PDF

La sección **Documentos** procesa PDF con OCR, indexa el texto en pgvector y
responde con citas por página. [Guía del flujo documental](docs/DOCUMENTOS.md).

### Buscar canciones por sonido

Importa al menos dos canciones. El trabajador local analiza en segundo plano
las pistas importadas y las que ya estaban en la biblioteca sin un vector vigente.
En **Biblioteca** o en un álbum, abre **Buscar similares** para una canción. En
**Explorar** verás su estado y podrás pulsar **Buscar canciones por sonido** cuando esté
lista. Si el análisis falla, puedes reintentarlo desde la misma pantalla.

El análisis usa hasta los primeros 30 segundos de cada pista, calcula un
embedding acústico de 26 dimensiones y lo guarda en PostgreSQL con pgvector.
La búsqueda compara por distancia coseno. Se ejecuta localmente con FFmpeg y usa
características del espectro y la intensidad. Los resultados son candidatos acústicos
y dependen de lo que se escucha al comienzo de cada pista.

La importación y la reproducción pueden continuar durante el análisis. Si se
reinicia el servidor, las pistas pendientes y los análisis interrumpidos se retoman.
`PROCESSING_WORKER_ENABLED=false` pausa el análisis automático. Para preparar el
índice manualmente sigue disponible `docker compose exec backend python -m app.index_audio`.

### Detener y volver a iniciar

Para detener EchoBeats:

```bash
docker compose stop
```

Para volver a iniciarlo:

```bash
docker compose up -d --wait
```

El preparador crea un `.env` privado con una contraseña aleatoria cuando el archivo no existe. Si ya tienes una biblioteca, conserva su `.env`, la carpeta `data/`, el volumen de PostgreSQL y los respaldos. Cambiar la contraseña en `.env` por sí solo deja desincronizada la credencial de una base ya inicializada.

### Si hay un error de arranque

```bash
docker compose ps -a
docker compose logs --tail=50 migrate
docker compose logs --tail=50 backend backend-java gateway frontend
```

- Si Docker no responde, comprueba que Docker Desktop o Docker Engine esté iniciado.
- Si falla `migrate` por autenticación y ya existía una biblioteca, recupera el `.env` correspondiente a ese volumen o sincroniza la credencial de PostgreSQL antes de arrancar de nuevo.
- Si Docker informa que un puerto está ocupado, comprueba los puertos locales predeterminados `5173` (interfaz), `8000` (API) y `5433` (PostgreSQL).
