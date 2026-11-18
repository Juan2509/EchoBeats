import { useEffect, useId, useRef, useState } from 'react'
import {createPortal} from 'react-dom'
import type { ButtonHTMLAttributes, KeyboardEvent, PointerEvent } from 'react'
import { initialWallState, isDirty, orderedElements, WallController } from './controller'
import type { WallElement } from './controller'
import { useAppearance,AppearanceSettings } from '../appearance/Appearance'
import { wallSurfaceFor,stickerOutlineFor,defaultStickerOutline } from '../appearance/theme'
import type {StickerOutline} from '../appearance/theme'
import { imageStyle } from '../appearance/BackgroundEditor'
import { WallToolsDialog } from './WallToolsDialog'
import {resizeHandles} from './resize'
import type {ResizeHandle} from './resize'

const kinds = { poster: 'Imagen', sticker: 'Sticker', image: 'Imagen', gif: 'Imagen animada' }
const handleNames:Record<ResizeHandle,string>={nw:'esquina superior izquierda',n:'borde superior',ne:'esquina superior derecha',e:'borde derecho',se:'esquina inferior derecha',s:'borde inferior',sw:'esquina inferior izquierda',w:'borde izquierdo'}
function Decoration({ item, index, animated, editable, selected, rotating, handlers,resizeHandlers,outline }: { item: WallElement; index: number; animated: boolean; editable: boolean; selected: boolean; rotating:boolean; handlers: ButtonHTMLAttributes<HTMLButtonElement>;resizeHandlers:(handle:ResizeHandle)=>ButtonHTMLAttributes<HTMLButtonElement>;outline:StickerOutline }) {
  const paused = item.kind === 'gif' && !animated
  const source = paused ? item.static_preview_url : item.content_url
  const filterId=`sticker-outline-${useId().replace(/:/g,'')}`
  const geometry={left:`${item.cx*100}%`,top:`${item.cy*100}%`,width:`${item.width*100}%`,height:`${item.height*100}%`,transform:`translate(-50%, -50%) rotate(${item.rotation_deg}deg)`}
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [source])
  return <><li className="wall-element" data-selected={selected&&editable} style={{...geometry,zIndex:item.z_index}}>
    <button type="button" className="wall-object" data-kind={item.kind==='sticker'?'sticker':'image'} data-rotating={rotating} disabled={!editable} tabIndex={editable ? 0 : -1} aria-pressed={selected} aria-label={`${kinds[item.kind]} ${index + 1}${editable ? rotating?': rotación activada; doble clic o R para mover':': mover con las flechas; doble clic o R para rotar' : ''}`} {...handlers}>
      {item.kind==='sticker'&&<svg className="sticker-filter-defs" width="0" height="0" aria-hidden="true" focusable="false"><defs><filter id={filterId} x="-50%" y="-50%" width="200%" height="200%" primitiveUnits="objectBoundingBox" colorInterpolationFilters="sRGB"><feMorphology in="SourceAlpha" operator="dilate" radius={`${outline.thickness/(item.width*1000)} ${outline.thickness/(item.height*700)}`} result="expanded"/><feFlood floodColor={outline.color} result="outlineColor"/><feComposite in="outlineColor" in2="expanded" operator="in" result="outline"/><feMerge><feMergeNode in="outline"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs></svg>}
      {failed || !source ? <span className="wall-placeholder">{paused ? 'GIF en pausa' : 'Imagen no disponible'}</span> : <img src={source} alt="" loading="lazy" decoding="async" draggable={false} style={{filter:item.kind==='sticker'&&outline.thickness>0?`url(#${filterId})`:'none'}} onError={() => setFailed(true)} />}
      {rotating&&<span className="rotation-indicator" aria-hidden="true">↻</span>}
    </button>
  </li>{selected&&editable&&<li className="wall-selection-overlay" style={geometry}>{!rotating&&resizeHandles.map(handle=><button type="button" key={handle} className="wall-resize-handle" data-handle={handle} aria-label={`Cambiar tamaño: ${handleNames[handle]}`} title="Arrastra para estirar. Shift conserva proporciones. Flechas para ajustar." style={{left:handle.includes('w')?'0%':handle.includes('e')?'100%':'50%',top:handle.includes('n')?'0%':handle.includes('s')?'100%':'50%',cursor:handle.length===1?(handle==='n'||handle==='s'?'ns-resize':'ew-resize'):(handle==='nw'||handle==='se'?'nwse-resize':'nesw-resize')}} {...resizeHandlers(handle)}><span aria-hidden="true"/></button>)}</li>}</>
}
export function WallView({ albumId, title, onDirty,toolbar }: { albumId: string; title: string; onDirty: (dirty: boolean) => void;toolbar?:HTMLElement|null }) {
  const {appearance,registerWall,setStickerOutline,notice:appearanceNotice}=useAppearance()
  const [rotationId,setRotationId]=useState<string|null>(null)
  const [expanded,setExpanded]=useState(false)
  const [toolsOpen,setToolsOpen]=useState(false)
  const [toolPage,setToolPage]=useState<'add'|'object'|'layers'|'save'|'outline'|'wall'>('add')
  const surface=wallSurfaceFor(appearance,albumId)
  const wallBackground=appearance.wallBackgrounds[albumId]
  const controller = useRef<WallController | null>(null)
  const canvas = useRef<HTMLDivElement>(null), upload = useRef<HTMLInputElement>(null)
  const drag = useRef<{ id: string; pointerId: number; x: number; y: number; cx: number; cy: number; rotating:boolean; angle:number; rotation:number; centerX:number; centerY:number;resize?:ResizeHandle } | null>(null)
  const [state, setState] = useState(initialWallState)
  const [kind, setKind] = useState<'sticker' | 'image'>('image')
  const [animated, setAnimated] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const instance = new WallController(albumId, undefined, undefined, { autosaveMs: 700 }); controller.current = instance
    const unsubscribe = instance.subscribe(() => setState(instance.state))
    setState(instance.state); void instance.load()
    return () => { drag.current = null; unsubscribe(); instance.dispose(); controller.current = null }
  }, [albumId])
  const dirty = isDirty(state), busy = state.saving || state.uploading || state.moving
  const editable = controller.current?.canEdit ?? false
  useEffect(()=>{registerWall({albumId,color:state.color,editable:editable&&!busy,expanded,setColor:value=>controller.current?.setColor(value),expand:()=>setExpanded(value=>!value)})},[albumId,state.color,editable,busy,expanded,registerWall])
  useEffect(()=>()=>registerWall(null),[registerWall])
  useEffect(()=>{if(!state.editing||state.selectedId!==rotationId)setRotationId(null)},[state.editing,state.selectedId,rotationId])
  useEffect(()=>{if(!state.editing)setToolsOpen(false)},[state.editing])
  useEffect(() => { onDirty(dirty || busy); return () => onDirty(false) }, [dirty, busy, onDirty])
  useEffect(() => {
    const prevent = (event: BeforeUnloadEvent) => { if (dirty || busy) event.preventDefault() }
    window.addEventListener('beforeunload', prevent)
    return () => window.removeEventListener('beforeunload', prevent)
  }, [dirty, busy])
  useEffect(()=>{
    const shortcut=(event:globalThis.KeyboardEvent)=>{
      if(event.defaultPrevented||!(event.ctrlKey||event.metaKey)||event.shiftKey||event.altKey||!['z','y'].includes(event.key.toLowerCase())||document.querySelector('dialog[open]'))return
      const target=event.target;if(target instanceof Element&&target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"]),[role="textbox"]'))return
      const changed=event.key.toLowerCase()==='z'?controller.current?.undo():controller.current?.redo()
      if(changed){drag.current=null;event.preventDefault()}
    };document.addEventListener('keydown',shortcut);return()=>document.removeEventListener('keydown',shortcut)
  },[])
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
  function remove(id: string) { controller.current?.remove(id) }
  function selectOnWall(id:string){controller.current?.select(id);if(toolsOpen)setToolPage('object')}
  async function openTools(){const current=controller.current;if(!current)return;if(!current.state.editing)await current.toggleEditing();if(current.state.editing){setToolPage(current.state.selectedId?'object':'add');setToolsOpen(true)}}
  async function finishEditing(){const current=controller.current;if(!current?.state.editing||current.state.needsReload)return;await current.toggleEditing();if(!current.state.editing)setToolsOpen(false)}
  function toggleRotation(id:string){const current=controller.current;if(!current?.canEdit||current.state.moving)return;current.select(id);setRotationId(value=>value===id?null:id)}
  function down(item: WallElement, event: PointerEvent<HTMLButtonElement>) {
    if (!editable || !event.isPrimary || event.button !== 0 || !controller.current?.beginMove(item.id)) return
    event.preventDefault(); event.currentTarget.focus({ preventScroll: true }); event.currentTarget.setPointerCapture(event.pointerId)
    const bounds=canvas.current!.getBoundingClientRect(),centerX=bounds.left+item.cx*bounds.width,centerY=bounds.top+item.cy*bounds.height
    drag.current = { id: item.id, pointerId: event.pointerId, x: event.clientX, y: event.clientY, cx: item.cx, cy: item.cy, rotating:rotationId===item.id,angle:Math.atan2(event.clientY-centerY,event.clientX-centerX),rotation:item.rotation_deg,centerX,centerY }
  }
  function move(event: PointerEvent<HTMLButtonElement>) {
    const gesture = drag.current, bounds = canvas.current?.getBoundingClientRect()
    if (!gesture || gesture.pointerId !== event.pointerId || !bounds) return
    if(gesture.resize)controller.current?.resizeGesture(gesture.id,gesture.resize,(event.clientX-gesture.x)/bounds.width*1000,(event.clientY-gesture.y)/bounds.height*700,event.shiftKey)
    else if(gesture.rotating){const angle=Math.atan2(event.clientY-gesture.centerY,event.clientX-gesture.centerX);controller.current?.rotateGesture(gesture.id,gesture.rotation+(angle-gesture.angle)*180/Math.PI)}
    else controller.current?.move(gesture.id, gesture.cx + (event.clientX - gesture.x) / bounds.width, gesture.cy + (event.clientY - gesture.y) / bounds.height)
  }
  function finish(event: PointerEvent<HTMLButtonElement>) {
    if (drag.current?.pointerId !== event.pointerId) return
    drag.current = null; controller.current?.finishMove()
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId)
  }
  function cancel() { drag.current = null; controller.current?.cancelMove() }
  function resizeDown(item:WallElement,handle:ResizeHandle,event:PointerEvent<HTMLButtonElement>){event.stopPropagation();if(rotationId===item.id)return;down(item,event);if(drag.current?.id===item.id){drag.current.resize=handle;drag.current.rotating=false}}
  function resizeKeys(item:WallElement,handle:ResizeHandle,event:KeyboardEvent<HTMLButtonElement>){
    if(event.ctrlKey||event.metaKey||rotationId===item.id)return
    event.stopPropagation();const arrows:Record<string,[number,number]>={ArrowLeft:[-5,0],ArrowRight:[5,0],ArrowUp:[0,-5],ArrowDown:[0,5]}
    if(event.key==='Escape'){event.preventDefault();if(drag.current)cancel();else controller.current?.select(null);return}
    if(!arrows[event.key])return;event.preventDefault();const current=controller.current;if(!current?.beginMove(item.id))return
    const [dx,dy]=arrows[event.key];current.resizeGesture(item.id,handle,dx,dy,event.shiftKey);current.finishMove()
  }
  function keyboard(item: WallElement, event: KeyboardEvent<HTMLButtonElement>) {
    if (!editable) return
    const step = event.shiftKey ? .05 : .01
    const delta: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }
    if(event.key.toLowerCase()==='r'){event.preventDefault();toggleRotation(item.id)}
    if (delta[event.key]) { event.preventDefault(); if(rotationId===item.id)controller.current?.transform(item.id,{rotation_deg:item.rotation_deg+(event.key==='ArrowLeft'||event.key==='ArrowUp'?-1:1)*(event.shiftKey?15:2)});else controller.current?.nudge(item.id, ...delta[event.key]) }
    if (event.key === 'Escape') { event.preventDefault(); if (drag.current) cancel(); else {setRotationId(null);controller.current?.select(null)} }
    if ((event.key === 'Delete' || event.key === 'Backspace') && !state.moving) { event.preventDefault(); remove(item.id) }
  }
  const wall = state.wall, selected = state.elements.find(item => item.id === state.selectedId)
  const selectedOutline=selected?stickerOutlineFor(appearance,albumId,selected.id):defaultStickerOutline
  useEffect(()=>{if(toolPage==='outline'&&selected?.kind!=='sticker')setToolPage('object')},[toolPage,selected?.kind])
  const ordered = orderedElements(state.elements), layer = ordered.findIndex(item => item.id === state.selectedId)
  const status = state.loading ? 'Cargando pared…' : state.uploading ? 'Importando recurso…' : state.saving ? 'Guardando pared…' : state.moving ? 'Moviendo objeto…' : state.error ? 'No se pudo completar la operación' : dirty ? 'Cambios pendientes' : state.notice || 'Sin cambios'
  const editActions=wall&&<><button disabled={state.loading || busy} aria-expanded={toolsOpen} aria-controls={`wall-tools-${albumId}`} onClick={() => void openTools()}>Editar pared</button>{expanded&&<button type="button" className="secondary" onClick={()=>setExpanded(false)}>Ver panel del álbum</button>}</>
  return <section className="wall-panel" data-expanded={expanded} onFocusCapture={event => {
    const target = event.target
    if (target.closest('dialog, .wall-tools-floating')) return
    requestAnimationFrame(() => {
      if (!target.isConnected || document.activeElement !== target || drag.current) return
      const control = target.getBoundingClientRect(), player = document.querySelector('.player-bar')?.getBoundingClientRect()
      if (player && control.bottom > player.top - 16 && control.top < player.bottom) window.scrollBy(0, control.bottom - player.top + 24)
    })
  }} aria-labelledby={`wall-title-${albumId}`}>
    <h2 className="visually-hidden" id={`wall-title-${albumId}`}>La pared de {title}</h2>
    {toolbar?createPortal(editActions,toolbar):<div className="wall-heading">{editActions}</div>}
    <p className="visually-hidden" role="status">{status}{wall && !state.loading ? ` · ${state.editing ? 'Edición activada' : 'Diseño bloqueado'}` : ''}</p>
    {state.error && <div className="wall-error" role="alert"><p>{state.error}</p><button className="secondary" disabled={busy} onClick={reload}>Recargar pared guardada</button></div>}
    {wall && !state.loading && <>
      <div ref={canvas} className="wall-canvas" data-surface={surface} data-mode={state.editing ? 'editing' : 'locked'} style={{ backgroundColor: surface==='scene'?'transparent':state.color }} role="group" aria-label={`Muro de ${title}, ${state.elements.length} elementos decorativos`} onPointerDown={event => { if (event.target === event.currentTarget || (event.target as HTMLElement).classList.contains('wall-elements')) controller.current?.select(null) }}>
        {surface==='image'&&wallBackground?.image&&<div className="wall-background" aria-hidden="true"><div className="wallpaper-image" style={imageStyle(wallBackground.image,wallBackground)}/></div>}
        <ul className="wall-elements" aria-label="Composición de la pared">{ordered.map((item, index) => <Decoration key={`${item.id}-${item.content_url}`} item={item} index={index} animated={animated} editable={editable} selected={item.id === state.selectedId} rotating={rotationId===item.id} outline={stickerOutlineFor(appearance,albumId,item.id)} resizeHandlers={handle=>({onPointerDown:event=>resizeDown(item,handle,event),onPointerMove:move,onPointerUp:finish,onPointerCancel:cancel,onLostPointerCapture:()=>{if(drag.current)cancel()},onKeyDown:event=>resizeKeys(item,handle,event),onDoubleClick:event=>event.stopPropagation()})} handlers={{ onClick: () => selectOnWall(item.id), onDoubleClick:()=>toggleRotation(item.id), onFocus: () => selectOnWall(item.id), onPointerDown: event => down(item, event), onPointerMove: move, onPointerUp: finish, onPointerCancel: cancel, onLostPointerCapture: () => { if (drag.current) cancel() }, onKeyDown: event => keyboard(item, event) }} />)}</ul>
      </div>
      {state.editing && toolsOpen && <WallToolsDialog close={()=>setToolsOpen(false)} finishEditing={()=>void finishEditing()} finishDisabled={busy||state.needsReload}><div className="wall-tools" data-page={toolPage} id={`wall-tools-${albumId}`}>
        <nav className="wall-tools-pages" aria-label="Herramientas de la pared">{([['add','Añadir'],['object','Objeto'],['layers','Capas'],['wall','Fondo'],['save','Guardar']] as const).map(([page,label])=><button key={page} type="button" aria-pressed={toolPage===page||page==='object'&&toolPage==='outline'} onClick={()=>setToolPage(page)}>{label}</button>)}</nav>
        {toolPage==='wall'&&<div className="appearance-settings wall-appearance-settings"><AppearanceSettings albumId={albumId} wallOnly/></div>}
        {state.error&&<p role="alert">{state.error}</p>}
        <div className="wall-add" hidden={toolPage!=='add'}><label>Añadir como<select value={kind} disabled={!editable || state.moving} onChange={event => setKind(event.target.value as typeof kind)}><option value="image">Imagen sin marco</option><option value="sticker">Sticker con contorno</option></select></label>
          <label>Añadir recurso PNG, JPEG o GIF<input ref={upload} type="file" accept="image/png,image/jpeg,image/gif" disabled={!editable || busy || state.elements.length >= 30} onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) void controller.current?.addFile(file, kind) }} /></label>
          <p className="note">{state.elements.length}/30 objetos · Hasta 5 MiB por archivo, 4096 píxeles por lado. GIF: hasta 200 fotogramas y 32 millones de píxeles en total.</p>
          {state.elements.some(item => item.kind === 'gif') && <label className="wall-animation"><input type="checkbox" checked={animated} onChange={event => setAnimated(event.target.checked)} /> Animar GIF de esta pared</label>}
        </div>
        {(toolPage==='object'||toolPage==='layers')&&!selected&&<p>Haz clic en una imagen del muro para editarla. Haz clic en un espacio vacío para quitar la selección.</p>}
        {selected && (toolPage==='object'||toolPage==='layers') && <div className="wall-selection">
          <p className="wall-selected-name">{kinds[selected.kind]} seleccionado</p>
          {toolPage==='object'&&<><p className="note">Arrastra los cuadros para estirar; Shift conserva proporciones. Doble clic alterna rotación (sin tiradores). Ctrl+Z deshace y Ctrl+Y rehace.</p><div className="wall-history-actions"><button type="button" className="secondary" disabled={!controller.current?.canUndo} onClick={()=>{if(controller.current?.undo())drag.current=null}}>Deshacer · Ctrl+Z</button><button type="button" className="secondary" disabled={!controller.current?.canRedo} onClick={()=>controller.current?.redo()}>Rehacer · Ctrl+Y</button></div>
          {selected.kind!=='gif'?<label>Apariencia del objeto seleccionado<select value={selected.kind==='sticker'?'sticker':'image'} disabled={!editable||state.moving} onChange={event=>controller.current?.setKind(selected.id,event.target.value as 'image'|'sticker')}><option value="image">Imagen sin marco</option><option value="sticker">Sticker con contorno</option></select></label>:<p className="note">Los GIF conservan su modo de imagen animada.</p>}
          <button type="button" className="secondary" disabled={!editable||state.moving} onClick={()=>controller.current?.fit(selected.id)}>Ajustar al muro</button><p className="note">Amplía y centra la imagen al máximo sin deformarla. El contorno del lienzo indica todo el espacio disponible.</p>
          {selected.kind==='sticker'&&<button type="button" className="secondary" onClick={()=>setToolPage('outline')}>Editar contorno · grosor {selectedOutline.thickness}</button>}
          </>}
          {toolPage==='layers'&&<><div className="wall-move-buttons" role="group" aria-label="Orden de superposición">
            {(['back', 'backward', 'forward', 'front'] as const).map((direction, index) => <button key={direction} disabled={!editable || state.moving || (index < 2 ? layer === 0 : layer === ordered.length - 1)} onClick={() => controller.current?.reorder(selected.id, direction)}>{['Al fondo', 'Una capa atrás', 'Una capa delante', 'Al frente'][index]}</button>)}
          </div><p>Capa {layer + 1} de {ordered.length}</p></>}
          {toolPage==='object'&&<div className="wall-move-buttons">{[[-.01, 0, 'Izquierda'], [0, -.01, 'Arriba'], [0, .01, 'Abajo'], [.01, 0, 'Derecha']].map(([dx, dy, label]) => <button key={label} disabled={!editable || state.moving} aria-label={`Mover objeto: ${label}`} onClick={() => controller.current?.nudge(selected.id, Number(dx), Number(dy))}>{label}</button>)}
          <button disabled={!editable || state.moving} onClick={() => remove(selected.id)}>Quitar objeto</button></div>}
        </div>}
        {toolPage==='outline'&&selected?.kind==='sticker'&&<section className="sticker-outline-page" aria-label="Contorno del sticker"><h3>Contorno del sticker</h3><p className="note">Elige el color y ajusta el grosor. La vista del muro cambia al instante.</p><div className="sticker-outline-controls"><label>Color del contorno<input type="color" value={selectedOutline.color} disabled={!editable||state.moving} onChange={event=>setStickerOutline(albumId,selected.id,{color:event.target.value})}/></label><label>Grosor · {selectedOutline.thickness}<input type="range" min={0} max={12} step={.5} aria-label="Grosor del contorno" value={selectedOutline.thickness} disabled={!editable||state.moving} onChange={event=>setStickerOutline(albumId,selected.id,{thickness:Number(event.target.value)})}/><span className="sticker-thickness-labels"><span>Sin contorno</span><span>Grueso</span></span></label></div><p className="note" role="status">Contorno por sticker · {appearanceNotice}</p><button type="button" className="secondary" onClick={()=>setToolPage('object')}>Volver a Objeto</button></section>}
        {toolPage==='save'&&<div className="wall-save-actions"><p className="note">El guardado es automático. También puedes guardar ahora o recuperar el diseño.</p>
        <button disabled={!dirty || busy || state.needsReload} onClick={() => void controller.current?.save()}>Guardar ahora</button>
        <button className="secondary" disabled={busy || state.needsReload || state.loading} onClick={reload}>Restaurar pared guardada</button>
        <button className="secondary" disabled={!editable || busy} onClick={reset}>Restablecer diseño</button>
        </div>}
        <footer className="wall-tools-footer"><p role="status">{status}</p><button disabled={busy||state.needsReload} onClick={()=>void finishEditing()}>Terminar edición</button></footer>
      </div></WallToolsDialog>}
    </>}
  </section>
}
