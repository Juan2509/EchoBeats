import {useState} from 'react'
import {ConfirmDialog} from './ConfirmDialog'
type DeleteProps={id:string;title:string;onDeleted?:()=>void}
export function DeleteTrackButton(props:DeleteProps){return <DeleteCatalogButton {...props} kind="tracks"/>}
export function DeleteAlbumButton(props:DeleteProps){return <DeleteCatalogButton {...props} kind="albums"/>}
function DeleteCatalogButton({id,title,onDeleted=()=>{},kind}:{id:string;title:string;onDeleted?:()=>void;kind:'tracks'|'albums'}){
  const album=kind==='albums',url=`/api/v1/${kind}/${id}`
  const [confirmation,setConfirmation]=useState<{message:string;resolve:(confirmed:boolean)=>void}|null>(null)
  const [busy,setBusy]=useState(false),[uncertain,setUncertain]=useState(false),[error,setError]=useState('')
  function removed(ids:string[]=[]){if(album){window.dispatchEvent(new CustomEvent('echobeats:album-deleted',{detail:id}));for(const trackId of ids)window.dispatchEvent(new CustomEvent('echobeats:track-deleted',{detail:trackId}));window.dispatchEvent(new Event('echobeats:library-changed'))}else window.dispatchEvent(new CustomEvent('echobeats:track-deleted',{detail:id}));onDeleted()}
  async function act(){if(busy)return;setBusy(true);setError('');let sent=false
    try{const current=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(current.status===404){removed();return}if(!current.ok)throw Error('No se pudo consultar el elemento.');const data=await current.json(),etag=current.headers.get('etag');if(!etag||data.id!==id)throw Error('Recarga los datos antes de eliminar.')
      if(uncertain){setUncertain(false);setError('El elemento sigue en la biblioteca. Puedes volver a solicitar su eliminación.');return}
      const confirmed=await new Promise<boolean>(resolve=>setConfirmation({resolve,message:album?`¿Eliminar el álbum «${data.title??title}», todas sus canciones y su muro? Las canciones se retirarán también de las listas. Se conservan los archivos originales y el historial musical.`:`¿Eliminar «${data.title??title}» de la biblioteca y sus listas? Se conserva el archivo original y su historial.`}))
      if(!confirmed)return
      sent=true;const response=await fetch(url,{method:'DELETE',headers:{'If-Match':etag},signal:AbortSignal.timeout(15000)});if(!response.ok){if(response.status<500)sent=false;const data=await response.json();throw Error(data.error?.message??'No se pudo eliminar el elemento.')}
      const result=await response.json();if(result[album?'album_id':'track_id']!==id||!result.deleted||album&&(!Array.isArray(result.track_ids)||!result.track_ids.every((value:unknown)=>typeof value==='string')))throw Error('Respuesta no válida.');removed(album?result.track_ids:[])
    }catch(cause){setUncertain(sent||uncertain);setError(sent?'No se confirmó la eliminación. Comprueba el estado antes de volver a intentarlo.':cause instanceof Error&&!(cause instanceof TypeError)&&cause.name!=='TimeoutError'?cause.message:'No se pudo consultar el elemento.')}
    finally{setBusy(false)}
  }
  return <div className="delete-track-control"><button className="secondary danger-button" type="button" disabled={busy} onClick={()=>void act()}>{busy?'Comprobando…':uncertain?'Comprobar eliminación':album?'Eliminar álbum':'Eliminar canción de la biblioteca'}</button>{error&&<p role="alert">{error}</p>}{confirmation&&<ConfirmDialog message={confirmation.message} answer={confirmed=>{setConfirmation(null);confirmation.resolve(confirmed)}}/>}</div>
}
