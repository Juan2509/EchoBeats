import { useId, useRef, useState } from 'react'
import type { Album, Track } from '../../shared/api/metadata'
import { editOptions, metadataRequest } from '../../shared/api/metadata'
import defaultCover from '../../shared/assets/default-cover.svg'
import { readAlbumTracks } from '../library/albumTracks'

export function AlbumDialog({ albumId, disabled, onSaved }: { albumId: string; disabled: boolean; onSaved: () => Promise<void> }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const headingId = useId()
  const [title, setTitle] = useState('')
  const [artists, setArtists] = useState('')
  const [etag, setEtag] = useState('')
  const [initial, setInitial] = useState({ title: '', artists: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [coverUrl, setCoverUrl] = useState<string | null>(null)
  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [coverTracks, setCoverTracks] = useState<Track[] | null>(null)
  const [coverTrackId, setCoverTrackId] = useState('')
  const [loadingCovers, setLoadingCovers] = useState(false)
  const selectedCover = coverTracks?.find(track => track.id === coverTrackId)

  async function load() {
    setError(''); setBusy(true)
    try {
      const response = await metadataRequest<Album>(`/albums/${albumId}`)
      if (response.data.system_key) throw new Error('Crea otro álbum para cambiar la agrupación de estas canciones.')
      setTitle(response.data.title); setArtists(response.data.artists.map(item => item.name).join('\n')); setEtag(response.etag)
      setInitial({ title: response.data.title, artists: response.data.artists.map(item => item.name).join('\n') })
      setCoverUrl(response.data.cover_url)
      setCoverFile(null)
      setCoverTracks(null)
      setCoverTrackId('')
      if (fileInput.current) fileInput.current.value = ''
      if (!dialog.current?.open) dialog.current?.showModal()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo cargar el álbum.') }
    finally { setBusy(false) }
  }

  async function loadCovers() {
    setError('')
    setLoadingCovers(true)
    try {
      const songs = await readAlbumTracks(albumId, AbortSignal.timeout(15000))
      setCoverTracks(songs.filter(track => track.cover_asset_id && track.cover_url))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudieron cargar las portadas de las canciones.')
    } finally {
      setLoadingCovers(false)
    }
  }

  async function save() {
    if (busy || loadingCovers) return
    setError(''); setBusy(true)
    try {
      const changes: Record<string, unknown> = {}
      if (title.trim() !== initial.title) changes.title = title.trim()
      if (artists !== initial.artists) changes.artist_names = artists.split('\n').map(value => value.trim()).filter(Boolean)
      if (coverFile) {
        const body = new FormData()
        body.append('file', coverFile)
        body.append('purpose', 'cover')
        const { data } = await metadataRequest<{ id: string }>('/assets', { method: 'POST', body })
        changes.cover_asset_id = data.id
      } else if (selectedCover) {
        changes.cover_asset_id = selectedCover.cover_asset_id
      }
      await metadataRequest(`/albums/${albumId}`, editOptions('PATCH', etag, changes))
      dialog.current?.close()
      await onSaved()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo guardar el álbum.') }
    finally { setBusy(false) }
  }

  return <>
    <button type="button" disabled={disabled || busy} onClick={load}>Editar álbum y portada</button>
    {error && !dialog.current?.open && <p role="alert">{error}</p>}
    <dialog ref={dialog} className="album-dialog" aria-labelledby={headingId} aria-busy={busy || loadingCovers} onCancel={event => { if (busy || loadingCovers) event.preventDefault() }}>
      <form onSubmit={event => { event.preventDefault(); void save() }}>
        <h3 id={headingId}>Editar álbum</h3>
        <label>Nombre del álbum<input required maxLength={255} value={title} onChange={event => setTitle(event.target.value)} disabled={busy} /></label>
        <label>Artistas del álbum (uno por línea)<textarea value={artists} onChange={event => setArtists(event.target.value)} disabled={busy} /></label>
        <div className="album-cover-options">
          <img key={selectedCover?.cover_url ?? coverUrl ?? ''} src={selectedCover?.cover_url ?? coverUrl ?? defaultCover}
            width="88" height="88" alt={selectedCover ? 'Portada de la canción seleccionada' : 'Portada actual del álbum'}
            onError={event => { if (!event.currentTarget.src.endsWith(defaultCover)) event.currentTarget.src = defaultCover }} />
          <label>Subir una portada (PNG o JPEG, hasta 5 MiB)
            <input ref={fileInput} type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" disabled={busy} onChange={event => {
              const file = event.target.files?.[0] ?? null
              setCoverFile(file)
              if (file) setCoverTrackId('')
            }} />
          </label>
          {coverTracks === null && <button type="button" disabled={busy || loadingCovers} onClick={loadCovers}>
            {loadingCovers ? 'Cargando portadas…' : 'Elegir portada de una canción'}
          </button>}
          {coverTracks?.length === 0 && <p role="status">Este álbum todavía no tiene canciones con portada propia.</p>}
          {!!coverTracks?.length && <label>Portada de una canción
            <select value={coverTrackId} disabled={busy} onChange={event => {
              setCoverTrackId(event.target.value)
              if (event.target.value) {
                setCoverFile(null)
                if (fileInput.current) fileInput.current.value = ''
              }
            }}>
              <option value="">Seleccionar canción</option>
              {coverTracks.map(track => <option key={track.id} value={track.id}>{track.title}{track.artists.length ? ` · ${track.artists.map(artist => artist.name).join(', ')}` : ''}</option>)}
            </select>
          </label>}
        </div>
        {error && <p role="alert">{error}</p>}
        <button disabled={busy || loadingCovers || !title.trim() || (title.trim() === initial.title && artists === initial.artists && !coverFile && !selectedCover)}>Guardar álbum</button>
        <button type="button" disabled={busy || loadingCovers} onClick={load}>Recargar datos del álbum</button>
        <button type="button" disabled={busy || loadingCovers} onClick={() => dialog.current?.close()}>Cancelar</button>
      </form>
    </dialog>
  </>
}
