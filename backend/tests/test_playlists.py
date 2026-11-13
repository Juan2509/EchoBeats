"""Persistencia, revisión y aislamiento de playlists sobre PostgreSQL real."""
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from app.config import Settings
from app.main import create_app
from test_metadata import client, tagged, upload, png

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_order_image_and_reopen_preserve_albums(client):
    api, app = client
    ids = [(await upload(api, tagged(title=title, collection=title)))['track_id'] for title in ['Uno', 'Dos']]
    originals = [(await api.get(f'/api/v1/tracks/{value}')).json() for value in ids]
    created = await api.post('/api/v1/playlists', json={'name': '  Mi selección  '})
    assert created.status_code == 201 and created.json()['name'] == 'Mi selección'
    url = f"/api/v1/playlists/{created.json()['id']}"
    ordered = await api.put(url + '/tracks', headers={'If-Match': created.headers['etag']}, json={'track_ids': ids[::-1]})
    assert [item['id'] for item in ordered.json()['items']] == ids[::-1]
    image = await api.post('/api/v1/assets', files={'file': ('foto.png', png(), 'image/png')}, data={'purpose': 'playlist'})
    assert image.status_code == 201
    changed = await api.patch(url, headers={'If-Match': ordered.headers['etag']}, json={'name': 'Renombrada', 'appearance': 'image', 'image_asset_id': image.json()['id']})
    assert changed.status_code == 200
    assert (await api.get(changed.json()['image_url'])).status_code == 200
    # Nueva aplicación/conexión HTTP: lee del almacenamiento persistido.
    reopened = create_app(Settings(_env_file=None, media_root=app.state.settings.media_root))
    original_engine = reopened.state.database_engine
    reopened.state.database_engine = app.state.database_engine
    async with AsyncClient(transport=ASGITransport(app=reopened), base_url='http://localhost') as other:
        result = await other.get(url)
        assert result.json() == changed.json()
        assert result.headers['etag'] == changed.headers['etag']
    if original_engine is not None:
        original_engine.dispose()
    for identity, before in zip(ids, originals):
        assert (await api.get(f'/api/v1/tracks/{identity}')).json() == before
    removed = await api.put(url + '/tracks', headers={'If-Match': changed.headers['etag']}, json={'track_ids': [ids[0]]})
    cleared = await api.put(url + '/tracks', headers={'If-Match': removed.headers['etag']}, json={'track_ids': []})
    assert cleared.json()['items'] == []
    assert (await api.get('/api/v1/tracks')).json()['total'] == 2


async def test_conflict_and_invalid_changes_are_atomic(client):
    api, _ = client
    identity = (await upload(api, tagged()))['track_id']
    created = await api.post('/api/v1/playlists', json={'name': 'A'})
    url = f"/api/v1/playlists/{created.json()['id']}"
    token = created.headers['etag']
    assert (await api.patch(url, json={'name': 'B'})).status_code == 428
    for invalid in [None, '*', '"old"']:
        headers = {} if invalid is None else {'If-Match': invalid}
        assert (await api.put(url + '/tracks', headers=headers, json={'track_ids': [identity]})).status_code == (428 if invalid is None else 412)
    for ids in [[identity, identity], [identity, str(uuid4())]]:
        assert (await api.put(url + '/tracks', headers={'If-Match': token}, json={'track_ids': ids})).status_code == 422
    for body in [{'name': None}, {'appearance': None}, {'name': '  '}, {'name': 'a\x00b'}, {'appearance': 'other'}, {'image_asset_id': str(uuid4())}, {'extra': 1}]:
        assert (await api.patch(url, headers={'If-Match': token}, json=body)).status_code == 422
    assert (await api.get(url)).json() == created.json()
    success = await api.patch(url, headers={'If-Match': token}, json={'name': 'B'})
    assert success.status_code == 200
    assert (await api.patch(url, headers={'If-Match': token}, json={'name': 'C'})).status_code == 412
    assert (await api.get(f'/api/v1/playlists/{uuid4()}')).status_code == 404


async def test_search_pagination_and_invalid_image(client):
    api, _ = client
    for name in ['100%_real', 'Otra']:
        assert (await api.post('/api/v1/playlists', json={'name': name})).status_code == 201
    page = (await api.get('/api/v1/playlists', params={'q': '%_'})).json()
    assert page['total'] == 1 and page['items'][0]['name'] == '100%_real'
    assert 'items' not in page['items'][0]
    assert (await api.get('/api/v1/playlists?limit=1&offset=1')).json()['total'] == 2
    response = await api.post('/api/v1/assets', files={'file': ('bad.png', b'invalid', 'image/png')}, data={'purpose': 'playlist'})
    assert response.status_code == 422
    assert (await api.get('/api/v1/playlists', params={'q': '%_'})).json() == page


async def test_concurrent_writers_do_not_overwrite(client):
    import asyncio
    api, _ = client
    created = await api.post('/api/v1/playlists', json={'name': 'Inicial'})
    url = f"/api/v1/playlists/{created.json()['id']}"
    results = await asyncio.gather(*[api.patch(url, headers={'If-Match': created.headers['etag']}, json={'name': name}) for name in ['Uno', 'Dos']])
    assert sorted(result.status_code for result in results) == [200, 412]
    winner = next(result for result in results if result.status_code == 200)
    assert (await api.get(url)).json() == winner.json()
