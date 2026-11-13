import test from 'node:test'
import assert from 'node:assert/strict'
import { WallController, WallRequestError, composition, isDirty, requestWall } from '../src/features/walls/controller.ts'
import type { WallGateway, WallResult } from '../src/features/walls/controller.ts'

const initial = (): WallResult => ({ wall: { id: 'wall-a', album_id: 'a', schema_version: 1, revision: 1, background_color: '#242038', updated_at: '', elements: [] }, etag: '1' })
const pause = () => new Promise(resolve => setTimeout(resolve, 30))
function deferred<T>() { let resolve!: (value: T) => void; const promise = new Promise<T>(yes => { resolve = yes }); return { promise, resolve } }
function storage() {
  let value = initial(), writes = 0
  const gateway: WallGateway = async (_id, _signal, write) => {
    if (write) { writes++; value = { wall: { ...value.wall, ...write.body, elements: [], revision: value.wall.revision + 1 }, etag: String(writes + 1) } }
    return structuredClone(value)
  }
  return { gateway, writes: () => writes }
}
test('agrupa cambios, guarda automáticamente y restaura el álbum al reabrir', async () => {
  const db = storage(), c = new WallController('a', db.gateway, undefined, { autosaveMs: 5 })
  try {
    await c.load(); await c.toggleEditing(); c.setColor('#123456'); c.setColor('#654321')
    await pause(); assert.equal(db.writes(), 1); assert.equal(isDirty(c.state), false)
    c.dispose()
    const reopened = new WallController('a', db.gateway)
    await reopened.load(); assert.equal(reopened.state.color, '#654321'); assert.equal(reopened.state.editing, false); reopened.dispose()
  } finally { c.dispose() }
})
test('respuesta atrasada confirma su revisión sin pisar cambios nuevos; serializa la siguiente escritura', async () => {
  const pending = deferred<WallResult>(); let writes = 0; const bodies: string[] = []
  const c = new WallController('a', async (_id, _signal, write) => {
    if (!write) return initial()
    writes++; bodies.push(write.body.background_color)
    if (writes === 1) return pending.promise
    assert.equal(write.etag, '2')
    return { wall: { ...initial().wall, ...write.body, elements: [] }, etag: '3' }
  }, undefined, { autosaveMs: 5 })
  try {
    await c.load(); await c.toggleEditing(); c.setColor('#123456'); const saving = c.save()
    c.setColor('#654321'); assert.equal(writes, 1)
    pending.resolve({ wall: { ...initial().wall, background_color: '#123456' }, etag: '2' }); await saving
    assert.equal(c.state.color, '#654321'); assert.equal(isDirty(c.state), true)
    await pause(); assert.deepEqual(bodies, ['#123456', '#654321']); assert.equal(isDirty(c.state), false)
  } finally { c.dispose() }
})
test('fallo de autoguardado conserva borrador y no crea un bucle de reintentos', async () => {
  let writes = 0
  const c = new WallController('a', async (_id, _signal, write) => {
    if (write) { writes++; throw new WallRequestError('No disponible', 503) } return initial()
  }, undefined, { autosaveMs: 5 })
  try {
    await c.load(); await c.toggleEditing(); c.setColor('#123456'); await pause(); await pause()
    assert.equal(writes, 1); assert.equal(c.state.color, '#123456'); assert.equal(c.state.needsReload, true)
    await c.load(); assert.equal(c.state.color, '#242038'); assert.equal(isDirty(c.state), false)
  } finally { c.dispose() }
})
test('restablecimiento persistente usa reset versionado y no modifica otro álbum', async () => {
  let stored = { wall: { ...initial().wall, background_color: '#123456' }, etag: '2' }; let resets = 0
  const c = new WallController('a', async (_id, _signal, write) => {
    if (write) { assert.equal(write.reset, true); assert.equal(write.etag, '2'); resets++; stored = { wall: { ...stored.wall, ...write.body, elements: [] }, etag: '3' } } return stored
  }, undefined, { autosaveMs: 5 })
  try {
    await c.load(); await c.toggleEditing(); assert.equal(await c.reset(), true)
    await c.load(); assert.equal(c.state.color, '#242038'); assert.deepEqual(c.state.elements, []); assert.equal(resets, 1)
    const b = new WallController('b', async () => ({ ...initial(), wall: { ...initial().wall, album_id: 'b', background_color: '#654321' } }))
    await b.load(); assert.equal(b.state.color, '#654321'); b.dispose()
  } finally { c.dispose() }
})
test('reset fallido conserva el borrador anterior y bloquea reintentos inciertos', async () => {
  const c = new WallController('a', async (_id, _signal, write) => { if (write) throw new TypeError('network'); return initial() }, undefined, { autosaveMs: 1000 })
  try {
    await c.load(); await c.toggleEditing(); c.setColor('#123456')
    assert.equal(await c.reset(), false); assert.equal(c.state.color, '#123456'); assert.equal(c.state.needsReload, true); assert.equal(isDirty(c.state), true)
  } finally { c.dispose() }
})
test('salir cancela el temporizador y una respuesta de A no cambia B', async () => {
  const db = storage(), c = new WallController('a', db.gateway, undefined, { autosaveMs: 5 })
  await c.load(); await c.toggleEditing(); c.setColor('#123456'); c.dispose(); await pause(); assert.equal(db.writes(), 0)
  const pending = deferred<WallResult>(), a = new WallController('a', async (_id, _signal, write) => write ? pending.promise : initial(), undefined, { autosaveMs: 1000 })
  await a.load(); await a.toggleEditing(); a.setColor('#123456'); const saving = a.save(); a.dispose()
  const b = new WallController('b', async () => initial()); await b.load(); pending.resolve(initial()); assert.equal(await saving, false); assert.equal(b.state.color, '#242038'); b.dispose()
})
test('gateway de reset manda POST e If-Match sin cuerpo de composición', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/v1/albums/a/wall/reset'); assert.equal(options?.method, 'POST'); assert.equal(options?.body, undefined)
    assert.equal((options?.headers as Record<string, string>)['If-Match'], '1')
    return new Response(JSON.stringify(initial().wall), { headers: { etag: '2' } })
  }
  try { await requestWall('a', new AbortController().signal, { reset: true, etag: '1', body: { schema_version: 1, background_color: '#242038', elements: [] } }) } finally { globalThis.fetch = original }
})

