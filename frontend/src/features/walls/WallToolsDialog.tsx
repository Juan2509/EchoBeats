import {useLayoutEffect,useRef,useState} from 'react'
import type {ReactNode,PointerEvent,KeyboardEvent} from 'react'

export function WallToolsDialog({children,close,finishEditing,finishDisabled}:{children:ReactNode;close:()=>void;finishEditing:()=>void;finishDisabled:boolean}){
  const panel=useRef<HTMLElement>(null),handle=useRef<HTMLElement>(null)
  const drag=useRef<{pointer:number;x:number;y:number;left:number;top:number;docked:boolean}|null>(null)
  const docked=useRef(true)
  const [position,setPosition]=useState({left:8,top:8,scale:1})
  const [collapsed,setCollapsed]=useState(false)
  function fit(left:number,top:number){
    const element=panel.current,bounds=element?.getBoundingClientRect()
    const scale=bounds&&element?.offsetWidth?bounds.width/element.offsetWidth:1
    const maxLeft=document.documentElement.clientWidth-(bounds?.width??440)-8
    const maxTop=window.innerHeight-(bounds?.height??100)-8
    return {left:Math.max(8,Math.min(maxLeft,left)),top:Math.max(8,Math.min(maxTop,top)),scale}
  }
  function placeAtRight(){
    const wall=panel.current?.closest('.wall-panel')?.querySelector('.wall-canvas')?.getBoundingClientRect()
    const right=fit(Infinity,96)
    return wall&&right.left>=wall.right+8?fit(right.left,wall.top):right
  }
  useLayoutEffect(()=>{
    const previous=document.activeElement,element=panel.current
    handle.current?.focus({preventScroll:true})
    setPosition(placeAtRight())
    const constrain=()=>setPosition(previousPosition=>{
      const next=docked.current?placeAtRight():fit(previousPosition.left,previousPosition.top)
      return next.left===previousPosition.left&&next.top===previousPosition.top&&next.scale===previousPosition.scale?previousPosition:next
    })
    const observer=new ResizeObserver(constrain)
    if(element)observer.observe(element)
    observer.observe(document.documentElement)
    const wall=element?.closest('.wall-panel')?.querySelector('.wall-canvas')
    if(wall)observer.observe(wall)
    window.addEventListener('resize',constrain)
    window.addEventListener('pointermove',move)
    window.addEventListener('pointerup',finish)
    window.addEventListener('pointercancel',cancel)
    window.addEventListener('blur',cancel)
    return()=>{
      observer.disconnect()
      window.removeEventListener('resize',constrain)
      window.removeEventListener('pointermove',move)
      window.removeEventListener('pointerup',finish)
      window.removeEventListener('pointercancel',cancel)
      window.removeEventListener('blur',cancel)
      if(element?.contains(document.activeElement)&&previous instanceof HTMLElement&&previous.isConnected)previous.focus({preventScroll:true})
    }
  },[])
  function down(event:PointerEvent<HTMLElement>){if(event.button!==0||!event.isPrimary||(event.target as HTMLElement).closest('button'))return;event.preventDefault();event.currentTarget.focus({preventScroll:true});event.currentTarget.setPointerCapture(event.pointerId);drag.current={pointer:event.pointerId,x:event.clientX,y:event.clientY,left:position.left,top:position.top,docked:docked.current}}
  function move(event:globalThis.PointerEvent){const d=drag.current;if(d?.pointer===event.pointerId){docked.current=false;setPosition(fit(d.left+event.clientX-d.x,d.top+event.clientY-d.y))}}
  function finish(event:globalThis.PointerEvent){if(drag.current?.pointer===event.pointerId)drag.current=null}
  function cancel(event?:Event){
    const d=drag.current
    if(!d||(event instanceof window.PointerEvent&&d.pointer!==event.pointerId))return
    drag.current=null
    docked.current=d.docked
    if(handle.current?.hasPointerCapture(d.pointer))handle.current.releasePointerCapture(d.pointer)
    setPosition(d.docked?placeAtRight():fit(d.left,d.top))
  }
  function keys(event:KeyboardEvent<HTMLElement>){if(event.target!==event.currentTarget)return;const delta:Record<string,[number,number]>={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};if(delta[event.key]){event.preventDefault();docked.current=false;const [x,y]=delta[event.key],step=event.shiftKey?30:10;setPosition(p=>fit(p.left+x*step,p.top+y*step))}if(event.key==='Home'){event.preventDefault();docked.current=true;setPosition(placeAtRight())}}
  return <aside ref={panel} role="dialog" aria-modal="false" className="wall-tools-dialog wall-tools-floating" data-collapsed={collapsed} aria-labelledby="wall-tools-heading" style={{left:position.left/position.scale,top:position.top/position.scale}} onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();if(drag.current)cancel();else close()}}}><header ref={handle} className="wall-tools-drag-handle" tabIndex={0} aria-label="Mover herramientas: arrastra o usa las flechas. Inicio vuelve a la derecha." onKeyDown={keys} onPointerDown={down}><h2 id="wall-tools-heading"><span aria-hidden="true">⠿ </span>Editar pared</h2><div><button type="button" className="secondary" aria-expanded={!collapsed} onClick={()=>setCollapsed(value=>!value)}>{collapsed?'Expandir':'Minimizar'}</button><button type="button" className="secondary" aria-label="Terminar edición de la pared" disabled={finishDisabled} onClick={finishEditing}>✕</button></div></header><div hidden={collapsed}>{children}</div></aside>
}
