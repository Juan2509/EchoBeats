import { useEffect, useRef, useState } from 'react'
import type { Track } from '../../shared/api/metadata'
import { artists } from '../library/Library'
import { usePlayer } from '../player/Player'

type IndexState = {
  status: 'pending' | 'processing' | 'failed' | 'ready'
  worker_enabled: boolean
  error: string | null
}

export function AudioSimilarity({ track }: { track: Track }) {
  const player = usePlayer()
  const request = useRef<AbortController | null>(null)
  const retryRequest = useRef<AbortController | null>(null)
  const [index, setIndex] = useState<IndexState | null>(null)
  const [indexError, setIndexError] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const [retrying, setRetrying] = useState(false)
  const base = `/api/v1/tracks/${encodeURIComponent(track.id)}/audio-index`
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [matches, setMatches] = useState<Track[] | null>(null)
  useEffect(() => () => {
    request.current?.abort()
    retryRequest.current?.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    async function read() {
      try {
        const response = await fetch(base, {
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
          cache: 'no-store',
        })
        if (!response.ok) throw new Error()
        const value: IndexState = await response.json()
        if (controller.signal.aborted) return
        setIndex(value)
        setIndexError(false)
        if (value.worker_enabled && (value.status === 'pending' || value.status === 'processing')) {
          timer = setTimeout(() => void read(), 2000)
        }
      } catch {
        if (!controller.signal.aborted) setIndexError(true)
      }
    }
    void read()
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [base, refresh])

  async function retry() {
    if (retryRequest.current) return
    const controller = new AbortController()
    retryRequest.current = controller
    setRetrying(true)
    setError('')
    try {
      const response = await fetch(`${base}/retry`, {
        method: 'POST',
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
      })
      if (!response.ok) throw new Error()
      const value: IndexState = await response.json()
      if (!controller.signal.aborted) setIndex(value)
    } catch {
      if (!controller.signal.aborted) setError('No se pudo confirmar el reintento. Se consultará el estado.')
    } finally {
      if (!controller.signal.aborted) {
        retryRequest.current = null
        setRetrying(false)
        setRefresh(value => value + 1)
      }
    }
  }

  async function search() {
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError('')
    setMatches(null)
    try {
      const response = await fetch(`/api/v1/tracks/${encodeURIComponent(track.id)}/audio-similar`, {
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
        cache: 'no-store',
      })
      const data = await response.json()
      if (controller.signal.aborted) return
      if (!response.ok) {
        if (response.status === 409) setRefresh(value => value + 1)
        setError(response.status === 409
          ? 'Esta canción aún no está lista para buscar por sonido.'
          : 'No se pudo consultar el índice de audio.')
        return
      }
      const results = (data.results as { track: Track }[]).map(item => item.track)
      setMatches(results)
    } catch {
      if (!controller.signal.aborted) setError('No se pudo consultar el índice de audio.')
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  const indexMessage = !index ? 'Consultando el estado del audio…'
    : index.status === 'ready' ? 'Audio listo para buscar por sonido.'
    : index.status === 'failed' ? index.error ?? 'No se pudo analizar el audio.'
    : index.status === 'processing' ? 'Analizando el audio…'
    : index.worker_enabled ? 'Audio pendiente de análisis.'
    : 'El análisis de audio en segundo plano está desactivado.'

  return <section className="explore-reference" aria-label="Similitud acústica">
    {indexError
      ? <p role="status">No se pudo consultar el estado del audio.{' '}
        <button type="button" className="secondary" onClick={() => setRefresh(value => value + 1)}>Actualizar estado</button>
      </p>
      : <p role="status">{indexMessage}</p>}
    {index?.status === 'failed' && index.worker_enabled &&
      <button type="button" className="secondary" disabled={retrying || indexError} onClick={() => void retry()}>
        {retrying ? 'Enviando…' : 'Reintentar análisis'}
      </button>}
    <button type="button" className="secondary" disabled={loading || index?.status !== 'ready'} onClick={() => void search()}>
      {loading ? 'Buscando por sonido…' : 'Buscar canciones por sonido'}
    </button>
    {error && <p role="alert">{error}</p>}
    {matches && <p role="status">{matches.length
      ? 'Candidatos ordenados por similitud acústica.'
      : 'Aún no hay otras canciones indexadas para comparar.'}</p>}
    {!!matches?.length && <ol className="explore-results">
      {matches.map(match => <li key={match.id}>
        <strong>{match.title}</strong> · {artists(match)}{' '}
        <button type="button" aria-label={`Escuchar ${match.title}`} onClick={() =>
          player.selectSnapshot(match, matches, 'Similitud acústica')}>Escuchar</button>
      </li>)}
    </ol>}
  </section>
}