test('arrastre guarda solo al soltar y preserva la composición completa al reabrir', async () => {
  let stored = initial(), writes = 0
  stored.wall.elements = [{ id: 'object', asset_id: 'gif', kind: 'gif', cx: .5, cy: .5, width: .2, height: .3, rotation_deg: 25, z_index: 3, content_url: '/gif', static_preview_url: '/preview' }]
  const gateway: WallGateway = async (_id, _signal, write) => {
    if (write) { writes++; stored = { wall: { ...stored.wall, ...write.body, elements: write.body.elements.map(e => ({ ...e, content_url: '/gif', static_preview_url: '/preview' })) }, etag: '2' } } return structuredClone(stored)
  }
  const c = new WallController('a', gateway, undefined, { autosaveMs: 5 })
  try {
    await c.load(); await c.toggleEditing(); c.beginMove('object'); c.move('object', .6, .6)
    await pause(); assert.equal(writes, 0); c.finishMove(); await pause(); assert.equal(writes, 1)
    c.transform('object', { width: .4, height: .2, rotation_deg: -40 }); await pause()
    const wanted = composition(c.state.wall!, c.state.color, c.state.elements)
    c.dispose(); const reopened = new WallController('a', gateway); await reopened.load()
    assert.deepEqual(composition(reopened.state.wall!, reopened.state.color, reopened.state.elements), wanted)
    assert.equal(reopened.state.elements[0].static_preview_url, '/preview'); reopened.dispose()
  } finally { c.dispose() }
})

test('bloquear espera también los cambios hechos durante su guardado', async () => {
  const pending = deferred<WallResult>(); let writes = 0
  const c = new WallController('a', async (_id, _signal, write) => {
    if (!write) return initial()
    if (++writes === 1) return pending.promise
    return { wall: { ...initial().wall, ...write.body, elements: [] }, etag: '3' }
  }, undefined, { autosaveMs: 1000 })
  try {
    await c.load(); await c.toggleEditing(); c.setColor('#123456'); const locking = c.toggleEditing()
    c.setColor('#654321'); pending.resolve({ wall: { ...initial().wall, background_color: '#123456' }, etag: '2' }); await locking
    assert.equal(writes, 2); assert.equal(c.state.editing, false); assert.equal(c.state.color, '#654321'); assert.equal(isDirty(c.state), false)
  } finally { c.dispose() }
})
