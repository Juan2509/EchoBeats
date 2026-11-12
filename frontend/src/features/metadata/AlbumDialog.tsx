import { useRef, useState } from 'react'
import type { Album } from '../../shared/api/metadata'
import { editOptions, metadataRequest } from '../../shared/api/metadata'

export function AlbumDialog({ albumId, disabled, onSaved }: { albumId: string; disabled: boolean; onSaved: () => Promise<void> }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [title, setTitle] = useState('')
  const [artists, setArtists] = useState('')
  const [etag, setEtag] = useState('')
  const [initial, setInitial] = useState({ title: '', artists: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setError(''); setBusy(true)
    try {
      const response = await metadataRequest<Album>(`/albums/${albumId}`)
      if (response.data.system_key) throw new Error('Crea otro álbum para cambiar la agrupación de estas canciones.')
      setTitle(response.data.title); setArtists(response.data.artists.map(item => item.name).join('\n')); setEtag(response.etag)
      setInitial({ title: response.data.title, artists: response.data.artists.map(item => item.name).join('\n') })
      if (!dialog.current?.open) dialog.current?.showModal()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo cargar el álbum.') }
    finally { setBusy(false) }
  }

  async function save() {
    setError(''); setBusy(true)
    try {
      const changes: Record<string, unknown> = {}
      if (title.trim() !== initial.title) changes.title = title.trim()
      if (artists !== initial.artists) changes.artist_names = artists.split('\n').map(value => value.trim()).filter(Boolean)
      await metadataRequest(`/albums/${albumId}`, editOptions('PATCH', etag, changes))
      dialog.current?.close()
      await onSaved()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo guardar el álbum.') }
    finally { setBusy(false) }
  }

  return <>
    <button type="button" disabled={disabled || busy} onClick={load}>Editar nombre y artistas del álbum</button>
    {error && !dialog.current?.open && <p role="alert">{error}</p>}
    <dialog ref={dialog} className="album-dialog" onCancel={event => { if (busy) event.preventDefault() }}>
      <form onSubmit={event => { event.preventDefault(); void save() }}>
        <h3>Editar álbum</h3>
        <p>Estos cambios se aplican a todas las canciones de este álbum.</p>
        <label>Nombre del álbum<input required maxLength={255} value={title} onChange={event => setTitle(event.target.value)} disabled={busy} /></label>
        <label>Artistas del álbum (uno por línea)<textarea value={artists} onChange={event => setArtists(event.target.value)} disabled={busy} /></label>
        {error && <p role="alert">{error}</p>}
        <button disabled={busy || !title.trim() || (title.trim() === initial.title && artists === initial.artists)}>Guardar álbum</button>
        <button type="button" disabled={busy} onClick={load}>Recargar datos del álbum</button>
        <button type="button" disabled={busy} onClick={() => dialog.current?.close()}>Cancelar</button>
      </form>
    </dialog>
  </>
}
