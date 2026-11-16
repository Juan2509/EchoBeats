import {useState} from 'react'
export function DeleteTrackButton({id,title,onDeleted=()=>{}}:{id:string;title:string;onDeleted?:()=>void}){
  const [busy,setBusy]=useState(false),[uncertain,setUncertain]=useState(false),[error,setError]=useState('')
  function removed(){window.dispatchEvent(new CustomEvent('echobeats:track-deleted',{detail:id}));onDeleted()}
  async function act(){if(busy)return;setBusy(true);setError('');let sent=false
    try{const current=await fetch(`/api/v1/tracks/${id}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(current.status===404){removed();return}if(!current.ok)throw Error('No se pudo consultar la canción.');const data=await current.json(),etag=current.headers.get('etag');if(!etag||data.id!==id)throw Error('Recarga la canción antes de eliminarla.')
      if(uncertain){setUncertain(false);setError('La canción sigue en la biblioteca. Puedes volver a solicitar su eliminación.');return}
      if(!window.confirm(`¿Eliminar «${data.title??title}» de la biblioteca y sus listas? Se conserva el archivo original y su historial.`))return
      sent=true;const response=await fetch(`/api/v1/tracks/${id}`,{method:'DELETE',headers:{'If-Match':etag},signal:AbortSignal.timeout(15000)});if(!response.ok){if(response.status<500)sent=false;const data=await response.json();throw Error(data.error?.message??'No se pudo eliminar la canción.')}
      const result=await response.json();if(result.track_id!==id||!result.deleted)throw Error('Respuesta no válida.');removed()
    }catch(cause){setUncertain(sent||uncertain);setError(sent?'No se confirmó la eliminación. Comprueba el estado antes de volver a intentarlo.':cause instanceof Error&&!(cause instanceof TypeError)&&cause.name!=='TimeoutError'?cause.message:'No se pudo consultar la canción.')}
    finally{setBusy(false)}
  }
  return <div className="delete-track-control"><button className="secondary danger-button" type="button" disabled={busy} onClick={()=>void act()}>{busy?'Comprobando…':uncertain?'Comprobar eliminación':'Eliminar canción de la biblioteca'}</button>{error&&<p role="alert">{error}</p>}</div>
}
