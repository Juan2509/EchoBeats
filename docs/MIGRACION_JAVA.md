# Migración de EchoBeats a Java y Spring Boot

La migración conserva el frontend de EchoBeats, los contratos HTTP, el esquema
de catálogo, las composiciones de los muros y las rutas de los medios. La
aplicación habitual sigue arrancando con el Compose existente mientras se
comprueba la equivalencia de cada grupo de rutas en PostgreSQL aislado.

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

La comprobación de disponibilidad reconoce la revisión existente
`0011_wall_full_size` y pgvector. El módulo arranca por defecto en
`127.0.0.1:8001` con Java 21 o posterior. Para una prueba local, utilizar Java
y Maven desde la raíz del repositorio y pasar las variables `POSTGRES_HOST`,
`POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`
del entorno PostgreSQL aislado.

```powershell
mvn -f backend-java/pom.xml package
java -jar backend-java/target/echobeats-api-0.1.0-SNAPSHOT.jar
```

## Contratos pendientes antes de sustituir FastAPI

1. Portar la escritura de álbumes y pistas, la importación y extracción de
   metadatos multiformato, y la subida de imágenes, portadas y GIF.
2. Ejecutar la regresión completa de compatibilidad HTTP y visual, incluidos
   los casos concurrentes y recuperación de un respaldo previo.
3. Portar fichas, trabajos persistentes, embeddings, consultas híbridas y chat.
   Reutilizar el esquema pgvector y comparar versiones, ranking y citas con el
   comportamiento de referencia. Validar OpenAI cuando la cuenta tenga créditos.
4. Incorporar el flujo documental como módulo adicional. Debe recibir el PDF
   temporalmente, validar y escanear el archivo, ejecutar extracción y OCR en un
   trabajo duradero, indexar fragmentos por página y retirar la copia según la
   política de retención. El audio gestionado sigue disponible para reproducción.
5. Incorporar autenticación y autorización en todas las rutas con datos. Definir
   propiedad y migración de los datos existentes antes de habilitar tenants.
   Probar que lecturas, búsquedas, medios y trabajos respetan ese aislamiento.
6. Preparar HTTPS y el arranque en VPS. Probar desde una base vacía y desde una
   restauración aislada de la versión de origen, incluida la reproducción de
   audio y el flujo de PDF sin el equipo cliente disponible.

La sustitución de servidor se verifica con los contratos HTTP de la aplicación
actual y la misma interfaz React. El flujo documental requerirá acceso a sus
propias pantallas o rutas adicionales.
