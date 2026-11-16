import {useEffect,useState} from 'react'
import type {ReactNode} from 'react'
import type {Album} from '../../shared/api/metadata'
import {readAlbumFolders} from '../library/albumFolders'
import {AppearanceSettings,useAppearance} from './Appearance'
import {presentationFor,backgroundFor} from './theme'
import {WallpaperThumbnail} from './BackgroundEditor'
import defaultCover from '../../shared/assets/default-cover.svg'

const sections=[['principal','Fondo principal','El ambiente de toda tu colección'],['albumes','Álbumes','Elige qué álbum personalizar'],['colores','Colores y estilo','Paneles, acentos y degradados'],['sistema','Conexión y estado','Servidor e integración de IA']] as const
export function SettingsPage({search,navigate,children}:{search:string;navigate:(path:string)=>void;children?:ReactNode}){
  const {appearance,change}=useAppearance(),params=new URLSearchParams(search)
  const section=sections.some(([key])=>key===params.get('seccion'))?params.get('seccion')!:'principal'
  const selected=params.get('album')??''
  const [albums,setAlbums]=useState<Album[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[attempt,retry]=useState(0)
  useEffect(()=>{let active=true;const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),15000)
    setLoading(true);setError('');readAlbumFolders(abort.signal).then(items=>{if(active)setAlbums(items)}).catch(()=>{if(active)setError('No se pudieron cargar tus álbumes. Vuelve a intentarlo.')}).finally(()=>{clearTimeout(timer);if(active)setLoading(false)})
    return()=>{active=false;clearTimeout(timer);abort.abort()}
  },[attempt])
  const album=albums.find(item=>item.id===selected)
  function move(key:string,id?:string){navigate(`/configuracion?${new URLSearchParams({seccion:key,...(id?{album:id}:{})})}`)}
  return <section className="settings-page" aria-labelledby="settings-title"><p className="eyebrow">Hazlo tuyo</p><h1 id="settings-title">Configuración</h1><p className="intro">Elige qué quieres personalizar. El fondo principal y cada álbum tienen su propio espacio.</p><div className="settings-layout"><nav className="settings-navigation" aria-label="Apartados de configuración">{sections.map(([key,title,description])=><a key={key} href={`/configuracion?seccion=${key}`} aria-current={section===key?'page':undefined} onClick={event=>{event.preventDefault();move(key)}}><strong>{title}</strong><span>{description}</span></a>)}</nav><div className="settings-content appearance-settings">
    {section==='principal'&&<div key="principal"><h2>El fondo de tu colección</h2><AppearanceSettings area="background"/></div>}
    {section==='colores'&&<div key="colores"><h2>Colores y estilo</h2><AppearanceSettings area="colors"/></div>}
    {section==='sistema'&&<div><h2>Conexión y estado</h2>{children}</div>}
    {section==='albumes'&&<div><h2>Personalizar un álbum</h2><p>Selecciona el álbum que quieres editar. Estos ajustes no cambian los demás álbumes.</p>{loading?<p role="status">Cargando álbumes…</p>:error?<div role="alert"><p>{error}</p><button onClick={()=>retry(value=>value+1)}>Recargar álbumes</button></div>:!albums.length?<p>No hay álbumes. <a href="/biblioteca" onClick={event=>{event.preventDefault();navigate('/biblioteca')}}>Ve a Biblioteca para crear uno.</a></p>:<><label className="settings-album-select">Álbum que quieres editar<select value={album?.id??''} onChange={event=>move('albumes',event.target.value)}><option value="">Selecciona un álbum</option>{albums.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</select></label>{selected&&!album&&<p role="alert">Ese álbum ya no está disponible. Elige otro.</p>}{album&&<div key={album.id}><div className="settings-album-overview"><div className={`collection-art ${presentationFor(appearance,album.id)}`}><img className="cover" src={album.cover_url??defaultCover} alt={`Portada de ${album.title}`} onError={event=>{event.currentTarget.onerror=null;event.currentTarget.src=defaultCover}}/></div><div><h3>{album.title}</h3><p>{album.track_count} pistas</p><label>Apariencia<select value={presentationFor(appearance,album.id)} onChange={event=>change({albumPresentations:{...appearance.albumPresentations,[album.id]:event.target.value as 'vinyl'|'image'}})}><option value="vinyl">Vinilo</option><option value="image">Portada</option></select></label><a href={`/albumes/${album.id}`} onClick={event=>{event.preventDefault();navigate(`/albumes/${album.id}`)}}>Abrir álbum y editar su pared</a></div></div><div className="settings-current-background"><WallpaperThumbnail value={backgroundFor(appearance,album.id)}/><p>Fondo actual · {appearance.albumBackgrounds[album.id]?'Propio de este álbum':'Usa el fondo principal'}</p></div><AppearanceSettings albumId={album.id} area="background"/></div>}</> }</div>}
  </div></div></section>
}
