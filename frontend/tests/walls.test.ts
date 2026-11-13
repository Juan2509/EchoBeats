import test from 'node:test'
import assert from 'node:assert/strict'
import { composition, isDirty, requestWall, WallController, WallRequestError } from '../src/features/walls/controller.ts'
import type { WallGateway, WallResult } from '../src/features/walls/controller.ts'
const initial = (id = 'album-a'): WallResult => ({ wall: {
  id: `wall-${id}`, album_id: id, schema_version: 1, revision: 1, background_color: '#242038', updated_at: '2026-11-13T12:00:00Z',
  elements: [{ id: 'element-1', asset_id: 'image-1', kind: 'poster', cx: .3, cy: .4, width: .2, height: .3, rotation_deg: 15, z_index: 29, content_url: '/api/v1/assets/image-1/content' }],
}, etag: '"wall-1"' })
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (error: unknown) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }

test('carga bloqueada y guarda color sin perder elementos ni enviar campos de solo lectura', async () => {
  const calls: { id: string; body?: unknown; etag?: string }[] = []
  const original = initial()
  const gateway: WallGateway = async (id, _signal, write) => {
    calls.push({ id, body: write?.body, etag: write?.etag })
    return write ? { wall: { ...original.wall, ...write.body, elements: original.wall.elements, revision: 2 }, etag: '"wall-2"' } : original
  }
  const controller = new WallController('album-a', gateway)
  await controller.load()
  assert.equal(controller.state.editing, false)
  controller.setColor('#193A55'); assert.equal(controller.state.color, '#242038')
  await controller.toggleEditing(); controller.setColor('#193a55')
  assert.equal(isDirty(controller.state), true)
  await controller.toggleEditing()
  assert.equal(controller.state.editing, false); assert.equal(isDirty(controller.state), false)
  assert.equal(controller.state.notice, 'Fondo guardado.')
  assert.equal(calls[1].etag, '"wall-1"')
  assert.deepEqual(calls[1].body, composition(original.wall, '#193A55'))
  assert.equal('content_url' in (calls[1].body as ReturnType<typeof composition>).elements[0], false)
  assert.equal('revision' in (calls[1].body as object), false)
  assert.deepEqual(controller.state.wall?.elements, original.wall.elements)
  assert.equal(original.wall.background_color, '#242038')
})

test('bloquear sin cambios no escribe; edición inválida no cambia fondo', async () => {
  let calls = 0
  const controller = new WallController('album-a', async () => { calls++; return initial() })
  await controller.load(); await controller.toggleEditing()
  for (const value of ['red', '#123', '#12345678']) controller.setColor(value)
  await controller.toggleEditing()
  assert.equal(calls, 1); assert.equal(controller.state.color, '#242038')
})

test('guardado único bloquea cambios en vuelo y no acepta una segunda escritura', async () => {
  const pending = deferred<WallResult>(); let writes = 0
  const controller = new WallController('album-a', async (_id, _signal, write) => { if (write) { writes++; return pending.promise }; return initial() })
  await controller.load(); await controller.toggleEditing(); controller.setColor('#193A55')
  const saving = controller.save()
  assert.equal(controller.state.saving, true)
  controller.setColor('#284333'); await controller.load(); await controller.toggleEditing()
  assert.equal(await controller.save(), false); assert.equal(controller.state.color, '#193A55')
  pending.resolve({ wall: { ...initial().wall, background_color: '#193A55', revision: 2 }, etag: '"wall-2"' })
  assert.equal(await saving, true); assert.equal(writes, 1); assert.equal(controller.state.saving, false)
})

test('conflicto conserva borrador y requiere recargar antes de volver a escribir', async () => {
  let writes = 0
  const controller = new WallController('album-a', async (_id, _signal, write) => { if (write) { writes++; throw new WallRequestError('Conflicto', 412) }; return initial() })
  await controller.load(); await controller.toggleEditing(); controller.setColor('#193A55')
  await controller.toggleEditing()
  assert.equal(controller.state.editing, true); assert.equal(isDirty(controller.state), true)
  assert.equal(controller.state.needsReload, true); assert.match(controller.state.error, /otra pestaña/)
  assert.equal(await controller.save(), false); assert.equal(writes, 1)
  await controller.load()
  assert.equal(controller.state.color, '#242038'); assert.equal(controller.state.editing, false); assert.equal(isDirty(controller.state), false)
})

