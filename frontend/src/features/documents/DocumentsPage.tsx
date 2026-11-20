import { useEffect, useState } from 'react'

type Document = { id: string; name: string; status: 'pending' | 'processing' | 'ready' | 'failed'; error: string | null }
type Listing = { items: Document[]; query_enabled: boolean; upload_enabled: boolean }
type Answer = { answer: string | null; sources: { document: string; page: number; section: string | null; quote: string }[] }

const states = { pending: 'En espera', processing: 'Procesando', ready: 'Listo', failed: 'Falló' }
const errors: Record<string, string> = {
  unsafe_pdf: 'El escaneo rechazó el PDF.',
  scanner_unavailable: 'El escáner de archivos no está disponible.',
  invalid_pdf: 'No se pudo abrir el PDF o está cifrado.',
  page_limit: 'El PDF supera el límite de 12 páginas.',
  chunk_limit: 'El documento supera el límite de texto indexable.',
  no_text: 'No se pudo extraer texto.',
  processing_limit: 'El procesamiento superó sus límites.',
  ai_quota: 'OpenAI rechazó la solicitud por cuota o créditos.',
}

async function call<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1/documents${url}`, { cache: 'no-store', ...options })
  if (response.status === 204) return undefined as T
  const data = await response.json()
  if (!response.ok) throw Error(data.error?.message ?? 'No se pudo completar la operación.')
  return data
}

export function DocumentsPage() {
  const [listing, setListing] = useState<Listing | null>(null)
  const [page, setPage] = useState(0)
  const [refresh, setRefresh] = useState(0)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [listError, setListError] = useState(false)
  const [selection, setSelection] = useState<string | null>(null)
  const [remove, setRemove] = useState<Document | null>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<Answer | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    async function load() {
      try {
        const result = await call<Listing>(`?limit=20&offset=${page * 20}`, { signal: controller.signal })
        if (controller.signal.aborted) return
        setListing(result)
        setListError(false)
        if (result.items.some(item => item.status === 'pending' || item.status === 'processing')) {
          timer = setTimeout(() => void load(), 2500)
        }
      } catch {
        if (!controller.signal.aborted) setListError(true)
      }
    }
    void load()
    return () => { controller.abort(); clearTimeout(timer) }
  }, [page, refresh])

  async function work(action: () => Promise<void>) {
    setBusy(true)
    setMessage('')
    try { await action() }
    catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo completar la operación.')
    } finally { setBusy(false) }
  }

  const active = listing?.items.find(item => item.id === selection && item.status === 'ready')

  return <section className="explore-view documents-view" aria-labelledby="documents-title">
    <h1 id="documents-title">Documentos</h1>
    <form className="explore-form" onSubmit={event => {
      event.preventDefault()
      const form = event.currentTarget
      const file = new FormData(form).get('pdf')
      if (!(file instanceof File) || !file.size || file.size > 10 * 1024 * 1024) {
        setMessage('Selecciona un PDF de hasta 10 MiB.')
        return
      }
      void work(async () => {
        await call('', {
          method: 'POST', body: file,
          headers: { 'Content-Type': 'application/pdf', 'X-Document-Name': encodeURIComponent(file.name) },
        })
        form.reset()
        setPage(0)
        setRefresh(value => value + 1)
        setMessage('PDF recibido para procesamiento.')
      })
    }}>
      <fieldset disabled={busy || !listing?.upload_enabled}>
        <label>PDF de hasta 10 MiB y 12 páginas <input name="pdf" type="file" accept=".pdf,application/pdf" required /></label>
        <p>OpenAI recibe el texto extraído para indexarlo. Conserva el PDF original en tu equipo.</p>
        <button>Procesar PDF</button>
      </fieldset>
    </form>
    {listing && !listing.upload_enabled && <p>Para cargar PDF, activa el flujo documental y OpenAI en el servidor, y prepara las firmas de ClamAV.</p>}
    {listError && <p role="alert">No se pudo consultar la biblioteca documental. <button onClick={() => setRefresh(value => value + 1)}>Actualizar</button></p>}
    {message && <p role="status">{message}</p>}
    {!listing && !listError && <p role="status">Cargando documentos…</p>}
    {listing && !listing.items.length && <p>No hay documentos en esta página.</p>}
    <ul className="explore-results">
      {listing?.items.map(item => <li key={item.id} className="explore-result">
        <strong>{item.name}</strong> · {states[item.status]}
        {item.error && <p>{errors[item.error] ?? 'No se pudo completar el procesamiento. Puedes cargar el PDF de nuevo.'}</p>}
        <button type="button" disabled={busy || item.status !== 'ready' || !listing.query_enabled} onClick={() => {
          setSelection(item.id); setQuestion(''); setAnswer(null)
        }}>Consultar</button>
        <button type="button" className="secondary" disabled={busy} onClick={() => setRemove(item)}>Eliminar</button>
      </li>)}
    </ul>
    {(page > 0 || listing?.items.length === 20) && <nav aria-label="Páginas de documentos">
      <button disabled={busy || page === 0} onClick={() => { setSelection(null); setAnswer(null); setPage(value => value - 1) }}>Anterior</button>
      <span> Página {page + 1} </span>
      <button disabled={busy || listing?.items.length !== 20} onClick={() => { setSelection(null); setAnswer(null); setPage(value => value + 1) }}>Siguiente</button>
    </nav>}
    {remove && <section className="explore-result" aria-label="Confirmar eliminación">
      <p>¿Eliminar el índice y los datos de {remove.name}?</p>
      <button disabled={busy} onClick={() => void work(async () => {
        await call(`/${remove.id}`, { method: 'DELETE' })
        if (selection === remove.id) { setSelection(null); setAnswer(null) }
        setRemove(null)
        setRefresh(value => value + 1)
      })}>Eliminar documento</button>
      <button className="secondary" disabled={busy} onClick={() => setRemove(null)}>Cancelar</button>
    </section>}
    {active && <form className="explore-form" onSubmit={event => {
      event.preventDefault()
      setAnswer(null)
      void work(async () => setAnswer(await call<Answer>(`/${active.id}/query`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }),
      })))
    }}>
      <fieldset disabled={busy || !listing?.query_enabled}>
        <label>Pregunta sobre {active.name}
          <textarea required maxLength={500} value={question} onChange={event => setQuestion(event.target.value)} />
        </label>
        <button>Consultar con OpenAI</button>
      </fieldset>
    </form>}
    {answer && <section className="explore-result" aria-label="Respuesta documental">
      <p>{answer.answer ?? 'No se pudo confirmar una respuesta. Estos son los fragmentos recuperados.'}</p>
      {answer.sources.map((source, index) => <blockquote key={index}>
        <p>{source.quote}</p><cite>{source.document} · página {source.page}{source.section && ` · ${source.section}`}</cite>
      </blockquote>)}
    </section>}
  </section>
}
