"""Formatos reales, conservación de originales y migración no destructiva."""

import hashlib
from io import BytesIO
import json
import wave

from alembic import command
from mutagen import File
from sqlalchemy import select
import pytest

from app.database import migration_config
from app.integrations.storage import MediaStore
from app.models.catalog import media_asset, track
from test_metadata import FIXTURES, client

pytestmark = [pytest.mark.integration, pytest.mark.anyio]
FILES = json.loads((FIXTURES / 'multiformato' / 'manifest.json').read_text(encoding='utf-8'))['files']


@pytest.mark.parametrize('fixture', FILES, ids=lambda row: row['file'])
async def test_import_tags_cover_ranges_and_manual_changes(client, catalog_engine, fixture):
    api, app = client
    original = (FIXTURES / 'multiformato' / fixture['file']).read_bytes()
    assert hashlib.sha256(original).hexdigest() == fixture['sha256']
    response = await api.post('/api/v1/imports', files={'files': (fixture['file'].upper(), original, 'application/octet-stream')})
    item = response.json()['results'][0]
    assert item['status'] == 'imported', item
    assert not item.get('metadata_warnings'), item
    url = f"/api/v1/tracks/{item['track_id']}"
    initial = await api.get(url)
    data = initial.json()
    assert data['title'] == fixture['title']
    assert data['album_title'] == 'Colección multiformato'
    assert [value['name'] for value in data['artists']] == ['Señal técnica EchoBeats']
    assert data['audio_mime_type'] == fixture['mime_type']
    assert data['duration_ms'] == pytest.approx(2500, abs=50)
    assert data['track_number'] in {1, 2, 3, 4}
    assert (await api.get(data['cover_url'])).headers['content-type'] == 'image/png'
    for method in [api.get, api.head]:
        result = await method(data['audio_url'])
        assert result.status_code == 200
        assert result.headers['content-type'] == fixture['mime_type']
        assert int(result.headers['content-length']) == len(original)
        if method == api.get:
            assert result.content == original
    for header, expected in [('bytes=1000-1999', original[1000:2000]), ('bytes=-128', original[-128:])]:
        partial = await api.get(data['audio_url'], headers={'Range': header})
        assert partial.status_code == 206 and partial.content == expected
    changed = await api.patch(url, headers={'If-Match': initial.headers['etag']}, json={'title': 'Corrección manual'})
    assert changed.status_code == 200
    reread = await api.post(url + '/extract-metadata', headers={'If-Match': changed.headers['etag']})
    assert reread.json()['title'] == 'Corrección manual'
    duplicate = (await api.post('/api/v1/imports', files={'files': (fixture['file'], original)})).json()['results'][0]
    assert duplicate['status'] == 'duplicate' and duplicate['track_id'] == item['track_id']
    assert (await api.get(url)).json()['title'] == 'Corrección manual'
    with catalog_engine.connect() as connection:
        asset = connection.execute(select(media_asset).where(media_asset.c.kind == 'audio')).one()
    assert MediaStore(app.state.settings.media_root).path_for(asset.storage_key).read_bytes() == original


@pytest.mark.parametrize('name', ['falso.wav', 'falso.flac', 'falso.ogg', 'falso.opus'])
async def test_disguised_mp3_is_not_accepted_as_other_format(client, name):
    api, _ = client
    original = (FIXTURES / 'tono_grave.mp3').read_bytes()
    result = (await api.post('/api/v1/imports', files={'files': (name, original)})).json()['results'][0]
    assert result['status'] == 'rejected' and result['error']['code'] == 'invalid_audio'
    assert (await api.get('/api/v1/tracks')).json()['total'] == 0


async def test_mixed_batch_alias_duplicate_and_unsupported_files(client):
    api, _ = client
    directory = FIXTURES / 'multiformato'
    opus = (directory / 'tono.opus').read_bytes()
    files = [('files', ('opus-en-ogg.ogg', opus)), ('files', ('copia.opus', opus)),
             ('files', ('vorbis.opus', (directory / 'tono.ogg').read_bytes())),
             ('files', ('truncado.wav', (directory / 'tono.wav').read_bytes()[:1000])),
             ('files', ('no-admitido.aiff', b'FORM')), ('files', ('incorrecto.flac', b'fLaC'))]
    results = (await api.post('/api/v1/imports', files=files)).json()['results']
    assert [item['status'] for item in results] == ['imported', 'duplicate', 'rejected', 'rejected', 'rejected', 'rejected']
    assert results[0]['track_id'] == results[1]['track_id']
    assert results[4]['error']['code'] == 'unsupported_format'


async def test_no_tags_and_compressed_wav_are_handled(client, tmp_path):
    api, _ = client
    path = tmp_path / 'unlabelled.flac'
    path.write_bytes((FIXTURES / 'multiformato' / 'tono.flac').read_bytes())
    audio = File(path); audio.delete(); audio = File(path); audio.clear_pictures(); audio.save()
    item = (await api.post('/api/v1/imports', files={'files': ('sin-datos.flac', path.read_bytes())})).json()['results'][0]
    data = (await api.get(f"/api/v1/tracks/{item['track_id']}")).json()
    assert data['title'] == 'sin-datos' and data['album_title'] == 'Sin álbum'
    wav = bytearray((FIXTURES / 'multiformato' / 'tono.wav').read_bytes())
    # La fixture tiene fmt PCM en el offset 20: simular IEEE float (no prometido).
    wav[20:22] = b'\x03\x00'
    result = (await api.post('/api/v1/imports', files={'files': ('float.wav', bytes(wav))})).json()['results'][0]
    assert result['status'] == 'rejected'


async def test_invalid_ogg_cover_does_not_prevent_import(client, tmp_path):
    api, _ = client
    path = tmp_path / 'bad-cover.ogg'; path.write_bytes((FIXTURES / 'multiformato' / 'tono.ogg').read_bytes())
    audio = File(path); audio['metadata_block_picture'] = ['no-es-base64']; audio.save()
    result = (await api.post('/api/v1/imports', files={'files': (path.name, path.read_bytes())})).json()['results'][0]
    assert result['status'] == 'imported' and result['metadata_warnings'] == ['cover_ignored']


@pytest.mark.parametrize('width', [1, 3, 4], ids=['PCM8', 'PCM24', 'PCM32'])
async def test_other_integer_pcm_widths(client, width):
    api, _ = client
    stream = BytesIO()
    with wave.open(stream, 'wb') as audio:
        audio.setparams((2, width, 8000, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\x00' * (8000 * 2 * width))
    original = stream.getvalue()
    result = (await api.post('/api/v1/imports', files={'files': (f'pcm{width * 8}.wav', original)})).json()['results'][0]
    assert result['status'] == 'imported', result
    data = (await api.get(f"/api/v1/tracks/{result['track_id']}")).json()
    assert data['duration_ms'] == 1000 and data['audio_mime_type'] == 'audio/wav'
    assert (await api.get(data['audio_url'])).content == original


async def test_downgrade_refuses_to_remove_support_with_new_assets(client, catalog_engine):
    api, _ = client
    original = (FIXTURES / 'multiformato' / 'tono.flac').read_bytes()
    item = (await api.post('/api/v1/imports', files={'files': ('tono.flac', original)})).json()['results'][0]
    with pytest.raises(RuntimeError, match='existen medios'):
        with catalog_engine.begin() as connection:
            config = migration_config(); config.attributes['connection'] = connection
            command.downgrade(config, '0003_metadata')
    assert (await api.get(f"/api/v1/tracks/{item['track_id']}/audio")).content == original
