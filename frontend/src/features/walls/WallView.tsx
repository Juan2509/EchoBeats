import { useEffect, useRef, useState } from 'react'
import type { ButtonHTMLAttributes, KeyboardEvent, PointerEvent } from 'react'
import { initialWallState, isDirty, orderedElements, WallController } from './controller'
import type { WallElement } from './controller'

const kinds = { poster: 'Póster', sticker: 'Sticker', image: 'Imagen', gif: 'GIF' }
function TransformField({ label, value, min, max, disabled, change }: { label: string; value: number; min: number; max: number; disabled: boolean; change: (value: number) => void }) {
  const [draft, setDraft] = useState(String(value))
  useEffect(() => setDraft(String(value)), [value])
  return <label>{label}<input type="number" value={draft} min={min} max={max} step="any" disabled={disabled} onChange={event => {
    const text = event.target.value; setDraft(text)
    if (text !== '' && Number.isFinite(Number(text)) && Number(text) >= min && Number(text) <= max) change(Number(text))
  }} onBlur={() => setDraft(String(value))} /></label>
}
function Decoration({ item, index, animated, editable, selected, handlers }: { item: WallElement; index: number; animated: boolean; editable: boolean; selected: boolean; handlers: ButtonHTMLAttributes<HTMLButtonElement> }) {
  const paused = item.kind === 'gif' && !animated
  const source = paused ? item.static_preview_url : item.content_url
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [source])
  return <li className="wall-element" style={{ left: `${item.cx * 100}%`, top: `${item.cy * 100}%`, width: `${item.width * 100}%`, height: `${item.height * 100}%`, transform: `translate(-50%, -50%) rotate(${item.rotation_deg}deg)`, zIndex: item.z_index }}>
    <button type="button" className="wall-object" disabled={!editable} tabIndex={editable ? 0 : -1} aria-pressed={selected} aria-label={`${kinds[item.kind]} ${index + 1}${editable ? ': mover con las flechas' : ''}`} {...handlers}>
      {failed || !source ? <span className="wall-placeholder">{paused ? 'GIF en pausa' : 'Imagen no disponible'}</span> : <img src={source} alt="" draggable={false} onError={() => setFailed(true)} />}
    </button>
  </li>
}
export function WallView({ albumId, title, onDirty }: { albumId: string; title: string; onDirty: (dirty: boolean) => void }) {
  const controller = useRef<WallController | null>(null)
  const canvas = useRef<HTMLDivElement>(null), upload = useRef<HTMLInputElement>(null)
  const drag = useRef<{ id: string; pointerId: number; x: number; y: number; cx: number; cy: number } | null>(null)
  const [state, setState] = useState(initialWallState)
  const [kind, setKind] = useState<'poster' | 'sticker' | 'image'>('poster')
  const [animated, setAnimated] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const instance = new WallController(albumId, undefined, undefined, { autosaveMs: 700 }); controller.current = instance
    const unsubscribe = instance.subscribe(() => setState(instance.state))
    setState(instance.state); void instance.load()
    return () => { drag.current = null; unsubscribe(); instance.dispose(); controller.current = null }
  }, [albumId])
  const dirty = isDirty(state), busy = state.saving || state.uploading || state.moving
  const editable = controller.current?.canEdit ?? false
  useEffect(() => { onDirty(dirty || busy); return () => onDirty(false) }, [dirty, busy, onDirty])
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => { if (dirty || busy) event.preventDefault() }
    window.addEventListener('beforeunload', prevent)
    return () => window.removeEventListener('beforeunload', prevent)
  }, [dirty, busy])
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const changed = () => { if (preference.matches) setAnimated(false) }
    preference.addEventListener('change', changed)
    return () => preference.removeEventListener('change', changed)
  }, [])
  function reload() {
    if (!dirty || window.confirm('¿Descartar el borrador y recargar la pared guardada?')) void controller.current?.load()
  }
  function reset() {
    if (window.confirm('¿Restablecer esta pared? Se guardará el fondo inicial sin objetos y se reemplazará el diseño de este álbum. Los archivos importados se conservan.')) void controller.current?.reset()
  }
  function remove(id: string) { controller.current?.remove(id); requestAnimationFrame(() => upload.current?.focus()) }
  function down(item: WallElement, event: PointerEvent<HTMLButtonElement>) {
    if (!editable || !event.isPrimary || event.button !== 0 || !controller.current?.beginMove(item.id)) return
    event.preventDefault(); event.currentTarget.focus({ preventScroll: true }); event.currentTarget.setPointerCapture(event.pointerId)
    drag.current = { id: item.id, pointerId: event.pointerId, x: event.clientX, y: event.clientY, cx: item.cx, cy: item.cy }
  }
  function move(event: PointerEvent<HTMLButtonElement>) {
    const gesture = drag.current, bounds = canvas.current?.getBoundingClientRect()
    if (!gesture || gesture.pointerId !== event.pointerId || !bounds) return
    controller.current?.move(gesture.id, gesture.cx + (event.clientX - gesture.x) / bounds.width, gesture.cy + (event.clientY - gesture.y) / bounds.height)
  }
  function finish(event: PointerEvent<HTMLButtonElement>) {
    if (drag.current?.pointerId !== event.pointerId) return
    drag.current = null; controller.current?.finishMove()
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId)
  }
  function cancel() { drag.current = null; controller.current?.cancelMove() }
  function keyboard(item: WallElement, event: KeyboardEvent<HTMLButtonElement>) {
    if (!editable) return
    const step = event.shiftKey ? .05 : .01
    const delta: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }
    if (delta[event.key]) { event.preventDefault(); controller.current?.nudge(item.id, ...delta[event.key]) }
    if (event.key === 'Escape') { event.preventDefault(); if (drag.current) cancel(); else controller.current?.select(null) }
    if ((event.key === 'Delete' || event.key === 'Backspace') && !state.moving) { event.preventDefault(); remove(item.id) }
  }
  const wall = state.wall, selected = state.elements.find(item => item.id === state.selectedId)
  const ordered = orderedElements(state.elements), layer = ordered.findIndex(item => item.id === state.selectedId)
  const status = state.loading ? 'Cargando pared…' : state.uploading ? 'Importando recurso…' : state.saving ? 'Guardando pared…' : state.moving ? 'Moviendo objeto…' : state.error ? 'No se pudo completar la operación' : dirty ? 'Cambios pendientes' : state.notice || 'Sin cambios'
  return <section className="wall-panel" onFocusCapture={event => {
    const target = event.target
    requestAnimationFrame(() => {
      if (!target.isConnected || drag.current) return
      const control = target.getBoundingClientRect(), player = document.querySelector('.player-bar')?.getBoundingClientRect()
      if (player && control.bottom > player.top - 16 && control.top < player.bottom) window.scrollBy(0, control.bottom - player.top + 24)
    })
  }} aria-labelledby={`wall-title-${albumId}`}>
    <div className="wall-heading"><div><p className="eyebrow">Tu espacio</p><h2 id={`wall-title-${albumId}`}>La pared de {title}</h2></div>
      {wall && <button disabled={state.loading || busy} aria-pressed={state.editing} aria-controls={`wall-tools-${albumId}`} onClick={() => void controller.current?.toggleEditing()}>{state.editing ? 'Bloquear diseño' : 'Editar pared'}</button>}
    </div>
    <p className="wall-status" role="status">{status}{wall && !state.loading ? ` · ${state.editing ? 'Edición activada' : 'Diseño bloqueado'}` : ''}</p>
    {state.error && <div className="wall-error" role="alert"><p>{state.error}</p><button className="secondary" disabled={busy} onClick={reload}>Recargar pared guardada</button></div>}
    {wall && !state.loading && <>
      <div ref={canvas} className="wall-canvas" data-mode={state.editing ? 'editing' : 'locked'} style={{ backgroundColor: state.color }} role="group" aria-label={`Muro de ${title}, ${state.elements.length} elementos decorativos`} onPointerDown={event => { if (event.target === event.currentTarget || (event.target as HTMLElement).classList.contains('wall-elements')) controller.current?.select(null) }}>
        <ul className="wall-elements" aria-label="Composición de la pared">{ordered.map((item, index) => <Decoration key={`${item.id}-${item.content_url}`} item={item} index={index} animated={animated} editable={editable} selected={item.id === state.selectedId} handlers={{ onClick: () => controller.current?.select(item.id), onFocus: () => controller.current?.select(item.id), onPointerDown: event => down(item, event), onPointerMove: move, onPointerUp: finish, onPointerCancel: cancel, onLostPointerCapture: () => { if (drag.current) cancel() }, onKeyDown: event => keyboard(item, event) }} />)}</ul>
        {!state.elements.length && <p className="wall-empty">Un espacio para tus recuerdos musicales.</p>}
      </div>
      {state.elements.some(item => item.kind === 'gif') && <label className="wall-animation"><input type="checkbox" checked={animated} onChange={event => setAnimated(event.target.checked)} /> Animar GIF de esta pared</label>}
      {state.editing && <div className="wall-tools" id={`wall-tools-${albumId}`}>
        <label htmlFor={`wall-color-${albumId}`}>Color del fondo</label><div className="wall-color-controls">
          <input id={`wall-color-${albumId}`} type="color" value={state.color} disabled={!editable || state.moving} onChange={event => controller.current?.setColor(event.target.value)} /><output htmlFor={`wall-color-${albumId}`}>{state.color}</output>
          {[['#242038', 'Ciruela'], ['#193A55', 'Azul nocturno'], ['#284333', 'Verde bosque'], ['#442244', 'Malva']].map(([color, label]) => <button key={color} className="wall-swatch" style={{ backgroundColor: color }} aria-label={`Fondo ${label}`} aria-pressed={state.color === color} disabled={!editable || state.moving} onClick={() => controller.current?.setColor(color)} />)}
        </div>
        <div className="wall-add"><label>Añadir como<select value={kind} disabled={!editable || state.moving} onChange={event => setKind(event.target.value as typeof kind)}><option value="poster">Póster</option><option value="sticker">Sticker</option><option value="image">Imagen</option></select></label>
          <label>Añadir recurso PNG, JPEG o GIF<input ref={upload} type="file" accept="image/png,image/jpeg,image/gif" disabled={!editable || busy || state.elements.length >= 30} onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) void controller.current?.addFile(file, kind) }} /></label>
          <p className="note">{state.elements.length}/30 objetos · Hasta 5 MiB por archivo, 4096 píxeles por lado. GIF: hasta 200 fotogramas y 32 millones de píxeles en total.</p>
        </div>
        {!!ordered.length && <label>Seleccionar objeto (de atrás hacia delante)<select value={state.selectedId ?? ''} disabled={!editable || state.moving} onChange={event => controller.current?.select(event.target.value || null)}><option value="">Ninguno</option>{ordered.map((item, index) => <option key={item.id} value={item.id}>{index + 1}. {kinds[item.kind]} · {item.id.slice(0, 8)}</option>)}</select></label>}
        {selected && <div className="wall-selection"><h3>{kinds[selected.kind]} seleccionado</h3><p>Arrastra el objeto o usa las flechas. Mayús mueve más; Escape cancela un arrastre. También puedes usar estos botones.</p><p>Centro: {(selected.cx * 100).toFixed(1)} % horizontal · {(selected.cy * 100).toFixed(1)} % vertical</p>
          <div className="wall-transforms" key={selected.id}>
            <TransformField label="Ancho (% del lienzo)" value={Number((selected.width * 100).toFixed(3))} min={3} max={60} disabled={!editable || state.moving} change={value => controller.current?.transform(selected.id, { width: value / 100 })} />
            <TransformField label="Alto (% del lienzo)" value={Number((selected.height * 100).toFixed(3))} min={3} max={60} disabled={!editable || state.moving} change={value => controller.current?.transform(selected.id, { height: value / 100 })} />
            <TransformField label="Giro (grados)" value={Number(selected.rotation_deg.toFixed(3))} min={-180} max={180} disabled={!editable || state.moving} change={value => controller.current?.transform(selected.id, { rotation_deg: value })} />
          </div>
          <p className="note">Tamaño entre 3 y 60 %. Al girar o ampliar, el objeto se recoloca y, si es necesario, se reduce proporcionalmente para caber en la pared.</p>
          <div className="wall-move-buttons" role="group" aria-label="Orden de superposición">
            {(['back', 'backward', 'forward', 'front'] as const).map((direction, index) => <button key={direction} disabled={!editable || state.moving || (index < 2 ? layer === 0 : layer === ordered.length - 1)} onClick={() => controller.current?.reorder(selected.id, direction)}>{['Al fondo', 'Una capa atrás', 'Una capa delante', 'Al frente'][index]}</button>)}
          </div><p>Capa {layer + 1} de {ordered.length}</p>
          <div className="wall-move-buttons">{[[-.01, 0, 'Izquierda'], [0, -.01, 'Arriba'], [0, .01, 'Abajo'], [.01, 0, 'Derecha']].map(([dx, dy, label]) => <button key={label} disabled={!editable || state.moving} aria-label={`Mover objeto: ${label}`} onClick={() => controller.current?.nudge(selected.id, Number(dx), Number(dy))}>{label}</button>)}
          <button disabled={!editable || state.moving} onClick={() => remove(selected.id)}>Quitar objeto</button></div>
        </div>}
        <p className="note">Guardado automático tras finalizar los cambios. Puedes seguir editando durante un guardado; los cambios nuevos se guardarán después.</p>
        <button disabled={!dirty || busy || state.needsReload} onClick={() => void controller.current?.save()}>Guardar ahora</button>
        <button className="secondary" disabled={busy || state.needsReload || state.loading} onClick={reload}>Restaurar pared guardada</button>
        <button className="secondary" disabled={!editable || busy} onClick={reset}>Restablecer diseño</button>
      </div>}
    </>}
  </section>
}
