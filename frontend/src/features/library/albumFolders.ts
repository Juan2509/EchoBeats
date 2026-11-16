import type {Album} from '../../shared/api/metadata'
export async function readAlbumFolders(signal:AbortSignal,fetcher:typeof fetch=fetch):Promise<Album[]>{
  const rows:Album[]=[],ids=new Set<string>();let total=0
  do{signal.throwIfAborted();const response=await fetcher(`/api/v1/albums?limit=100&offset=${rows.length}&include_empty_system=false`,{signal,cache:'no-store'});const page=await response.json();signal.throwIfAborted();if(!response.ok)throw new Error('No se pudieron cargar los álbumes.')
    if(!Array.isArray(page.items)||!Number.isSafeInteger(page.total)||page.total<0||page.offset!==rows.length||page.items.length>100||!page.items.length&&rows.length<page.total)throw new Error('La lista de álbumes cambió. Vuelve a cargarla.')
    total=Number(page.total);for(const item of page.items){if(typeof item.id!=='string'||typeof item.title!=='string'||ids.has(item.id))throw new Error('Lista de álbumes no válida.');ids.add(item.id);rows.push(item)}
  }while(rows.length<total)
  return rows.filter(item=>!item.system_key)
}
