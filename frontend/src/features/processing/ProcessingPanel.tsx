import { useEffect, useRef, useState } from 'react'

type Job = { id: string; status: 'pending' | 'processing' | 'completed' | 'error' | 'stale'; input_version: number; is_current: boolean; attempts: number; error_message: string | null }
const labels = { pending: 'Pendiente', processing: 'Procesando', completed: 'Completado', error: 'Error', stale: 'Desactualizado' }
export function ProcessingPanel({ trackId, revision }: { trackId: string; revision: number }) {
  const [open, setOpen] = useState(false), [sequence, refresh] = useState(0)
  const [jobs, setJobs] = useState<Job[]>([]), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const command = useRef<string | null>(null)
  useEffect(() => {
    if (!open) return
    let active = true, timer: ReturnType<typeof setTimeout> | undefined
    let pending: AbortController | undefined
    const action = command.current; command.current = null
    async function request(path: string, method = 'GET') {
      const abort = new AbortController(); pending = abort
      const timeout = setTimeout(() => abort.abort(), 15000)
      try {
        const response = await fetch(`/api/v1${path}`, { method, signal: abort.signal, cache: 'no-store', ...(method === 'POST' && path.endsWith('/processing-jobs') ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ operation: 'prepare_metadata' }) } : {}) })
        const value = await response.json()
        if (!response.ok) throw new Error(value.error?.message ?? 'No se pudo consultar el procesamiento.')
        return value
      } finally { clearTimeout(timeout) }
    }
    async function load(first = false) {
      if (!active) return
      setBusy(true); setError('')
      try {
        if (first && action) await request(action, 'POST')
        if (!active) return
        const value = await request(`/tracks/${encodeURIComponent(trackId)}/processing-jobs`)
        if (!active) return
        if (!Array.isArray(value.items) || value.items.some((job: Job) => !job || typeof job.id !== 'string' || !Object.prototype.hasOwnProperty.call(labels, job.status) || !Number.isInteger(job.attempts) || typeof job.is_current !== 'boolean')) throw new Error('La respuesta de procesamiento no es válida. Actualiza el estado.')
        setJobs(value.items)
        if (value.items.some((job: Job) => job.status === 'pending' || job.status === 'processing')) timer = setTimeout(() => void load(), 2000)
      } catch (cause) {
        if (active) setError(cause instanceof Error && !(cause instanceof TypeError) && !(cause instanceof SyntaxError) && cause.name !== 'AbortError' ? cause.message : 'No se pudo confirmar la operación. Actualiza el estado antes de reintentar.')
      } finally { if (active) setBusy(false) }
    }
    void load(true)
    return () => { active = false; pending?.abort(); clearTimeout(timer) }
  }, [open, trackId, revision, sequence])
  const current = jobs.find(job => job.is_current)
  function send(path: string) { command.current = path; refresh(value => value + 1) }
  return <details className="processing-panel" onToggle={event => { const value = event.currentTarget.open; if (!value) command.current = null; setOpen(value) }}>
    <summary>Preparación de información</summary>
    {open && <div>
      <p className="note">Prepara metadatos existentes en segundo plano. Todavía no analiza el sonido ni genera fichas musicales o embeddings.</p>
      {error && <p role="alert">{error}</p>}
      <p role="status">{busy ? 'Consultando…' : current ? `${labels[current.status]} · intento ${current.attempts}/3` : 'Sin preparación para los metadatos actuales.'}</p>
      {current?.error_message && <p>{current.error_message}</p>}
      <div className="processing-actions">
        <button className="secondary" disabled={busy || !!current} onClick={() => send(`/tracks/${encodeURIComponent(trackId)}/processing-jobs`)}>Preparar información</button>
        {current && ['error', 'stale'].includes(current.status) && <button className="secondary" disabled={busy || current.attempts >= 3} onClick={() => send(`/jobs/${encodeURIComponent(current.id)}/retry`)}>Reintentar preparación</button>}
        <button className="secondary" disabled={busy} onClick={() => refresh(value => value + 1)}>Actualizar estado</button>
      </div>
      {!!jobs.length && <ul aria-label="Historial de preparación">{jobs.map(job => <li key={job.id}>Versión {job.input_version}: {labels[job.status]}{job.is_current ? '' : ' · metadatos anteriores'}</li>)}</ul>}
    </div>}
  </details>
}
