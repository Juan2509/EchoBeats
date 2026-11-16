import {useEffect,useState} from 'react'
import type {Track} from '../../shared/api/metadata'
import {readAlbumTracks} from './albumTracks'
import {DescriptionEditor} from '../descriptions/DescriptionEditor'
import {ProcessingPanel} from '../processing/ProcessingPanel'
import {DeleteTrackButton} from './DeleteTrackButton'

export function AlbumTrackTools({albumId,refresh,navigate}:{albumId:string;refresh:number;navigate:(path:string)=>void}){
  const [open,setOpen]=useState(false)
  return <details className="album-track-tools" onToggle={event=>setOpen(event.currentTarget.open)}><summary>Fichas y opciones del álbum</summary>{open&&<TrackTools albumId={albumId} refresh={refresh} navigate={navigate}/>}</details>
}
function TrackTools({albumId,refresh,navigate}:{albumId:string;refresh:number;navigate:(path:string)=>void}){
  const [tracks,setTracks]=useState<Track[]>([]),[selectedId,setSelectedId]=useState(''),[loading,setLoading]=useState(true),[error,setError]=useState(''),[attempt,retry]=useState(0)
  useEffect(()=>{const abort=new AbortController();let active=true;setLoading(true);setError('');const timeout=setTimeout(()=>abort.abort(),15000)
    readAlbumTracks(albumId,abort.signal).then(items=>{if(active){setTracks(items);setSelectedId(current=>items.some(item=>item.id===current)?current:items[0]?.id??'')}}).catch(cause=>{if(active)setError(cause instanceof Error&&!(cause instanceof TypeError)&&!(cause instanceof SyntaxError)&&cause.name!=='AbortError'?cause.message:'No se pudieron cargar las pistas. Comprueba la conexión y vuelve a intentarlo.')}).finally(()=>{clearTimeout(timeout);if(active)setLoading(false)})
    return()=>{active=false;clearTimeout(timeout);abort.abort()}
  },[albumId,refresh,attempt])
  const selected=tracks.find(track=>track.id===selectedId)
  return <div className="album-track-tools-content">{loading?<p role="status">Cargando todas las pistas…</p>:error?<div role="alert"><p>{error}</p><button onClick={()=>retry(value=>value+1)}>Volver a cargar pistas</button></div>:!tracks.length?<p>No hay pistas para editar.</p>:<><label>Pista que quieres editar<select value={selectedId} onChange={event=>setSelectedId(event.target.value)}>{tracks.map((track,index)=><option key={track.id} value={track.id}>{track.track_number??index+1}. {track.title}</option>)}</select></label>{selected&&<div key={selected.id} className="album-track-actions"><DescriptionEditor trackId={selected.id} title={selected.title} label="Editar descripción musical"/><ProcessingPanel key={`${selected.id}-${selected.revision}`} trackId={selected.id} revision={selected.revision}/><a href={`/explorar?similar=${selected.id}`} onClick={event=>{event.preventDefault();navigate(`/explorar?similar=${selected.id}`)}}>Buscar similares</a><DeleteTrackButton id={selected.id} title={selected.title}/></div>}</>}</div>
}
