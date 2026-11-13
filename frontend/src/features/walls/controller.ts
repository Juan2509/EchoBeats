export type WallElement = {
  id: string; asset_id: string; kind: 'poster' | 'sticker' | 'image' | 'gif'
  cx: number; cy: number; width: number; height: number; rotation_deg: number; z_index: number; content_url: string
}
export type Wall = { id: string; album_id: string; schema_version: 1; revision: number; background_color: string; updated_at: string; elements: WallElement[] }
export type WallResult = { wall: Wall; etag: string }
export type Composition = ReturnType<typeof composition>
export function composition(wall: Wall, color: string) {
  return { schema_version: wall.schema_version, background_color: color, elements: wall.elements.map(({ id, asset_id, kind, cx, cy, width, height, rotation_deg, z_index }) =>
    ({ id, asset_id, kind, cx, cy, width, height, rotation_deg, z_index })) }
}
export class WallRequestError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}
export type WallGateway = (id: string, signal: AbortSignal, write?: { body: Composition; etag: string }) => Promise<WallResult>
export const requestWall: WallGateway = async (id, signal, write) => {
  const response = await fetch(`/api/v1/albums/${encodeURIComponent(id)}/wall`, {
    signal, cache: 'no-store', ...(write ? { method: 'PUT', headers: { 'Content-Type': 'application/json', 'If-Match': write.etag }, body: JSON.stringify(write.body) } : {}),
  })
  const data = await response.json()
  if (!response.ok) throw new WallRequestError(data.error?.message ?? 'No se pudo completar la operación del muro.', response.status)
  const etag = response.headers.get('etag')
  if (data.album_id !== id || data.schema_version !== 1 || !Array.isArray(data.elements) || !/^#[0-9a-f]{6}$/i.test(data.background_color) || !etag) throw new Error('invalid_wall_response')
  return { wall: data as Wall, etag }
}
export type WallState = { wall: Wall | null; etag: string; color: string; editing: boolean; loading: boolean; saving: boolean; error: string; needsReload: boolean; notice: string }
export const initialWallState: WallState = { wall: null, etag: '', color: '#242038', editing: false, loading: true, saving: false, error: '', needsReload: false, notice: '' }
export const isDirty = (state: WallState) => !!state.wall && state.color !== state.wall.background_color

/** Una composición confirmada por álbum; no hay escrituras concurrentes ni reintentos ciegos. */
export class WallController {
  state: WallState = { ...initialWallState }
  private alive = true
  private operation = 0
  private pending: AbortController | null = null
  private listeners = new Set<() => void>()
  private albumId: string
  private gateway: WallGateway
  constructor(albumId: string, gateway: WallGateway = requestWall) { this.albumId = albumId; this.gateway = gateway }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private update(changes: Partial<WallState>) { if (!this.alive) return; this.state = { ...this.state, ...changes }; this.listeners.forEach(listener => listener()) }
  private accept(result: WallResult) { this.update({ wall: result.wall, etag: result.etag, color: result.wall.background_color, loading: false, error: '', needsReload: false }) }
  async load() {
    if (!this.alive || this.state.saving) return
    this.pending?.abort()
    const abort = new AbortController(); this.pending = abort
    const token = ++this.operation, timeout = setTimeout(() => abort.abort(), 15000)
    this.update({ loading: true, error: '', editing: false, notice: '' })
    try {
      const result = await this.gateway(this.albumId, abort.signal)
      if (this.alive && token === this.operation) {
        if (abort.signal.aborted) throw new Error('wall_request_aborted')
        this.accept(result)
      }
    } catch (cause) {
      if (token === this.operation) this.update({ loading: false, error: cause instanceof WallRequestError ? cause.message : 'No se pudo cargar la pared. Comprueba la conexión y vuelve a intentarlo.' })
    } finally { clearTimeout(timeout) }
  }
  setColor(value: string) {
    if (!this.state.editing || this.state.saving || this.state.loading || !/^#[0-9a-f]{6}$/i.test(value)) return
    this.update({ color: value.toUpperCase(), notice: '' })
  }
  async toggleEditing() {
    if (!this.state.wall || this.state.loading || this.state.saving) return
    if (!this.state.editing) { this.update({ editing: true }); return }
    if (isDirty(this.state) && !await this.save()) return
    this.update({ editing: false })
  }
  async save(): Promise<boolean> {
    if (!this.alive || !this.state.wall || this.state.loading || this.state.saving || this.state.needsReload) return false
    if (!isDirty(this.state)) return true
    const wanted = composition(this.state.wall, this.state.color), token = ++this.operation
    const abort = new AbortController(); this.pending = abort
    const timeout = setTimeout(() => abort.abort(), 15000)
    this.update({ saving: true, error: '', notice: '' })
    try {
      const result = await this.gateway(this.albumId, abort.signal, { body: wanted, etag: this.state.etag })
      if (!this.alive || token !== this.operation) return false
      if (abort.signal.aborted) throw new Error('wall_request_aborted')
      this.accept(result); this.update({ notice: 'Fondo guardado.' }); return true
    } catch (cause) {
      if (token !== this.operation || !this.alive) return false
      const conflict = cause instanceof WallRequestError && cause.status === 412
      const uncertain = !(cause instanceof WallRequestError) || cause.status >= 500
      this.update({ needsReload: conflict || uncertain, error: conflict ? 'El diseño cambió en otra pestaña. Tu color sigue en el borrador; recarga la pared guardada para revisar el cambio.' : uncertain ? 'No se pudo confirmar el guardado. Tu color sigue en el borrador; recarga la pared guardada para comprobar el resultado antes de volver a editar.' : cause instanceof Error ? cause.message : 'No se pudo guardar el fondo.' })
      return false
    } finally { clearTimeout(timeout); if (token === this.operation) this.update({ saving: false }) }
  }
  dispose() { this.alive = false; ++this.operation; this.pending?.abort(); this.listeners.clear() }
}
