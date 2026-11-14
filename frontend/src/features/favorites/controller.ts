export type FavoriteState = { status: 'idle' | 'loading' | 'ready' | 'saving' | 'error'; favorite?: boolean; error?: string }
const idle: FavoriteState = { status: 'idle' }
type Gateway = (id: string, desired?: boolean) => Promise<boolean>

export async function favoriteRequest(id: string, desired?: boolean, fetcher: typeof fetch = fetch): Promise<boolean> {
  const abort = new AbortController(), timeout = setTimeout(() => abort.abort(), 15000)
  try {
    const response = await fetcher(`/api/v1/tracks/${encodeURIComponent(id)}/favorite`, {
      method: desired === undefined ? 'GET' : 'PUT', signal: abort.signal, cache: 'no-store',
      ...(desired === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ favorite: desired }) }),
    })
    if (!response.ok) throw new Error('favorite_unavailable')
    const value = await response.json()
    if (value.track_id !== id || typeof value.favorite !== 'boolean' || desired !== undefined && value.favorite !== desired) throw new Error('invalid_favorite')
    return value.favorite
  } finally { clearTimeout(timeout) }
}

/** Estado único para todas las vistas; ningún cambio optimista ni reintento PUT. */
export class FavoritesController {
  private states = new Map<string, FavoriteState>()
  private listeners = new Set<() => void>()
  private tokens = new Map<string, number>()
  private disposed = false
  private gateway: Gateway
  revision = 0
  constructor(gateway: Gateway = favoriteRequest) { this.gateway = gateway }
  get(id: string) { return this.states.get(id) ?? idle }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private publish(id: string, state: FavoriteState, changed = false) {
    if (this.disposed) return
    this.states.set(id, state)
    if (changed) this.revision++
    this.listeners.forEach(listener => listener())
  }
  async load(id: string) {
    if (this.disposed || ['loading', 'saving'].includes(this.get(id).status)) return
    const token = (this.tokens.get(id) ?? 0) + 1; this.tokens.set(id, token)
    this.publish(id, { status: 'loading' })
    try {
      const favorite = await this.gateway(id)
      if (this.tokens.get(id) === token) this.publish(id, { status: 'ready', favorite })
    } catch {
      if (this.tokens.get(id) === token) this.publish(id, { status: 'error', error: 'No se pudo comprobar el favorito. Consulta su estado para reintentar.' })
    }
  }
  async set(id: string, desired: boolean) {
    if (this.disposed || this.get(id).status !== 'ready') return
    const token = (this.tokens.get(id) ?? 0) + 1; this.tokens.set(id, token)
    this.publish(id, { status: 'saving', favorite: this.get(id).favorite })
    try {
      const favorite = await this.gateway(id, desired)
      if (this.tokens.get(id) === token) this.publish(id, { status: 'ready', favorite }, true)
    } catch {
      if (this.tokens.get(id) === token) this.publish(id, { status: 'error', error: 'No se confirmó el guardado. Puede haberse completado; consulta el estado antes de cambiarlo de nuevo.' }, true)
    }
  }
  invalidate() {
    if (this.disposed) return
    for (const [id, state] of this.states) {
      if (state.status === 'saving') continue
      this.tokens.set(id, (this.tokens.get(id) ?? 0) + 1)
      this.states.set(id, idle)
    }
    this.revision++; this.listeners.forEach(listener => listener())
  }
  dispose() { this.disposed = true; this.listeners.clear() }
}
