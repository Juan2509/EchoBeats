import { useEffect, useRef, useState } from 'react'
import { assetUrl, sceneNames } from './theme'
import type { SceneMode, Wallpaper } from './theme'
import { SceneArtwork } from './SceneArtwork'
import { prepareWallpaper } from './image'
import {WallpaperCanvas} from './WallpaperCanvas'
import {imageStyle} from './wallpaperStyle'
export {imageStyle} from './wallpaperStyle'

export function WallpaperThumbnail({value,image}:{value:Wallpaper;image?:string|null}){
  const source=image??value.image
  return <span className="background-thumbnail" data-mode={value.mode} aria-hidden="true">{source&&value.mode==='image'?<span className="wallpaper-image" style={imageStyle(source,value)}/>:value.mode==='image'?<svg viewBox="0 0 160 90"><path d="M10 75 55 25 85 58 110 38 150 75Z" fill="#7995ba"/><circle cx="120" cy="20" r="10" fill="#f9c9e9"/></svg>:value.mode!=='synthwave'?<SceneArtwork mode={value.mode}/>:<><i className="thumbnail-sun"/><i className="thumbnail-grid"/></>}</span>
}

export function BackgroundEditor({value,label,onSave,onInherit,onRemove,inherited=false,imageOnly=false,previewRatio,inheritValue}:{value:Wallpaper;label:string;onSave:(value:Wallpaper)=>void;onInherit?:()=>void;onRemove?:()=>void;inherited?:boolean;imageOnly?:boolean;previewRatio?:number;inheritValue?:Wallpaper}){
  const [draft,setDraft]=useState(value),[dirty,setDirty]=useState(false),[prepared,setPrepared]=useState<Blob|null>(null),[preview,setPreview]=useState<string|null>(null)
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  const [ratio,setRatio]=useState(()=>window.innerWidth/window.innerHeight)
  const alive=useRef(true),pending=useRef<AbortController|null>(null)
  const fileInput=useRef<HTMLInputElement>(null)
  const cropArea=useRef<HTMLDivElement>(null)
  useEffect(()=>{if(preview)requestAnimationFrame(()=>cropArea.current?.scrollIntoView({block:'center'}))},[preview])
  const stamp=JSON.stringify(value)
  useEffect(()=>{if(!dirty&&!prepared)setDraft(JSON.parse(stamp))},[stamp,dirty,prepared])
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;pending.current?.abort()}},[])
  useEffect(()=>{const guard=(event:Event)=>{if(busy||dirty){event.preventDefault();setNotice(busy?'Espera a que termine la preparación o el guardado.':'Aplica o descarta los ajustes del fondo antes de cambiar de apartado.')}};window.addEventListener('echobeats:before-navigation',guard);return()=>window.removeEventListener('echobeats:before-navigation',guard)},[busy,dirty])
  useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview)},[preview])
  useEffect(()=>{const resize=()=>setRatio(window.innerWidth/window.innerHeight);window.addEventListener('resize',resize);return()=>window.removeEventListener('resize',resize)},[])
  function edit(changes:Partial<Wallpaper>){setDraft(current=>({...current,...changes}));setDirty(true);setNotice('Vista previa · pulsa Aplicar fondo para guardar.')}
  function choose(mode:SceneMode){
    setPrepared(null);setPreview(null);setDirty(false);setError('');onSave({...value,mode});setNotice('Estilo predeterminado aplicado. Tu imagen guardada sigue disponible.')
  }
  async function load(file:File){
    setBusy(true);setError('');setNotice('Preparando una copia compatible…')
    try{const blob=await prepareWallpaper(file);if(alive.current){setPrepared(blob);setPreview(URL.createObjectURL(blob));setDraft(current=>({...current,mode:'image',fit:'cover',x:50,y:50,zoom:1,panX:0,panY:0,rotation:0}));setDirty(true);setNotice('Arrastra o gira en el lienzo y pulsa Aplicar fondo. El original no se modifica.')}}
    catch(cause){if(alive.current){setError(cause instanceof Error?cause.message:'No se pudo preparar la imagen.');setNotice('El fondo anterior se conserva.')}}
    finally{if(alive.current)setBusy(false)}
  }
  async function apply(){
    setBusy(true);setError('');const abort=new AbortController();pending.current=abort;const timer=setTimeout(()=>abort.abort(),25000)
    try{
      let image=draft.image
      if(prepared){
        const body=new FormData();body.append('file',prepared,'fondo.jpg');body.append('purpose','wall')
        const response=await fetch('/api/v1/assets',{method:'POST',body,signal:abort.signal});const data=await response.json()
        if(!response.ok||!assetUrl(data.content_url))throw new Error(response.ok?'El recurso recibido no es válido.':data.error?.message??'No se pudo guardar la imagen.')
        image=data.content_url
      }
      if(draft.mode==='image'&&!image)throw new Error('Selecciona una imagen primero.')
      if(alive.current&&!abort.signal.aborted){onSave({...draft,image});setPrepared(null);setPreview(null);setDirty(false);setNotice('Fondo aplicado. Puedes volver a encuadrarlo o elegir un estilo predeterminado.')}
    }catch(cause){if(alive.current)setError(cause instanceof Error&&!(cause instanceof TypeError)&&!(cause instanceof SyntaxError)&&cause.name!=='AbortError'?cause.message:'No se confirmó el guardado; el recurso puede haberse registrado. El fondo anterior se conserva y no se reintentó.')}
    finally{clearTimeout(timer);if(alive.current)setBusy(false)}
  }
  const image=preview??draft.image
  function removeImage(){setPrepared(null);setPreview(null);setDirty(false);if(!prepared)onRemove?.();setNotice(prepared?'Imagen pendiente descartada.':'Fondo personalizado quitado. Los predeterminados se conservan.')}
  return <section className="background-editor" aria-label={label}><h3>{label}</h3>
    {onInherit&&<p>{inherited?'Este álbum está usando el fondo principal.':'Este álbum tiene un fondo propio.'}</p>}
    <fieldset disabled={busy}><legend>Elegir fondo</legend><div className="background-modes background-gallery">
      {!imageOnly&&(Object.keys(sceneNames) as SceneMode[]).map(mode=><button type="button" className="background-choice" key={mode} aria-pressed={value.mode===mode&&!dirty&&!inherited} onClick={()=>choose(mode)}><WallpaperThumbnail value={{...value,mode}}/><span>{sceneNames[mode]}</span><span className="choice-check" aria-hidden="true">✓</span></button>)}
      <div className="background-custom-choice"><button type="button" className="background-choice" aria-pressed={draft.mode==='image'&&!inherited} onClick={()=>{if(preview){edit({mode:'image'});return}if(value.image){setDraft({...value,mode:'image'});setDirty(true)}else fileInput.current?.click()}}><WallpaperThumbnail value={{...draft,mode:'image'}} image={image}/><span>{image?'Tu imagen':'Usa tu imagen'}</span><span className="choice-check" aria-hidden="true">✓</span></button>{image&&(prepared||onRemove&&!inherited)&&<button type="button" className="background-remove" aria-label={prepared?'Descartar imagen pendiente':'Quitar fondo personalizado'} title="Quitar esta imagen" onClick={removeImage}>×</button>}</div>
      {onInherit&&<button type="button" className="background-choice" aria-pressed={inherited&&!dirty} onClick={()=>{setPrepared(null);setPreview(null);setDirty(false);onInherit();setNotice('Se usa el fondo principal.')}}><WallpaperThumbnail value={inheritValue??value}/><span>Usar fondo principal</span><span className="choice-check" aria-hidden="true">✓</span></button>}
    </div>
    <label>Elegir imagen PNG, JPEG o WebP<input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" onChange={event=>{const file=event.target.files?.[0];event.target.value='';if(file)void load(file)}}/></label>
    <p className="note">Se prepara una copia de hasta 2560 px y 5 MiB. Puedes ajustar o recortar sin estirar ni modificar el original. Entrada: hasta 25 MiB y 48 megapíxeles.</p>
    {image&&<><div ref={cropArea} className="wallpaper-canvas-wrap" style={{maxWidth:`min(100%, calc(42dvh * ${previewRatio??ratio}))`}}><WallpaperCanvas image={image} value={draft} ratio={previewRatio??ratio} onChange={edit} disabled={busy}/></div>
      <label>Encuadre<select value={draft.fit} onChange={event=>edit({fit:event.target.value as Wallpaper['fit'],mode:'image'})}><option value="cover">Rellenar / recortar bordes</option><option value="contain">Ajustar · mostrar imagen completa</option></select></label>
      <label>Zoom / recorte · {draft.zoom.toFixed(2)}×<input type="range" min={1} max={3} step={.05} value={draft.zoom} onChange={event=>edit({zoom:Number(event.target.value),mode:'image'})}/></label>
      <button type="button" className="secondary" onClick={()=>edit({fit:'cover',x:50,y:50,zoom:1,panX:0,panY:0,rotation:0,mode:'image'})}>Centrar imagen</button>
    </>}
    {image&&<button type="button" disabled={!dirty} onClick={()=>void apply()}>Aplicar fondo</button>}{dirty&&<button type="button" className="secondary" onClick={()=>{setDraft(value);setPrepared(null);setPreview(null);setDirty(false);setError('');setNotice('Ajustes descartados. El fondo guardado se conserva.')}}>Descartar ajustes</button>}</fieldset>
    <p role="status">{busy?'Preparando o guardando fondo…':notice}</p>{error&&<p role="alert">{error}</p>}
  </section>
}
