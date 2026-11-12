import { useEffect, useRef, useState } from 'react'
import type { Album, Track } from '../../shared/api/metadata'
import { allMetadata, editOptions, metadataRequest } from '../../shared/api/metadata'
import defaultCover from '../../shared/assets/default-cover.svg'
import { AlbumDialog } from './AlbumDialog'

type Draft = { title: string; artists: string; album: string; number: string }
const blank: Draft = { title: '', artists: '', album: '', number: '' }
const sourceName = (source?: string) => ({ file: 'Del archivo', manual: 'Editado por ti', fallback: 'Provisional', album: 'Del álbum' }[source ?? 'fallback'] ?? 'Registrado')

export function MetadataEditor({ refresh, onSaved }: { refresh: number; onSaved?: () => void }) {
  const [tracks, setTracks] = useState<Track[]>([])
  const [albums, setAlbums] = useState<Album[]>([])
  const [selected, setSelected] = useState('')
  const [current, setCurrent] = useState<Track | null>(null)
  const [draft, setDraft] = useState<Draft>(blank)
  const [token, setToken] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [cover, setCover] = useState<File | null>(null)
  const [defaultRequested, setDefaultRequested] = useState(false)
  const [newAlbum, setNewAlbum] = useState('')
  const coverInput = useRef<HTMLInputElement>(null)
  const requestSequence = useRef(0)

  const dirty = !!current && (draft.title !== current.title || draft.artists !== current.artists.map(item => item.name).join('\n') || draft.album !== current.album_id || draft.number !== String(current.track_number ?? '') || !!cover || defaultRequested)
  const discard = () => !dirty || window.confirm('Hay cambios sin guardar. ¿Quieres descartarlos?')

  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  async function loadLists() {
    const [songs, collections] = await Promise.all([allMetadata<Track>('/tracks'), allMetadata<Album>('/albums')])
    setTracks(songs); setAlbums(collections)
    setSelected(value => value || songs[0]?.id || '')
  }

  useEffect(() => {
    let active = true
    setLoading(true)
    Promise.all([allMetadata<Track>('/tracks'), allMetadata<Album>('/albums')])
      .then(([songs, collections]) => { if (active) { setTracks(songs); setAlbums(collections); setSelected(value => value || songs[0]?.id || '') } })
      .catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'No se pudieron cargar las canciones.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [refresh])

  function accept(data: Track, etag: string) {
    setCurrent(data); setToken(etag)
    setDraft({ title: data.title, artists: data.artists.map(item => item.name).join('\n'), album: data.album_id, number: String(data.track_number ?? '') })
    setCover(null); setDefaultRequested(false)
    if (coverInput.current) coverInput.current.value = ''
    setTracks(values => values.map(item => item.id === data.id ? data : item))
  }

  async function loadTrack(id: string) {
    const sequence = ++requestSequence.current
    setBusy(true); setError(''); setMessage('')
    try {
      const response = await metadataRequest<Track>(`/tracks/${id}`)
      if (sequence === requestSequence.current) accept(response.data, response.etag)
    } catch (cause) { if (sequence === requestSequence.current) { setCurrent(null); setError(cause instanceof Error ? cause.message : 'No se pudo cargar la canción.') } }
    finally { if (sequence === requestSequence.current) setBusy(false) }
  }

  useEffect(() => { if (selected) void loadTrack(selected); return () => { requestSequence.current += 1 } }, [selected])

  async function save() {
    if (!current || busy) return
    setError(''); setMessage(''); setBusy(true)
    try {
      const changes: Record<string, unknown> = {}
      if (draft.title !== current.title) changes.title = draft.title.trim()
      if (draft.artists !== current.artists.map(item => item.name).join('\n')) changes.artist_names = draft.artists.split('\n').map(item => item.trim()).filter(Boolean)
      if (draft.album !== current.album_id) changes.album_id = draft.album
      if (draft.number !== String(current.track_number ?? '')) changes.track_number = draft.number ? Number(draft.number) : null
      if (cover) {
        const body = new FormData(); body.append('file', cover); body.append('purpose', 'cover')
        const result = await metadataRequest<{ id: string }>('/assets', { method: 'POST', body })
        changes.cover_asset_id = result.data.id
      } else if (defaultRequested) changes.cover_asset_id = null
      const response = await metadataRequest<Track>(`/tracks/${current.id}`, editOptions('PATCH', token, changes))
      accept(response.data, response.etag)
      setMessage('Cambios guardados en tu biblioteca. El audio original se conserva.')
      await loadLists()
      onSaved?.()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo guardar. Tus cambios siguen en el formulario.') }
    finally { setBusy(false) }
  }

  async function extract() {
    if (!current || !discard()) return
    setError(''); setMessage(''); setBusy(true)
    try {
      const response = await metadataRequest<Track>(`/tracks/${current.id}/extract-metadata`, editOptions('POST', token))
      accept(response.data, response.etag)
      setMessage(response.data.metadata_warnings?.length ? 'Etiquetas leídas. Alguna portada no era válida y se ignoró; los cambios manuales se conservaron.' : 'Etiquetas leídas; los campos editados manualmente se conservaron.')
      await loadLists()
      onSaved?.()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudieron leer las etiquetas.') }
    finally { setBusy(false) }
  }

  async function createAlbum() {
    if (!newAlbum.trim()) return
    setBusy(true); setError('')
    try {
      const result = await metadataRequest<Album>('/albums', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newAlbum.trim(), artist_names: [] }) })
      setAlbums(values => [...values, result.data]); setDraft(value => ({ ...value, album: result.data.id })); setNewAlbum('')
      setMessage('Álbum creado. Guarda la canción para asignarla a él.')
      onSaved?.()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo crear el álbum.') }
    finally { setBusy(false) }
  }

  return <section className="metadata-editor" aria-labelledby="metadata-title">
    <h2 id="metadata-title">Revisa los datos de tu música</h2>
    <p className="note">Corrige los datos de tu biblioteca. No se cambia el contenido del archivo MP3.</p>
    <button type="button" disabled={busy} onClick={async () => { setBusy(true); setError(''); try { await loadLists() } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo recargar la lista.') } finally { setBusy(false) } }}>Recargar lista de canciones y álbumes</button>
    {loading && <p role="status">Cargando canciones…</p>}
    {!loading && !tracks.length && <p>Importa un MP3 para revisar sus datos aquí.</p>}
    <label>Canción<select disabled={busy || !tracks.length} value={selected} onChange={event => { if (discard()) setSelected(event.target.value) }}>
      {!tracks.length && <option value="">Sin canciones</option>}
      {tracks.map(item => <option key={item.id} value={item.id}>{item.title} · {item.artists.map(credit => credit.name).join(', ') || 'Artista desconocido'}</option>)}
    </select></label>
    <button type="button" disabled={!selected || busy} onClick={() => { if (discard()) void loadTrack(selected) }}>Recargar datos de la canción</button>
    {current && <>
      <div className="metadata-summary"><img src={current.cover_url ?? defaultCover} width="128" height="128" alt="Portada de la canción" onError={event => { if (!event.currentTarget.src.endsWith(defaultCover)) event.currentTarget.src = defaultCover }} />
        <p>{current.album_title}<br />Duración: {Math.floor(current.duration_ms / 60000)}:{String(Math.floor(current.duration_ms / 1000) % 60).padStart(2, '0')}<br />{dirty ? 'Cambios sin guardar' : 'Datos guardados'}</p></div>
      <form onSubmit={event => { event.preventDefault(); void save() }}>
        <label>Título <small>{sourceName(current.metadata_sources.title)}</small><input required maxLength={255} value={draft.title} disabled={busy} onChange={event => setDraft(value => ({ ...value, title: event.target.value }))} /></label>
        <label>Artistas (uno por línea) <small>{sourceName(current.metadata_sources.artists)}</small><textarea value={draft.artists} disabled={busy} onChange={event => setDraft(value => ({ ...value, artists: event.target.value }))} /></label>
        <label>Número de pista <small>{sourceName(current.metadata_sources.track_number)}</small><input type="number" min="1" max="2147483647" step="1" value={draft.number} disabled={busy} onChange={event => setDraft(value => ({ ...value, number: event.target.value }))} /></label>
        <label>Álbum <small>{sourceName(current.metadata_sources.album)}</small><select value={draft.album} disabled={busy} onChange={event => setDraft(value => ({ ...value, album: event.target.value }))}>
          {albums.map(item => <option key={item.id} value={item.id}>{item.title}{item.artists.length ? ` · ${item.artists.map(credit => credit.name).join(', ')}` : ''}</option>)}
        </select></label>
        <label>Portada PNG o JPEG (hasta 5 MiB) <small>{sourceName(current.cover_source)}</small><input ref={coverInput} type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" disabled={busy} onChange={event => { setCover(event.target.files?.[0] ?? null); setDefaultRequested(false) }} /></label>
        <button type="button" disabled={busy} onClick={() => { setCover(null); setDefaultRequested(true); if (coverInput.current) coverInput.current.value = '' }}>Usar portada predeterminada al guardar</button>
        {defaultRequested && <p>Se aplicará la portada predeterminada al guardar.</p>}
        <div className="editor-actions"><button disabled={busy || !dirty || !draft.title.trim()}>Guardar cambios</button>
          <button type="button" disabled={busy} onClick={extract}>Volver a leer etiquetas del original</button></div>
      </form>
      <fieldset disabled={busy}><legend>Crear otro álbum</legend><label>Nombre del nuevo álbum<input value={newAlbum} maxLength={255} onChange={event => setNewAlbum(event.target.value)} /></label><button type="button" disabled={!newAlbum.trim()} onClick={createAlbum}>Crear álbum y seleccionarlo</button></fieldset>
      {albums.find(item => item.id === current.album_id)?.system_key === null && <AlbumDialog albumId={current.album_id} disabled={busy || dirty} onSaved={async () => { await loadLists(); await loadTrack(selected); onSaved?.() }} />}
      {dirty && <p className="note">Guarda o descarta los cambios de la canción antes de editar el álbum compartido.</p>}
    </>}
    {busy && <p role="status">Procesando…</p>}
    {error && <p className="import-error" role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
  </section>
}
