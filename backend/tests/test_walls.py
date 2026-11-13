"""Muros reales aislados: creación transaccional, geometría, recursos y revisiones."""
import asyncio
import hashlib
import json
from io import BytesIO
from uuid import UUID, uuid4
from alembic import command
from PIL import Image
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.database import migration_config
from app.integrations.storage import MediaStore
from app.models.catalog import WALL_DEFAULT_BACKGROUND, UNKNOWN_ALBUM_ID, album, media_asset, wall, wall_element
from app.services import metadata, walls
from test_metadata import client, tagged, upload, png

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def new_album(api, name='Muro A'):
    result = await api.post('/api/v1/albums', json={'title': name})
    assert result.status_code == 201, result.text
    return f"/api/v1/albums/{result.json()['id']}/wall"


async def image(api):
    result = await api.post('/api/v1/assets', files={'file': ('prueba.png', png(), 'image/png')}, data={'purpose': 'cover'})
    assert result.status_code == 201, result.text
    return result.json()['id']


def element(asset_id, **changes):
    return {'id': str(uuid4()), 'asset_id': asset_id, 'kind': 'poster', 'cx': 0.5, 'cy': 0.5,
            'width': 0.2, 'height': 0.3, 'rotation_deg': 15, 'z_index': 0, **changes}


def composition(*elements, color='#123456'):
    return {'schema_version': 1, 'background_color': color, 'elements': list(elements)}


async def test_initial_walls_for_manual_imported_and_system_albums(client, catalog_engine):
    api, _ = client
    url = await new_album(api)
    manual = await api.get(url)
    system = await api.get(f'/api/v1/albums/{UNKNOWN_ALBUM_ID}/wall')
    item = await upload(api, tagged(collection='Álbum con muro'))
    song = (await api.get(f"/api/v1/tracks/{item['track_id']}")).json()
    imported_url = f"/api/v1/albums/{song['album_id']}/wall"
    imported = await api.get(imported_url)
    ids = set()
    for result in (manual, system, imported):
        assert result.status_code == 200
        row = result.json()
        ids.add(row['id'])
        assert row['schema_version'] == row['revision'] == 1
        assert row['elements'] == [] and row['background_color'] == WALL_DEFAULT_BACKGROUND
        assert result.headers['etag'] == f'"wall-{row["id"]}-1"'
    assert len(ids) == 3
    await upload(api, tagged(collection='Álbum con muro'))
    assert (await api.get(imported_url)).json() == imported.json()
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(album)) == connection.scalar(select(func.count()).select_from(wall))
    assert (await api.get(f'/api/v1/albums/{uuid4()}/wall')).status_code == 404


async def test_full_composition_isolated_and_reset_keeps_shared_asset(client, catalog_engine):
    api, app = client
    a, b = await new_album(api), await new_album(api, 'Muro B')
    before_b = await api.get(b)
    initial = await api.get(a)
    asset = await image(api)
    first, second = element(asset), element(asset, kind='sticker', rotation_deg=375)
    second['id'], first['id'] = str(UUID(int=1)), str(UUID(int=2))
    saved = await api.put(a, headers={'If-Match': initial.headers['etag']}, json=composition(first, second, color='#aabbcc'))
    assert saved.status_code == 200, saved.text
    data = saved.json()
    assert data['background_color'] == '#AABBCC' and data['revision'] == 2
    assert [item['id'] for item in data['elements']] == [second['id'], first['id']]
    assert all(item['rotation_deg'] == 15 for item in data['elements'])
    assert (await api.get(data['elements'][0]['content_url'])).status_code == 200
    assert 'storage_key' not in saved.text
    assert (await api.get(b)).json() == before_b.json()
    # Nueva conexión del servicio recupera exactamente la composición almacenada.
    with catalog_engine.connect() as connection:
        reloaded, token = walls.data(connection, UUID(data['album_id']))
    from fastapi.encoders import jsonable_encoder
    assert jsonable_encoder(reloaded) == data and token == saved.headers['etag']
    removed = await api.put(a, headers={'If-Match': saved.headers['etag']}, json=composition(first))
    assert len(removed.json()['elements']) == 1
    reset = await api.post(a + '/reset', headers={'If-Match': removed.headers['etag']})
    assert reset.json()['elements'] == [] and reset.json()['background_color'] == WALL_DEFAULT_BACKGROUND
    assert reset.json()['revision'] == 4 and reset.json()['id'] == data['id']
    assert (await api.get(b)).json() == before_b.json()
    assert (await api.get(data['elements'][0]['content_url'])).status_code == 200
    assert (await api.post(a + '/reset', headers={'If-Match': saved.headers['etag']})).status_code == 412