test('red o respuesta incierta no anuncia éxito ni repite PUT; rechazos confirmados permiten reintentar', async () => {
  for (const cause of [new TypeError('network'), new WallRequestError('BD no disponible', 503), new WallRequestError('Imagen ausente', 422)]) {
    let writes = 0
    const controller = new WallController('album-a', async (_id, _signal, write) => { if (write) { writes++; throw cause }; return initial() })
    await controller.load(); await controller.toggleEditing(); controller.setColor('#193A55')
    assert.equal(await controller.save(), false)
    assert.equal(isDirty(controller.state), true); assert.equal(controller.state.notice, '')
    assert.equal(controller.state.needsReload, !(cause instanceof WallRequestError) || cause.status === 503)
    if (controller.state.needsReload) { await controller.save(); assert.equal(writes, 1) }
    else { await controller.save(); assert.equal(writes, 2) }
  }
})

test('respuesta tardía de otra lectura no pisa la carga más reciente', async () => {
  const old = deferred<WallResult>(); let reads = 0
  const controller = new WallController('album-a', async () => ++reads === 1 ? old.promise : { wall: { ...initial().wall, background_color: '#193A55', revision: 2 }, etag: '"wall-2"' })
  const first = controller.load(); await controller.load(); old.resolve(initial()); await first
  assert.equal(controller.state.color, '#193A55'); assert.equal(controller.state.etag, '"wall-2"')
})

test('salir de A aborta peticiones y no aplica sus respuestas a B', async () => {
  const pending = deferred<WallResult>(); let signal: AbortSignal | undefined
  const a = new WallController('album-a', async (_id, abort) => { signal = abort; return pending.promise })
  let notices = 0; a.subscribe(() => notices++)
  const loading = a.load(); a.dispose(); const before = notices
  const b = new WallController('album-b', async () => initial('album-b')); await b.load()
  pending.resolve(initial()); await loading
  assert.equal(signal?.aborted, true); assert.equal(notices, before)
  assert.equal(b.state.wall?.album_id, 'album-b'); assert.equal(a.state.wall, null)
})

test('carga fallida admite reintento y conserva edición bloqueada', async () => {
  let attempts = 0
  const controller = new WallController('album-a', async () => { if (++attempts === 1) throw new TypeError('offline'); return initial() })
  await controller.load(); assert.match(controller.state.error, /cargar/); assert.equal(controller.state.loading, false)
  await controller.load(); assert.equal(controller.state.error, ''); assert.equal(controller.state.editing, false)
})

test('gateway exige ETag, álbum correcto y envía If-Match y composición al guardar', async () => {
  const original = globalThis.fetch
  try {
    let options: RequestInit | undefined
    globalThis.fetch = (async (_url, init) => { options = init; return new Response(JSON.stringify(initial().wall), { headers: { ETag: '"wall-1"' } }) }) as typeof fetch
    await requestWall('album-a', new AbortController().signal, { body: composition(initial().wall, '#193A55'), etag: '"wall-1"' })
    assert.equal(options?.method, 'PUT'); assert.equal((options?.headers as Record<string, string>)['If-Match'], '"wall-1"')
    globalThis.fetch = (async () => new Response(JSON.stringify(initial('album-b').wall), { headers: { ETag: '"wall-1"' } })) as typeof fetch
    await assert.rejects(requestWall('album-a', new AbortController().signal))
    globalThis.fetch = (async () => new Response(JSON.stringify(initial().wall))) as typeof fetch
    await assert.rejects(requestWall('album-a', new AbortController().signal))
  } finally { globalThis.fetch = original }
})
