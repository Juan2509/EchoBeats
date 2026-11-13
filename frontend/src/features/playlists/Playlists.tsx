import { useEffect, useRef, useState } from 'react'
import { allMetadata, editOptions, metadataRequest } from '../../shared/api/metadata'
import type { Track } from '../../shared/api/metadata'
import { Cover, Pagination, ReadState, useRead } from '../library/Library'
import { usePlayer } from '../player/Player'

type Navigate = (path: string) => void
export type Playlist = { id: string; name: string; appearance: 'vinyl' | 'image'; image_asset_id: string | null; image_url: string | null; revision: number; track_count: number; items: Track[] }
type Page = { items: Playlist[]; total: number }
const message = (cause: unknown) => cause instanceof Error ? cause.message : 'No se pudo guardar la playlist.'
export function PlaylistArt({ item }: { item: Playlist }) {
  return <div className={`playlist-art ${item.appearance}`}><Cover url={item.image_url} title={item.name} /></div>
}
export function PlaylistLibrary({ refresh, navigate, search }: { refresh: number; navigate: Navigate; search: string }) {
  const params = new URLSearchParams(search), query = params.get('q') ?? ''
  const raw = Number(params.get('offset') ?? 0), offset = Number.isSafeInteger(raw) && raw >= 0 ? raw : 0
  const result = useRead<Page>(`/playlists?${new URLSearchParams({ q: query, limit: '24', offset: String(offset) })}`, refresh)
  const [name, setName] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function create() {
    setBusy(true); setError('')
    try { const { data } = await metadataRequest<Playlist>('/playlists', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }); navigate(`/playlists/${data.id}`) }
    catch (cause) { setError(message(cause)) } finally { setBusy(false) }
  }
  return <><form className="playlist-create" onSubmit={event => { event.preventDefault(); void create() }}><label htmlFor="new-playlist">Nueva playlist</label><div><input id="new-playlist" maxLength={255} required value={name} onChange={event => setName(event.target.value)} disabled={busy} /><button disabled={busy || !name.trim()}>{busy ? 'Creando…' : 'Crear playlist'}</button></div></form>
    {error && <p role="alert">{error}</p>}<ReadState {...result} />{result.data && <><p role="status">{result.data.total} playlists{query && ` para «${query}»`}</p>
      {!result.data.items.length && <p className="empty-state">{query ? 'No hay playlists con ese nombre.' : 'Crea tu primera playlist y reúne tus canciones favoritas.'}</p>}
      <div className="album-grid">{result.data.items.map(item => <a className="album-card" key={item.id} href={`/playlists/${item.id}`} onClick={event => { event.preventDefault(); navigate(event.currentTarget.pathname) }}><PlaylistArt item={item} /><h2>{item.name}</h2><p>{item.track_count} pistas</p></a>)}</div>
      <Pagination offset={offset} total={result.data.total} move={value => navigate(`/biblioteca?${new URLSearchParams({ vista: 'playlists', q: query, offset: String(value) })}`)} /></>}</>
}