@pytest.mark.parametrize('change', [
    {'cx': 0.01}, {'cy': 0.01}, {'cx': 1.0}, {'width': 0.02}, {'height': 0.61},
    {'cx': 0.11, 'rotation_deg': 45}, {'z_index': -1}, {'z_index': 30}, {'z_index': True},
    {'rotation_deg': 'NaN'}, {'rotation_deg': 'Infinity'}, {'cx': True}, {'height': None},
    {'kind': 'script'}, {'extra': 'no'},
])
async def test_invalid_element_preserves_wall(client, change):
    api, _ = client
    url = await new_album(api)
    initial = await api.get(url)
    body = composition(element(await image(api), **change))
    response = await api.put(url, headers={'If-Match': initial.headers['etag']}, json=body)
    assert response.status_code == 422, response.text
    assert (await api.get(url)).json() == initial.json()


async def test_schema_limits_duplicates_and_rotated_edge(client):
    api, _ = client
    url = await new_album(api)
    initial = await api.get(url)
    asset = await image(api)
    same = element(asset)
    invalid = [composition(same, same), composition(*[element(asset) for _ in range(31)]),
               {**composition(), 'schema_version': 2}, {**composition(), 'schema_version': True},
               {**composition(), 'background_color': 'red'}, {**composition(), 'background_color': '#123456\n'},
               {**composition(), 'album_id': str(uuid4())}]
    for body in invalid:
        assert (await api.put(url, headers={'If-Match': initial.headers['etag']}, json=body)).status_code == 422
    edge = element(asset, cx=0.15, cy=0.15, rotation_deg=90)
    accepted = await api.put(url, headers={'If-Match': initial.headers['etag']}, json=composition(edge))
    assert accepted.status_code == 200, accepted.text
    full = await api.put(url, headers={'If-Match': accepted.headers['etag']}, json=composition(*[element(asset) for _ in range(30)]))
    assert full.status_code == 200 and len(full.json()['elements']) == 30


async def test_wrong_missing_and_foreign_resources_rollback_entire_composition(client, catalog_engine):
    api, app = client
    a, b = await new_album(api), await new_album(api, 'B')
    initial = await api.get(a)
    asset = await image(api)
    owned = element(asset)
    saved = await api.put(a, headers={'If-Match': initial.headers['etag']}, json=composition(owned))
    initial_b = await api.get(b)
    response = await api.put(b, headers={'If-Match': initial_b.headers['etag']}, json=composition(owned))
    assert response.status_code == 422 and response.json()['error']['code'] == 'wall_element_conflict'
    assert (await api.get(b)).json() == initial_b.json()
    item = await upload(api, tagged())
    with catalog_engine.connect() as connection:
        audio_id = connection.scalar(select(media_asset.c.id).where(media_asset.c.kind == 'audio'))
        resource = connection.execute(select(media_asset).where(media_asset.c.id == UUID(asset))).one()
    for invalid in [element(str(uuid4())), element(str(audio_id)), element(asset, kind='gif')]:
        result = await api.put(a, headers={'If-Match': saved.headers['etag']}, json=composition(element(asset), invalid))
        assert result.status_code == 422
        assert (await api.get(a)).json() == saved.json()
    path = MediaStore(app.state.settings.media_root).path_for(resource.storage_key)
    path.unlink()  # Solo el archivo sintético de esta prueba temporal.
    result = await api.put(a, headers={'If-Match': saved.headers['etag']}, json=composition(owned))
    assert result.status_code == 422 and result.json()['error']['code'] == 'wall_asset_missing'
    assert (await api.get(a)).json() == saved.json()


async def test_revision_and_concurrent_same_wall(client):
    api, _ = client
    url = await new_album(api)
    initial = await api.get(url)
    for suffix, method in [('', api.put), ('/reset', api.post)]:
        for token in [None, '*', '"old"']:
            arguments = {'headers': {} if token is None else {'If-Match': token}}
            if not suffix:
                arguments['json'] = composition()
            result = await method(url + suffix, **arguments)
            assert result.status_code == (428 if token is None else 412)
            if token is not None:
                assert result.json()['error']['current_revision'] == 1
                assert result.json()['error']['current_etag'] == initial.headers['etag']
    results = await asyncio.gather(*[api.put(url, headers={'If-Match': initial.headers['etag']}, json=composition(color=color)) for color in ['#123456', '#654321']])
    assert sorted(result.status_code for result in results) == [200, 412]
    winner = next(result for result in results if result.status_code == 200)
    assert (await api.get(url)).json() == winner.json()


async def test_same_new_element_id_cannot_cross_walls_concurrently(client):
    api, _ = client
    urls = [await new_album(api, name) for name in ['A', 'B']]
    tokens = [(await api.get(url)).headers['etag'] for url in urls]
    body = composition(element(await image(api)))
    results = await asyncio.gather(*[api.put(url, headers={'If-Match': token}, json=body) for url, token in zip(urls, tokens)])
    assert sorted(result.status_code for result in results) == [200, 422]
    for url, result in zip(urls, results):
        row = (await api.get(url)).json()
        assert row['revision'] == (2 if result.status_code == 200 else 1)
        assert len(row['elements']) == (1 if result.status_code == 200 else 0)


