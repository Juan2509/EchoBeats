import { useState } from 'react'
import type { FormEvent } from 'react'

type ImportResult = {
  index: number
  file_name: string
  status: 'imported' | 'duplicate' | 'rejected'
  track_id?: string
  error?: { code: string; message: string }
}

export function ImportPanel() {
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<ImportResult[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!files.length || busy) return
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
      const response = await fetch('/api/v1/imports', { method: 'POST', body, signal: controller.signal })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error?.message ?? 'No se pudo completar la importación.')
      if (!Array.isArray(data.results) || data.results.length !== files.length) throw new Error('La respuesta de importación no está completa.')
      setResults(data.results)
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
      <p id="import-help" className="note">MP3 · hasta 50 MiB por archivo · 20 archivos y 200 MiB por solicitud, incluido el formulario.</p>
      <form onSubmit={submit}>
        <label htmlFor="music-files">Seleccionar archivos MP3</label>
        <input id="music-files" name="files" type="file" accept=".mp3,audio/mpeg" multiple
          aria-describedby="import-help" disabled={busy}
          onChange={event => { setFiles(Array.from(event.target.files ?? [])); setResults([]); setError('') }} />
        <p className="note">{files.length ? `${files.length} archivo(s) seleccionado(s)` : 'Todavía no has seleccionado archivos.'}</p>
        <button type="submit" disabled={!files.length || busy}>{busy ? 'Importando…' : 'Importar a mi biblioteca'}</button>
      </form>
      <div aria-live="polite" aria-atomic="true">
        {busy && <p>Guardando y comprobando tus archivos. Espera antes de cerrar esta página.</p>}
        {error && <p role="alert" className="import-error">{error}</p>}
        {results.length > 0 && <p>{results.filter(item => item.status === 'imported').length} importados · {results.filter(item => item.status === 'duplicate').length} ya existentes · {results.filter(item => item.status === 'rejected').length} rechazados</p>}
      </div>
      {results.length > 0 && <ul className="import-results" aria-label="Resultados de importación">
        {results.map(result => <li key={result.index}>
          <strong>{result.file_name}</strong>
          <span>{result.status === 'imported' ? 'Guardado en tu biblioteca' : result.status === 'duplicate' ? 'Ya está en tu biblioteca' : result.error?.message ?? 'No se pudo importar'}</span>
        </li>)}
      </ul>}
    </section>
  )
}
