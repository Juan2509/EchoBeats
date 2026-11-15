# P27 — Accesibilidad, recursos y protección de datos

14 de noviembre de 2026. **Correcciones y revisión automática listas; recorrido
visual/escucha y evaluación real pendientes.** No se declara preparación comercial.

Hallazgos Q01–Q08, mediciones antes/después y límites en
[REVISION_CALIDAD_P27.md](REVISION_CALIDAD_P27.md). Persistencia/recorridos previos
siguen en la matriz P26; este paso no cierra CA-10/CA-11 ni RF-14 con simulaciones.

## Cambios

Lectura agrupada de páginas de pistas/álbumes; editor de metadatos activado bajo
demanda; carga diferida/decodificación async de imágenes; validación de imágenes
antes de responder con errores seguros; nombres de diálogo y cierre nativo de
ficha; foco visible protegido frente al reproductor y fondo personalizado.
Sin cambio de API ni regla P25, migración, dependencias ni transcodificación.

## Evidencia técnica

- Regresión completa: **241 pruebas backend**, cero fallos/errores/omitidas, con
  avisos como errores. **62 pruebas frontend**, cero fallos/omitidas. Build final
  aprobado: 52 módulos, JS 324,47 kB (98,93 kB gzip), CSS 18,73 kB (4,70 kB gzip).
- Revisión acotada final: 223 archivos examinados, cero coincidencias, cero rutas
  privadas versionadas y cero commits para los tres nombres .env revisados;
  últimas 2000 líneas del backend examinadas sin coincidencias. No se emitieron
  contenidos/valores. El número de archivos puede crecer al añadir documentación.
- Fixture de Explorar: seis candidatos, una llamada simulada de embedding y una
  de selección, cinco fuentes y 599 bytes de contexto; respuesta 10.992 bytes.
  No representa costo, latencia o pertinencia de API real.
- Backend final reiniciado, healthy/ready y lectura por proxy correctos. Huella de
  medios antes/después idéntica: 516 archivos, 83.797.981 bytes, SHA-256 del
  manifiesto `7dfe1a55f1a3aa33b2e124d3fd30fcb5867520eae5697d69037da12c714efe6d`.
  Cero faltantes/staging, 506 archivos sin fila conservados e IA desactivada.

Cuatro casos nuevos backend: presupuesto SQL/recursos (24 pistas/álbumes, muro 30),
entrega visual con truncado/permiso/symlink, portadas manuales/heredadas, presupuesto
de llamadas/contexto de IA simulado. Trece casos de biblioteca/metadatos/medición
pasaron durante la refactorización. Test adicional frontend de detección de secretos
verifica resultado booleano sin exponer el valor sintético.

Informes bajo data/validation (ignorados por Git): p27_before.xml, p27_after.xml,
p27_backend.xml, p27_frontend.txt, p27_secrets.json y huellas de medios antes/después.
Los conteos/tiempos de medición van en propiedades JUnit p27_measurements y
p27_exploration. El resumen versionado no incluye claves, contenido privado ni logs.

## Auditoría de secretos acotada

```powershell
node scripts/revisar_secretos.mjs --docker "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" --output data/validation/p27_secrets.json
```

Lee valores privados solo dentro del proceso para comprobar coincidencias y nunca
los imprime. Revisa archivos no ignorados del árbol actual y dist, patrones OpenAI
y cabeceras de clave privada, y coincidencias de OPENAI_API_KEY/POSTGRES_PASSWORD/
DATABASE_URL configurados. Comprueba rutas privadas versionadas e historial de
.env/.env.local/.env.production, no todos los blobs de todas las revisiones.
Con Docker examina hasta 2000 líneas del backend sin emitirlas ni persistirlas.
Logs más antiguos, paquetes externos y secretos no reconocidos quedan fuera.
No confundir cero coincidencias con garantía de inexistencia de secretos.

## Conservación y pendientes

Los 506 MP3 sin fila siguen conservados; no se eligen descartes por patrones de
nombre o semejanza con fixtures. No se usa la principal para pruebas de escritura.
Mantener el aislamiento de Settings y medios P26, la clave vacía en tests y
proveedores simulados solo en BD aisladas.

Visual/teclado/densos/lector de pantalla y escucha siguen pendientes por falta de
node_repl. La habilidad
[Computer Use](C:/Users/lickn/.codex/plugins/cache/openai-bundled/computer-use/26.1111.21308/skills/computer-use/SKILL.md)
remite a la guía: «Use node_repl JavaScript for all Computer Use actions».
No se acredita accesibilidad completa ni actividad real de navegador con estos tests.

Sin llamadas OpenAI por solicitud previa; no calibrar vectores/umbrales con pruebas
artificiales ni afirmar latencia/pertinencia real del proveedor. P26 y pendientes
visuales/audio/P20–P25 permanecen abiertos. Próximo bloque P28 cuando el usuario
lo solicite; no se creó commit.
