# Migración de EchoBeats a Java y Spring Boot

Docker Compose arranca Spring Boot y FastAPI junto con la misma interfaz React.
Vite dirige `/api` al servicio `gateway`, que también publica la API local
en el puerto configurado por `BACKEND_PORT` (8000 por defecto). Conserva métodos,
URLs, cabeceras de revisión y la reproducción por rangos. La asignación está
en [gateway/api.conf](../gateway/api.conf).

| Spring Boot | FastAPI |
| --- | --- |
| Estado y disponibilidad, consultas del catálogo y búsqueda de biblioteca | Importación, carga de imágenes y escritura de pistas y álbumes |
| Reproducción y entrega de imágenes | Etiquetas, fichas, trabajos de preparación e indexación |
| Favoritos, playlists y muros | Explorar, chat, embeddings y búsqueda acústica |

Los dos servicios usan el mismo PostgreSQL y almacenamiento de medios. Alembic
aplica el esquema una vez antes del arranque. Spring Boot monta los medios en
solo lectura. En Compose, su endpoint `/ready` comprueba también FastAPI.
El proxy entrega cada solicitud al servicio asignado, sin reintentos cruzados
de operaciones de escritura.

## Primer grupo de rutas

El módulo `backend-java` usa Spring Boot y JDBC con PostgreSQL. Incluye
`GET /api/v1/health`, `GET /api/v1/ready` y `GET/PUT
/api/v1/tracks/{id}/favorite`. La escritura de favoritos bloquea la pista,
mantiene la fecha original al repetir el mismo PUT y rechaza pistas retiradas.

Se comprobó el JAR arrancado contra PostgreSQL y pgvector en una base aislada
creada con las migraciones de EchoBeats. La prueba HTTP cubrió disponibilidad,
lectura, alta idempotente, baja, validación estricta, origen rechazado y pistas
inexistentes o retiradas. Solo se escribieron datos sintéticos de esa prueba.

## Catálogo, reproducción, playlists y muros

Spring Boot lee las páginas y el detalle de canciones, álbumes, playlists y
favoritos, y sirve la búsqueda combinada de biblioteca. Conserva URLs de
recursos, créditos, herencia de portada, filtros contra pistas retiradas y
ETags de los documentos versionados.

El servicio Java entrega audio e imágenes desde el almacenamiento gestionado.
Se comprobaron bytes completos, rangos parciales, sufijos, rangos múltiples,
`If-Range`, el tamaño de `HEAD` y la respuesta 416. En medios, el ETag del
servidor Java se deriva del SHA-256 registrado, por lo que su valor inicial
difiere del ETag que emite FastAPI. El contenido se sirve sin transcodificar.

Se comprobaron la creación y edición de playlists, la sustitución ordenada de
pistas y el rechazo de pistas retiradas. Los muros conservan el lienzo lógico
1000 × 700, la validación del encaje con giro, el reemplazo transaccional, la
precondición por ETag y el restablecimiento. Se verificaron guardar, detectar
conflicto y restablecer sobre una base aislada con archivos sintéticos.

La comprobación de disponibilidad reconoce la revisión
`0013_audio_index_queue` y pgvector. El módulo arranca por defecto en
`127.0.0.1:8001` con Java 21 o posterior. Para una prueba local, utilizar Java
y Maven desde la raíz del repositorio y pasar las variables `POSTGRES_HOST`,
`POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`
del entorno PostgreSQL aislado.

```powershell
mvn -f backend-java/pom.xml package
java -jar backend-java/target/echobeats-api-0.1.0-SNAPSHOT.jar
```

## Alcance de la integración

El modo integrado se ejecuta con `docker compose up --build -d --wait`.
El modo nativo de Java conserva su puerto 8001 y puede probarse por separado.
Los endpoints de Python mantienen sus contratos para las funciones restantes
y la referencia de la API se conserva en `/docs` del puerto publicado.

La autenticación multicliente, el despliegue en VPS con HTTPS y el flujo PDF/OCR
pertenecen a la ampliación de alcance registrada en los requerimientos.
La validación de OpenAI con créditos sigue pendiente.
