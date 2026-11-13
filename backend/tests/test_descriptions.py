"""Fichas reales en PostgreSQL aislado; sin proveedor, audio o rasgos inventados."""
import asyncio
import hashlib
import json
from pathlib import Path
from uuid import UUID
from alembic import command
import pytest
from sqlalchemy import select, func
from app.models.catalog import track_description, description_revision, track
from test_metadata import client, tagged, upload
from test_database import migrate

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def body(**changes):
    return {'text': 'Tono sintético documentado por el generador.', 'features': [
        {'name': 'timbre', 'value': 'onda sinusoidal', 'source': 'verified', 'evidence': 'Parámetros del generador de prueba.', 'interpretation': False}],
        'source': 'verified', 'source_details': 'Generador original; no análisis de IA.', **changes}


async def target(api):
    identity = (await upload(api, tagged()))['track_id']
    return identity, f'/api/v1/tracks/{identity}/description'


async def test_create_update_history_and_audio_unchanged(client, catalog_engine):
    api, _ = client; identity, url = await target(api)
    before = (await api.get(f'/api/v1/tracks/{identity}')).json()
    missing = await api.get(url); assert missing.status_code == 404 and missing.json()['error']['code'] == 'description_missing'
    created = await api.put(url, headers={'If-None-Match': '*'}, json=body())
    assert created.status_code == 200, created.text
    first = created.json(); assert first['version'] == 1 and first['index_status'] == 'not_indexed' and first['needs_indexing']
    updated = await api.put(url, headers={'If-Match': created.headers['etag']}, json=body(text='Corrección manual.', source='manual'))
    assert updated.json()['version'] == 2 and updated.json()['id'] == first['id']
    historical = await api.get(url + '/versions/1')
    assert historical.json()['text'] == first['text'] and historical.json()['historical'] is True
    assert historical.json()['source_details'] == first['source_details']
    assert (await api.get(url)).json() == updated.json()
    assert (await api.get(f'/api/v1/tracks/{identity}')).json() == before
    assert (await api.get(f'/api/v1/tracks/{identity}/audio', headers={'Range':'bytes=0-31'})).status_code == 206
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(description_revision)) == 2


async def test_concurrent_creation_and_revision_conflict_keep_winner(client):
    api, _ = client; _, url = await target(api)
    assert (await api.put(url, json=body())).status_code == 428
    results = await asyncio.gather(*[api.put(url, headers={'If-None-Match': '*'}, json=body(text=str(i))) for i in range(2)])
    assert sorted(r.status_code for r in results) == [200, 412]
    saved = next(r for r in results if r.status_code == 200)
    assert (await api.put(url, json=body())).status_code == 428
    changed = await api.put(url, headers={'If-Match': saved.headers['etag']}, json=body(text='Nueva versión'))
    assert changed.status_code == 200
    stale = await api.put(url, headers={'If-Match': saved.headers['etag']}, json=body(text='Tardía'))
    assert stale.status_code == 412 and stale.headers['etag'] == changed.headers['etag']
    assert (await api.get(url)).json()['text'] == 'Nueva versión'


@pytest.mark.parametrize('invalid', [
    body(source='model'), body(source_details=''), body(text='x' * 6001),
    body(features=[{'name':'mood','value':'triste','source':'verified','evidence':'Título','interpretation':False}]),
    body(features=[{'name':'tempo_bpm','value':'NaN','source':'verified','evidence':'Fuente','interpretation':False}]),
    body(features=[{'name':'timbre','value':'seno','source':'verified','evidence':'','interpretation':False}]),
    body(features=[{'name':'unknown','value':'x','source':'manual','evidence':'Fuente','interpretation':False}]),
    body(features=body()['features'] * 2), body(text='x\x00y'),
])
async def test_invalid_features_do_not_replace_manual_description(client, invalid):
    api, _ = client; _, url = await target(api)
    created = await api.put(url, headers={'If-None-Match':'*'}, json=body(source='manual'))
    rejected = await api.put(url, headers={'If-Match':created.headers['etag']}, json=invalid)
    assert rejected.status_code == 422, rejected.text
    assert (await api.get(url)).json() == created.json()


