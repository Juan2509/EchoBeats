# Preferencias explícitas — P25

14 de noviembre de 2026. Regla `adjacent_pairs_v1`, local y determinista.
No entrena modelos, no deduce gustos desde decoraciones, no registra escuchas
ni garantiza que una pista guste al usuario. Solo usa favoritos P24 persistidos.

## Opciones en Explorar

- **Conservar orden de la consulta** (`off`, predeterminada): mismo orden P22.
- **Favorecer mis favoritos** (`favorites`): sobre los K candidatos recuperados,
  dividir posiciones en pares disjuntos (1,2), (3,4), etc. Si el segundo es favorito
  y el primero no, intercambiarlos. Cada pista se mueve como máximo una posición;
  ambos favoritos o ninguno conserva el orden. Una última pista impar permanece.
- **Descubrir sin mis favoritos guardados** (`discovery`): excluir favoritos antes
  de recuperar y limitar candidatos. Conservar el orden de consulta restante.

La opción se aplica al pulsar Buscar; cambiarla, abrir la página o marcar un corazón
no repite búsquedas, no reordena una respuesta anterior y no inicia audio.
Biblioteca y reproductor mantienen sus listas y funcionamiento habituales.

## Límites y comparación

El ajuste no añade pistas fuera del top K, no supera filtros ni resucita fichas o
vectores obsoletos. Tampoco cambia distancia, ranks semántico/textual ni RRF.
No combina una preferencia con un score para fabricar confianza. El desplazamiento
máximo de uno es una decisión conservadora de producto, no un umbral musical
calibrado ni un peso ajustado con las consultas reservadas P17.

Sin favoritos entre candidatos se mantiene el orden. Si todos son favoritos,
favorecer tampoco cambia nada; descubrir puede quedar vacío sin consultar API si
el filtro no deja pistas. La referencia sigue excluida en similares aunque sea
favorita. Filtros de álbum y playlist se combinan con las opciones.

Descubrir facilita encontrar pistas distintas de las guardadas; no promete una
canción nunca escuchada ni variedad entre consultas idénticas. No existe historial
de escucha ni rotación aleatoria oculta. El ajuste de favoritos nunca arrastra una
favorita ajena a la consulta y se recalcula desde el orden original en cada petición.

La tabla **Comparar orden de consulta y orden mostrado** usa la misma respuesta:
no necesita otra llamada API. Muestra el contrafactual sin ajuste para ese conjunto
recuperado. En descubrir, el conjunto ya excluye favoritos: la tabla no equivale a
una segunda búsqueda sin ese filtro. Para cambiar el conjunto, consultar de nuevo
con la opción deseada; el consumo habitual del modo elegido sigue aplicando.

Ejemplo técnico reproducible en tests (C1…C5 son posiciones, no juicios musicales):

| Señal | Orden base | Orden mostrado |
| --- | --- | --- |
| Sin favoritos | C1 C2 C3 C4 C5 | C1 C2 C3 C4 C5 |
| C2 y C4 favoritos, ajuste activo | C1 C2 C3 C4 C5 | C2 C1 C4 C3 C5 |
| Mismos favoritos, opción off | C1 C2 C3 C4 C5 | C1 C2 C3 C4 C5 |
| Descubrir excluye C1 y C2; K=1 | candidatos elegibles restantes | C3, si es el primero por consulta |

La comparación técnica verifica el algoritmo; no demuestra mejora de pertinencia.

## API y consistencia

POST `/api/v1/explore/search`, POST `/api/v1/explore/similar` y GET
`/api/v1/tracks/{id}/similar` admiten `preferences=off|favorites|discovery`.
En POST es un campo JSON; en GET es un parámetro. Valor inválido devuelve 422.

Respuesta raíz `preferences`: mode, policy, baseline_order, result_order, reordered.
Cada resultado añade `preference`: favorite, base_rank, rank, reason. Los IDs de
comparación pertenecen al mismo conjunto y las posiciones empiezan en uno. La
razón de orden es determinista y está separada de citas/atributos musicales.
Los flags describen el momento de respuesta, no un estado vivo de los corazones.

Lectura de favoritos y candidatos en la misma instantánea después del embedding.
Si hay selección de citas P23, al terminar se revalidan elegibilidad, versión/hash,
modelo/receta, referencia y filtros, se leen de nuevo favoritos y se reconstruye
comparación. Un nuevo favorito durante descubrir se retira sin rellenar la lista
ni repetir proveedor; puede quedar más corta o vacía. La UI comunica los cambios.
No se mantienen transacciones durante red. Los favoritos y razones no se añaden
al contexto de generación: solo las fichas acotadas que P23 ya enviaba.

No requiere migración, nuevas dependencias ni API adicional. No modifica .env,
favoritos, medios ni vectores por el hecho de consultar. Para la evidencia y los
pendientes reales/visuales, ver [VALIDACION_P25.md](VALIDACION_P25.md).
