import test from 'node:test'
import assert from 'node:assert/strict'
import {readAlbumFolders} from '../src/features/library/albumFolders.ts'
test('destinos incluyen todos los álbumes paginados y excluyen el álbum de sistema',async()=>{
  const albums=Array.from({length:102},(_,i)=>({id:String(i),title:'Álbum '+i,system_key:i===0?'unknown':null})),calls:string[]=[]
  const result=await readAlbumFolders(new AbortController().signal,async(input)=>{calls.push(String(input));const offset=Number(new URL(String(input),'http://local').searchParams.get('offset'));return new Response(JSON.stringify({items:albums.slice(offset,offset+100),total:102,offset}))});assert.equal(result.length,101);assert.equal(calls.length,2);assert.equal(result[100].id,'101')
})
test('destinos no aceptan listado incompleto ni continúan tras cancelar',async()=>{
  await assert.rejects(()=>readAlbumFolders(new AbortController().signal,async()=>new Response(JSON.stringify({items:[],total:2,offset:0}))))
  const abort=new AbortController();abort.abort();let called=false;await assert.rejects(()=>readAlbumFolders(abort.signal,async()=>{called=true;return new Response('{}')}));assert.equal(called,false)
})
