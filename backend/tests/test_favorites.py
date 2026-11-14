"""Favoritos persistentes en bases aisladas, sin consumo de IA."""
from uuid import uuid4
import os
import subprocess
import sys
from anyio import to_thread
import pytest
from alembic import command
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from app.main import create_app
from app.config import Settings
from app.models.catalog import favorite, track
from test_metadata import client, tagged, upload
from test_database import migrate

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def check_in_new_process(engine, identity, desired):
    # Proceso de API nuevo, apuntando exclusivamente a la base aleatoria del caso.
    assert engine.url.database.startswith('echobeats_test_')
    code = '''
import asyncio, os
from httpx import AsyncClient, ASGITransport
from pydantic import SecretStr
from app.main import create_app
from app.config import Settings
async def main():
    name=os.environ['TEST_FAVORITES_DATABASE']
    assert name.startswith('echobeats_test_')
    settings=Settings().model_copy(update={'postgres_db':name,'database_url':SecretStr(''),'processing_worker_enabled':False})
    app=create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://localhost') as api:
        response=await api.get('/api/v1/tracks/'+os.environ['TEST_FAVORITES_TRACK']+'/favorite')
        assert response.status_code==200
        assert response.json()['favorite'] is (os.environ['TEST_FAVORITES_DESIRED']=='true')
    app.state.database_engine.dispose()
asyncio.run(main())
'''
    env = {**os.environ, 'TEST_FAVORITES_DATABASE': engine.url.database,
           'TEST_FAVORITES_TRACK': identity, 'TEST_FAVORITES_DESIRED': 'true' if desired else 'false'}
    result = await to_thread.run_sync(lambda: subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, timeout=30))
    assert result.returncode == 0, 'El proceso nuevo no confirmó el estado persistente en la base aislada.'


async def test_explicit_idempotent_state_and_persistence_across_app_restart(client, catalog_engine):
    api, _ = client
    identity = (await upload(api, tagged()))['track_id']
    url = f'/api/v1/tracks/{identity}/favorite'
    initial = await api.get(url)
    assert initial.json()['favorite'] is False and initial.headers['cache-control'] == 'no-store'
    first = await api.put(url, json={'favorite': True})
    again = await api.put(url, json={'favorite': True})
    assert first.status_code == again.status_code == 200 and first.json() == again.json()
    await check_in_new_process(catalog_engine, identity, True)
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(favorite)) == 1
        revision = connection.scalar(select(track.c.revision))
    app = create_app(Settings(_env_file=None, processing_worker_enabled=False))
    original = app.state.database_engine
    app.state.database_engine = catalog_engine
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://localhost') as restarted:
            assert (await restarted.get(url)).json()['favorite'] is True
            assert (await restarted.get('/api/v1/favorites')).json()['items'][0]['id'] == identity
            assert (await restarted.put(url, json={'favorite': False})).json()['favorite'] is False
            assert (await restarted.put(url, json={'favorite': False})).json()['created_at'] is None
        await check_in_new_process(catalog_engine, identity, False)
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://localhost') as reconnected:
            assert (await reconnected.get(url)).json()['favorite'] is False
            assert (await reconnected.get('/api/v1/favorites')).json()['total'] == 0
        with catalog_engine.connect() as connection:
            assert connection.scalar(select(track.c.revision)) == revision
    finally:
        if original is not None: original.dispose()


async def test_filtered_paginated_favorites_and_audio_are_only_saved_tracks(client):
    api, _ = client
    a = (await upload(api, tagged(title='Alfa 100%', collection='Disco', names=['Lunar'])))['track_id']
    b = (await upload(api, tagged(title='Beta', collection='Otro')))['track_id']
    await upload(api, tagged(title='No favorita', collection='Disco'))
    for identity in [a, b]:
        await api.put(f'/api/v1/tracks/{identity}/favorite', json={'favorite': True})
    first = (await api.get('/api/v1/favorites', params={'limit': 1})).json()
    second = (await api.get('/api/v1/favorites', params={'limit': 1, 'offset': 1})).json()
    assert first['total'] == second['total'] == 2
    assert [first['items'][0]['id'], second['items'][0]['id']] == [a, b]
    for query in ['%', 'LUNAR', 'Disco']:
        result = (await api.get('/api/v1/favorites', params={'q': query})).json()
        assert [item['id'] for item in result['items']] == [a]
    assert (await api.get(first['items'][0]['audio_url'])).status_code == 200
    assert (await api.get('/api/v1/favorites', params={'offset': 20})).json()['items'] == []
    assert (await api.get('/api/v1/favorites', params={'q': "' OR 1=1 --"})).json()['total'] == 0


@pytest.mark.parametrize('body', [{'favorite': 'true'}, {'favorite': 1}, {'favorite': None}, {}, {'favorite': True, 'user_id': 'x'}])
async def test_invalid_input_never_creates_favorites(client, body):
    api, _ = client
    identity = (await upload(api, tagged()))['track_id']
    assert (await api.put(f'/api/v1/tracks/{identity}/favorite', json=body)).status_code == 422
    assert (await api.get('/api/v1/favorites')).json()['total'] == 0


async def test_unknown_track_origin_and_limits(client):
    api, _ = client
    url = f'/api/v1/tracks/{uuid4()}/favorite'
    assert (await api.get(url)).status_code == 404
    assert (await api.put(url, json={'favorite': True})).status_code == 404
    assert (await api.put(url, json={'favorite': True}, headers={'Origin': 'https://foreign.example'})).status_code == 403
    for params in [{'limit': 101}, {'limit': 0}, {'offset': -1}]:
        assert (await api.get('/api/v1/favorites', params=params)).status_code == 422


async def test_downgrade_refuses_saved_favorites_and_empty_roundtrip(client, catalog_engine):
    api, _ = client
    identity = (await upload(api, tagged()))['track_id']
    await api.put(f'/api/v1/tracks/{identity}/favorite', json={'favorite': True})
    with pytest.raises(RuntimeError, match='favoritos existentes'):
        migrate(catalog_engine, command.downgrade, '0008_track_embeddings')
    assert (await api.get(f'/api/v1/tracks/{identity}/favorite')).json()['favorite'] is True
    await api.put(f'/api/v1/tracks/{identity}/favorite', json={'favorite': False})
    migrate(catalog_engine, command.downgrade, '0008_track_embeddings')
    migrate(catalog_engine, command.upgrade, 'head')
    assert (await api.get('/api/v1/favorites')).json()['total'] == 0
