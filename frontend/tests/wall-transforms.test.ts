import test from 'node:test'
import assert from 'node:assert/strict'
import { WallController, composition, orderedElements, transformWithinWall } from '../src/features/walls/controller.ts'
import type { WallElement, WallResult, WallGateway } from '../src/features/walls/controller.ts'

const item: WallElement = { id: 'a', asset_id: 'asset-a', kind: 'image', cx: .1, cy: .1, width: .1, height: .1, rotation_deg: 0, z_index: 29, content_url: '/a' }
function inside(value: WallElement) {
  const a = value.rotation_deg * Math.PI / 180
  const bx = (Math.abs(value.width * 1000 * Math.cos(a)) + Math.abs(value.height * 700 * Math.sin(a))) / 2000
  const by = (Math.abs(value.width * 1000 * Math.sin(a)) + Math.abs(value.height * 700 * Math.cos(a))) / 1400
  assert.ok(value.cx >= bx - 1e-10 && value.cx <= 1 - bx + 1e-10)
  assert.ok(value.cy >= by - 1e-10 && value.cy <= 1 - by + 1e-10)
  assert.ok(value.width >= .03 && value.width <= 1 && value.height >= .03 && value.height <= 1)
}
test('tamaños extremos y giros mantienen el rectángulo completo dentro del lienzo', () => {
  for (const width of [.03, .1, .6, 1]) for (const height of [.03, .1, .6, 1]) for (const rotation_deg of [-540, -180, -90, -45, 0, 45, 90, 180, 540]) {
    const value = transformWithinWall(item, { width, height, rotation_deg })
    inside(value); assert.ok(value.rotation_deg >= -180 && value.rotation_deg < 180)
    assert.equal(value.id, item.id); assert.equal(value.asset_id, item.asset_id)
  }
  assert.equal(transformWithinWall(item, { width: NaN }), item)
  assert.equal(transformWithinWall(item, { rotation_deg: Infinity }), item)
  inside(transformWithinWall(item, { width: -1, height: 10 }))
})
test('girar ajusta centro, reduce proporcionalmente solo si hace falta y conserva recursos', () => {
  const value = transformWithinWall(item, { width: .6, height: .6, rotation_deg: 45 })
  assert.ok(value.width < .6); assert.equal(value.width, value.height)
  assert.equal(value.content_url, '/a'); inside(value)
  const next = transformWithinWall(value, { rotation_deg: -90 })
  assert.equal(next.width, value.width); inside(next)
})
const initial = (): WallResult => ({ wall: { id: 'wall', album_id: 'album', schema_version: 1, revision: 1, background_color: '#242038', updated_at: '', elements: [item, { ...item, id: 'b' }, { ...item, id: 'c' }] }, etag: '1' })

