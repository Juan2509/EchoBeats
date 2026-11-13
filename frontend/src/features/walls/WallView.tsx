import { useEffect, useRef, useState } from 'react'
import { initialWallState, isDirty, WallController } from './controller'
import type { WallElement } from './controller'

const kinds = { poster: 'Póster', sticker: 'Sticker', image: 'Imagen', gif: 'GIF' }
function Decoration({ item, animated }: { item: WallElement; animated: boolean }) {
  const [failed, setFailed] = useState(false)
  const paused = item.kind === 'gif' && !animated
  return <li className="wall-element" style={{ left: `${item.cx * 100}%`, top: `${item.cy * 100}%`, width: `${item.width * 100}%`, height: `${item.height * 100}%`, transform: `translate(-50%, -50%) rotate(${item.rotation_deg}deg)`, zIndex: item.z_index }}>
    {paused || failed ? <span className="wall-placeholder">{paused ? 'GIF en pausa' : 'Imagen no disponible'}</span> : <img src={item.content_url} alt={`${kinds[item.kind]} decorativo`} draggable={false} onError={() => setFailed(true)} />}
  </li>
}
export function WallView({ albumId, title, onDirty }: { albumId: string; title: string; onDirty: (dirty: boolean) => void }) {
  const controller = useRef<WallController | null>(null)
  const [state, setState] = useState(initialWallState)
  const [animated, setAnimated] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const instance = new WallController(albumId); controller.current = instance
    const unsubscribe = instance.subscribe(() => setState(instance.state))
    setState(instance.state); void instance.load()
    return () => { unsubscribe(); instance.dispose(); controller.current = null }
  }, [albumId])
  const dirty = isDirty(state)
  useEffect(() => { onDirty(dirty || state.saving); return () => onDirty(false) }, [dirty, state.saving, onDirty])
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => { if (dirty || state.saving) event.preventDefault() }
    window.addEventListener('beforeunload', prevent)
    return () => window.removeEventListener('beforeunload', prevent)
  }, [dirty, state.saving])
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const changed = () => { if (preference.matches) setAnimated(false) }
    preference.addEventListener('change', changed)
    return () => preference.removeEventListener('change', changed)
  }, [])
  function reload() {
    if (!dirty || window.confirm('¿Descartar el borrador y recargar la pared guardada?')) void controller.current?.load()
  }
  const wall = state.wall
  const status = state.loading ? 'Cargando pared…' : state.saving ? 'Guardando fondo…' : state.error ? 'No se pudo completar la operación' : dirty ? 'Cambios pendientes' : state.notice || 'Sin cambios'
  return <section className="wall-panel" onFocusCapture={event => {
    const target = event.target
    requestAnimationFrame(() => {
      if (!target.isConnected) return
      const control = target.getBoundingClientRect(), player = document.querySelector('.player-bar')?.getBoundingClientRect()
      if (player && control.bottom > player.top - 16 && control.top < player.bottom) window.scrollBy(0, control.bottom - player.top + 24)
    })
  }} aria-labelledby={`wall-title-${albumId}`}>
    <div className="wall-heading"><div><p className="eyebrow">Tu espacio</p><h2 id={`wall-title-${albumId}`}>La pared de {title}</h2></div>
      {wall && <button disabled={state.loading || state.saving} aria-pressed={state.editing} aria-controls={`wall-tools-${albumId}`} onClick={() => void controller.current?.toggleEditing()}>{state.editing ? 'Bloquear diseño' : 'Editar pared'}</button>}
    </div>
    <p className="wall-status" role="status">{status}{wall && !state.loading ? ` · ${state.editing ? 'Edición activada' : 'Diseño bloqueado'}` : ''}</p>
    {state.error && <div className="wall-error" role="alert"><p>{state.error}</p><button className="secondary" disabled={state.saving} onClick={reload}>Recargar pared guardada</button></div>}
    {wall && !state.loading && <>
      <div className="wall-canvas" data-mode={state.editing ? 'editing' : 'locked'} style={{ backgroundColor: state.color }} role="group" aria-label={`Muro de ${title}, ${wall.elements.length} elementos decorativos`}>
        <ul className="wall-elements" aria-label="Composición guardada">{wall.elements.map(item => <Decoration key={`${item.id}-${item.content_url}`} item={item} animated={animated} />)}</ul>
        {!wall.elements.length && <p className="wall-empty">Un espacio para tus recuerdos musicales.</p>}
      </div>
      {wall.elements.some(item => item.kind === 'gif') && <label className="wall-animation"><input type="checkbox" checked={animated} onChange={event => setAnimated(event.target.checked)} /> Animar GIF de esta pared</label>}
      {state.editing && <div className="wall-tools" id={`wall-tools-${albumId}`}><label htmlFor={`wall-color-${albumId}`}>Color del fondo</label><div className="wall-color-controls">
        <input id={`wall-color-${albumId}`} type="color" value={state.color} disabled={state.saving || state.needsReload} onChange={event => controller.current?.setColor(event.target.value)} /><output htmlFor={`wall-color-${albumId}`}>{state.color}</output>
        {[['#242038', 'Ciruela'], ['#193A55', 'Azul nocturno'], ['#284333', 'Verde bosque'], ['#442244', 'Malva']].map(([color, label]) => <button key={color} className="wall-swatch" style={{ backgroundColor: color }} aria-label={`Fondo ${label}`} aria-pressed={state.color === color} disabled={state.saving || state.needsReload} onClick={() => controller.current?.setColor(color)} />)}
        <button disabled={!dirty || state.saving || state.needsReload} onClick={() => void controller.current?.save()}>Guardar fondo</button>
      </div></div>}
    </>}
  </section>
}
