export type Artist = { id: string; name: string }
export type Track = {
  id: string; title: string; artists: Artist[]; album_id: string; album_title: string
  duration_ms: number; track_number: number | null; cover_asset_id: string | null; cover_url: string | null
  cover_source: string
  metadata_sources: Record<string, string>; revision: number; metadata_warnings?: string[]
}
export type Album = { id: string; title: string; artists: Artist[]; system_key: string | null; cover_url: string | null; track_count: number }
type Page<T> = { items: T[]; total: number; limit: number; offset: number }

export async function metadataRequest<T>(path: string, options: RequestInit = {}): Promise<{ data: T; etag: string }> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 15000)
  try {
    const response = await fetch(`/api/v1${path}`, { ...options, signal: controller.signal, cache: 'no-store' })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error?.message ?? 'No se pudo completar la operación.')
    return { data: data as T, etag: response.headers.get('etag') ?? '' }
  } catch (error) {
    if (error instanceof TypeError || error instanceof SyntaxError || (error instanceof DOMException && error.name === 'AbortError')) {
      throw new Error('No se pudo confirmar la respuesta. Recarga los datos para comprobar el resultado antes de reintentar.')
    }
    throw error
  } finally { window.clearTimeout(timeout) }
}

export async function allMetadata<T>(path: string): Promise<T[]> {
  const values: T[] = []
  let total = 0
  do {
    const { data } = await metadataRequest<Page<T>>(`${path}?limit=100&offset=${values.length}`)
    values.push(...data.items)
    total = data.total
    if (!data.items.length) break
  } while (values.length < total)
  return values
}

export function editOptions(method: string, etag: string, body?: unknown): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json', 'If-Match': etag }, body: body === undefined ? undefined : JSON.stringify(body) }
}
