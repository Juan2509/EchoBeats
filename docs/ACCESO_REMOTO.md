# Acceso remoto de EchoBeats

El modo remoto en Linux publica EchoBeats por HTTPS con Caddy. Cada cuenta
administrada tiene su propio subdominio y proyecto Docker Compose, con red,
PostgreSQL, pgvector y volumen de audio propios. El navegador solicita usuario
y contraseña antes de abrir la interfaz o acceder a cualquier ruta de la API.
La cuenta se administra en el servidor. El navegador conserva las credenciales
durante su sesión HTTP y controla cuándo volver a solicitarlas.

Caddy es el único servicio público de EchoBeats. Cada frontend sirve la
compilación estática y se publica en un puerto distinto de loopback. El puerto
del gateway y el de PostgreSQL quedan internos. Cada frontend rechaza solicitudes
que lleguen con un dominio distinto al de su cuenta. Caddy quita la cabecera
`Authorization` antes de reenviar la petición. Para escribir, el navegador
debe enviar el origen HTTPS de esa cuenta. Los medios y archivos importados
se alojan en el VPS y siguen disponibles con el computador de origen apagado.

## Preparar el VPS

Usa Linux, Docker Engine 28 o posterior, Docker Compose 2.24.4 o posterior y
Caddy 2.10 o posterior instalado como servicio del host. Apunta un subdominio
DNS al VPS por cuenta y deja accesibles los puertos 80 y 443 para Caddy y la
emisión de certificados. Restringe SSH a los administradores. Mantén los
puertos locales de EchoBeats fuera del acceso público. El modo remoto se
aplica con un segundo archivo Compose. La instalación local conserva su
arranque habitual.

## Crear una cuenta

1. Elige un nombre de proyecto, un subdominio y un puerto local únicos.
   Este ejemplo usa `echobeats-ana`, `ana.musica.example.com` y `18101`.
2. En un directorio privado fuera del repositorio, crea un archivo de entorno
   exclusivo para la cuenta. Usa permisos 0600 y una contraseña aleatoria de
   base de datos distinta por cuenta. Puedes generarla con `openssl rand -hex 32`.
   `REMOTE_ENV_FILE` debe apuntar al propio archivo. Sustituye los valores de
   ejemplo antes del arranque.

   ```dotenv
   REMOTE_ENV_FILE=/ruta/privada/echobeats/ana.env
   REMOTE_DOMAIN=ana.musica.example.com
   REMOTE_HTTP_PORT=18101
   POSTGRES_PASSWORD=<contraseña aleatoria exclusiva>
   AI_ENABLED=false
   ```

3. Desde la raíz del repositorio, inicia la cuenta. Repite el procedimiento
   con un nombre de proyecto, archivo, subdominio, usuario y puerto propios
   para cada biblioteca. Usa siempre la misma combinación al actualizarla.

   ```bash
   docker compose --env-file /ruta/privada/echobeats/ana.env \
     -p echobeats-ana -f compose.yaml -f compose.remote.yaml config --quiet
   docker compose --env-file /ruta/privada/echobeats/ana.env \
     -p echobeats-ana -f compose.yaml -f compose.remote.yaml up --build -d --wait
   ```

4. Copia `deploy/remote/accounts.caddy` a `/etc/caddy/echobeats.caddy`.
   Genera el hash de una contraseña larga y única para la cuenta con
   `caddy hash-password`. Escribe la contraseña cuando el comando la solicite.
   Guarda el hash en la configuración privada de Caddy, con acceso de lectura
   solo para el servicio y sus administradores. Añade al Caddyfile, después de
   cualquier bloque de opciones globales, un `import` por cuenta.

   ```caddyfile
   import /etc/caddy/echobeats.caddy
   import echobeats_account ana.musica.example.com ana HASH_BCRYPT_ANA 18101
   import echobeats_account luis.musica.example.com luis HASH_BCRYPT_LUIS 18102
   ```

   Valida y recarga Caddy. Si administras otros sitios en el mismo Caddyfile,
   conserva esos bloques.

   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```

5. Abre el subdominio por HTTPS desde otro equipo, acepta únicamente un
   certificado válido y autentícate. Crea un álbum, importa audio de prueba
   y reproduce una pista. Repite con otra cuenta y comprueba que sus
   credenciales no abren el primer subdominio y que su biblioteca es independiente.

## Operación

Para revocar una cuenta, retira su línea de Caddy, valida y recarga. Puedes
detener sus contenedores con `docker compose … stop`, usando los archivos
y el proyecto de esa cuenta. Conserva los volúmenes `postgres_data` y
`remote_media` para recuperar sus datos. Para respaldar una cuenta, guarda
su base y una copia de sus medios, junto con su configuración privada.
Reutilizar un nombre de proyecto para otro usuario también reutilizaría esos
volúmenes. La biblioteca local se puede trasladar con una restauración de
base y medios dentro de la instancia elegida. Cada instancia nueva parte vacía.

Referencias oficiales. [Autenticación de Caddy](https://caddyserver.com/docs/caddyfile/directives/basic_auth) · [HTTPS automático](https://caddyserver.com/docs/automatic-https) · [Combinación de Compose](https://docs.docker.com/reference/compose-file/merge/)
