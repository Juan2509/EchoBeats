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
  assert.ok(value.width >= .03 && value.width <= .6 && value.height >= .03 && value.height <= .6)
}
test('tamaños extremos y giros mantienen el rectángulo completo dentro del lienzo', () => {
  for (const width of [.03, .1, .6]) for (const height of [.03, .1, .6]) for (const rotation_deg of [-540, -180, -90, -45, 0, 45, 90, 180, 540]) {
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
