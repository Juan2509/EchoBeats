"""Entrega de bytes reales y errores seguros en una base PostgreSQL aislada."""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.integrations.storage import MediaStore
from app.models.catalog import media_asset, track
from test_metadata import FIXTURES, client, upload

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def sample(api, app, engine):
    original = (FIXTURES / 'tono_grave.mp3').read_bytes()
    item = await upload(api, original, 'nombre_privado.mp3')
    url = f"/api/v1/tracks/{item['track_id']}/audio"
    with engine.connect() as connection:
        asset = connection.execute(select(media_asset).join(track, track.c.audio_asset_id == media_asset.c.id)
                                   .where(track.c.id == item['track_id'])).one()
    path = MediaStore(app.state.settings.media_root).path_for(asset.storage_key)
    return original, url, path, asset


async def test_full_audio_head_and_public_url(client, catalog_engine):
    api, app = client
    original, url, _, _ = await sample(api, app, catalog_engine)
    data = (await api.get(url.removesuffix('/audio'))).json()
    assert data['audio_url'] == url and data['duration_ms'] > 0
    full = await api.get(url)
    assert full.status_code == 200 and full.content == original
    assert full.headers['content-type'] == 'audio/mpeg'
    assert full.headers['accept-ranges'] == 'bytes'
    assert full.headers['content-length'] == str(len(original))
    assert full.headers['x-content-type-options'] == 'nosniff'
    assert full.headers['content-disposition'] == 'inline'
    assert full.headers['cache-control'] == 'private, no-cache'
    assert 'nombre_privado' not in str(full.headers)
    for headers in [{}, {'Range': 'bytes=10-19'}]:
        head = await api.head(url, headers=headers)
        assert head.status_code == 200 and head.content == b''
        for key in ['content-type', 'content-length', 'etag', 'last-modified', 'accept-ranges']:
            assert head.headers[key] == full.headers[key]


@pytest.mark.parametrize('header,start,stop', [
    ('bytes=0-31', 0, 32), ('bytes=1000-1999', 1000, 2000),
    ('bytes=1000-', 1000, None), ('bytes=-128', -128, None),
    ('bytes=0-999999999', 0, None),
])
async def test_ranges_are_exact_original_bytes(client, catalog_engine, header, start, stop):
    api, app = client
    original, url, _, _ = await sample(api, app, catalog_engine)
    partial = await api.get(url, headers={'Range': header})
    first = start if start >= 0 else len(original) + start
    end = stop if stop is not None else len(original)
    assert partial.status_code == 206
    assert partial.content == original[start:stop]
    assert partial.headers['content-range'] == f'bytes {first}-{end - 1}/{len(original)}'
    assert int(partial.headers['content-length']) == end - first


async def test_if_range_and_invalid_ranges(client, catalog_engine):
    api, app = client
    original, url, _, _ = await sample(api, app, catalog_engine)
    full = await api.get(url)
    for token in [full.headers['etag'], full.headers['last-modified']]:
        result = await api.get(url, headers={'Range': 'bytes=1000-1999', 'If-Range': token})
        assert result.status_code == 206 and result.content == original[1000:2000]
    changed = await api.get(url, headers={'Range': 'bytes=1000-1999', 'If-Range': '"obsolete"'})
    assert changed.status_code == 200 and changed.content == original
    invalid = await api.get(url, headers={'Range': f'bytes={len(original)}-'})
    assert invalid.status_code == 416
    assert invalid.headers['content-range'] == f'bytes */{len(original)}'
    malformed = await api.get(url, headers={'Range': 'bytes=no-es-un-rango'})
    assert malformed.status_code == 400
    multiple = await api.get(url, headers={'Range': 'bytes=0-9,1000-1009'})
    assert multiple.status_code == 206
    assert multiple.headers['content-type'].startswith('multipart/byteranges; boundary=')
    assert f'Content-Range: bytes 1000-1009/{len(original)}'.encode() in multiple.content
    assert len(multiple.content) == int(multiple.headers['content-length'])


async def test_unknown_track_and_invalid_id(client):
    api, _ = client
    for method in [api.get, api.head]:
        missing = await method(f'/api/v1/tracks/{uuid4()}/audio')
        assert missing.status_code == 404
        invalid = await method('/api/v1/tracks/not-a-uuid/audio')
        assert invalid.status_code == 422


@pytest.mark.parametrize('failure', ['missing', 'directory', 'truncated', 'wrong_kind', 'outside', 'permission'])
async def test_unavailable_resource_is_safe_and_preserves_track(client, catalog_engine, monkeypatch, failure):
    api, app = client
    original, url, path, asset = await sample(api, app, catalog_engine)
    expected = 404
    if failure == 'missing':
        path.unlink()  # solo fixture temporal; nunca MEDIA_ROOT principal
    elif failure == 'directory':
        path.unlink()
        path.mkdir()
    elif failure == 'truncated':
        path.write_bytes(original[:10])
    elif failure == 'wrong_kind':
        with catalog_engine.begin() as connection:
            connection.execute(media_asset.update().where(media_asset.c.id == asset.id).values(kind='image'))
    elif failure == 'outside':
        outside = path.parent.parent.parent / 'private.mp3'
        outside.write_bytes(original)
        path.unlink()
        path.symlink_to(outside)
    else:
        original_open = Path.open

        def denied(target, *args, **kwargs):
            if target == path:
                raise PermissionError(f'Privado: {target}')
            return original_open(target, *args, **kwargs)

        monkeypatch.setattr(Path, 'open', denied)
        expected = 503
    response = await api.get(url)
    assert response.status_code == expected
    assert response.json()['error']['code'] == ('media_unavailable' if expected == 503 else 'media_missing')
    assert str(path) not in response.text and asset.storage_key not in response.text
    assert (await api.get(url.removesuffix('/audio'))).status_code == 200
