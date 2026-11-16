import { useEffect,useState } from 'react'
import type { FormEvent } from 'react'
import { audioFileAccept, audioFormatsLabel } from '../../shared/audioFormats'
import {readAlbumFolders} from '../library/albumFolders'
import type {Album} from '../../shared/api/metadata'

type ImportResult = {
  index: number
  file_name: string
  status: 'imported' | 'duplicate' | 'rejected'
  track_id?: string
  error?: { code: string; message: string }
  metadata_warnings?: string[]
  destination_mismatch?:boolean
  restored?:boolean
}

export function ImportPanel({ onImported,albumId,albumTitle }: { onImported: () => void;albumId?:string;albumTitle?:string }) {
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<ImportResult[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [albums,setAlbums]=useState<Album[]>([]),[destination,setDestination]=useState(albumId??''),[loadingAlbums,setLoadingAlbums]=useState(!albumId),[albumError,setAlbumError]=useState(''),[attempt,retry]=useState(0)
  useEffect(()=>{if(albumId){setDestination(albumId);return}const abort=new AbortController();let active=true;setLoadingAlbums(true);setAlbumError('');const timer=setTimeout(()=>abort.abort(),15000);readAlbumFolders(abort.signal).then(items=>{if(active){setAlbums(items);setDestination(current=>items.some(item=>item.id===current)?current:'')}}).catch(()=>{if(active)setAlbumError('No se pudieron cargar los álbumes. Vuelve a intentarlo.')}).finally(()=>{clearTimeout(timer);if(active)setLoadingAlbums(false)});return()=>{active=false;clearTimeout(timer);abort.abort()}},[albumId,attempt])
  useEffect(()=>{if(!busy)return;const guard=(event:Event)=>event.preventDefault();window.addEventListener('echobeats:before-navigation',guard);window.addEventListener('beforeunload',guard);return()=>{window.removeEventListener('echobeats:before-navigation',guard);window.removeEventListener('beforeunload',guard)}},[busy])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!files.length || busy||!destination) return
    setError('')
    setResults([])
    if (files.length > 20 || files.reduce((size, file) => size + file.size, 0) > 200 * 1024 * 1024) {
      setError('Selecciona hasta 20 archivos y menos de 200 MiB en total.')
      return
    }
    const body = new FormData()
    files.forEach(file => body.append('files', file))
    setBusy(true)
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 120000)
    try {
      const response = await fetch(`/api/v1/imports?${new URLSearchParams({album_id:destination})}`, { method: 'POST', body, signal: controller.signal })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error?.message ?? 'No se pudo completar la importación.')
      if (!Array.isArray(data.results) || data.results.length !== files.length) throw new Error('La respuesta de importación no está completa.')
      setResults(data.results)
      onImported()
    } catch (cause) {
      const message = 'No se pudo confirmar la respuesta. Puedes reintentar; los archivos ya guardados se detectarán como duplicados.'
      setError(cause instanceof Error && !(cause instanceof TypeError) && !(cause instanceof SyntaxError) && cause.name !== 'AbortError' ? cause.message : message)
    } finally {
      window.clearTimeout(timeout)
      setBusy(false)
    }
  }

  return (
    <section className="import-panel" aria-labelledby="import-title">
      <h2 id="import-title">Añade tu música</h2>
      <p id="import-help" className="note">{audioFormatsLabel} · hasta 50 MiB por archivo · 20 archivos y 200 MiB por solicitud, incluido el formulario. La reproducción depende de los códecs del navegador.</p>
      <form onSubmit={submit}>
        {albumId?<p className="import-destination">Destino: <strong>{albumTitle??'Este álbum'}</strong></p>:<><label>Álbum de destino<select required value={destination} disabled={busy||loadingAlbums} onChange={event=>setDestination(event.target.value)}><option value="">Elige un álbum / vinilo</option>{albums.map(album=><option key={album.id} value={album.id}>{album.title}</option>)}</select></label>{loadingAlbums&&<p role="status">Cargando álbumes…</p>}{albumError&&<p role="alert">{albumError} <button type="button" onClick={()=>retry(value=>value+1)}>Recargar álbumes</button></p>}{!loadingAlbums&&!albums.length&&!albumError&&<p>Crea primero un álbum desde Biblioteca para guardar tu música.</p>}</>}
        <label htmlFor="music-files">Seleccionar archivos de audio</label>
        <input id="music-files" name="files" type="file" accept={audioFileAccept} multiple
          aria-describedby="import-help" disabled={busy||!destination}
          onChange={event => { setFiles(Array.from(event.target.files ?? [])); setResults([]); setError('') }} />
        <p className="note">{files.length ? `${files.length} archivo(s) seleccionado(s)` : 'Todavía no has seleccionado archivos.'}</p>
        <button type="submit" disabled={!files.length || busy||!destination}>{busy ? 'Importando…' : 'Importar al álbum elegido'}</button>
      </form>
      <div aria-live="polite" aria-atomic="true">
        {busy && <p>Guardando y comprobando tus archivos. Espera antes de cerrar esta página.</p>}
        {error && <p role="alert" className="import-error">{error}</p>}
        {results.length > 0 && <p>{results.filter(item => item.status === 'imported').length} importados · {results.filter(item => item.status === 'duplicate').length} ya existentes · {results.filter(item => item.status === 'rejected').length} rechazados</p>}
      </div>
      {results.length > 0 && <ul className="import-results" aria-label="Resultados de importación">
        {results.map(result => <li key={result.index}>
          <strong>{result.file_name}</strong>
          <span>{result.status === 'imported' ? result.restored?'Recuperada y añadida al álbum':'Guardado en el álbum elegido' : result.status === 'duplicate' ? result.destination_mismatch?'Ya existe en otro álbum. No se ha movido.':'Ya está en este álbum' : result.error?.message ?? 'No se pudo importar'}</span>
          {!!result.metadata_warnings?.length && <span>El audio está guardado; revisa sus datos y portada en el editor.</span>}
        </li>)}
      </ul>}
    </section>
  )
}
