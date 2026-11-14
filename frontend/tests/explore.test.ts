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
