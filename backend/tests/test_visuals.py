"""Carga visual real, GIF completo, preview y conservación de referencias."""
from io import BytesIO
from uuid import UUID, uuid4
from PIL import Image, PngImagePlugin
import pytest
from sqlalchemy import func, select
from app.integrations import visuals
from app.integrations.storage import MediaStore
from app.media_audit import audit
from app.models.catalog import media_asset
from test_metadata import client

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def picture(format='PNG', size=(80, 50)):
    stream = BytesIO()
    image = Image.new('RGBA' if format == 'PNG' else 'RGB', size, 'purple')
    info = PngImagePlugin.PngInfo(); info.add_text('comment', '<script>ejemplo</script>')
    image.save(stream, format=format, **({'pnginfo': info} if format == 'PNG' else {}))
    return stream.getvalue()


def animation(frames=3):
    output = BytesIO()
    images = [Image.new('RGB', (10, 10), (index, 40, 200)) for index in range(frames)]
    images[0].save(output, format='GIF', save_all=True, append_images=images[1:], duration=100, loop=0, optimize=False)
    return output.getvalue()


async def post(api, payload, purpose='wall', name='recurso.png'):
    return await api.post('/api/v1/assets', files={'file': (name, payload, 'application/octet-stream')}, data={'purpose': purpose})


@pytest.mark.parametrize('format', ['PNG', 'JPEG'])
async def test_static_images_preserve_dimensions_normalize_and_deduplicate(client, catalog_engine, format):
    api, _ = client
    payload = picture(format, (1200, 50))
    result = await post(api, payload)
    assert result.status_code == 201, result.text
    data = result.json()
    assert (data['width_px'], data['height_px']) == (1200, 50)
    assert data['mime_type'] == 'image/png' and data['frame_count'] == 1
    content = await api.get(data['content_url'])
    with Image.open(BytesIO(content.content)) as decoded:
        assert decoded.format == 'PNG' and decoded.size == (1200, 50)
        assert 'comment' not in decoded.info
    assert (await post(api, payload)).json()['id'] == data['id']
    with catalog_engine.connect() as connection:
        resource = connection.execute(select(media_asset).where(media_asset.c.id == UUID(data['id']))).one()
        assert resource.kind == 'image' and resource.static_preview_id is None
        assert connection.scalar(select(func.count()).select_from(media_asset)) == 1


async def test_gif_preview_and_wall_references_survive_removal(client, catalog_engine):
    api, app = client
    payload = animation()
    result = await post(api, payload, name='animacion.gif')
    assert result.status_code == 201, result.text
    data = result.json()
    assert data['mime_type'] == 'image/gif' and data['frame_count'] == 3
    assert (await api.get(data['content_url'])).content == payload
    preview = await api.get(data['static_preview_url'])
    with Image.open(BytesIO(preview.content)) as image:
        assert image.format == 'PNG' and getattr(image, 'n_frames', 1) == 1
    assert (await post(api, payload)).json() == data
    urls = []
    for name in ['A', 'B']:
        album = (await api.post('/api/v1/albums', json={'title': name})).json()
        url = f"/api/v1/albums/{album['id']}/wall"
        current = await api.get(url)
        element = dict(id=str(uuid4()), asset_id=data['id'], kind='gif', cx=.5, cy=.5, width=.2, height=.2, rotation_deg=0, z_index=0)
        saved = await api.put(url, headers={'If-Match': current.headers['etag']}, json={'schema_version': 1, 'background_color': '#242038', 'elements': [element]})
        assert saved.status_code == 200, saved.text
        assert saved.json()['elements'][0]['static_preview_url'] == data['static_preview_url']
        urls.append((url, saved))
    removed = await api.put(urls[0][0], headers={'If-Match': urls[0][1].headers['etag']}, json={'schema_version': 1, 'background_color': '#242038', 'elements': []})
    assert removed.status_code == 200 and removed.json()['elements'] == []
    assert (await api.get(urls[1][0])).json() == urls[1][1].json()
    assert (await api.get(data['content_url'])).content == payload
    assert (await api.get(data['static_preview_url'])).content == preview.content
    assert audit(catalog_engine, MediaStore(app.state.settings.media_root))['unreferenced_files'] == []


@pytest.mark.parametrize('payload', [b'', b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>', b'GIF89a\x00', b'not an image'])
async def test_invalid_visual_does_not_publish(client, catalog_engine, payload):
    api, app = client
    result = await post(api, payload, name='falsa.gif')
    assert result.status_code == 422 and result.json()['error']['code'] == 'invalid_visual'
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(media_asset)) == 0
    report = audit(catalog_engine, MediaStore(app.state.settings.media_root))
    assert report['unreferenced_files'] == report['staging_files'] == []


async def test_limits_and_cover_regression(client):
    api, _ = client
    assert (await post(api, picture(size=(4097, 1)))).status_code == 422
    assert (await post(api, animation(201))).status_code == 422
    assert (await post(api, b'x' * (5 * 1024 * 1024 + 1))).status_code == 422
    accepted = await post(api, animation(200))
    assert accepted.status_code == 201 and accepted.json()['frame_count'] == 200
    for purpose in ['cover', 'playlist']:
        assert (await post(api, animation(), purpose)).status_code == 422
    assert (await api.post('/api/v1/assets', files={'file': ('x.png', picture(), 'image/png')}, data={'purpose': 'unknown'})).status_code == 422


def test_decoding_budget_checked_before_loading_frames(monkeypatch):
    monkeypatch.setattr(visuals, 'MAX_DECODED_PIXELS', 299)
    with pytest.raises(ValueError, match='32 millones'):
        visuals.prepare_visual(animation(3))


async def test_storage_failure_rolls_back_gif_and_preview(client, catalog_engine, monkeypatch):
    api, app = client
    original = MediaStore.publish
    calls = 0
    def fail_second(store, staged, key):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('fallo de disco de prueba')
        return original(store, staged, key)
    monkeypatch.setattr(MediaStore, 'publish', fail_second)
    response = await post(api, animation())
    assert response.status_code == 503 and response.json()['error']['code'] == 'visual_storage_unavailable'
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(media_asset)) == 0
    report = audit(catalog_engine, MediaStore(app.state.settings.media_root))
    assert report['unreferenced_files'] == report['missing_asset_ids'] == report['staging_files'] == []