async def test_incomplete_and_interpretation_are_explicit_noop_does_not_bump(client):
    api, _ = client; identity, url = await target(api)
    data = body(text='', features=[], source='manual')
    saved = await api.put(url, headers={'If-None-Match':'*'}, json=data)
    assert saved.status_code == 200 and saved.json()['can_index'] is False and saved.json()['needs_indexing'] is False
    repeat = await api.put(url, headers={'If-Match':saved.headers['etag']}, json=data)
    assert repeat.headers['etag'] == saved.headers['etag'] and repeat.json()['version'] == 1
    data = body(features=[{'name':'mood','value':'pausado','source':'manual','evidence':'Interpretación personal, no acústica objetiva.','interpretation':True}])
    value = await api.put(url, headers={'If-Match':saved.headers['etag']}, json=data)
    assert value.json()['features'][0]['interpretation'] is True
    assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code == 200


async def test_metadata_derived_ficha_becomes_stale_without_overwriting_it(client, catalog_engine):
    api, _ = client; identity, url = await target(api)
    created = await api.put(url, headers={'If-None-Match':'*'}, json=body(source='metadata'))
    assert created.json()['metadata_stale'] is False
    with catalog_engine.begin() as connection:
        connection.execute(track.update().where(track.c.id == UUID(identity)).values(revision=track.c.revision + 1, title='Título corregido'))
    stale = (await api.get(url)).json()
    assert stale['metadata_stale'] is True and stale['can_index'] is False
    assert stale['text'] == created.json()['text']
    corrected = await api.put(url, headers={'If-Match':created.headers['etag']}, json=body(source='metadata', text='Datos corregidos con el título nuevo.'))
    assert corrected.json()['metadata_stale'] is False and corrected.json()['version'] == 2


async def test_metadata_job_does_not_overwrite_ficha_and_downgrade_protected(client, catalog_engine):
    api, _ = client; identity, url = await target(api)
    saved = await api.put(url, headers={'If-None-Match':'*'}, json=body(source='manual'))
    from app.services import processing
    processing.enqueue(catalog_engine, UUID(identity)); claimed = processing.claim(catalog_engine)
    processing.finish(catalog_engine, claimed, processing.prepare(catalog_engine, claimed))
    assert (await api.get(url)).json() == saved.json()
    with pytest.raises(RuntimeError, match='historial'):
        migrate(catalog_engine, command.downgrade, '0006_processing_jobs')
    assert (await api.get(url)).json() == saved.json()


async def test_p17_profiles_import_by_hash_and_preserve_actual_audio(client):
    api, _ = client
    root = Path('/app/semantic-fixtures')
    if not root.is_dir():
        root = Path(__file__).resolve().parents[2] / 'pruebas' / 'semantica'
    profiles = json.loads((root / 'fichas.json').read_text())['proposals']
    assert len(profiles) == 5
    for proposal in profiles:
        audio = (root / proposal['file']).read_bytes()
        assert hashlib.sha256(audio).hexdigest() == proposal['content_sha256']
        imported = await api.post('/api/v1/imports', files={'files': (proposal['file'], audio, 'audio/wav')})
        identity = imported.json()['results'][0]['track_id']
        track_data = (await api.get(f'/api/v1/tracks/{identity}')).json()
        assert track_data['content_sha256'] == proposal['content_sha256']
        saved = await api.put(f'/api/v1/tracks/{identity}/description', headers={'If-None-Match':'*'}, json=proposal['body'])
        assert saved.status_code == 200, saved.text
        assert saved.json()['source'] == 'verified' and saved.json()['can_index'] is True
        assert not any(f['name'] in {'mood','energy','context'} for f in saved.json()['features'])
        assert (await api.get(f'/api/v1/tracks/{identity}/audio')).content == audio
