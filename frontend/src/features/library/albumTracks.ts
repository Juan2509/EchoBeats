import type {Track} from '../../shared/api/metadata'

/** Lee todas las páginas solo al abrir las herramientas; no descarga audio. */
export async function readAlbumTracks(albumId:string,signal:AbortSignal,fetcher:typeof fetch=fetch):Promise<Track[]>{
  const tracks:Track[]=[],ids=new Set<string>();let total:number|undefined
  do{
    signal.throwIfAborted()
    const response=await fetcher(`/api/v1/tracks?${new URLSearchParams({album_id:albumId,limit:'100',offset:String(tracks.length)})}`,{signal,cache:'no-store'})
    const page=await response.json();signal.throwIfAborted()
    if(!response.ok)throw new Error(typeof page.error?.message==='string'?page.error.message:'No se pudieron cargar las pistas del álbum.')
    if(!Array.isArray(page.items)||!Number.isSafeInteger(page.total)||page.total<0||page.offset!==tracks.length||page.items.length>100||total!==undefined&&page.total!==total)throw new Error('La lista de pistas cambió o no es válida. Vuelve a cargarla.')
    total=Number(page.total)
    for(const track of page.items){if(!track||typeof track.id!=='string'||track.album_id!==albumId||typeof track.title!=='string'||!Number.isInteger(track.revision)||track.revision<1||ids.has(track.id))throw new Error('La lista de pistas cambió o no es válida. Vuelve a cargarla.');ids.add(track.id);tracks.push(track)}
    if(tracks.length>total||!page.items.length&&tracks.length<total)throw new Error('La lista de pistas cambió. Vuelve a cargarla.')
  }while(tracks.length<total)
  return tracks
}