export function PlaylistView({ id, navigate, onSaved, onDirty }: { id: string; navigate: Navigate; onSaved: () => void; onDirty: (dirty: boolean) => void }) {
  const [item, setItem] = useState<Playlist | null>(null), [etag, setEtag] = useState('')
  const [name, setName] = useState(''), [appearance, setAppearance] = useState<'vinyl' | 'image'>('vinyl')
  const [songs, setSongs] = useState<Track[]>([]), [available, setAvailable] = useState<Track[]>([])
  const [candidateLimit, setCandidateLimit] = useState(24)
  const [query, setQuery] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('')
  const [catalogAttempt, setCatalogAttempt] = useState(0)
  const [catalogError, setCatalogError] = useState('')
  const [loaded, setLoaded] = useState(false), [dirty, setDirty] = useState(false)
  const active = useRef(true), saving = useRef(false)
  useEffect(() => { onDirty(dirty || busy); return () => onDirty(false) }, [dirty, busy, onDirty])
  const player = usePlayer()
  function accept(data: Playlist, token: string) { setItem(data); setEtag(token); setName(data.name); setAppearance(data.appearance); setSongs(data.items); setDirty(false); setLoaded(true) }
  async function reload() {
    setBusy(true); setError('')
    try { const result = await metadataRequest<Playlist>(`/playlists/${id}`); if (active.current) accept(result.data, result.etag) }
    catch (cause) { if (active.current) setError(message(cause)) } finally { if (active.current) setBusy(false) }
  }
  useEffect(() => { active.current = true; void reload(); return () => { active.current = false } }, [id])
  useEffect(() => {
    let live = true
    setCatalogError('')
    allMetadata<Track>('/tracks').then(values => { if (live) setAvailable(values) }).catch(cause => { if (live) setCatalogError(message(cause)) })
    return () => { live = false }
  }, [catalogAttempt])
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => { if (dirty || saving.current) event.preventDefault() }
    window.addEventListener('beforeunload', prevent)
    return () => window.removeEventListener('beforeunload', prevent)
  }, [dirty])
  async function write(image?: File | null) {
    if (!item || saving.current) return
    saving.current = true; setBusy(true); setError(''); setNotice('')
    let token = etag
    try {
      let imageId = item.image_asset_id
      if (image === null) imageId = null
      else if (image) { const form = new FormData(); form.append('file', image); form.append('purpose', 'playlist'); imageId = (await metadataRequest<{ id: string }>('/assets', { method: 'POST', body: form })).data.id }
      const renamed = await metadataRequest<Playlist>(`/playlists/${id}`, editOptions('PATCH', token, { name, appearance, image_asset_id: imageId }))
      token = renamed.etag
      // Conservar revisión confirmada si el segundo guardado falla.
      if (active.current) { setEtag(token); setItem(renamed.data) }
      const ordered = await metadataRequest<Playlist>(`/playlists/${id}/tracks`, editOptions('PUT', token, { track_ids: songs.map(song => song.id) }))
      if (active.current) { accept(ordered.data, ordered.etag); setNotice('Playlist guardada.'); onSaved() }
    } catch (cause) { if (active.current) { setError(`${message(cause)} Si se guardó solo una parte, recarga para revisar el resultado; tu borrador sigue aquí.`); setDirty(true) } }
    finally { saving.current = false; if (active.current) setBusy(false) }
  }
  function reorder(index: number, delta: number) {
    const next = [...songs]; [next[index], next[index + delta]] = [next[index + delta], next[index]]; setSongs(next); setDirty(true)
  }
  const selected = new Set(songs.map(song => song.id))
  const candidates = available.filter(song => !selected.has(song.id) && `${song.title} ${song.album_title} ${song.artists.map(value => value.name).join(' ')}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  return <section><a href="/biblioteca?vista=playlists" onClick={event => { event.preventDefault(); navigate('/biblioteca?vista=playlists') }}>← Mis playlists</a>
    {error && <p role="alert">{error}</p>}<p role="status">{busy ? 'Procesando playlist…' : notice || (dirty ? 'Cambios sin guardar' : '')}</p>
    <button className="secondary" disabled={busy} onClick={() => { if (!dirty || window.confirm('¿Descartar el borrador y recargar los datos guardados?')) void reload() }}>Recargar datos guardados</button>
    {!loaded && !error && <p>Cargando playlist…</p>}{item && <><div className="album-heading"><PlaylistArt item={item} /><div><p className="eyebrow">Tu selección</p><h1>{item.name}</h1><p>{item.track_count} pistas guardadas</p></div></div>
      <fieldset disabled={busy} className="playlist-editor"><legend>Editar playlist</legend><label>Nombre<input maxLength={255} value={name} onChange={event => { setName(event.target.value); setDirty(true) }} /></label>
        <label>Apariencia<select value={appearance} onChange={event => { setAppearance(event.target.value as 'vinyl' | 'image'); setDirty(true) }}><option value="vinyl">Vinilo con imagen central</option><option value="image">Tarjeta de imagen</option></select></label>
        <p className="note">Elegir o retirar una imagen guarda también el nombre, la apariencia y el orden actuales.</p>
        <label>Imagen PNG o JPEG (hasta 5 MiB)<input type="file" accept="image/png,image/jpeg" onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) { if (file.size > 5 * 1024 * 1024) setError('La imagen supera 5 MiB.'); else void write(file) } }} /></label>
        <button type="button" disabled={!item.image_asset_id} onClick={() => void write(null)}>Usar imagen predeterminada</button>
        <h2>Canciones y orden</h2><p>Los botones Subir y Bajar cambian el orden. Quitar conserva la canción en su álbum.</p>
        {!songs.length && <p>Esta playlist está vacía.</p>}<ol className="playlist-songs">{songs.map((song, index) => <li key={song.id}><span>{song.title} · {song.album_title}</span><div>
          <button type="button" aria-label={`Reproducir ${song.title} en la playlist guardada`} disabled={dirty} onClick={() => player.select(song, { path: `/playlists/${id}`, label: item.name }, item.items)}>▶</button>
          <button type="button" aria-label={`Subir ${song.title}`} disabled={index === 0} onClick={() => reorder(index, -1)}>Subir</button><button type="button" aria-label={`Bajar ${song.title}`} disabled={index === songs.length - 1} onClick={() => reorder(index, 1)}>Bajar</button>
          <button type="button" aria-label={`Quitar ${song.title}`} onClick={() => { setSongs(songs.filter(value => value.id !== song.id)); setDirty(true) }}>Quitar</button></div></li>)}</ol>
        {catalogError && <p role="alert">{catalogError} <button type="button" onClick={() => setCatalogAttempt(value => value + 1)}>Reintentar catálogo</button></p>}
        <label>Buscar canciones para añadir<input type="search" maxLength={200} value={query} onChange={event => setQuery(event.target.value)} /></label>
        <p>{candidates.length} canciones disponibles · {songs.length}/1000 en la lista</p><ul className="playlist-songs">{candidates.slice(0, candidateLimit).map(song => <li key={song.id}><span>{song.title} · {song.album_title}</span><button type="button" disabled={songs.length >= 1000} onClick={() => { setSongs([...songs, song]); setDirty(true) }}>Añadir {song.title}</button></li>)}</ul>{candidates.length > candidateLimit && <button type="button" onClick={() => setCandidateLimit(value => value + 24)}>Mostrar más canciones</button>}
        <button type="button" disabled={!name.trim()} onClick={() => void write()}>Guardar playlist</button>
      </fieldset><p className="note">Guarda los cambios para reproducir la lista en su nuevo orden.</p></>}
  </section>
}
