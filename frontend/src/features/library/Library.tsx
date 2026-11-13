import { useEffect, useState } from 'react'
import type { Album, Track } from '../../shared/api/metadata'
import defaultCover from '../../shared/assets/default-cover.svg'
import { PlaylistLibrary } from '../playlists/Playlists'
import { WallView } from '../walls/WallView'
import { usePlayer } from '../player/Player'
import { ProcessingPanel } from '../processing/ProcessingPanel'

type Page<T> = { items: T[]; total: number; limit: number; offset: number }
type Navigate = (path: string) => void
export function Cover({ url, title }: { url: string | null; title: string }) {
  return <img className="cover" src={url ?? defaultCover} alt={`Portada de ${title}`} loading="lazy"
    onError={event => { if (!event.currentTarget.src.endsWith(defaultCover)) event.currentTarget.src = defaultCover }} />
}
export const artists = (item: Album | Track) => item.artists.map(value => value.name).join(', ') || 'Artista desconocido'
const duration = (ms: number) => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`

export function useRead<T>(url: string, refresh: number, enabled = true) {
  const [state, setState] = useState<{ url: string; data?: T; loading: boolean; error: string }>({ url: '', loading: true, error: '' })
  const [attempt, retry] = useState(0)
  useEffect(() => {
    if (!enabled) return
    let active = true
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 15000)
    setState({ url, loading: true, error: '' })
    fetch(`/api/v1${url}`, { signal: controller.signal, cache: 'no-store' }).then(async response => {
      const data = await response.json()
      if (!response.ok) throw new Error(data.error?.message ?? 'No se pudieron cargar los datos.')
      if (active) setState({ url, data, loading: false, error: '' })
    }).catch(cause => { if (active) setState({ url, loading: false, error: cause instanceof Error && !(cause instanceof TypeError) && !(cause instanceof SyntaxError) && cause.name !== 'AbortError' ? cause.message : 'No se pudo cargar la biblioteca. Comprueba la conexión y vuelve a intentarlo.' }) })
      .finally(() => window.clearTimeout(timeout))
    return () => { active = false; controller.abort(); window.clearTimeout(timeout) }
  }, [url, refresh, attempt, enabled])
  return { ...(state.url === url ? state : { loading: true, error: '', data: undefined }), retry: () => retry(value => value + 1) }
}

export function ReadState({ loading, error, retry }: { loading: boolean; error: string; retry: () => void }) {
  return <>{loading && <p role="status">Cargando tu música…</p>}{error && <div role="alert"><p>{error}</p><button onClick={retry}>Reintentar</button></div>}</>
}
export function Pagination({ offset, total, move }: { offset: number; total: number; move: (offset: number) => void }) {
  return total > 24 ? <nav className="pagination" aria-label="Páginas de resultados">
    <button disabled={offset === 0} onClick={() => move(Math.max(0, offset - 24))}>Anterior</button>
    <span>{offset + 1}–{Math.min(offset + 24, total)} de {total}</span>
    <button disabled={offset + 24 >= total} onClick={() => move(offset + 24)}>Siguiente</button>
  </nav> : null
}
function TrackList({ tracks, navigate, queuePath, queueLabel }: { tracks: Track[]; navigate: Navigate; queuePath: string; queueLabel: string }) {
  const player = usePlayer()
  return <ul className="track-list">{tracks.map(item => <li key={item.id} className={player.state.track?.id === item.id ? 'active-track' : undefined}>
    <button className="track-play" aria-label={`${player.state.track?.id === item.id && (player.state.playing || player.state.loading) ? 'Pausar' : 'Reproducir'} ${item.title}`}
      aria-pressed={player.state.track?.id === item.id && player.state.playing} onClick={() => {
        if (player.state.track?.id === item.id) player.control()?.toggle()
        else player.select(item, { path: queuePath, label: queueLabel }, tracks)
      }}>{player.state.track?.id === item.id && (player.state.playing || player.state.loading) ? 'Ⅱ' : '▶'}</button>
    <Cover url={item.cover_url} title={item.title} />
    <div><strong>{item.track_number ? `${item.track_number}. ` : ''}{item.title}</strong><span>{artists(item)}</span>
      <a href={`/albumes/${item.album_id}`} onClick={event => { event.preventDefault(); navigate(event.currentTarget.pathname) }}>{item.album_title}</a>
      <ProcessingPanel key={`${item.id}-${item.revision}`} trackId={item.id} revision={item.revision} /></div>
    <time aria-label={`Duración ${duration(item.duration_ms)}`}>{duration(item.duration_ms)}</time>
  </li>)}</ul>
}

export function Library({ refresh, navigate, search }: { refresh: number; navigate: Navigate; search: string }) {
  const params = new URLSearchParams(search)
  const query = params.get('q') ?? ''
  const view = params.get('vista') === 'playlists' ? 'playlists' : params.get('vista') === 'canciones' ? 'canciones' : 'albumes'
  const rawOffset = Number(params.get('offset') ?? '0')
  const offset = Number.isSafeInteger(rawOffset) && rawOffset >= 0 ? rawOffset : 0
  const [draft, setDraft] = useState(query)
  useEffect(() => setDraft(query), [query])
  function move(nextView = view, nextQuery = query, nextOffset = 0) {
    const next = new URLSearchParams({ vista: nextView, q: nextQuery, offset: String(nextOffset) })
    navigate(`/biblioteca?${next}`)
  }
  const result = useRead<Page<Album | Track>>(`/${view === 'albumes' ? 'albums' : 'tracks'}?${new URLSearchParams({ q: query, limit: '24', offset: String(offset), include_empty_system: 'false' })}`, refresh, view !== 'playlists')
  return <section aria-labelledby="library-title">
    <p className="eyebrow">Tus discos, tus recuerdos</p><h1 id="library-title">Mi biblioteca</h1>
    <p className="intro">Un espacio para toda la música que has hecho tuya.</p>
    <form className="search-form" role="search" onSubmit={event => { event.preventDefault(); move(view, draft.trim()) }}>
      <label htmlFor="library-query">Buscar por canción, artista, álbum o nombre de playlist</label>
      <div><input id="library-query" type="search" maxLength={200} value={draft} onChange={event => setDraft(event.target.value)} placeholder="¿Qué quieres encontrar?" /><button>Buscar</button></div>
      {query && <button type="button" className="secondary" onClick={() => { setDraft(''); move(view, '') }}>Limpiar búsqueda</button>}
    </form>
    <div className="view-switch" aria-label="Mostrar colección"><button aria-pressed={view === 'albumes'} onClick={() => move('albumes')}>Álbumes</button><button aria-pressed={view === 'canciones'} onClick={() => move('canciones')}>Canciones</button><button aria-pressed={view === 'playlists'} onClick={() => move('playlists')}>Playlists</button></div>
    {view === 'playlists' && <PlaylistLibrary refresh={refresh} navigate={navigate} search={search} />}
    {view !== 'playlists' && <ReadState {...result} />}
    {view !== 'playlists' && result.data && <><p role="status" className="note">{result.data.total} {view === 'albumes' ? 'álbumes' : 'canciones'}{query ? ` para «${query}»` : ' en tu colección'}</p>
      {!result.data.items.length && <div className="empty-state"><h2>{query ? 'Sin coincidencias' : offset ? 'No hay más resultados' : 'Tu colección empieza aquí'}</h2><p>{query ? 'Prueba otro título, artista o álbum. La búsqueda conserva las tildes.' : offset ? 'Vuelve a la primera página para ver la colección actual.' : 'Importa tus archivos de audio para verlos en este espacio.'}</p>{offset > 0 && <button onClick={() => move()}>Primera página</button>}</div>}
      {view === 'albumes' ? <div className="album-grid">{(result.data.items as Album[]).map(item => <a className="album-card" key={item.id} href={`/albumes/${item.id}`} onClick={event => { event.preventDefault(); navigate(event.currentTarget.pathname) }}>
        <Cover url={item.cover_url} title={item.title} /><h2>{item.title}</h2><p>{artists(item)}</p><span>{item.track_count} pistas</span>
      </a>)}</div> : <TrackList tracks={result.data.items as Track[]} navigate={navigate} queuePath={`/tracks?${new URLSearchParams({ q: query })}`} queueLabel={query ? `Búsqueda: ${query}` : 'Mi biblioteca'} />}
      <Pagination offset={offset} total={result.data.total} move={value => move(view, query, value)} />
    </>}
  </section>
}

export function AlbumView({ id, refresh, navigate, onDirty }: { id: string; refresh: number; navigate: Navigate; onDirty: (dirty: boolean) => void }) {
  const [offset, setOffset] = useState(0)
  const info = useRead<Album>(`/albums/${encodeURIComponent(id)}`, refresh)
  const songs = useRead<Page<Track>>(`/tracks?album_id=${encodeURIComponent(id)}&limit=24&offset=${offset}`, refresh)
  return <section><a href="/biblioteca" onClick={event => { event.preventDefault(); navigate('/biblioteca') }}>← Mi biblioteca</a>
    <ReadState {...info} />{info.data && <div className="album-room"><aside className="album-sidebar"><div className="album-heading"><Cover url={info.data.cover_url} title={info.data.title} /><div><p className="eyebrow">En tu colección</p><h1>{info.data.title}</h1><p>{artists(info.data)} · {info.data.track_count} pistas</p></div></div>
      <h2>Canciones del álbum</h2><ReadState {...songs} />{songs.data && <><TrackList tracks={songs.data.items} navigate={navigate} queuePath={`/tracks?album_id=${encodeURIComponent(id)}`} queueLabel={info.data.title} />{!songs.data.total && <p className="empty-state">Este álbum todavía no tiene canciones.</p>}<Pagination offset={offset} total={songs.data.total} move={setOffset} /></>}
      <p className="note">Abrir este álbum no cambia la canción que está sonando.</p>
    </aside><WallView key={id} albumId={id} title={info.data.title} onDirty={onDirty} /></div>}
  </section>
}
