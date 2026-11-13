import type { Track } from '../../shared/api/metadata'

/** Solo descarga fichas; el audio se solicita cuando se selecciona una pista. */
export async function loadQueue(path: string, signal: AbortSignal, fetcher: typeof fetch = fetch): Promise<Track[]> {
  if (/^\/playlists\/[0-9a-f-]{36}$/i.test(path)) {
    const response = await fetcher(`/api/v1${path}`, { signal, cache: 'no-store' })
    if (!response.ok) throw new Error('queue_unavailable')
    const data: { items: Track[] } = await response.json()
    if (!Array.isArray(data.items)) throw new Error('invalid_queue')
    return data.items
  }
  const queue: Track[] = []
  let total = 1
  while (queue.length < total) {
    const params = new URLSearchParams(path.split('?')[1])
    params.set('limit', '100'); params.set('offset', String(queue.length))
    const response = await fetcher(`/api/v1/tracks?${params}`, { signal, cache: 'no-store' })
    if (!response.ok) throw new Error('queue_unavailable')
    const page: { items: Track[]; total: number } = await response.json()
    if (!Array.isArray(page.items) || !Number.isSafeInteger(page.total) || page.total < 0) throw new Error('invalid_queue')
    if (!page.items.length) break
    queue.push(...page.items); total = page.total
  }
  return [...new Map(queue.map(item => [item.id, item])).values()]
}