def migrate(engine, operation, target):
    with engine.begin() as connection:
        config = migration_config(); config.attributes['connection'] = connection
        operation(config, target)


def test_migration_backfills_old_albums_and_refuses_customized_downgrade(catalog_engine):
    migrate(catalog_engine, command.downgrade, '0004_audio_formats')
    identity = uuid4()
    with catalog_engine.begin() as connection:
        connection.execute(album.insert().values(id=identity, title='Preexistente'))
    migrate(catalog_engine, command.upgrade, 'head')
    with catalog_engine.connect() as connection:
        rows = connection.execute(select(wall)).all()
        assert {row.album_id for row in rows} == {identity, UNKNOWN_ALBUM_ID}
    migrate(catalog_engine, command.upgrade, 'head')
    with catalog_engine.begin() as connection:
        assert connection.scalar(select(func.count()).select_from(wall)) == 2
        connection.execute(wall.update().where(wall.c.album_id == identity).values(revision=2, background_color='#123456'))
    with pytest.raises(RuntimeError, match='hay muros guardados'):
        migrate(catalog_engine, command.downgrade, '0004_audio_formats')
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(wall.c.background_color).where(wall.c.album_id == identity)) == '#123456'
        assert connection.scalar(select(album.c.title).where(album.c.id == identity)) == 'Preexistente'


def test_album_and_wall_creation_rollback_together(catalog_engine, monkeypatch):
    original = walls.create_initial
    def fail(connection, album_id):
        original(connection, album_id)
        raise RuntimeError('fallo de prueba después de crear muro')
    monkeypatch.setattr(walls, 'create_initial', fail)
    with pytest.raises(RuntimeError, match='fallo de prueba'):
        metadata.create_album(catalog_engine, 'No debe persistir', [])
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(album)) == 1
        assert connection.scalar(select(func.count()).select_from(wall)) == 1


def test_database_restricts_duplicate_wall_and_non_finite_geometry(catalog_engine):
    with pytest.raises(IntegrityError), catalog_engine.begin() as connection:
        connection.execute(wall.insert().values(album_id=UNKNOWN_ALBUM_ID))
    with catalog_engine.connect() as connection:
        initial = connection.execute(select(wall)).one()
    # El CHECK de dimensiones se evalúa antes de las referencias: NaN no evade los límites.
    with pytest.raises(IntegrityError) as invalid_geometry, catalog_engine.begin() as connection:
        connection.execute(wall_element.insert().values(id=uuid4(), wall_id=initial.id, asset_id=uuid4(), kind='image',
            cx=0.5, cy=0.5, width=float('nan'), height=0.2, rotation_deg=0, z_index=0))

    assert invalid_geometry.value.orig.diag.constraint_name == 'ck_wall_element_size'


async def test_gif_reference_uses_managed_resource_and_enforces_animation_limits(client, catalog_engine):
    api, app = client
    url = await new_album(api)
    initial = await api.get(url)
    stream = BytesIO()
    Image.new('RGB', (40, 30), 'red').save(stream, format='GIF', save_all=True,
        append_images=[Image.new('RGB', (40, 30), 'blue')], duration=100, loop=0)
    payload, identity = stream.getvalue(), uuid4()
    key = f'images/{identity.hex}.gif'
    store = MediaStore(app.state.settings.media_root)
    with store.stage(BytesIO(payload), 5 * 1024 * 1024) as (staged, _, _):
        store.publish(staged, key)
    with catalog_engine.begin() as connection:
        connection.execute(media_asset.insert().values(id=identity, kind='gif', storage_key=key,
            sha256=hashlib.sha256(payload).hexdigest(), original_name='prueba.gif', mime_type='image/gif',
            byte_size=len(payload), width_px=40, height_px=30, frame_count=2))
    saved = await api.put(url, headers={'If-Match': initial.headers['etag']}, json=composition(element(str(identity), kind='gif')))
    assert saved.status_code == 200, saved.text
    image_response = await api.get(saved.json()['elements'][0]['content_url'])
    assert image_response.content == payload and image_response.headers['content-type'] == 'image/gif'
    assert image_response.headers['x-content-type-options'] == 'nosniff'
    with catalog_engine.begin() as connection:
        connection.execute(media_asset.update().where(media_asset.c.id == identity).values(frame_count=201))
    rejected = await api.put(url, headers={'If-Match': saved.headers['etag']}, json=composition(element(str(identity), kind='gif')))
    assert rejected.status_code == 422
    assert (await api.get(url)).json() == saved.json()


async def test_non_finite_numbers_in_raw_json_are_rejected(client):
    api, _ = client
    url = await new_album(api)
    initial = await api.get(url)
    body = composition(element(await image(api)))
    for number in [float('nan'), float('inf'), float('-inf')]:
        body['elements'][0]['rotation_deg'] = number
        response = await api.put(url, headers={'If-Match': initial.headers['etag'], 'Content-Type': 'application/json'}, content=json.dumps(body))
        assert response.status_code == 422
        assert (await api.get(url)).json() == initial.json()
