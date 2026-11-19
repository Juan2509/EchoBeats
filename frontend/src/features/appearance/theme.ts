export const sceneNames = {
  synthwave: 'Synthwave',
  city: 'Ciudad al atardecer',
  aurora: 'Aurora boreal',
  winter: 'Bosque nevado',
  rain: 'Noche de lluvia',
} as const
export type SceneMode = keyof typeof sceneNames
export type Wallpaper = { mode:SceneMode|'image'; image:string|null; fit:'cover'|'contain'; x:number; y:number; zoom:number;panX:number;panY:number;rotation:number }
export type StickerOutline={color:string;thickness:number}
export const defaultStickerOutline:StickerOutline={color:'#FFFFFF',thickness:2}
export type Appearance = {
  version:1; skyTop:string; skyBottom:string; panelTop:string; panelBottom:string; pink:string; cyan:string;
  animateBackgrounds:boolean; grid:boolean; wallSurface:'scene'|'album'; background:Wallpaper;
  albumBackgrounds:Record<string,Wallpaper>; wallBackgrounds:Record<string,Wallpaper>; wallSurfaces:Record<string,'scene'|'album'|'image'>;
  albumPresentation:'vinyl'|'image'; albumPresentations:Record<string,'vinyl'|'image'>;
  stickerOutlines:Record<string,StickerOutline>;
}
export const STORAGE_KEY='echobeats.appearance.v1'
export const baseWallpaper:Wallpaper={mode:'synthwave',image:null,fit:'cover',x:50,y:50,zoom:1,panX:0,panY:0,rotation:0}
export const defaults:Appearance={version:1,skyTop:'#090C20',skyBottom:'#251039',panelTop:'#12182E',panelBottom:'#351431',pink:'#F16BC7',cyan:'#6EE7F2',animateBackgrounds:true,grid:true,wallSurface:'scene',background:{...baseWallpaper},albumBackgrounds:{},wallBackgrounds:{},wallSurfaces:{},albumPresentation:'vinyl',albumPresentations:{},stickerOutlines:{}}
export const presets:Record<string,Partial<Appearance>>={
  'Colores originales':{skyTop:defaults.skyTop,skyBottom:defaults.skyBottom,panelTop:defaults.panelTop,panelBottom:defaults.panelBottom,pink:defaults.pink,cyan:defaults.cyan},
  'Atardecer':{skyTop:'#170F2B',skyBottom:'#54223F',panelTop:'#261734',panelBottom:'#4C2044',pink:'#FF8CCF',cyan:'#83DBFF'},
  'Índigo':{skyTop:'#090F26',skyBottom:'#162752',panelTop:'#111A35',panelBottom:'#24254E',pink:'#B9A0FF',cyan:'#71DFFF'},
  'Bosque':{skyTop:'#101812',skyBottom:'#19362F',panelTop:'#17271F',panelBottom:'#24453D',pink:'#C9DA9B',cyan:'#8EDBCC'},
}
const uuid=/^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i
const color=(value:unknown,fallback:string)=>typeof value==='string'&&/^#[\da-f]{6}$/i.test(value)?value.toUpperCase():fallback
export const assetUrl=(value:unknown):value is string=>typeof value==='string'&&/^\/api\/v1\/assets\/[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}\/content$/i.test(value)
const number=(value:unknown,fallback:number,min:number,max:number)=>typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max?value:fallback
export function decodeWallpaper(value:unknown):Wallpaper{
  const b=(value&&typeof value==='object'?value:{}) as Wallpaper
  const image=assetUrl(b.image)?b.image:null
  return {mode:b.mode==='image'&&image?'image':Object.hasOwn(sceneNames,b.mode)?b.mode as SceneMode:'synthwave',image,fit:b.fit==='contain'?'contain':'cover',x:number(b.x,50,0,100),y:number(b.y,50,0,100),zoom:number(b.zoom,1,1,3),panX:number(b.panX,0,-1,1),panY:number(b.panY,0,-1,1),rotation:number(b.rotation,0,-180,180)}
}
export function decodeAppearance(value:unknown):Appearance{
  if(!value||typeof value!=='object'||(value as Appearance).version!==1)return structuredClone(defaults)
  const d=value as Appearance & {backgroundImage?:unknown}
  const backgrounds:Record<string,Wallpaper>={},walls:Record<string,Wallpaper>={},surfaces:Appearance['wallSurfaces']={},presentations:Appearance['albumPresentations']={}
  const outlines:Appearance['stickerOutlines']={}
  if(d.stickerOutlines&&typeof d.stickerOutlines==='object')for(const [key,value] of Object.entries(d.stickerOutlines).slice(0,3000)){const ids=key.split(':');if(ids.length===2&&ids.every(id=>uuid.test(id)))outlines[key]=decodeStickerOutline(value)}
  if(d.albumBackgrounds&&typeof d.albumBackgrounds==='object')for(const [id,b] of Object.entries(d.albumBackgrounds).slice(0,2000))if(uuid.test(id))backgrounds[id]=decodeWallpaper(b)
  if(d.wallBackgrounds&&typeof d.wallBackgrounds==='object')for(const [id,b] of Object.entries(d.wallBackgrounds).slice(0,2000))if(uuid.test(id)){const w=decodeWallpaper(b);if(w.image)walls[id]=w}
  if(d.wallSurfaces&&typeof d.wallSurfaces==='object')for(const [id,s] of Object.entries(d.wallSurfaces).slice(0,2000))if(uuid.test(id)&&(s==='scene'||s==='album'||s==='image'&&walls[id]))surfaces[id]=s
  if(d.albumPresentations&&typeof d.albumPresentations==='object')for(const [id,p] of Object.entries(d.albumPresentations).slice(0,2000))if(uuid.test(id)&&(p==='vinyl'||p==='image'))presentations[id]=p
  const migrated=d.background??{...baseWallpaper,mode:assetUrl(d.backgroundImage)?'image':'synthwave',image:d.backgroundImage}
  return {version:1,skyTop:color(d.skyTop,defaults.skyTop),skyBottom:color(d.skyBottom,defaults.skyBottom),panelTop:color(d.panelTop,defaults.panelTop),panelBottom:color(d.panelBottom,defaults.panelBottom),pink:color(d.pink,defaults.pink),cyan:color(d.cyan,defaults.cyan),animateBackgrounds:typeof d.animateBackgrounds==='boolean'?d.animateBackgrounds:true,grid:typeof d.grid==='boolean'?d.grid:true,wallSurface:d.wallSurface==='album'?'album':'scene',background:decodeWallpaper(migrated),albumBackgrounds:backgrounds,wallBackgrounds:walls,wallSurfaces:surfaces,albumPresentation:d.albumPresentation==='image'?'image':'vinyl',albumPresentations:presentations,stickerOutlines:outlines}
}
export function decodeStickerOutline(value:unknown):StickerOutline{const d=(value&&typeof value==='object'?value:{}) as StickerOutline;return {color:color(d.color,defaultStickerOutline.color),thickness:number(d.thickness,2,0,12)}}
export function stickerOutlineFor(a:Appearance,albumId:string,itemId:string):StickerOutline{return a.stickerOutlines[`${albumId}:${itemId}`]??defaultStickerOutline}
export function changeStickerOutline(a:Appearance,albumId:string,itemId:string,value:Partial<StickerOutline>):Appearance{return decodeAppearance({...a,stickerOutlines:{...a.stickerOutlines,[`${albumId}:${itemId}`]:{...stickerOutlineFor(a,albumId,itemId),...value}}})}
export function backgroundFor(a:Appearance,albumId?:string):Wallpaper{return albumId&&a.albumBackgrounds[albumId]?a.albumBackgrounds[albumId]:a.background}
export function wallSurfaceFor(a:Appearance,albumId:string){return a.wallSurfaces[albumId]??a.wallSurface}
export function presentationFor(a:Appearance,albumId:string){return a.albumPresentations[albumId]??a.albumPresentation}
export function replaceWallBackground(a:Appearance,albumId:string,value:Wallpaper){return decodeAppearance({...a,wallBackgrounds:{...a.wallBackgrounds,[albumId]:{...value,mode:'image'}},wallSurfaces:{...a.wallSurfaces,[albumId]:'image'}})}
export function removeCustomBackground(a:Appearance,scope:'main'|'album'|'wall',id?:string):Appearance{
  if(scope==='wall'&&id){const walls={...a.wallBackgrounds};delete walls[id];return decodeAppearance({...a,wallBackgrounds:walls,wallSurfaces:{...a.wallSurfaces,[id]:a.wallSurfaces[id]==='image'?'scene':a.wallSurfaces[id]}})}
  const current=scope==='album'&&id?a.albumBackgrounds[id]:scope==='main'?a.background:undefined
  if(!current)return a
  return replaceBackground(a,scope==='album'?id:undefined,{...current,image:null,mode:current.mode==='image'?'synthwave':current.mode})
}
export function replaceBackground(a:Appearance,albumId:string|undefined,value:Wallpaper|null):Appearance{
  if(!albumId)return decodeAppearance({...a,background:value??baseWallpaper})
  const backgrounds={...a.albumBackgrounds};if(value)backgrounds[albumId]=value;else delete backgrounds[albumId]
  return decodeAppearance({...a,albumBackgrounds:backgrounds})
}
export function cssVariables(theme:Appearance,albumId?:string){
  const a=decodeAppearance(theme),b=backgroundFor(a,albumId)
  const skyTop = a.skyTop === defaults.skyTop ? undefined : a.skyTop
  const skyBottom = a.skyBottom === defaults.skyBottom ? undefined : a.skyBottom
  return {
    '--sky-top': a.skyTop,
    '--sky-bottom': a.skyBottom,
    '--synth-top': a.skyTop, '--synth-bottom': a.skyBottom,
    '--city-top': skyTop ?? '#8B5A95', '--city-bottom': skyBottom ?? '#F2A983',
    '--aurora-top': skyTop ?? '#071837', '--aurora-bottom': skyBottom ?? '#102957',
    '--winter-top': skyTop ?? '#182653', '--winter-bottom': skyBottom ?? '#D4A5C6',
    '--rain-top': skyTop ?? '#08234A', '--rain-bottom': skyBottom ?? '#247DAD',
    '--landscape-tint-top': skyTop ?? 'transparent', '--landscape-tint-bottom': skyBottom ?? 'transparent',
    '--panel-top': a.panelTop, '--panel-bottom': a.panelBottom,
    '--neon-pink': a.pink, '--neon-cyan': a.cyan, '--scene-image': 'none',
    '--grid-opacity': a.grid && b.mode === 'synthwave' ? '1' : '0',
  }
}
