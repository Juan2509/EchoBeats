import {useEffect,useId,useRef,useState} from 'react'
import type {Track} from '../../shared/api/metadata'
import {readAlbumTracks} from './albumTracks'

export function DeleteAlbumTracks({albumId}:{albumId:string}){
  const [open,setOpen]=useState(false)
  return <div className="album-delete-tracks"><button type="button" className="secondary danger-button" onClick={()=>setOpen(true)}>Eliminar pistas</button>{open&&<TrackSelection albumId={albumId} close={()=>setOpen(false)}/>}</div>
}
function TrackSelection({albumId,close:finish}:{albumId:string;close:()=>void}){
  const dialog=useRef<HTMLDialogElement>(null),heading=useId()
  const changed=useRef(false)
  function close(){finish();if(changed.current)window.dispatchEvent(new Event('echobeats:library-changed'))}
  const [tracks,setTracks]=useState<Track[]>([]),[chosen,setChosen]=useState<Set<string>>(new Set()),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[uncertain,setUncertain]=useState<string|null>(null),[attempt,retry]=useState(0)
  useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close()},[])
  useEffect(()=>{let active=true;const abort=new AbortController(),timeout=setTimeout(()=>abort.abort(),15000);setLoading(true);setError('')
    readAlbumTracks(albumId,abort.signal).then(items=>{if(active&&!abort.signal.aborted){setTracks(items);setChosen(new Set());setError('')}}).catch(()=>{if(active)setError(abort.signal.aborted?'La carga tardó demasiado. Vuelve a intentarlo.':'No se pudieron cargar las pistas. Vuelve a intentarlo.')}).finally(()=>{clearTimeout(timeout);if(active)setLoading(false)})
    return()=>{active=false;clearTimeout(timeout);abort.abort()}
  },[albumId,attempt])
  function removed(id:string){changed.current=true;setTracks(current=>current.filter(track=>track.id!==id));setChosen(current=>new Set([...current].filter(value=>value!==id)));window.dispatchEvent(new CustomEvent('echobeats:track-retired',{detail:id}))}
  async function erase(){if(busy||loading||uncertain||!chosen.size)return;setBusy(true);setError('');setNotice('');let sent:string|null=null,count=0
    try{for(const track of tracks.filter(track=>chosen.has(track.id))){
      const url=`/api/v1/tracks/${track.id}`,current=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(15000)})
      if(current.status===404){removed(track.id);continue}
      if(!current.ok)throw Error('No se pudo consultar la pista. No se continuó con las restantes.')
      const data=await current.json(),etag=current.headers.get('etag')
      if(!etag||data.id!==track.id||data.revision!==track.revision||data.album_id!==albumId)throw Error('Una pista cambió. Cierra y vuelve a abrir esta ventana para revisar la selección.')
      sent=track.id;const response=await fetch(url,{method:'DELETE',headers:{'If-Match':etag},signal:AbortSignal.timeout(15000)})
      if(!response.ok){if(response.status<500)sent=null;throw Error('No se pudo confirmar la eliminación. Se detuvo el resto de la selección.')}
      const result=await response.json();if(result.track_id!==track.id||!result.deleted)throw Error('Respuesta no válida.')
      sent=null;removed(track.id);count++
    }}catch(cause){if(sent)setUncertain(sent);setError(sent?'Respuesta incierta. Comprueba esa pista antes de continuar; no se repetirá la eliminación automáticamente.':cause instanceof Error?cause.message:'No se pudo completar la eliminación.')}
    finally{setBusy(false);setNotice(`${count} pistas eliminadas en esta operación.`)}
  }
  async function check(){if(!uncertain||busy)return;setBusy(true);setError('');try{const response=await fetch(`/api/v1/tracks/${uncertain}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(response.status===404){removed(uncertain);setUncertain(null);setNotice('La pista ya fue eliminada.')}else if(response.ok){setUncertain(null);setNotice('La pista sigue en la biblioteca. Puedes revisar y confirmar otra vez.')}else throw Error()}catch{setError('No se pudo comprobar el estado. Vuelve a comprobar antes de continuar.')}finally{setBusy(false)}}
  return <dialog ref={dialog} className="album-dialog deletion-dialog track-selection-dialog" aria-labelledby={heading} onCancel={event=>{event.preventDefault();if(!busy)close()}}><header><h2 id={heading}>Eliminar pistas</h2><button type="button" className="secondary" disabled={busy} onClick={close}>Cerrar</button></header><p>Selecciona las pistas que quieres retirar de la biblioteca y sus listas. Se conservarán los archivos originales y el historial.</p>{loading?<p role="status">Cargando pistas…</p>:<><fieldset disabled={busy||!!uncertain}><legend>Pistas de este álbum</legend>{tracks.length>0&&<button type="button" className="secondary" onClick={()=>setChosen(chosen.size===tracks.length?new Set():new Set(tracks.map(track=>track.id)))}>{chosen.size===tracks.length?'Deseleccionar todas':'Seleccionar todas'}</button>}<div className="delete-track-options">{tracks.map(track=><label key={track.id}><input type="checkbox" checked={chosen.has(track.id)} onChange={event=>setChosen(current=>{const next=new Set(current);event.target.checked?next.add(track.id):next.delete(track.id);return next})}/><span>{track.title}<small>{track.artists.map(artist=>artist.name).join(', ')}</small></span></label>)}</div>{!tracks.length&&<p>No hay pistas para eliminar.</p>}</fieldset><p role="status">{chosen.size} seleccionadas. {notice}</p></>}{error&&<p role="alert">{error}</p>}{!loading&&!tracks.length&&error&&<button disabled={busy} onClick={()=>retry(value=>value+1)}>Recargar pistas</button>}<div className="editor-actions"><button className="secondary" disabled={busy} onClick={close}>Cancelar</button>{uncertain?<button disabled={busy} onClick={()=>void check()}>Comprobar eliminación</button>:<button className="danger-button" disabled={busy||loading||!chosen.size} onClick={()=>void erase()}>{busy?'Eliminando…':`Eliminar seleccionadas (${chosen.size})`}</button>}</div></dialog>
}
