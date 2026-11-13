// Verificación local del material P17; no evalúa embeddings ni consume APIs.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'
const root = fileURLToPath(new URL('../pruebas/semantica/', import.meta.url))
const manifest = JSON.parse(readFileSync(join(root, 'manifest.json'), 'utf8'))
const cases = JSON.parse(readFileSync(join(root, 'consultas.json'), 'utf8'))
assert.equal(manifest.collection, cases.collection)
const ids = new Set(manifest.tracks.map(t => t.id)); assert.equal(ids.size, 5)
assert.deepEqual([...ids].sort(), [...cases.corpus].sort())
for (const track of manifest.tracks) {
  assert.match(track.file, /^[a-z_]+\.wav$/)
  const bytes = readFileSync(join(root, track.file))
  assert.equal(bytes.length, track.bytes); assert.equal(createHash('sha256').update(bytes).digest('hex'), track.sha256)
  assert.equal(bytes.toString('ascii', 0, 4), 'RIFF'); assert.equal(bytes.toString('ascii', 8, 16), 'WAVEfmt ')
  assert.equal(bytes.readUInt32LE(4), bytes.length - 8); assert.equal(bytes.readUInt16LE(20), 1)
  assert.equal(bytes.readUInt16LE(22), track.channels); assert.equal(bytes.readUInt32LE(24), track.sample_rate_hz)
  assert.equal(bytes.readUInt16LE(34), 16); assert.equal(bytes.readUInt32LE(40), bytes.length - 44)
  assert.equal((bytes.length - 44) / 2 / track.channels / track.sample_rate_hz, track.duration_seconds)
  let peak = 0; for (let i = 44; i < bytes.length; i += 2) peak = Math.max(peak, Math.abs(bytes.readInt16LE(i)))
  assert.ok(peak > 100 && peak < 32767, 'Señal no vacía y sin saturación')
  for (const field of ['origin', 'author', 'permission', 'text', 'source_details']) assert.ok(track[field])
  assert.equal(track.description_version, 1); assert.equal(track.annotation.source, 'manual')
}
const queryIds = new Set()
for (const q of cases.queries) {
  assert.ok(!queryIds.has(q.id)); queryIds.add(q.id)
  assert.ok(q.text.length > 0 && q.text.length <= 1000)
  assert.ok(['results', 'insufficient_evidence', 'human_review'].includes(q.expected))
  for (const [id, grade] of Object.entries(q.grades)) { assert.ok(ids.has(id)); assert.ok([0, 1, 2].includes(grade)) }
  if (q.expected === 'results') assert.ok(Object.values(q.grades).includes(2))
  else assert.equal(Object.keys(q.grades).length, 0)
  if (q.reference) { assert.ok(ids.has(q.reference)); assert.ok(q.exclude.includes(q.reference)); assert.equal(q.grades[q.reference], undefined) }
  for (const field of q.evidence) assert.ok(manifest.tracks.every(t => field in t), `Campo de evidencia inexistente: ${field}`)
}
assert.equal(queryIds.size, 18); assert.equal(new Set(cases.fault_cases.map(c => c.id)).size, 10)
console.log(`P17: ${ids.size} WAV íntegros/no silenciosos, ${queryIds.size} consultas coherentes y ${cases.fault_cases.length} escenarios de fallo. Recuperación e IA: no ejecutadas.`)
