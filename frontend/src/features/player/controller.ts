import type { Track } from '../../shared/api/metadata'

export type PlayerState = {
  track: Track | null; queue: Track[]; index: number; context: string
  playing: boolean; loading: boolean; ready: boolean; pendingQueue: boolean
  position: number; duration: number; volume: number; error: string; notice: string
}
export const initialPlayer: PlayerState = {
  track: null, queue: [], index: -1, context: '', playing: false, loading: false,
  ready: false, pendingQueue: false, position: 0, duration: 0, volume: .7, error: '', notice: '',
}
export type AudioPort = Pick<HTMLAudioElement, 'src' | 'currentSrc' | 'currentTime' | 'duration' |
  'volume' | 'paused' | 'ended' | 'readyState' | 'error' | 'play' | 'pause' | 'load' |
  'addEventListener' | 'removeEventListener' | 'removeAttribute' | 'canPlayType'>

/** Un único audio; las promesas antiguas nunca actualizan la pista nueva. */
export class PlayerController {
  state: PlayerState = { ...initialPlayer }
  private listeners = new Set<() => void>()
  private events: [string, () => void][] = []
  private generation = 0
  private intent = 0
  private wantsPlay = false
  private endedPending = false
  private disposed = false
  private audio: AudioPort

  constructor(audio: AudioPort) {
    this.audio = audio
    audio.volume = this.state.volume
    this.listen('loadedmetadata', () => this.syncTime())
    this.listen('durationchange', () => this.syncTime())
    this.listen('timeupdate', () => this.syncTime())
    this.listen('playing', () => {
      this.wantsPlay = !audio.paused
      this.patch({ playing: !audio.paused, loading: false, error: '' })
    })
    this.listen('pause', () => {
      if (!audio.paused) return
      // Una pausa externa (controles del navegador/teclado multimedia) también
      // cancela la intención. El pause natural de fin deja continuar la lista.
      if (!audio.ended && audio.readyState >= 1) { this.wantsPlay = false; this.intent += 1 }
      this.patch({ playing: false, loading: false })
    })
    this.listen('waiting', () => { if (this.wantsPlay && audio.readyState < 3) this.patch({ loading: true }) })
    this.listen('seeking', () => { if (this.wantsPlay) this.patch({ loading: true }) })
    this.listen('seeked', () => { this.syncTime(); this.patch({ loading: false }) })
    this.listen('ended', () => { if (audio.ended) this.ended() })
    this.listen('error', () => {
      if (!audio.error) return
      this.wantsPlay = false; this.intent += 1
      this.patch({ playing: false, loading: false, error: audio.error?.code === 2
        ? 'Se interrumpió la conexión con el audio. Puedes reintentar.'
        : audio.error?.code === 4 ? 'El navegador no pudo decodificar este formato. Prueba un navegador compatible o revisa el archivo.'
        : 'No se pudo reproducir esta canción. Comprueba que su archivo esté disponible.' })
    })
    const volume = () => this.patch({ volume: audio.volume })
    audio.addEventListener('volumechange', volume)
    this.events.push(['volumechange', volume])
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private patch(changes: Partial<PlayerState>) {
    if (this.disposed) return
    this.state = { ...this.state, ...changes }
    this.listeners.forEach(listener => listener())
  }
  private listen(type: string, handler: () => void) {
    const guarded = () => {
      if (!this.disposed && this.state.track && this.audio.currentSrc === this.audio.src) handler()
    }
    this.audio.addEventListener(type, guarded); this.events.push([type, guarded])
  }
  private syncTime() {
    const ready = this.audio.readyState >= 1 && Number.isFinite(this.audio.duration) && this.audio.duration > 0
    this.patch({ ready, ...(ready ? { duration: this.audio.duration, position: Math.max(0, Math.min(this.audio.currentTime, this.audio.duration)) } : {}) })
  }
  start(track: Track, context: string): number {
    this.generation += 1
    this.patch({ queue: [track], index: 0, context, pendingQueue: true, notice: '' })
    this.load(track)
    return this.generation
  }
  private load(track: Track) {
    this.intent += 1; this.wantsPlay = false; this.endedPending = false
    this.audio.pause()
    this.patch({ track, playing: false, loading: true, ready: false, position: 0,
      duration: track.duration_ms / 1000, error: '' })
    if (!this.supportsFormat()) {
      this.audio.removeAttribute('src'); this.audio.load()
      return
    }
    this.audio.src = track.audio_url
    this.audio.load()
    this.play()
  }
  completeQueue(token: number, queue: Track[], notice = '') {
    if (this.disposed || token !== this.generation || !this.state.track) return
    const active = this.state.track
    queue = queue.map(item => item.id === active.id ? active : item)
    const index = queue.findIndex(track => track.id === this.state.track?.id)
    this.patch({ queue: index >= 0 ? queue : [this.state.track], index: Math.max(0, index), pendingQueue: false, notice })
    if (this.endedPending && this.wantsPlay) { this.endedPending = false; this.ended() }
  }
  play() {
    if (!this.state.track || this.disposed) return
    if (!this.supportsFormat()) return
    if (this.state.error) { this.audio.load(); this.patch({ ready: false }) }
    if (this.state.ready && this.audio.currentTime >= this.state.duration) this.audio.currentTime = 0
    const ticket = ++this.intent
    this.wantsPlay = true
    this.patch({ error: '', loading: true })
    // play se llama durante la acción del usuario, antes de cualquier fetch.
    void this.audio.play().then(() => {
      if (ticket === this.intent && !this.disposed) this.patch({ playing: !this.audio.paused, loading: false })
    }).catch(cause => {
      if (ticket !== this.intent || this.disposed) return
      this.wantsPlay = false
      this.patch({ playing: false, loading: false, error: cause?.name === 'NotAllowedError'
        ? 'El navegador necesita que pulses Reproducir para iniciar el audio.'
        : 'No se pudo iniciar el audio. Puedes reintentar o elegir otra canción.' })
    })
  }
  private supportsFormat() {
    const type = this.state.track?.audio_mime_type
    if (type && !this.audio.canPlayType(type)) {
      this.wantsPlay = false
      this.patch({ playing: false, loading: false, error: 'Este navegador no anuncia compatibilidad con el formato de esta canción. Prueba otro navegador compatible.' })
      return false
    }
    return true
  }
  pause() {
    this.intent += 1; this.wantsPlay = false; this.endedPending = false
    this.audio.pause(); this.patch({ playing: false, loading: false })
  }
  toggle() { if (this.wantsPlay || this.state.playing) this.pause(); else this.play() }
  seek(seconds: number) {
    if (!this.state.ready || !Number.isFinite(seconds)) return
    try { this.audio.currentTime = Math.max(0, Math.min(seconds, this.state.duration)); this.syncTime() }
    catch { this.patch({ error: 'No se pudo cambiar la posición. Vuelve a intentarlo.' }) }
  }
  setVolume(value: number) { if (Number.isFinite(value)) { this.audio.volume = Math.max(0, Math.min(value, 1)); this.patch({ volume: this.audio.volume }) } }
  previous() {
    if (!this.state.track || this.state.pendingQueue) return
    if (this.state.index === 0) { this.seek(0); return }
    this.patch({ index: this.state.index - 1 }); this.load(this.state.queue[this.state.index])
  }
  next() {
    if (this.state.pendingQueue || this.state.index >= this.state.queue.length - 1) return
    this.patch({ index: this.state.index + 1 }); this.load(this.state.queue[this.state.index])
  }
  private ended() {
    this.patch({ playing: false, loading: false, position: this.state.duration })
    if (!this.wantsPlay) return
    if (this.state.pendingQueue) { this.endedPending = true; return }
    if (this.state.index < this.state.queue.length - 1) this.next()
    else this.wantsPlay = false
  }
  updateTrack(track: Track) {
    if (track.id === this.state.track?.id && track.revision >= this.state.track.revision) this.patch({ track, queue: this.state.queue.map(item => item.id === track.id ? track : item) })
  }
  dispose() {
    this.disposed = true; this.intent += 1
    this.events.forEach(([type, handler]) => this.audio.removeEventListener(type, handler))
    this.listeners.clear(); this.audio.pause(); this.audio.removeAttribute('src'); this.audio.load()
  }
}
