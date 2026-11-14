import test from 'node:test'
import assert from 'node:assert/strict'
import { ExploreController,decode,requestSearch } from '../src/features/explore/controller.ts'
import type { SearchInput,SearchResponse } from '../src/features/explore/controller.ts'
const input:SearchInput={query:'tono',mode:'lexical',limit:5,explain:false}
const response=():SearchResponse=>({status:'ok',query:'tono',mode:'lexical',warnings:[],results:[{
  track:{id:'a',title:'Pista',artists:[],album_id:'album',album_title:'Álbum',audio_url:'/api/v1/tracks/a/audio',duration_ms:12000,cover_url:null,cover_asset_id:null,track_number:null,cover_source:'fallback',metadata_sources:{},revision:1},
  description:{id:'ficha',version:1,text:'Tono sin voces.',source:'verified',source_details:'Generador',features:[]},
  evidence:[{source_id:'ficha',version:1,field:'text',quote:'sin voces'}],explanation_source:'recorded'}]})
function deferred<T>(){let resolve!:(v:T)=>void;const promise=new Promise<T>(yes=>{resolve=yes});return{resolve,promise}}

test('abrir no consulta; solicitud explícita y respuesta vieja no reemplaza nueva',async()=>{
  const first=deferred<SearchResponse>();let calls=0
  const c=new ExploreController(async()=>++calls===1?first.promise:response())
  assert.equal(calls,0)
  const old=c.search(input);await c.search({...input,query:'nueva'})
  first.resolve({...response(),query:'vieja'});await old
  assert.equal(c.state.request?.query,'nueva');assert.equal(c.state.data?.query,'tono');c.dispose()
})

test('cancelar o salir ignora respuestas tardías y no reintenta',async()=>{
  const pending=deferred<SearchResponse>();let calls=0
  const c=new ExploreController(async()=>{calls++;return pending.promise})
  const job=c.search(input);c.cancel();pending.resolve(response());await job
  assert.equal(c.state.data,null);assert.equal(c.state.loading,false);assert.equal(calls,1)
  c.dispose();await c.search(input);assert.equal(calls,1)
})

test('fallo conserva consulta, elimina resultados previos y no fabrica éxito vacío',async()=>{
  let fail=false
  const c=new ExploreController(async()=>{if(fail)throw new TypeError('network');return response()})
  await c.search(input);fail=true;await c.search({...input,query:'otra'})
  assert.equal(c.state.data,null);assert.equal(c.state.request?.query,'otra');assert.match(c.state.error,/confirmar/);c.dispose()
})

test('rechaza citas ajenas, pistas duplicadas y audio externo',()=>{
  const foreign=response();foreign.results[0].evidence[0].version=2;assert.throws(()=>decode(foreign))
  const duplicate=response();duplicate.results.push(duplicate.results[0]);assert.throws(()=>decode(duplicate))
  const external=response();external.results[0].track.audio_url='https://example.com/audio';assert.throws(()=>decode(external))
})

test('gateway distingue referencia de consulta y selección IA es explícita',async()=>{
  const original=globalThis.fetch;let calls=0
  globalThis.fetch=async(url,options)=>{
    calls++;const body=JSON.parse(options?.body as string)
    if(calls===1){assert.equal(url,'/api/v1/explore/search');assert.equal(body.explain,false);assert.equal(body.query,'tono')}
    else{assert.equal(url,'/api/v1/explore/similar');assert.equal(body.track_id,'a');assert.equal(body.explain,true);assert.equal('query' in body,false)}
    return new Response(JSON.stringify(response()))
  }
  try{await requestSearch(input,new AbortController().signal);await requestSearch({...input,track_id:'a',explain:true},new AbortController().signal)}finally{globalThis.fetch=original}
})

function preferenceResponse(): SearchResponse {
  const first=response().results[0]
  const second=structuredClone(first);second.track.id='b';second.track.audio_url='/api/v1/tracks/b/audio'
  return {...response(),results:[
    {...second,preference:{favorite:true,base_rank:2,rank:1,reason:'Favorito explícito: sube una posición.'}},
    {...first,preference:{favorite:false,base_rank:1,rank:2,reason:'Cede una posición.'}},
  ],preferences:{mode:'favorites',policy:'adjacent_pairs_v1',baseline_order:['a','b'],result_order:['b','a'],reordered:true}}
}

test('comparación de preferencias conserva orden base y señal explícita sin consultar otra vez',async()=>{
  let calls=0
  const controller=new ExploreController(async request=>{calls++;assert.equal(request.preferences,'favorites');return preferenceResponse()})
  await controller.search({...input,preferences:'favorites'})
  const data=controller.state.data!
  assert.deepEqual(data.preferences?.baseline_order,['a','b']);assert.deepEqual(data.results.map(item=>item.track.id),['b','a'])
  assert.deepEqual([...data.results].sort((a,b)=>a.preference!.base_rank-b.preference!.base_rank).map(item=>item.track.id),['a','b'])
  assert.equal(calls,1);controller.dispose()
})

test('rechaza comparación ajena, cambio de orden oculto o descubrimiento que conserva favoritos',()=>{
  for(const modify of [
    (data:SearchResponse)=>{data.preferences!.baseline_order=['a','ajena']},
    (data:SearchResponse)=>{data.preferences!.reordered=false},
    (data:SearchResponse)=>{data.results[0].preference!.base_rank=3},
    (data:SearchResponse)=>{data.preferences!.mode='off'},
    (data:SearchResponse)=>{data.preferences!.mode='discovery'},
    (data:SearchResponse)=>{delete data.preferences},
  ]){const data=preferenceResponse();modify(data);assert.throws(()=>decode(data))}
  assert.doesNotThrow(()=>decode(preferenceResponse()))
})

test('gateway envía preferencias explícitas para consulta y referencia, desactivadas por defecto',async()=>{
  const previous=globalThis.fetch;const sent:{preferences:string;track_id?:string}[]=[]
  globalThis.fetch=async(_url,options)=>{sent.push(JSON.parse(options?.body as string));return new Response(JSON.stringify(response()))}
  try{
    await requestSearch(input,new AbortController().signal)
    await requestSearch({...input,preferences:'favorites'},new AbortController().signal)
    await requestSearch({...input,track_id:'a',preferences:'discovery'},new AbortController().signal)
    assert.deepEqual(sent.map(body=>body.preferences),['off','favorites','discovery'])
    assert.equal(sent[2].track_id,'a')
  }finally{globalThis.fetch=previous}
})
