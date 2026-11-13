export type WallElement = {
  id: string; asset_id: string; kind: 'poster' | 'sticker' | 'image' | 'gif'
  cx: number; cy: number; width: number; height: number; rotation_deg: number; z_index: number; content_url: string; static_preview_url?: string | null
}
/** Mismos límites rotados que P12, sobre el lienzo de referencia 1000 × 700. */
export function moveWithinWall(item: WallElement, cx: number, cy: number): WallElement {
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return item
  const angle = item.rotation_deg * Math.PI / 180
  const bx = (Math.abs(item.width * 1000 * Math.cos(angle)) + Math.abs(item.height * 700 * Math.sin(angle))) / 2000
  const by = (Math.abs(item.width * 1000 * Math.sin(angle)) + Math.abs(item.height * 700 * Math.cos(angle))) / 1400
  return { ...item, cx: Math.max(bx, Math.min(1 - bx, cx)), cy: Math.max(by, Math.min(1 - by, cy)) }
}

/** Ajusta el tamaño proporcionalmente si el rectángulo girado supera el lienzo. */
export function transformWithinWall(item: WallElement, changes: Partial<Pick<WallElement, 'width' | 'height' | 'rotation_deg'>>): WallElement {
  if (Object.values(changes).some(value => !Number.isFinite(value))) return item
  const next = { ...item, ...changes }
  next.width = Math.max(.03, Math.min(.6, next.width))
  next.height = Math.max(.03, Math.min(.6, next.height))
  next.rotation_deg = ((next.rotation_deg + 180) % 360 + 360) % 360 - 180
  const angle = next.rotation_deg * Math.PI / 180
  const factor = Math.min(1, 1000 / (Math.abs(next.width * 1000 * Math.cos(angle)) + Math.abs(next.height * 700 * Math.sin(angle))), 700 / (Math.abs(next.width * 1000 * Math.sin(angle)) + Math.abs(next.height * 700 * Math.cos(angle))))
  next.width *= factor; next.height *= factor
  return moveWithinWall(next, next.cx, next.cy)
}
// Coincide con el desempate del servidor; no depende del orden recibido.
export const orderedElements = (elements: WallElement[]) => [...elements].sort((a, b) => a.z_index - b.z_index || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0))

