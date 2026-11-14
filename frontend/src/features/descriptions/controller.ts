export type Feature = { name: string; value: string; source: 'manual' | 'verified' | 'metadata'; evidence: string; interpretation: boolean }
export type Draft = { text: string; features: Feature[]; source: 'manual' | 'verified' | 'metadata'; source_details: string }
export type Description = Draft & { id: string; track_id: string; version: number; can_index: boolean; index_notice: string; metadata_stale?: boolean }
export const blank = (): Draft => ({ text: '', features: [], source: 'manual', source_details: '' })
export const payload = ({ text, features, source, source_details }: Draft): Draft => ({ text, features, source, source_details })
export class DescriptionError extends Error {
  status: number; code: string
  constructor(message: string, status: number, code = '') { super(message); this.status = status; this.code = code }
}
export type Gateway = (trackId: string, signal: AbortSignal, write?: { body: Draft; etag: string }) => Promise<{ record: Description | null; etag: string }>
export const requestDescription: Gateway = async (id, signal, write) => {
  const response = await fetch(`/api/v1/tracks/${encodeURIComponent(id)}/description`, { signal, cache: 'no-store', ...(write ? { method: 'PUT', headers: { 'Content-Type': 'application/json', ...(write.etag ? { 'If-Match': write.etag } : { 'If-None-Match': '*' }) }, body: JSON.stringify(write.body) } : {}) })
  const value = await response.json()
  if (!write && response.status === 404 && value.error?.code === 'description_missing') return { record: null, etag: '' }
  if (!response.ok) throw new DescriptionError(value.error?.message ?? 'No se pudo completar la operación.', response.status, value.error?.code)
  const etag = response.headers.get('etag')
  if (!etag || value.track_id !== id || !Number.isInteger(value.version) || !Array.isArray(value.features)) throw new Error('Respuesta de ficha no válida.')
  return { record: value, etag }
}
export class DescriptionController {
  state = { record: null as Description | null, draft: blank(), baseline: blank(), etag: '', loading: true, saving: false, error: '', needsReload: false, notice: '' }
  private alive = true
  private pending: AbortController | null = null
  private listeners = new Set<() => void>()
  private trackId: string
  private gateway: Gateway
  constructor(trackId: string, gateway: Gateway = requestDescription) { this.trackId = trackId; this.gateway = gateway }
  get dirty() { return JSON.stringify(this.state.draft) !== JSON.stringify(this.state.baseline) }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener) } }
  private update(changes: Partial<typeof this.state>) { if (this.alive) { this.state = { ...this.state, ...changes }; this.listeners.forEach(f => f()) } }
  edit(draft: Draft) { if (this.alive && !this.state.loading && !this.state.saving && !this.state.needsReload) this.update({ draft, notice: '' }) }
  async load() { if (!this.state.saving) await this.run() }
  async save() { if (!this.state.loading && !this.state.saving && !this.state.needsReload && this.dirty) await this.run(true) }
  private async run(write = false) {
    if (!this.alive) return
    this.pending?.abort(); const abort = new AbortController(); this.pending = abort
    const timeout = setTimeout(() => abort.abort(), 15000)
    this.update(write ? { saving: true, error: '', notice: '' } : { loading: true, error: '', notice: '' })
    try {
      const result = await this.gateway(this.trackId, abort.signal, write ? { body: structuredClone(this.state.draft), etag: this.state.etag } : undefined)
      if (!this.alive || this.pending !== abort) return
      if (abort.signal.aborted) throw new Error('No se pudo confirmar la operación.')
      const draft = result.record ? payload(result.record) : blank()
      this.update({ record: result.record, draft, baseline: structuredClone(draft), etag: result.etag, needsReload: false, notice: write ? 'Ficha guardada. Consulta el estado de indexación de esta versión.' : '' })
    } catch (cause) {
      if (this.alive && this.pending === abort) this.update({ needsReload: this.state.needsReload || (write && (!(cause instanceof DescriptionError) || cause.status === 412 || cause.status >= 500)), error: cause instanceof DescriptionError ? cause.message : 'No se pudo confirmar la operación. Tu borrador se conserva; recarga para comprobar el estado.' })
    } finally { clearTimeout(timeout); if (this.pending === abort) this.update({ loading: false, saving: false }) }
  }
  dispose() { this.alive = false; this.pending?.abort(); this.listeners.clear() }
}
