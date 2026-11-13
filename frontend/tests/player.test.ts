import test from 'node:test'
import assert from 'node:assert/strict'
import { PlayerController } from '../src/features/player/controller.ts'
import type { AudioPort } from '../src/features/player/controller.ts'
import type { Track } from '../src/shared/api/metadata.ts'
import { loadQueue } from '../src/features/player/queue.ts'

class AudioDouble extends EventTarget {
  src = ''; currentSrc = ''; currentTime = 0; duration = NaN; readyState = 0
  volume = 1; paused = true; ended = false; error: { code: number } | null = null
  calls = 0
  playHook = () => Promise.resolve()
  canPlayType(_type: string): CanPlayTypeResult { return 'probably' }
  play() { this.calls += 1; this.paused = false; return this.playHook() }
  pause() { this.paused = true; this.dispatchEvent(new Event('pause')) }
  load() { this.currentSrc = this.src; this.currentTime = 0; this.readyState = 0; this.duration = NaN; this.error = null; this.ended = false }
  removeAttribute() { this.src = '' }
  metadata(duration = 12) { this.duration = duration; this.readyState = 4; this.emit('loadedmetadata') }
  emit(type: string) { if (type === 'ended') { this.ended = true; this.paused = true }; this.dispatchEvent(new Event(type)) }
}
const song = (id: string): Track => ({
  id, title: `Pista ${id}`, artists: [], album_id: 'album', album_title: 'Álbum', audio_url: `/api/v1/tracks/${id}/audio`,
  duration_ms: 12000, track_number: 1, cover_url: null, cover_asset_id: null, cover_source: 'fallback', metadata_sources: {}, revision: 1,
})
function setup() { const audio = new AudioDouble(); return { audio, player: new PlayerController(audio as unknown as AudioPort) } }
function deferred() { let resolve!: () => void; let reject!: (error: unknown) => void; const promise = new Promise<void>((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }
const flush = async () => { await Promise.resolve(); await Promise.resolve() }

test('no inicia audio automáticamente; selección sincroniza pista y tiempo real', async () => {
  const { audio, player } = setup()
  assert.equal(audio.calls, 0); assert.equal(player.state.track, null)
  const token = player.start(song('a'), 'Álbum A')
  assert.equal(audio.calls, 1); assert.equal(player.state.track?.title, 'Pista a')
  audio.metadata(12.08); audio.currentTime = 4; audio.emit('timeupdate'); await flush()
  assert.equal(player.state.position, 4); assert.equal(player.state.duration, 12.08)
  assert.equal(player.state.playing, true)
  player.completeQueue(token, [song('a')]); player.pause()
  assert.equal(player.state.playing, false); assert.equal(player.state.position, 4)
  player.play(); await flush(); assert.equal(player.state.playing, true)
})

test('rechazo tardío de play y cola antigua no contaminan la selección nueva', async () => {
  const { audio, player } = setup(); const old = deferred()
  audio.playHook = () => old.promise
  const first = player.start(song('a'), 'A')
  audio.playHook = () => Promise.resolve()
  const second = player.start(song('b'), 'B')
  old.reject(new Error('old source')); await flush()
  player.completeQueue(first, [song('a')]); player.completeQueue(second, [song('b'), song('c')])
  assert.equal(player.state.track?.id, 'b'); assert.equal(player.state.context, 'B')
  assert.equal(player.state.error, ''); assert.equal(player.state.queue[0].id, 'b')
})

test('pausa durante play pendiente gana a su resolución tardía', async () => {
  const { audio, player } = setup(); const waiting = deferred(); audio.playHook = () => waiting.promise
  player.start(song('a'), 'A'); player.pause(); waiting.resolve(); await flush()
  assert.equal(player.state.playing, false); assert.equal(player.state.loading, false)
})

test('pausa externa permite reanudar en un clic y pause natural permite avanzar', async () => {
  const { audio, player } = setup(); const token = player.start(song('a'), 'A')
  player.completeQueue(token, [song('a'), song('b')]); audio.metadata(); await flush()
  audio.pause(); assert.equal(player.state.playing, false)
  player.toggle(); await flush(); assert.equal(player.state.playing, true)
  audio.ended = true; audio.pause(); audio.emit('ended')
  assert.equal(player.state.track?.id, 'b')
})

test('anterior/siguiente y fin de lista respetan límites y conservan volumen', async () => {
  const { audio, player } = setup(); const token = player.start(song('a'), 'A')
  player.completeQueue(token, [song('a'), song('b')]); player.setVolume(.25)
  audio.metadata(); audio.currentTime = 8; player.previous()
  assert.equal(audio.currentTime, 0); assert.equal(player.state.track?.id, 'a')
  audio.emit('ended'); assert.equal(player.state.track?.id, 'b')
  audio.metadata(); player.next(); assert.equal(player.state.track?.id, 'b')
  audio.currentTime = 12; audio.paused = true; audio.emit('ended'); await flush()
  assert.equal(player.state.playing, false); assert.equal(player.state.position, 12)
  assert.equal(audio.volume, .25)
  player.previous(); assert.equal(player.state.track?.id, 'a')
})

test('final mientras se prepara cola continúa al llegar; pausa cancela continuación', () => {
  for (const paused of [false, true]) {
    const { audio, player } = setup(); const token = player.start(song('a'), 'A')
    audio.metadata(); audio.emit('ended')
    if (paused) player.pause()
    player.completeQueue(token, [song('a'), song('b')])
    assert.equal(player.state.track?.id, paused ? 'a' : 'b')
  }
})

test('avance requiere metadatos y limita valores; volumen cero funciona', () => {
  const { audio, player } = setup(); player.start(song('a'), 'A')
  player.seek(5); assert.equal(audio.currentTime, 0)
  audio.metadata(); player.seek(50); assert.equal(audio.currentTime, 12)
  player.seek(-2); assert.equal(audio.currentTime, 0)
  player.seek(NaN); assert.equal(audio.currentTime, 0)
  player.setVolume(0); assert.equal(audio.volume, 0)
  player.setVolume(10); assert.equal(audio.volume, 1)
})

test('autoplay bloqueado y error de red permiten reintentar', async () => {
  const { audio, player } = setup()
  audio.playHook = () => Promise.reject({ name: 'NotAllowedError' })
  player.start(song('a'), 'A'); await flush()
  assert.match(player.state.error, /navegador/); assert.equal(player.state.playing, false)
  audio.playHook = () => Promise.resolve(); player.play(); audio.metadata(); await flush()
  assert.equal(player.state.error, ''); assert.equal(player.state.playing, true)
  audio.error = { code: 2 }; audio.emit('error')
  assert.match(player.state.error, /conexión/); assert.equal(player.state.playing, false)
  player.play(); await flush(); assert.equal(player.state.error, '')
})

test('eventos de fuente anterior y metadatos desactualizados se descartan', () => {
  const { audio, player } = setup(); const token = player.start(song('b'), 'B')
  audio.currentSrc = '/old.mp3'; audio.currentTime = 9; audio.metadata(99)
  assert.equal(player.state.position, 0); assert.equal(player.state.ready, false)
  player.updateTrack({ ...song('b'), title: 'Corregida', revision: 2 })
  player.updateTrack(song('b'))
  player.completeQueue(token, [song('b')])
  assert.equal(player.state.track?.title, 'Corregida'); assert.equal(audio.src, song('b').audio_url)
  assert.equal(player.state.queue[0].title, 'Corregida')
})

test('desmontar libera audio y descarta promesas/colas pendientes', async () => {
  const { audio, player } = setup(); const waiting = deferred(); audio.playHook = () => waiting.promise
  const token = player.start(song('a'), 'A'); let notices = 0; player.subscribe(() => notices++)
  player.dispose(); waiting.reject(new Error('disposed')); await flush()
  player.completeQueue(token, [song('b')]); audio.emit('error')
  assert.equal(notices, 0); assert.equal(audio.src, ''); assert.equal(audio.paused, true)
})

test('eventos antiguos encolados no pausan ni terminan una fuente nueva sana', async () => {
  const { audio, player } = setup(); const token = player.start(song('a'), 'A')
  player.completeQueue(token, [song('a'), song('b')]); audio.metadata(); await flush()
  for (const type of ['pause', 'ended', 'error', 'waiting']) audio.dispatchEvent(new Event(type))
  assert.equal(player.state.playing, true); assert.equal(player.state.loading, false)
  assert.equal(player.state.track?.id, 'a'); assert.equal(player.state.error, '')
})

test('cola completa cruza páginas conservando filtros y sin descargar audio', async () => {
  const calls: string[] = []; const signal = new AbortController().signal
  const fetcher = (async (url, options) => {
    calls.push(String(url)); assert.equal(options?.signal, signal)
    const offset = Number(new URL(String(url), 'http://localhost').searchParams.get('offset'))
    return new Response(JSON.stringify({ items: Array.from({ length: offset ? 3 : 100 }, (_, index) => song(String(offset + index))), total: 103 }))
  }) as typeof fetch
  const queue = await loadQueue('/tracks?q=lluvia&album_id=album', signal, fetcher)
  assert.equal(queue.length, 103); assert.equal(queue[102].id, '102')
  assert.equal(calls.length, 2); assert.ok(calls[1].includes('offset=100'))
  assert.ok(calls.every(url => url.includes('q=lluvia') && url.includes('album_id=album') && !url.includes('/audio')))
})

test('fallo al cargar cola se propaga y permite alternativa visible', async () => {
  const signal = new AbortController().signal
  await assert.rejects(loadQueue('/tracks', signal, (async () => new Response('', { status: 503 })) as typeof fetch))
  const { player } = setup(); const token = player.start(song('b'), 'B')
  player.completeQueue(token, [song('a'), song('b')], 'Solo página actual')
  assert.equal(player.state.index, 1); assert.equal(player.state.notice, 'Solo página actual')
})

test('formato no anunciado por navegador no descarga audio y permite otra selección', async () => {
  const { audio, player } = setup()
  audio.canPlayType = type => type === 'audio/flac' ? '' : 'probably'
  player.start({ ...song('flac'), audio_mime_type: 'audio/flac' }, 'FLAC')
  assert.equal(audio.calls, 0); assert.equal(audio.src, '')
  assert.match(player.state.error, /navegador/)
  player.play(); assert.equal(audio.calls, 0)
  player.start({ ...song('wav'), audio_mime_type: 'audio/wav' }, 'WAV'); await flush()
  assert.equal(player.state.error, ''); assert.equal(player.state.playing, true)
})

test('cola de playlist conserva orden guardado y no consulta el catálogo ni audio', async () => {
  const path = '/playlists/00000000-0000-4000-8000-000000000001'
  const requested: string[] = []
  const queue = await loadQueue(path, new AbortController().signal, (async (url: string) => {
    requested.push(url)
    return new Response(JSON.stringify({ items: [song('b'), song('a')] }), { status: 200 })
  }) as typeof fetch)
  assert.deepEqual(requested, [`/api/v1${path}`])
  assert.deepEqual(queue.map(item => item.id), ['b', 'a'])
  const { player } = setup()
  player.completeQueue(player.start(queue[0], 'Playlist'), queue)
  player.next()
  assert.equal(player.state.track?.id, 'a')
})

test('playlist vacía y fallo de lectura se distinguen', async () => {
  const path = '/playlists/00000000-0000-4000-8000-000000000001'
  assert.deepEqual(await loadQueue(path, new AbortController().signal, (async () => new Response(JSON.stringify({ items: [] }))) as typeof fetch), [])
  await assert.rejects(loadQueue(path, new AbortController().signal, (async () => new Response('', { status: 503 })) as typeof fetch))
})