export type Wall = { id: string; album_id: string; schema_version: 1; revision: number; background_color: string; updated_at: string; elements: WallElement[] }
export type WallResult = { wall: Wall; etag: string }
export type Composition = ReturnType<typeof composition>
export function composition(wall: Wall, color: string, elements: WallElement[] = wall.elements) {
  return { schema_version: wall.schema_version, background_color: color, elements: elements.map(({ id, asset_id, kind, cx, cy, width, height, rotation_deg, z_index }) =>
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
export type VisualAsset = { id: string; mime_type: string; width_px: number; height_px: number; content_url: string; static_preview_url?: string | null }
export type VisualUploader = (file: File, signal: AbortSignal) => Promise<VisualAsset>
export const uploadVisual: VisualUploader = async (file, signal) => {
  const body = new FormData(); body.append('purpose', 'wall'); body.append('file', file)
  const response = await fetch('/api/v1/assets', { method: 'POST', body, signal })
  const data = await response.json()
  if (!response.ok) throw new WallRequestError(data.error?.message ?? 'No se pudo importar la imagen.', response.status)
  if (!data.id || !data.content_url || !['image/png', 'image/jpeg', 'image/gif'].includes(data.mime_type) || !(data.width_px > 0 && data.height_px > 0)) throw new Error('invalid_visual_response')
  return data
}
export type WallState = { wall: Wall | null; elements: WallElement[]; selectedId: string | null; uploading: boolean; moving: boolean; etag: string; color: string; editing: boolean; loading: boolean; saving: boolean; error: string; needsReload: boolean; notice: string }
export const initialWallState: WallState = { wall: null, elements: [], selectedId: null, uploading: false, moving: false, etag: '', color: '#242038', editing: false, loading: true, saving: false, error: '', needsReload: false, notice: '' }
export const isDirty = (state: WallState) => !!state.wall && JSON.stringify(composition(state.wall, state.color, state.elements)) !== JSON.stringify(composition(state.wall, state.wall.background_color))

/** Una composición confirmada por álbum; no hay escrituras concurrentes ni reintentos ciegos. */
export class WallController {
  state: WallState = { ...initialWallState }
  private alive = true
  private operation = 0
  private pending: AbortController | null = null
  private listeners = new Set<() => void>()
  private albumId: string
  private gateway: WallGateway
  private uploader: VisualUploader
  private gesture: WallElement | null = null
  constructor(albumId: string, gateway: WallGateway = requestWall, uploader: VisualUploader = uploadVisual) { this.albumId = albumId; this.gateway = gateway; this.uploader = uploader }
  private editable() { return this.alive && !!this.state.wall && this.state.editing && !this.state.loading && !this.state.saving && !this.state.uploading && !this.state.needsReload }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private update(changes: Partial<WallState>) { if (!this.alive) return; this.state = { ...this.state, ...changes }; this.listeners.forEach(listener => listener()) }
  private accept(result: WallResult) { this.update({ wall: result.wall, elements: result.wall.elements.map(item => ({ ...item })), selectedId: null, etag: result.etag, color: result.wall.background_color, loading: false, error: '', needsReload: false }) }
  async load() {
    if (!this.alive || this.state.saving || this.state.uploading || this.state.moving) return
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
    if (!this.editable() || this.state.moving || !/^#[0-9a-f]{6}$/i.test(value)) return
    this.update({ color: value.toUpperCase(), notice: '' })
  }
  async toggleEditing() {
    if (!this.state.wall || this.state.loading || this.state.saving || this.state.uploading || this.state.moving) return
    if (!this.state.editing) { this.update({ editing: true }); return }
    if (isDirty(this.state) && !await this.save()) return
    this.update({ editing: false, selectedId: null })
  }
  async save(): Promise<boolean> {
    if (!this.alive || !this.state.wall || this.state.loading || this.state.saving || this.state.uploading || this.state.moving || this.state.needsReload) return false
    if (!isDirty(this.state)) return true
    const wanted = composition(this.state.wall, this.state.color, this.state.elements), token = ++this.operation
    const abort = new AbortController(); this.pending = abort
    const timeout = setTimeout(() => abort.abort(), 15000)
    this.update({ saving: true, error: '', notice: '' })
    try {
      const result = await this.gateway(this.albumId, abort.signal, { body: wanted, etag: this.state.etag })
      if (!this.alive || token !== this.operation) return false
      if (abort.signal.aborted) throw new Error('wall_request_aborted')
      this.accept(result); this.update({ notice: 'Pared guardada.' }); return true
    } catch (cause) {
      if (token !== this.operation || !this.alive) return false
      const conflict = cause instanceof WallRequestError && cause.status === 412
      const uncertain = !(cause instanceof WallRequestError) || cause.status >= 500
      this.update({ needsReload: conflict || uncertain, error: conflict ? 'El diseño cambió en otra pestaña. Tu diseño sigue en el borrador; recarga la pared guardada para revisar el cambio.' : uncertain ? 'No se pudo confirmar el guardado. Tu diseño sigue en el borrador; recarga la pared guardada para comprobar el resultado antes de volver a editar.' : cause instanceof Error ? cause.message : 'No se pudo guardar la pared.' })
      return false
    } finally { clearTimeout(timeout); if (token === this.operation) this.update({ saving: false }) }
  }
  select(id: string | null) { if (this.editable() && !this.state.moving) this.update({ selectedId: id && this.state.elements.some(item => item.id === id) ? id : null }) }
  move(id: string, cx: number, cy: number) {
    if (!this.editable()) return
    this.update({ elements: this.state.elements.map(item => item.id === id ? moveWithinWall(item, cx, cy) : item), selectedId: id, notice: '' })
  }
  nudge(id: string, dx: number, dy: number) {
    if (this.state.moving) return
    const item = this.state.elements.find(value => value.id === id)
    if (item) this.move(id, item.cx + dx, item.cy + dy)
  }
  transform(id: string, changes: Partial<Pick<WallElement, 'width' | 'height' | 'rotation_deg'>>) {
    if (!this.editable() || this.state.moving) return
    this.update({ elements: this.state.elements.map(item => item.id === id ? transformWithinWall(item, changes) : item), notice: '' })
  }
  reorder(id: string, direction: 'back' | 'backward' | 'forward' | 'front') {
    if (!this.editable() || this.state.moving) return
    const sorted = orderedElements(this.state.elements), from = sorted.findIndex(item => item.id === id)
    if (from < 0) return
    const to = direction === 'back' ? 0 : direction === 'front' ? sorted.length - 1 : Math.max(0, Math.min(sorted.length - 1, from + (direction === 'forward' ? 1 : -1)))
    if (from === to) return
    sorted.splice(to, 0, sorted.splice(from, 1)[0])
    this.update({ elements: sorted.map((item, z_index) => ({ ...item, z_index })), notice: '' })
  }
  beginMove(id: string) {
    if (!this.editable() || this.state.moving) return false
    this.gesture = this.state.elements.find(item => item.id === id) ?? null
    if (!this.gesture) return false
    this.update({ selectedId: id, moving: true }); return true
  }
  finishMove() { this.gesture = null; this.update({ moving: false }) }
  cancelMove() {
    if (!this.gesture) return
    const original = this.gesture; this.gesture = null
    this.update({ elements: this.state.elements.map(item => item.id === original.id ? original : item), moving: false })
  }
  remove(id: string) {
    if (!this.editable() || this.state.moving) return
    this.update({ elements: this.state.elements.filter(item => item.id !== id), selectedId: null, notice: '' })
  }
  async addFile(file: File, kind: 'poster' | 'sticker' | 'image') {
    if (!this.editable() || this.state.moving) return
    if (this.state.elements.length >= 30) { this.update({ error: 'La pared admite hasta 30 objetos.' }); return }
    if (!file.size || file.size > 5 * 1024 * 1024) { this.update({ error: 'El recurso está vacío o supera 5 MiB.' }); return }
    const token = ++this.operation, abort = new AbortController(); this.pending = abort
    const timeout = setTimeout(() => abort.abort(), 15000)
    this.update({ uploading: true, error: '', notice: '' })
    try {
      const asset = await this.uploader(file, abort.signal)
      if (!this.alive || token !== this.operation) return
      if (abort.signal.aborted) throw new Error('upload_aborted')
      const item: WallElement = { id: crypto.randomUUID(), asset_id: asset.id, kind: asset.mime_type === 'image/gif' ? 'gif' : kind,
        cx: .5, cy: .5, width: .25, height: Math.max(.03, Math.min(.6, .25 * 1000 / 700 * asset.height_px / asset.width_px)), rotation_deg: 0,
        z_index: Math.min(29, Math.max(-1, ...this.state.elements.map(value => value.z_index)) + 1), content_url: asset.content_url, static_preview_url: asset.static_preview_url }
      this.update({ elements: [...orderedElements(this.state.elements).map((value, z_index) => ({ ...value, z_index })), { ...item, z_index: this.state.elements.length }], selectedId: item.id, notice: 'Recurso añadido al borrador. Guarda la pared para conservarlo.' })
    } catch (cause) {
      if (this.alive && token === this.operation) this.update({ error: cause instanceof WallRequestError ? cause.message : 'No se pudo confirmar la importación. La composición anterior se conserva.' })
    } finally { clearTimeout(timeout); if (token === this.operation) this.update({ uploading: false }) }
  }
  dispose() { this.alive = false; ++this.operation; this.pending?.abort(); this.listeners.clear() }
}
