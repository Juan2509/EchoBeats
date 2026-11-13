// Genera entradas de ficha por hash. No importa audios ni escribe en la API.
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
const root = new URL('../pruebas/semantica/', import.meta.url)
const manifest = JSON.parse(readFileSync(new URL('manifest.json', root), 'utf8'))
const timbres = { sine: 'sintetizador sinusoidal', harmonic: 'sintetizador de tres armónicos', bell: 'campanas sintetizadas con parciales inarmónicos' }
const proposals = manifest.tracks.map(t => {
  const evidence = `${t.origin}; definición ${t.id}; SHA-256 ${t.sha256}. Rasgos por construcción, sin análisis acústico.`
  const f = (name, value) => ({ name, value: String(value), source: 'verified', evidence, interpretation: false })
  return { fixture_id: t.id, file: t.file, content_sha256: t.sha256, title: t.title,
    body: { text: t.text, source: 'verified', source_details: evidence,
      features: [f('tempo_bpm', t.bpm), f('timbre', timbres[t.timbre]), f('mode', t.mode), f('percussion', t.drums ? 'percusión sintetizada' : 'sin percusión añadida'), f('voice', 'sin voces'), f('note_density', `${t.beatNotes} nota(s) por pulso`)] } }
})
writeFileSync(new URL('fichas.json', root), JSON.stringify({ version: 1, collection: manifest.collection, note: 'Propuestas verificables por generador; no contienen annotation ni emociones provisionales. Vincular con UUID real por content_sha256. No importadas.', proposals }, null, 2) + '\n')
console.log(`Preparadas ${proposals.length} fichas en ${fileURLToPath(new URL('fichas.json', root))}; sin modificar biblioteca ni API.`)
