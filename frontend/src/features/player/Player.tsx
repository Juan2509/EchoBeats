import { createContext, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Track } from '../../shared/api/metadata'
import defaultCover from '../../shared/assets/default-cover.svg'
import { initialPlayer, PlayerController } from './controller'
import type { PlayerState } from './controller'
import { loadQueue } from './queue'
import { FavoriteButton } from '../favorites/Favorites'

type QueueContext = { path: string; label: string }
type PlayerContextValue = { state: PlayerState; select: (track: Track, context: QueueContext, fallback: Track[]) => void; selectSnapshot: (track: Track, queue: Track[], label: string) => void; control: () => PlayerController | null }
const PlayerContext = createContext<PlayerContextValue | null>(null)
export function usePlayer() {
  const player = useContext(PlayerContext)
  if (!player) throw new Error('PlayerProvider debe envolver la aplicación.')
  return player
}

export function PlayerProvider({ children, refresh }: { children: ReactNode; refresh: number }) {
  const audio = useRef<HTMLAudioElement>(null)
  const controller = useRef<PlayerController | null>(null)
  const pending = useRef<AbortController | null>(null)
  const [state, setState] = useState(initialPlayer)
  useEffect(() => {
    const player = new PlayerController(audio.current!)
    controller.current = player
    const unsubscribe = player.subscribe(() => setState(player.state))
    const removed=(event:Event)=>{pending.current?.abort();player.removeTrack((event as CustomEvent<string>).detail)}
    window.addEventListener('echobeats:track-deleted',removed)
    window.addEventListener('echobeats:track-retired',removed)
    const albumRemoved=(event:Event)=>{const id=(event as CustomEvent<string>).detail;for(const item of [...player.state.queue])if(item.album_id===id)player.removeTrack(item.id)}
    window.addEventListener('echobeats:album-deleted',albumRemoved)
    setState(player.state)
    return () => { window.removeEventListener('echobeats:track-deleted',removed);window.removeEventListener('echobeats:track-retired',removed);window.removeEventListener('echobeats:album-deleted',albumRemoved);pending.current?.abort(); unsubscribe(); player.dispose(); controller.current = null }
  }, [])
  useEffect(() => {
    const id = controller.current?.state.track?.id
    if (!id) return
    const abort = new AbortController()
    const timeout = window.setTimeout(() => abort.abort(), 15000)
    fetch(`/api/v1/tracks/${id}`, { signal: abort.signal, cache: 'no-store' }).then(async response => {
      if (response.ok) {
        const track: Track = await response.json()
        if (!abort.signal.aborted) controller.current?.updateTrack(track)
      }else if(response.status===404&&!abort.signal.aborted)controller.current?.removeTrack(id)
    }).catch(() => { /* La edición no interrumpe el audio ya cargado. */ }).finally(() => window.clearTimeout(timeout))
    return () => { abort.abort(); window.clearTimeout(timeout) }
  }, [refresh])

  function select(track: Track, context: QueueContext, fallback: Track[]) {
    const player = controller.current
    if (!player) return
    pending.current?.abort()
    const abort = new AbortController(); pending.current = abort
    const token = player.start(track, context.label)
    const timeout = window.setTimeout(() => abort.abort(), 15000)
    void (async () => {
      try {
        player.completeQueue(token, await loadQueue(context.path, abort.signal))
      } catch {
        player.completeQueue(token, fallback, 'No se pudo cargar la lista completa. Se usarán las canciones de la página seleccionada.')
      } finally { window.clearTimeout(timeout) }
    })()
  }
  function selectSnapshot(track: Track, queue: Track[], label: string) {
    pending.current?.abort()
    controller.current?.startQueue(track,queue,label)
  }
  return <PlayerContext.Provider value={{ state, select, selectSnapshot, control: () => controller.current }}>
    {children}<audio ref={audio} preload="metadata" aria-hidden="true" />
  </PlayerContext.Provider>
}

