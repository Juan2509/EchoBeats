import test from 'node:test'
import assert from 'node:assert/strict'
import { DescriptionController, DescriptionError, blank, requestDescription } from '../src/features/descriptions/controller.ts'
import type { Description, Gateway } from '../src/features/descriptions/controller.ts'
const record = (id='a'): Description => ({ ...blank(), id: 'description', track_id: id, version: 1, text: 'Sintetizador documentado', source_details: 'Generador', can_index: true, index_notice: 'Sin embedding' })
function deferred<T>() { let resolve!: (value:T)=>void; const promise=new Promise<T>(yes=>{resolve=yes});return {resolve,promise} }
test('edición, guardado y fallo conservan borrador y bloquean reintentos inciertos', async () => {
  const c=new DescriptionController('a',async (_id,_signal,write)=>{if(write)throw new DescriptionError('Conflicto',412);return {record:record(),etag:'1'}})
  await c.load();c.edit({...c.state.draft,text:'Corregido'});await c.save()
  assert.equal(c.state.draft.text,'Corregido');assert.equal(c.dirty,true);assert.equal(c.state.needsReload,true)
  c.edit({...c.state.draft,text:'No permitido'});assert.equal(c.state.draft.text,'Corregido');await c.load();assert.equal(c.dirty,false);c.dispose()
})
test('guardado bloquea cambios, conserva solo payload y no acepta respuesta de otro controlador', async () => {
  const pending=deferred<{record:Description;etag:string}>();let calls=0
  const gateway:Gateway=async(_id,_signal,write)=>{if(write){calls++;assert.equal('version' in write.body,false);return pending.promise}return {record:record(),etag:'1'}}
  const a=new DescriptionController('a',gateway);await a.load();a.edit({...a.state.draft,text:'Nuevo'});const saving=a.save();a.edit({...a.state.draft,text:'Durante guardado'});assert.equal(a.state.draft.text,'Nuevo');await a.save();assert.equal(calls,1)
  a.dispose();const b=new DescriptionController('b',async()=>({record:record('b'),etag:'2'}));await b.load();pending.resolve({record:{...record(),text:'Antiguo'},etag:'3'});await saving;assert.equal(b.state.draft.text,'Sintetizador documentado');b.dispose()
})
test('gateway distingue falta de ficha y envía precondiciones de creación/edición', async () => {
  const original=globalThis.fetch;let count=0
  globalThis.fetch=async(_url,options)=>{count++;if(count===1)return new Response(JSON.stringify({error:{code:'description_missing'}}),{status:404});const h=options?.headers as Record<string,string>;assert.equal(h[count===2?'If-None-Match':'If-Match'],count===2?'*':'2');return new Response(JSON.stringify(record()),{headers:{etag:'2'}})}
  try { assert.equal((await requestDescription('a',new AbortController().signal)).record,null);await requestDescription('a',new AbortController().signal,{body:blank(),etag:''});await requestDescription('a',new AbortController().signal,{body:blank(),etag:'2'}) }finally{globalThis.fetch=original}
})
