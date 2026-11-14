import test from 'node:test'
import assert from 'node:assert/strict'
import { FavoritesController, favoriteRequest } from '../src/features/favorites/controller.ts'
import { loadQueue } from '../src/features/player/queue.ts'
function deferred<T>() { let resolve!:(value:T)=>void; const promise = new Promise<T>(yes=>{resolve=yes}); return {promise,resolve} }

test('estado compartido, sin escritura al abrir, guarda y quita solo una vez', async () => {
  const calls: (boolean|undefined)[] = [], saved = deferred<boolean>()
  const store = new FavoritesController(async (_id, desired) => { calls.push(desired); return desired === undefined ? false : saved.promise })
  let left=0,right=0
  store.subscribe(()=>left++);store.subscribe(()=>right++)
  assert.deepEqual(calls,[])
  await Promise.all([store.load('a'),store.load('a')]);assert.deepEqual(calls,[undefined])
  const saving=store.set('a',true);await store.set('a',false)
  assert.equal(store.get('a').status,'saving');assert.equal(store.get('a').favorite,false)
  saved.resolve(true);await saving
  assert.equal(store.get('a').favorite,true);assert.equal(left,right);assert.equal(store.revision,1)
  assert.deepEqual(calls,[undefined,true]);store.dispose()
})

test('guardado incierto no inventa éxito, no reintenta y exige consultar antes de escribir', async () => {
  const calls: (boolean|undefined)[]=[];let server=false
  const store=new FavoritesController(async(_id,desired)=>{
    calls.push(desired);if(desired!==undefined){server=desired;throw new Error('lost_response')}return server
  })
  await store.load('a');await store.set('a',true)
  assert.equal(store.get('a').status,'error');assert.equal(store.get('a').favorite,undefined)
  await store.set('a',false);assert.deepEqual(calls,[undefined,true])
  await store.load('a');assert.equal(store.get('a').favorite,true);store.dispose()
})

test('volver a la ventana invalida lecturas antiguas y preserva guardados en curso', async () => {
  const old=deferred<boolean>(),write=deferred<boolean>();let reads=0
  const store=new FavoritesController(async(_id,desired)=>desired===undefined?(++reads===1?old.promise:false):write.promise)
  const first=store.load('a');store.invalidate();await store.load('a')
  old.resolve(true);await first;assert.equal(store.get('a').favorite,false)
  const saving=store.set('a',true);store.invalidate();assert.equal(store.get('a').status,'saving')
  write.resolve(true);await saving;assert.equal(store.get('a').favorite,true)
  const revision=store.revision;store.dispose();store.invalidate();assert.equal(store.revision,revision)
})

test('salir ignora la respuesta tardía y error de lectura permite reconsulta', async () => {
  const late=deferred<boolean>();const store=new FavoritesController(()=>late.promise)
  const read=store.load('a');store.dispose();late.resolve(true);await read
  assert.equal(store.get('a').status,'loading')
  let count=0;const retry=new FavoritesController(async()=>{if(++count===1)throw new Error('offline');return true})
  await retry.load('b');assert.equal(retry.get('b').status,'error')
  await retry.load('b');assert.equal(retry.get('b').favorite,true);retry.dispose()
})

test('gateway usa estado deseado explícito y rechaza respuestas de otra pista o ambiguas', async () => {
  const calls: RequestInit[]=[]
  const fake=(async(_url:unknown,init:RequestInit)=>{calls.push(init);return new Response(JSON.stringify({track_id:'a',favorite:init.method==='PUT'}))}) as typeof fetch
  assert.equal(await favoriteRequest('a',undefined,fake),false)
  assert.equal(await favoriteRequest('a',true,fake),true)
  assert.equal(calls[0].method,'GET');assert.equal(calls[0].body,undefined)
  assert.deepEqual(JSON.parse(calls[1].body as string),{favorite:true})
  for(const data of [{track_id:'b',favorite:true},{track_id:'a',favorite:'true'},{track_id:'a',favorite:false}]){
    await assert.rejects(favoriteRequest('a',true,(async()=>new Response(JSON.stringify(data))) as typeof fetch))
  }
})

test('cola de favoritos pagina solo favoritos, conserva filtro y no descarga audio', async () => {
  const requested:string[]=[]
  const queue=await loadQueue('/favorites?q=Lunar',new AbortController().signal,(async(url:string)=>{
    requested.push(url);return new Response(JSON.stringify({items:[{id:requested.length===1?'a':'b'}],total:2}))
  }) as typeof fetch)
  assert.deepEqual(queue.map(item=>item.id),['a','b'])
  assert.ok(requested.every(url=>url.startsWith('/api/v1/favorites?')&&url.includes('q=Lunar')))
  assert.ok(requested[1].includes('offset=1'))
})