export const formatTime = (seconds: number) => `${Math.floor(Math.max(0, seconds) / 60)}:${String(Math.floor(Math.max(0, seconds)) % 60).padStart(2, '0')}`
export function PlayerBar({ navigate }: { navigate: (path: string) => void }) {
  const { state, control } = usePlayer()
  const [scrub, setScrub] = useState<number | null>(null)
  useEffect(() => setScrub(null), [state.track?.id])
  const track = state.track
  const status = state.error ? 'Audio no disponible' : state.loading ? 'Cargando audio…' : state.playing ? 'Sonando' : track ? 'En pausa' : 'Sin reproducción'
  function commit() { if (scrub !== null) { control()?.seek(scrub); setScrub(null) } }
  return <section className="player-bar" aria-label="Reproductor de música">
    <div className="player-track">{track && <img src={track.cover_url ?? defaultCover} alt="" onError={event => { if (!event.currentTarget.src.endsWith(defaultCover)) event.currentTarget.src = defaultCover }} />}
      <div><p className="visually-hidden" role="status">{status}</p>{track ? <><div className="track-title-row"><strong>{track.title}</strong><FavoriteButton iconOnly trackId={track.id} title={track.title} /></div><span>{track.artists.map(item => item.name).join(', ') || 'Artista desconocido'}</span>
        <a href={`/albumes/${track.album_id}`} onClick={event => { event.preventDefault(); navigate(event.currentTarget.pathname) }}>{track.album_title}</a></> : <span>Elige una canción en tu biblioteca.</span>}</div></div>
    <div className="player-controls"><div className="transport">
      <button className="playback-mode" aria-label="Reproducción aleatoria" title={state.shuffle ? 'Desactivar reproducción aleatoria' : 'Activar reproducción aleatoria'} aria-pressed={state.shuffle} disabled={!track || state.pendingQueue || state.queue.length < 2} onClick={() => control()?.toggleShuffle()}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h3c5 0 7 12 12 12h3m-4-4 4 4-4 4M3 18h3c2 0 4-3 6-6s4-6 6-6h3m-4-4 4 4-4 4"/></svg></button>
      <button aria-label={state.index === 0 ? 'Volver al inicio de la canción' : 'Canción anterior'} disabled={!track || state.pendingQueue} onClick={() => control()?.previous()}>◀◀</button>
      <button className="play-primary" aria-label={state.playing || state.loading ? 'Pausar' : 'Reproducir'} disabled={!track} onClick={() => control()?.toggle()}>{state.playing || state.loading ? 'Ⅱ' : '▶'}</button>
      <button aria-label="Canción siguiente" disabled={!track || state.pendingQueue || state.index >= state.queue.length - 1} onClick={() => control()?.next()}>▶▶</button>
      <button className="playback-mode repeat-mode" aria-label="Repetir canción" title={state.repeatOne ? 'Desactivar bucle de la canción' : 'Repetir esta canción en bucle'} aria-pressed={state.repeatOne} disabled={!track} onClick={() => control()?.toggleRepeat()}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V7a3 3 0 0 1 3-3h13m-3-3 3 3-3 3M20 15v2a3 3 0 0 1-3 3H4m3-3-3 3 3 3"/></svg></button></div>
      <div className="timeline"><time>{formatTime(scrub ?? state.position)}</time><input type="range" aria-label="Posición de reproducción" aria-valuetext={`${formatTime(scrub ?? state.position)} de ${formatTime(state.duration)}`}
        min="0" max={state.duration || 0} step="0.1" value={scrub ?? state.position} disabled={!state.ready || !!state.error}
        onChange={event => setScrub(Number(event.target.value))} onPointerUp={commit} onPointerCancel={() => setScrub(null)} onKeyUp={commit} onBlur={commit} /><time>{formatTime(state.duration)}</time></div>
      {track && <small>{state.pendingQueue ? 'Preparando lista…' : `${state.index + 1} de ${state.queue.length} · ${state.context}`}</small>}
    </div>
    <label className="volume">Volumen {Math.round(state.volume * 100)} %<input type="range" min="0" max="1" step="0.01" value={state.volume} aria-label="Volumen" onChange={event => control()?.setVolume(Number(event.target.value))} /></label>
    {state.error && <div className="player-error" role="alert">{state.error} <button onClick={() => control()?.play()}>Reintentar audio</button></div>}
    {state.notice && <p className="player-notice" role="status">{state.notice}</p>}
  </section>
}
