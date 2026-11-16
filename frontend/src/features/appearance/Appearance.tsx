import { createContext, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { defaults,presets,decodeAppearance,cssVariables,STORAGE_KEY,backgroundFor,replaceBackground,replaceWallBackground,baseWallpaper,removeCustomBackground,wallSurfaceFor } from './theme'
import type { Appearance,Wallpaper,StickerOutline } from './theme'
import {changeStickerOutline} from './theme'
import { BackgroundEditor,imageStyle } from './BackgroundEditor'

type WallControls={albumId:string;color:string;editable:boolean;expanded:boolean;setColor:(color:string)=>void;expand:()=>void}
type ContextValue={appearance:Appearance;change:(value:Partial<Appearance>)=>void;setBackground:(albumId:string|undefined,value:Wallpaper|null)=>void;setWallBackground:(albumId:string,value:Wallpaper)=>void;setStickerOutline:(albumId:string,itemId:string,value:Partial<StickerOutline>)=>void;removeBackground:(scope:'main'|'album'|'wall',id?:string)=>void;wallControls:WallControls|null;registerWall:(value:WallControls|null)=>void;notice:string}
const Context=createContext<ContextValue>({appearance:defaults,change:()=>{},setBackground:()=>{},setWallBackground:()=>{},setStickerOutline:()=>{},removeBackground:()=>{},wallControls:null,registerWall:()=>{},notice:''})
export const useAppearance=()=>useContext(Context)
export function AppearanceProvider({children,albumId}:{children:ReactNode;albumId?:string}){
  const [appearance,setAppearance]=useState(()=>{try{return decodeAppearance(JSON.parse(localStorage.getItem(STORAGE_KEY)??'null'))}catch{return structuredClone(defaults)}})
  const [notice,setNotice]=useState('')
  const [wallControls,registerWall]=useState<WallControls|null>(null)
  const active=backgroundFor(appearance,albumId)
  useEffect(()=>{for(const [key,value] of Object.entries(cssVariables(appearance,albumId)))document.documentElement.style.setProperty(key,value)},[appearance,albumId])
  useEffect(()=>{try{localStorage.setItem(STORAGE_KEY,JSON.stringify(appearance));setNotice('Preferencias guardadas en este navegador.')}catch{setNotice('Solo en esta sesión: el navegador no permite guardar las preferencias.')}},[appearance])
  useEffect(()=>{const sync=(event:StorageEvent)=>{if(event.key===STORAGE_KEY){try{setAppearance(decodeAppearance(JSON.parse(event.newValue??'null')))}catch{setAppearance(structuredClone(defaults))}}};window.addEventListener('storage',sync);return()=>window.removeEventListener('storage',sync)},[])
  return <Context.Provider value={{appearance,change:value=>setAppearance(current=>decodeAppearance({...current,...value})),setBackground:(id,value)=>setAppearance(current=>replaceBackground(current,id,value)),setWallBackground:(id,value)=>setAppearance(current=>replaceWallBackground(current,id,value)),setStickerOutline:(id,item,value)=>setAppearance(current=>changeStickerOutline(current,id,item,value)),removeBackground:(scope,id)=>setAppearance(current=>removeCustomBackground(current,scope,id)),wallControls,registerWall,notice}}>
    {active.mode==='image'&&active.image&&<div className="wallpaper-viewport" aria-hidden="true"><div className="wallpaper-image" style={imageStyle(active.image,active)}/></div>}{children}
  </Context.Provider>
}
export function AppearanceSettings({albumId,wallOnly=false}:{albumId?:string;wallOnly?:boolean}){
  const {appearance,change,setBackground,setWallBackground,removeBackground,wallControls,notice}=useAppearance()
  const fields:[keyof Pick<Appearance,'skyTop'|'skyBottom'|'panelTop'|'panelBottom'|'pink'|'cyan'>,string][]=[['skyTop','Synthwave · superior'],['skyBottom','Synthwave · inferior'],['panelTop','Panel · inicio'],['panelBottom','Panel · final'],['pink','Acento rosa'],['cyan','Acento cian']]
  return <><p className="note">{albumId?'Personaliza este álbum y su muro. El fondo principal se edita desde Inicio o Biblioteca.':'Personaliza el fondo principal. Los fondos propios de álbumes se editan dentro de cada álbum.'} Preferencias guardadas en este navegador.</p>
    {!wallOnly&&(albumId?<BackgroundEditor key={albumId} label="Fondo de este álbum" value={backgroundFor(appearance,albumId)} inheritValue={appearance.background} inherited={!appearance.albumBackgrounds[albumId]} onSave={value=>setBackground(albumId,value)} onInherit={()=>setBackground(albumId,null)} onRemove={appearance.albumBackgrounds[albumId]?.image?()=>removeBackground('album',albumId):undefined}/>:<BackgroundEditor label="Fondo principal" value={appearance.background} onSave={value=>setBackground(undefined,value)} onRemove={()=>removeBackground('main')}/>)}
    {albumId&&<section aria-label="Configuración del muro"><h3>Muro del álbum</h3><div className="wall-settings-modes">{(['scene','album','image'] as const).map((mode,index)=><button key={mode} disabled={mode==='image'&&!appearance.wallBackgrounds[albumId]} aria-pressed={wallSurfaceFor(appearance,albumId)===mode} onClick={()=>change({wallSurfaces:{...appearance.wallSurfaces,[albumId]:mode}})}>{['Transparente','Color del muro','Usar imagen del muro'][index]}</button>)}</div>
      {wallControls?.albumId===albumId&&<><label>Color del muro<input type="color" value={wallControls.color} disabled={!wallControls.editable} onChange={event=>{wallControls.setColor(event.target.value);change({wallSurfaces:{...appearance.wallSurfaces,[albumId]:'album'}})}}/></label>{!wallControls.editable&&<p className="note">Activa Editar pared antes de cambiar su color guardado.</p>}<button aria-pressed={wallControls.expanded} onClick={wallControls.expand}>{wallControls.expanded?'Vista normal':'Ampliar muro'}</button></>}
      <BackgroundEditor key={`wall-${albumId}`} imageOnly previewRatio={10/7} label="Imagen del muro" value={appearance.wallBackgrounds[albumId]??baseWallpaper} onSave={value=>setWallBackground(albumId,value)} onRemove={()=>removeBackground('wall',albumId)}/></section>}
    {!albumId&&<details className="color-customization"><summary>Colores de paneles y degradados</summary><div className="appearance-presets">{Object.entries(presets).map(([name,value])=><button type="button" className="secondary" key={name} onClick={()=>change(value)}>{name}</button>)}</div>
      <div className="appearance-colors">{fields.map(([key,label])=><label key={key}>{label}<span><input type="color" value={appearance[key]} onChange={event=>change({[key]:event.target.value})}/><output>{appearance[key]}</output></span></label>)}</div>
      <label>Dirección del degradado · {appearance.angle}°<input type="range" min={0} max={360} value={appearance.angle} onChange={event=>change({angle:Number(event.target.value)})}/></label>
      <label className="appearance-check"><input type="checkbox" checked={appearance.grid} onChange={event=>change({grid:event.target.checked})}/> Rejilla para estilos predeterminados</label>
    </details>}<p role="status">{notice}</p></>
}
export function AppearanceDialog({albumId,close,children,wallOnly=false}:{albumId?:string;close:()=>void;children?:ReactNode;wallOnly?:boolean}){
  const dialog=useRef<HTMLDialogElement>(null)
  useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close()},[])
  function dismiss(){dialog.current?.close();close()}
  return <dialog ref={dialog} className="appearance-dialog" aria-labelledby="appearance-dialog-title" onCancel={event=>{event.preventDefault();dismiss()}}><header><h2 id="appearance-dialog-title">{wallOnly?'Fondo del muro':'Fondos y apariencia'}</h2><button type="button" className="secondary" aria-label="Cerrar ajustes de apariencia" onClick={dismiss}>Cerrar</button></header><AppearanceSettings albumId={albumId} wallOnly={wallOnly}/>{children}</dialog>
}
