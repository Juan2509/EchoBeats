// Por defecto solo consulta. --apply crea únicamente fichas ausentes por hash exacto.
import { readFileSync } from 'node:fs'
const args = process.argv.slice(2)
if (args.includes('--help')) {
  console.log('node scripts/cargar_fichas_p17.mjs [--apply] [--base-url http://localhost:8000]\nRequiere audios P17 ya importados. Sin --apply solo informa. No sustituye fichas existentes.'); process.exit(0)
}
let base = 'http://localhost:8000', apply = false
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--apply') apply = true
  else if (args[i] === '--base-url' && args[i + 1]) base = args[++i]
  else throw new Error('Argumento no válido; consulta --help.')
}
const url = new URL(base)
if (url.protocol !== 'http:' || !['localhost', '127.0.0.1'].includes(url.hostname) || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('Solo se admite la API HTTP local sin credenciales en la URL.')
const proposals = JSON.parse(readFileSync(new URL('../pruebas/semantica/fichas.json', import.meta.url), 'utf8')).proposals
async function request(path, options = {}) {
  const response = await fetch(new URL(`/api/v1${path}`, url), { ...options, signal: AbortSignal.timeout(15000), cache: 'no-store' })
  const value = await response.json()
  if (!response.ok && !(response.status === 404 && value.error?.code === 'description_missing')) throw new Error(`HTTP ${response.status}: ${value.error?.message ?? 'operación no completada'}`)
  return { response, value }
}
const tracks = []
for (let offset = 0; ; offset += 100) {
  const { value } = await request(`/tracks?limit=100&offset=${offset}`)
  if (!Array.isArray(value.items) || !Number.isInteger(value.total)) throw new Error('Listado no válido.')
  tracks.push(...value.items)
  if (offset + value.items.length >= value.total) break
  if (!value.items.length) throw new Error('Paginación incompleta; no se aplicaron fichas de esta página.')
}
for (const proposal of proposals) {
  const candidates = tracks.filter(t => t.content_sha256 === proposal.content_sha256)
  if (candidates.length !== 1) { console.log(`${proposal.fixture_id}: sin coincidencia única importada; omitida.`); continue }
  const path = `/tracks/${encodeURIComponent(candidates[0].id)}/description`
  const { response } = await request(path)
  if (response.ok) { console.log(`${proposal.fixture_id}: ya tiene ficha; se conserva.`); continue }
  if (!apply) { console.log(`${proposal.fixture_id}: ficha ausente; preparada para crear (simulación).`); continue }
  await request(path, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-None-Match': '*' }, body: JSON.stringify(proposal.body) })
  console.log(`${proposal.fixture_id}: ficha creada por hash exacto.`)
}
console.log(apply ? 'Carga terminada; sin embeddings ni cambios de audio.' : 'Simulación terminada; no se modificó la biblioteca.')