test('ajuste al muro es explícito y puede deshacerse y rehacerse sin perder recursos',async()=>{
  const c=new WallController('album',async()=>initial());await c.load();c.fit('a');assert.equal(c.state.elements[0].width,.1)
  await c.toggleEditing();c.fit('a');assert.equal(c.state.elements[0].width,1);assert.equal(c.state.elements[0].cx,.5);assert.ok(c.undo());assert.equal(c.state.elements[0].width,.1);assert.ok(c.redo());assert.equal(c.state.elements[0].width,1);assert.equal(c.state.elements[0].asset_id,item.asset_id);c.dispose()
})
test('cambiar imagen/sticker conserva geometría y recurso, respeta bloqueo y persiste',async()=>{
  let stored=initial()
  stored.wall.elements.push({...item,id:'gif',kind:'gif'})
  const c=new WallController('album',async(_id,_signal,write)=>{if(write)stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/a'}))},etag:'2'};return stored})
  await c.load();c.setKind('a','sticker');assert.equal(c.state.elements[0].kind,'image')
  await c.toggleEditing();c.beginMove('a');c.setKind('a','sticker');assert.equal(c.state.elements[0].kind,'image');c.cancelMove()
  c.setKind('gif','sticker');assert.equal(c.state.elements.find(e=>e.id==='gif')!.kind,'gif')
  c.select('a');c.setKind('a','sticker');assert.deepEqual(c.state.elements[0],{...item,kind:'sticker'});assert.equal(c.state.selectedId,'a')
  assert.equal(await c.save(),true);await c.load();assert.equal(c.state.elements.find(e=>e.id==='a')!.kind,'sticker')
  await c.toggleEditing();c.setKind('a','image');assert.equal(await c.save(),true);await c.load();assert.deepEqual(c.state.elements.find(e=>e.id==='a'),item);c.dispose()
})
test('rotación por gesto conserva proporción, permite cancelar y guarda solo tras soltar',async()=>{
  let writes=0;let stored=initial()
  const c=new WallController('album',async(_id,_signal,write)=>{if(write){writes++;stored={wall:{...stored.wall,...write.body,elements:write.body.elements.map(e=>({...e,content_url:'/a'}))},etag:String(writes+1)}}return stored},undefined,{autosaveMs:5})
  await c.load();await c.toggleEditing()
  c.rotateGesture('a',45);assert.equal(c.state.elements[0].rotation_deg,0)
  assert.equal(c.beginMove('a'),true);c.rotateGesture('b',45);assert.equal(c.state.elements[1].rotation_deg,0)
  c.rotateGesture('a',65);assert.equal(c.state.elements[0].rotation_deg,65)
  await new Promise(r=>setTimeout(r,15));assert.equal(writes,0)
  c.cancelMove();assert.equal(c.state.elements[0].rotation_deg,0)
  c.beginMove('a');c.rotateGesture('a',-40);c.finishMove();await c.save()
  assert.equal(writes,1);assert.equal(c.state.elements[0].rotation_deg,-40);assert.equal(c.state.elements[0].width,item.width);assert.equal(c.state.elements[0].height,item.height)
  c.dispose();c.rotateGesture('a',90);assert.equal(c.state.elements[0].rotation_deg,-40)
})
test('capas empatadas tienen orden estable; transformaciones y orden sobreviven guardar y recargar', async () => {
  let stored = initial()
  const gateway: WallGateway = async (_id, _signal, write) => {
    if (write) stored = { wall: { ...stored.wall, ...write.body, elements: write.body.elements.map(element => ({ ...element, content_url: '/a' })) }, etag: '2' }
    return stored
  }
  const c = new WallController('album', gateway); await c.load()
  c.transform('a', { width: .5 }); c.reorder('a', 'front'); assert.equal(c.state.elements[0].width, .1)
  await c.toggleEditing(); c.transform('a', { width: .5, rotation_deg: 80 }); c.reorder('a', 'front')
  assert.deepEqual(orderedElements(c.state.elements).map(e => e.id), ['b', 'c', 'a'])
  assert.deepEqual(c.state.elements.map(e => e.z_index), [0, 1, 2])
  c.reorder('a', 'backward'); assert.deepEqual(c.state.elements.map(e => e.id), ['b', 'a', 'c'])
  c.reorder('a', 'back'); c.reorder('a', 'forward'); assert.deepEqual(c.state.elements.map(e => e.id), ['b', 'a', 'c'])
  const wanted = composition(c.state.wall!, c.state.color, c.state.elements)
  assert.equal(await c.save(), true); await c.load()
  assert.deepEqual(composition(c.state.wall!, c.state.color, c.state.elements), wanted)
  c.dispose()
})
test('gesto activo y guardado en curso bloquean tamaño, giro y capas', async () => {
  let finish!: (value: WallResult) => void
  const c = new WallController('album', async (_id, _signal, write) => write ? await new Promise(resolve => { finish = resolve }) : initial())
  await c.load(); await c.toggleEditing(); c.beginMove('a')
  c.transform('a', { width: .5 }); c.reorder('a', 'front'); assert.equal(c.state.elements[0].width, .1)
  c.finishMove(); c.transform('a', { rotation_deg: 35 }); const before = JSON.stringify(c.state.elements)
  const saving = c.save(); c.transform('a', { width: .5 }); c.reorder('a', 'front')
  assert.equal(JSON.stringify(c.state.elements), before)
  finish(initial()); await saving; c.dispose()
})
