import test from 'node:test'
import assert from 'node:assert/strict'
import {readAlbumTracks} from '../src/features/library/albumTracks.ts'
const track=(id:number,album='album')=>({id:String(id),album_id:album,title:`Pista ${id}`,revision:1})
test('selector obtiene todas las pistas, más allá de la página visible y del límite de 100',async()=>{
  const calls:URL[]=[],all=Array.from({length:205},(_,i)=>track(i))
  const fetcher:typeof fetch=async(input,options)=>{const url=new URL(String(input),'http://local');calls.push(url);assert.equal(options?.method,undefined);assert.equal(url.searchParams.get('album_id'),'album');assert.equal(url.searchParams.get('limit'),'100');const offset=Number(url.searchParams.get('offset'));return new Response(JSON.stringify({items:all.slice(offset,offset+100),total:205,offset}))}
  const items=await readAlbumTracks('album',new AbortController().signal,fetcher);assert.equal(items.length,205);assert.equal(items[204].title,'Pista 204');assert.deepEqual(calls.map(url=>url.searchParams.get('offset')),['0','100','200'])
})
test('listado rechaza pistas ajenas, duplicados, cambios de colección y cortes incompletos',async()=>{
  for(const items of [[track(1,'otro')],[track(1),track(1)]])await assert.rejects(()=>readAlbumTracks('album',new AbortController().signal,async()=>new Response(JSON.stringify({items,total:items.length,offset:0}))))
  let n=0;await assert.rejects(()=>readAlbumTracks('album',new AbortController().signal,async()=>new Response(JSON.stringify(++n===1?{items:[track(1)],total:2,offset:0}:{items:[track(2)],total:3,offset:1}))))
  await assert.rejects(()=>readAlbumTracks('album',new AbortController().signal,async()=>new Response(JSON.stringify({items:[],total:1,offset:0}))))
})
test('cancelar impide continuar paginación y un álbum vacío devuelve selección vacía',async()=>{
  const abort=new AbortController();abort.abort();let calls=0;await assert.rejects(()=>readAlbumTracks('album',abort.signal,async()=>{calls++;return new Response('{}')}));assert.equal(calls,0)
  assert.deepEqual(await readAlbumTracks('album',new AbortController().signal,async()=>new Response(JSON.stringify({items:[],total:0,offset:0}))),[])
})
