import { useEffect, useId, useRef, useState } from 'react'
import type { Album } from '../../shared/api/metadata'
import { ConfirmDialog } from './ConfirmDialog'
import { readAlbumFolders } from './albumFolders'
import { notifyAlbumDeleted } from './DeleteTrackButton'

export function DeleteLibraryAlbums() {
  const [open, setOpen] = useState(false)
  return <>
    <button type="button" className="secondary danger-button" onClick={() => setOpen(true)}>Eliminar álbumes</button>
    {open && <AlbumSelection close={() => setOpen(false)} />}
  </>
}

function AlbumSelection({ close }: { close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const heading = useId()
  const [albums, setAlbums] = useState<Album[]>([])
  const [chosen, setChosen] = useState<Set<string>>(new Set())
  const [attempt, setAttempt] = useState(0)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [uncertain, setUncertain] = useState<Album | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const selected = albums.filter(album => chosen.has(album.id))

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    return () => element?.close()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 15000)
    let active = true
    setLoading(true)
    setError('')
    readAlbumFolders(controller.signal)
      .then(items => {
        if (!active) return
        setAlbums(items)
        setChosen(new Set())
      })
      .catch(() => { if (active) setError('No se pudieron cargar los álbumes. Vuelve a intentarlo.') })
      .finally(() => {
        clearTimeout(timer)
        if (active) setLoading(false)
      })
    return () => {
      active = false
      clearTimeout(timer)
      controller.abort()
    }
  }, [attempt])

  useEffect(() => {
    if (!busy) return
    const keepOpen = (event: Event) => event.preventDefault()
    window.addEventListener('echobeats:before-navigation', keepOpen)
    return () => window.removeEventListener('echobeats:before-navigation', keepOpen)
  }, [busy])

  function removed(id: string, trackIds: string[] = []) {
    setAlbums(current => current.filter(album => album.id !== id))
    setChosen(current => {
      const next = new Set(current)
      next.delete(id)
      return next
    })
    notifyAlbumDeleted(id, trackIds)
  }

  async function erase() {
    if (busy || loading || uncertain || !selected.length) return
    setBusy(true)
    setError('')
    setNotice('')
    let sent: Album | null = null
    let count = 0
    try {
      for (const album of selected) {
        const url = `/api/v1/albums/${encodeURIComponent(album.id)}`
        const current = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(15000) })
        if (current.status === 404) {
          removed(album.id)
          continue
        }
        if (!current.ok) throw Error('No se pudo consultar el álbum. Se detuvo la selección.')
        const data = await current.json()
        const etag = current.headers.get('etag')
        if (!etag || !Number.isInteger(album.revision) || data.id !== album.id || data.revision !== album.revision ||
            data.track_count !== album.track_count || data.system_key !== null) {
          throw Error('Un álbum cambió. Cierra la ventana y vuelve a revisar la selección.')
        }

        sent = album
        const response = await fetch(url, { method: 'DELETE', headers: { 'If-Match': etag }, signal: AbortSignal.timeout(15000) })
        if (!response.ok) {
          if (response.status < 500) sent = null
          throw Error('No se pudo eliminar el álbum. Se detuvo el resto de la selección.')
        }
        const result = await response.json()
        if (result.album_id !== album.id || result.deleted !== true || !Array.isArray(result.track_ids) ||
            !result.track_ids.every((id: unknown) => typeof id === 'string')) {
          throw Error('Respuesta de eliminación no válida.')
        }
        sent = null
        removed(album.id, result.track_ids)
        count++
      }
    } catch (cause) {
      if (sent) setUncertain(sent)
      setError(sent ? `No se confirmó la eliminación de «${sent.title}». Comprueba su estado antes de continuar.`
        : cause instanceof Error && cause.name === 'Error' ? cause.message : 'Se interrumpió la operación. Revisa los álbumes restantes.')
    } finally {
      setBusy(false)
      setNotice(count === 1 ? '1 álbum eliminado.' : `${count} álbumes eliminados.`)
    }
  }

  async function check() {
    if (busy || !uncertain) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`/api/v1/albums/${encodeURIComponent(uncertain.id)}`, { cache: 'no-store', signal: AbortSignal.timeout(15000) })
      if (response.status === 404) {
        removed(uncertain.id)
        setNotice('El álbum ya fue eliminado.')
      } else if (response.ok) {
        setNotice('El álbum sigue en la biblioteca. Puedes revisar y confirmar otra vez.')
      } else {
        throw Error('No se pudo comprobar el estado.')
      }
      setUncertain(null)
    } catch {
      setError('No se pudo comprobar el estado. Vuelve a comprobar antes de continuar.')
    } finally {
      setBusy(false)
    }
  }

  const albumNames = selected.length === 1 ? `«${selected[0].title}»` : `estos ${selected.length} álbumes`
  return <dialog ref={dialog} className="album-dialog deletion-dialog" aria-labelledby={heading}
    onCancel={event => { event.preventDefault(); if (!busy) close() }}>
    <header><h2 id={heading}>Eliminar álbumes</h2>
      <button type="button" className="secondary" disabled={busy} onClick={close}>Cerrar</button>
    </header>
    <p>Selecciona los álbumes que quieres retirar de la biblioteca.</p>
    {loading ? <p role="status">Cargando álbumes…</p> : <fieldset disabled={busy || !!uncertain}>
      <legend>Álbumes de tu biblioteca</legend>
      {albums.length > 0 ? <>
        <button type="button" className="secondary" onClick={() => setChosen(chosen.size === albums.length ? new Set() : new Set(albums.map(album => album.id)))}>
          {chosen.size === albums.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
        </button>
        <div className="delete-track-options">
          {albums.map(album => <label key={album.id}>
            <input type="checkbox" checked={chosen.has(album.id)} onChange={event => {
              const checked = event.target.checked
              setChosen(current => {
                const next = new Set(current)
                if (checked) next.add(album.id)
                else next.delete(album.id)
                return next
              })
            }} />
            <span>{album.title}<small>{album.track_count} {album.track_count === 1 ? 'pista' : 'pistas'}</small></span>
          </label>)}
        </div>
      </> : !error && <p>No hay álbumes para eliminar.</p>}
    </fieldset>}
    {!loading && <p role="status">{chosen.size} {chosen.size === 1 ? 'seleccionado' : 'seleccionados'}. {notice}</p>}
    {error && <p role="alert">{error}</p>}
    {!loading && !albums.length && error && <button type="button" onClick={() => setAttempt(value => value + 1)}>Recargar álbumes</button>}
    <div className="editor-actions">
      <button type="button" className="secondary" disabled={busy} onClick={close}>Cancelar</button>
      {uncertain ? <button type="button" disabled={busy} onClick={() => void check()}>Comprobar eliminación</button>
        : <button type="button" className="danger-button" disabled={busy || loading || !selected.length}
          onClick={() => setConfirming(true)}>{busy ? 'Eliminando…' : `Eliminar seleccionados (${chosen.size})`}</button>}
    </div>
    {confirming && <ConfirmDialog
      message={`¿Eliminar ${albumNames} junto con sus muros y retirar sus canciones de la biblioteca y las listas? Se conservarán los archivos originales y el historial musical.`}
      answer={confirmed => { setConfirming(false); if (confirmed) void erase() }} />}
  </dialog>
}
