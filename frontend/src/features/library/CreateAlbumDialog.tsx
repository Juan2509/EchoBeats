import {useEffect,useRef,useState} from 'react'
import {useAppearance} from '../appearance/Appearance'
import defaultCover from '../../shared/assets/default-cover.svg'

export function CreateAlbumDialog({close,created}:{close:()=>void;created:(id:string)=>void}){
  const {appearance,change}=useAppearance(),dialog=useRef<HTMLDialogElement>(null),asset=useRef<string|null>(null)
  const [title,setTitle]=useState(''),[mode,setMode]=useState<'vinyl'|'image'>('vinyl'),[file,setFile]=useState<File|null>(null),[preview,setPreview]=useState<string|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[uncertain,setUncertain]=useState(false)
  useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close()},[])
  useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview)},[preview])
  async function save(){if(busy||!title.trim()||uncertain)return;setBusy(true);setError('');let creating=false
    try{
      if(file&&!asset.current){const body=new FormData();body.append('file',file);body.append('purpose','cover');const response=await fetch('/api/v1/assets',{method:'POST',body,signal:AbortSignal.timeout(25000)}),data=await response.json();if(!response.ok||typeof data.id!=='string')throw Error(data.error?.message??'No se confirmó la portada.');asset.current=data.id}
      creating=true;const response=await fetch('/api/v1/albums',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:title.trim(),artist_names:[],cover_asset_id:asset.current}),signal:AbortSignal.timeout(15000)})
      if(!response.ok){creating=response.status>=500;const data=await response.json();throw Error(data.error?.message??'No se pudo crear el álbum.')}
      const data=await response.json();if(typeof data.id!=='string')throw Error('No se confirmó el álbum.');change({albumPresentations:{...appearance.albumPresentations,[data.id]:mode}});created(data.id)
    }catch(cause){setUncertain(creating);setError(creating?'No se confirmó la creación. Puede haberse completado: revisa la biblioteca antes de crear otro álbum.':cause instanceof Error&&cause.name!=='TimeoutError'?cause.message:'No se pudo subir la imagen. El álbum aún no se ha creado.')}
    finally{setBusy(false)}
  }
  return <dialog ref={dialog} className="album-dialog create-album-dialog" aria-labelledby="create-album-heading" onCancel={event=>{event.preventDefault();if(!busy)close()}}><header><h2 id="create-album-heading">Crear álbum</h2><button disabled={busy} className="secondary" onClick={close}>Cerrar</button></header><p>Un espacio para guardar tus canciones, como una carpeta.</p><form onSubmit={event=>{event.preventDefault();void save()}}><fieldset disabled={busy||uncertain}><label>Nombre del álbum<input required maxLength={255} value={title} onChange={event=>setTitle(event.target.value)} autoFocus/></label><label>Apariencia<select value={mode} onChange={event=>setMode(event.target.value as 'vinyl'|'image')}><option value="vinyl">Vinilo</option><option value="image">Portada</option></select></label><label>Imagen del álbum (opcional)<input type="file" accept="image/png,image/jpeg" onChange={event=>{const selected=event.target.files?.[0];event.target.value='';if(!selected)return;if(selected.size>5*1024*1024){setError('La imagen supera 5 MiB.');return}asset.current=null;setFile(selected);setPreview(URL.createObjectURL(selected));setError('')}}/></label><div className={`collection-art ${mode}`}><img className="cover" src={preview??defaultCover} alt="Vista previa del álbum"/></div>{file&&<button type="button" className="secondary" onClick={()=>{setFile(null);setPreview(null);asset.current=null}}>Quitar imagen</button>}</fieldset>{error&&<p role="alert">{error}</p>}<button disabled={busy||uncertain||!title.trim()}>{busy?'Creando álbum…':'Crear álbum'}</button><p className="note">Después podrás añadir música a este álbum. Vinilo o portada se conserva en este navegador.</p></form></dialog>
}
