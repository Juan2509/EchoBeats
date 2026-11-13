import { useEffect, useRef, useState } from 'react'
import { DescriptionController } from './controller'
import type { Feature } from './controller'

const names = { tempo_bpm: 'Tempo (BPM)', timbre: 'Timbre', instruments: 'Instrumentos', energy: 'Energía', mood: 'Emoción', genre: 'Género', context: 'Contexto', mode: 'Modo', percussion: 'Percusión', voice: 'Voz', note_density: 'Densidad de notas' }
const sources = [['manual', 'Anotación manual'], ['verified', 'Verificado con fuente'], ['metadata', 'Metadatos existentes']]
export function DescriptionEditor({ trackId, title }: { trackId: string; title: string }) {
  const [open, setOpen] = useState(false)
  return <><button className="secondary" onClick={() => setOpen(true)}>Ficha musical</button>{open && <Editor key={trackId} trackId={trackId} title={title} close={() => setOpen(false)} />}</>
}
function Editor({ trackId, title, close }: { trackId: string; title: string; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const control = useRef<DescriptionController | null>(null)
  const [state, setState] = useState(() => new DescriptionController(trackId).state)
  useEffect(() => {
    const controller = new DescriptionController(trackId); control.current = controller
    const unsubscribe = controller.subscribe(() => setState(controller.state))
    setState(controller.state); void controller?.load(); dialog.current?.showModal()
    return () => { unsubscribe(); controller.dispose(); control.current = null; dialog.current?.close() }
  }, [trackId])
  const controller = control.current
  const dirty = controller?.dirty ?? false, blocked = state.loading || state.saving || state.needsReload
  const canClose = () => !state.saving && (!dirty || window.confirm('¿Descartar los cambios sin guardar de esta ficha?'))
  useEffect(() => {
    const unload = (event: BeforeUnloadEvent) => { if (dirty || state.saving) event.preventDefault() }
    const navigate = (event: Event) => { if (state.saving || (dirty && !window.confirm('Hay cambios sin guardar en una ficha musical. ¿Salir y descartarlos?'))) event.preventDefault() }
    window.addEventListener('beforeunload', unload); window.addEventListener('echobeats:before-navigation', navigate)
    return () => { window.removeEventListener('beforeunload', unload); window.removeEventListener('echobeats:before-navigation', navigate) }
  }, [dirty, state.saving])
  function feature(index: number, changes: Partial<Feature>) {
    controller?.edit({ ...state.draft, features: state.draft.features.map((f, i) => i === index ? { ...f, ...changes } : f) })
  }
  return <dialog ref={dialog} className="description-dialog" aria-labelledby={`description-${trackId}`} onCancel={event => { event.preventDefault(); if (canClose()) close() }}>
    <h2 id={`description-${trackId}`}>Ficha musical: {title}</h2>
    <p className="note">Registra lo que conoces y su fuente. No se ha analizado el sonido mediante IA. Deja desconocido lo que no puedas respaldar; las interpretaciones se distinguen de los hechos.</p>
    <p role="status">{state.loading ? 'Cargando ficha…' : state.saving ? 'Guardando ficha…' : dirty ? 'Cambios sin guardar' : state.notice || (state.record ? `Versión ${state.record.version} · sin embedding` : 'Sin ficha todavía')}</p>
    {state.error && <p role="alert">{state.error}</p>}
    {state.record?.metadata_stale && <p role="alert">Los metadatos cambiaron desde que se guardó esta ficha. Revisa y corrige los datos derivados antes de indexarla.</p>}
    <form onSubmit={event => { event.preventDefault(); void controller?.save() }}>
      <fieldset disabled={blocked}>
        <label>Descripción (puede quedar incompleta)<textarea maxLength={6000} value={state.draft.text} onChange={event => controller?.edit({ ...state.draft, text: event.target.value })} /></label>
        <label>Fuente de la descripción<select value={state.draft.source} onChange={event => controller?.edit({ ...state.draft, source: event.target.value as typeof state.draft.source })}>{sources.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>Procedencia y límites de lo descrito<textarea required maxLength={2000} value={state.draft.source_details} onChange={event => controller?.edit({ ...state.draft, source_details: event.target.value })} /></label>
        <h3>Atributos con evidencia</h3>
        {state.draft.features.map((f, index) => <fieldset key={index} className="description-feature"><legend>Atributo {index + 1}</legend>
          <label>Atributo<select value={f.name} onChange={event => { const name = event.target.value; feature(index, { name, ...(['mood', 'energy', 'context'].includes(name) ? { interpretation: true, source: 'manual' } : {}) }) }}>{Object.entries(names).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Valor<input required maxLength={255} value={f.value} onChange={event => feature(index, { value: event.target.value })} /></label>
          <label>Fuente<select value={f.source} disabled={f.interpretation} onChange={event => feature(index, { source: event.target.value as Feature['source'] })}>{sources.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Evidencia o motivo de la interpretación<textarea required maxLength={1000} value={f.evidence} onChange={event => feature(index, { evidence: event.target.value })} /></label>
          <label><input type="checkbox" checked={f.interpretation} disabled={['mood', 'energy', 'context'].includes(f.name)} onChange={event => feature(index, { interpretation: event.target.checked, ...(event.target.checked ? { source: 'manual' } : {}) })} /> Es una interpretación subjetiva</label>
          <button type="button" className="secondary" onClick={() => controller?.edit({ ...state.draft, features: state.draft.features.filter((_, i) => i !== index) })}>Quitar atributo {index + 1}</button>
        </fieldset>)}
        <button type="button" className="secondary" disabled={state.draft.features.length >= 20} onClick={() => controller?.edit({ ...state.draft, features: [...state.draft.features, { name: 'timbre', value: '', source: 'manual', evidence: '', interpretation: false }] })}>Añadir atributo</button>
      </fieldset>
      <p className="note">Guardar una corrección crea una nueva versión. No genera un embedding. Una descripción vacía conserva una ficha incompleta y no impide escuchar.</p>
      <button disabled={blocked || !dirty}>Guardar ficha</button>
      <button type="button" className="secondary" disabled={state.saving || state.loading} onClick={() => { if (!dirty || window.confirm('¿Descartar el borrador y recargar la ficha guardada?')) void controller?.load() }}>Recargar ficha guardada</button>
      <button type="button" className="secondary" disabled={state.saving} onClick={() => { if (canClose()) close() }}>Cerrar</button>
    </form>
  </dialog>
}
