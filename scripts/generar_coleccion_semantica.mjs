// Colección original P17: síntesis determinista, sin muestras ni servicios externos.
import { mkdirSync, writeFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const root = fileURLToPath(new URL('../pruebas/semantica/', import.meta.url))
const rate = 22050, seconds = 12
const definitions = [
  { id: 'M01', file: 'orbita_lenta.wav', title: 'Órbita lenta', bpm: 60, notes: [48, 55, 60, 55], beatNotes: 1, timbre: 'sine', drums: false, mode: 'sin tercera', density: 'baja', energy: 'baja', mood: 'contemplativo', use: 'concentración tranquila' },
  { id: 'M02', file: 'circuito_rapido.wav', title: 'Circuito rápido', bpm: 140, notes: [60, 64, 67, 72, 67, 64, 62, 67], beatNotes: 2, timbre: 'harmonic', drums: true, mode: 'mayor', density: 'alta', energy: 'alta', mood: 'activo', use: 'actividad con pulso rápido' },
  { id: 'M03', file: 'eco_menor.wav', title: 'Eco menor', bpm: 60, notes: [57, 60, 64, 60], beatNotes: 1, timbre: 'bell', drums: false, mode: 'menor', density: 'baja', energy: 'baja', mood: 'melancólico', use: 'escucha pausada' },
  { id: 'M04', file: 'campanas_al_sol.wav', title: 'Campanas al sol', bpm: 100, notes: [60, 64, 67, 72, 67, 64], beatNotes: 1, timbre: 'bell', drums: false, mode: 'mayor', density: 'media', energy: 'media', mood: 'luminoso', use: 'ambiente de campanas sintéticas' },
  { id: 'M05', file: 'orbita_gemela.wav', title: 'Órbita gemela', bpm: 60, notes: [60, 67, 72, 67], beatNotes: 1, timbre: 'sine', drums: false, mode: 'sin tercera', density: 'baja', energy: 'baja', mood: 'contemplativo', use: 'concentración tranquila' },
]
if (process.argv.includes('--help')) {
  console.log('node scripts/generar_coleccion_semantica.mjs [--overwrite]\nGenera cinco WAV originales y manifest.json. No sustituye archivos sin --overwrite.'); process.exit(0)
}
mkdirSync(root, { recursive: true })
for (const name of [...definitions.map(d => d.file), 'manifest.json']) {
  if (existsSync(join(root, name)) && !process.argv.includes('--overwrite')) throw new Error(`Ya existe ${name}; no se modificó la colección. Usa --overwrite solo para regenerarla.`)
}
const files = []
for (const d of definitions) {
  const samples = rate * seconds, out = Buffer.alloc(44 + samples * 2)
  out.write('RIFF'); out.writeUInt32LE(out.length - 8, 4); out.write('WAVEfmt ', 8)
  out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(1, 22)
  out.writeUInt32LE(rate, 24); out.writeUInt32LE(rate * 2, 28); out.writeUInt16LE(2, 32); out.writeUInt16LE(16, 34)
  out.write('data', 36); out.writeUInt32LE(samples * 2, 40)
  let seed = 173
  for (let i = 0; i < samples; i++) {
    const t = i / rate, beat = t * d.bpm / 60, event = beat * d.beatNotes, age = (event % 1) * 60 / d.bpm / d.beatNotes
    const freq = 440 * 2 ** ((d.notes[Math.floor(event) % d.notes.length] - 69) / 12)
    const phase = 2 * Math.PI * freq * age
    const envelope = Math.min(1, age / .015) * Math.exp(-age * (d.timbre === 'bell' ? 5 : 2))
    let value = Math.sin(phase)
    if (d.timbre === 'bell') value = .7 * value + .3 * Math.sin(phase * 2.76)
    if (d.timbre === 'harmonic') value = .65 * value + .25 * Math.sin(phase * 2) + .1 * Math.sin(phase * 3)
    value *= envelope * .45
    if (d.drums) {
      const drumAge = (beat % 1) * 60 / d.bpm
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
      value += .2 * Math.sin(2 * Math.PI * 65 * drumAge) * Math.exp(-drumAge * 25)
      value += .09 * (seed / 2 ** 31 - 1) * Math.exp(-((beat * 2 % 1) * 60 / d.bpm / 2) * 90)
    }
    value *= Math.min(1, t / .03, (seconds - t) / .1)
    out.writeInt16LE(Math.round(Math.max(-1, Math.min(1, value)) * 32767), 44 + i * 2)
  }
  writeFileSync(join(root, d.file), out)
  const timbre = { sine: 'sintetizador de onda sinusoidal', harmonic: 'sintetizador de tres armónicos', bell: 'síntesis de campanas con parciales inarmónicos' }[d.timbre]
  files.push({ ...d, bytes: out.length, sha256: createHash('sha256').update(out).digest('hex'), duration_seconds: seconds, sample_rate_hz: rate, channels: 1, format: 'WAV PCM 16-bit', album: 'Estudios sintéticos P17', author: 'Generador original del proyecto EchoBeats', origin: 'scripts/generar_coleccion_semantica.mjs', permission: 'Material sintético original creado para pruebas, modificación y demostración de EchoBeats; sin samples ni grabaciones de terceros.', description_version: 1, source: 'verified',
    text: `Fragmento musical sintético de 12 segundos a ${d.bpm} BPM; ${timbre}, secuencia de notas MIDI ${d.notes.join(', ')} y ${d.beatNotes} nota(s) por pulso. ${d.drums ? 'Percusión sintetizada con bombo sinusoidal y ruido pseudoaleatorio.' : 'Sin percusión añadida.'} Patrón ${d.mode}; densidad de eventos ${d.density}. No contiene voces ni instrumentos acústicos grabados.`,
    source_details: 'Rasgos verificables en el código de síntesis; no extraídos por IA ni inferidos del título. BPM es pulso del secuenciador, no una medición del audio.',
    annotation: { energy: d.energy, mood: d.mood, use: d.use, source: 'manual', status: 'hipótesis editorial de evaluación, pendiente de escucha humana; no rasgo objetivo ni inferencia acústica' },
  })
}
writeFileSync(join(root, 'manifest.json'), JSON.stringify({ version: 1, collection: 'echobeats-p17-v1', generator: 'scripts/generar_coleccion_semantica.mjs', tracks: files }, null, 2) + '\n')
console.log(`Generados ${files.length} WAV y manifiesto; no se importaron a la biblioteca.`)
