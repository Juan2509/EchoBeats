import {useEffect,useRef} from 'react'

/** Ajusta el scroll del panel al hueco entre navegación y reproductor, incluso con zoom. */
export function useAlbumPanelSpace(loadedId:string|undefined){
  const panel=useRef<HTMLElement>(null)
  useEffect(()=>{
    const element=panel.current
    if(!element||!loadedId)return
    const room=element.closest<HTMLElement>('.album-room'),workspace=element.closest<HTMLElement>('.workspace')
    if(!room||!workspace)return
    const header=document.querySelector('.site-header'),player=document.querySelector('.player-bar'),toolbar=workspace.querySelector('.album-toolbar')
    let frame=0
    const fit=()=>{frame=0;const box=workspace.getBoundingClientRect(),scale=workspace.offsetWidth?box.width/workspace.offsetWidth:1
      const top=Math.max(room.getBoundingClientRect().top,(header?.getBoundingClientRect().bottom??0)+8)
      const style=getComputedStyle(workspace),bottom=parseFloat(style.paddingBottom)*scale,gap=parseFloat(style.rowGap)*scale
      const available=Math.max(120,window.innerHeight-top-(player?.getBoundingClientRect().height??0)-bottom-gap)
      room.style.setProperty('--album-room-height',`${available/scale}px`)
      element.style.setProperty('--album-panel-height',`${available/scale}px`)
    }
    const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(fit)}
    const observer=new ResizeObserver(schedule)
    if(header)observer.observe(header);if(player)observer.observe(player)
    if(toolbar)observer.observe(toolbar)
    window.addEventListener('resize',schedule);window.addEventListener('scroll',schedule,{passive:true});schedule()
    return()=>{cancelAnimationFrame(frame);observer.disconnect();window.removeEventListener('resize',schedule);window.removeEventListener('scroll',schedule)}
  },[loadedId])
  return panel
}
