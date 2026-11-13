"""P18 con PostgreSQL aislado y trabajador real; sin llamadas de IA."""
import asyncio
from time import monotonic
from uuid import UUID, uuid4
from alembic import command
import pytest
from sqlalchemy import select
from app.models.catalog import processing_job, track
from app.services import processing
from app.services.metadata import MetadataError
from app.processing_worker import ProcessingWorker
from test_metadata import client, tagged, upload
from test_database import migrate

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def imported(api):
    return UUID((await upload(api, tagged()))['track_id'])


async def wait_status(api, identity, expected):
    until = monotonic() + 8
    while monotonic() < until:
        result = await api.get(f'/api/v1/jobs/{identity}')
        assert result.status_code == 200, result.text
        if result.json()['status'] == expected:
            return result.json()
        await asyncio.sleep(.02)
    raise AssertionError(f'El trabajo no llegó a {expected}: {result.text}')


async def test_request_deduplicates_and_does_not_touch_track_or_audio(client, catalog_engine):
    api, app = client
    identity = await imported(api)
    before = await api.get(f'/api/v1/tracks/{identity}')
    results = await asyncio.gather(*[asyncio.to_thread(processing.enqueue, catalog_engine, identity) for _ in range(6)])
    assert len({r['id'] for r in results}) == 1
    response = await api.post(f'/api/v1/tracks/{identity}/processing-jobs', json={})
    assert response.status_code == 202 and response.json()['status'] == 'pending'
    assert response.json()['attempts'] == 0 and response.json()['input_version'] == before.json()['revision']
    assert len((await api.get(f'/api/v1/tracks/{identity}/processing-jobs')).json()['items']) == 1
    assert (await api.get(f'/api/v1/tracks/{identity}')).json() == before.json()
    audio = await api.get(f'/api/v1/tracks/{identity}/audio', headers={'Range': 'bytes=0-31'})
    assert audio.status_code == 206 and len(audio.content) == 32
    assert (await api.post(f'/api/v1/tracks/{identity}/processing-jobs', json={'operation': 'index_description'})).status_code == 422
    assert (await api.get(f'/api/v1/jobs/{uuid4()}')).status_code == 404


async def test_worker_completes_metadata_and_keeps_public_errors_safe(client, catalog_engine, monkeypatch):
    api, app = client
    identity = await imported(api)
    created = processing.enqueue(catalog_engine, identity)
    worker = ProcessingWorker(catalog_engine, interval=.02)
    worker.start()
    try:
        value = await wait_status(api, created['id'], 'completed')
        assert value['result']['title'] == 'Canción etiquetada'
        assert value['result']['source'] == 'metadata' and value['attempts'] == 1
        assert value['is_current'] is True and value['result']['metadata_sources']['title'] == 'file'
        assert value['started_at'] and value['finished_at']
        assert 'storage_key' not in str(value)
        assert processing.enqueue(catalog_engine, identity)['id'] == created['id']
        assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code == 200
    finally:
        worker.stop()
    assert not worker.thread.is_alive()
    with catalog_engine.begin() as connection:
        connection.execute(track.update().where(track.c.id == identity).values(revision=track.c.revision + 1))
    historical = (await api.get(f"/api/v1/jobs/{created['id']}")).json()
    assert historical['status'] == 'completed' and historical['is_current'] is False


async def test_failure_retry_limit_and_audio_survive(client, catalog_engine, monkeypatch):
    api, _ = client
    identity = await imported(api)
    created = processing.enqueue(catalog_engine, identity)
    def fail(*args):
        raise RuntimeError('secreto-no-publicar /ruta/privada')
    monkeypatch.setattr(processing, 'prepare', fail)
    worker = ProcessingWorker(catalog_engine, interval=.02); worker.start()
    try:
        for attempt in range(1, 4):
            value = await wait_status(api, created['id'], 'error')
            assert value['attempts'] == attempt and value['error_code'] == 'processing_failed'
            assert 'secreto' not in str(value) and value['result'] is None
            if attempt < 3:
                response = await api.post(f"/api/v1/jobs/{created['id']}/retry")
                assert response.status_code == 202
        assert (await api.post(f"/api/v1/jobs/{created['id']}/retry")).status_code == 409
        assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code == 200
    finally:
        worker.stop()


async def test_restart_recovers_processing_without_automatic_retry(client, catalog_engine):
    api, _ = client
    identity = await imported(api)
    created = processing.enqueue(catalog_engine, identity)
    claimed = processing.claim(catalog_engine)
    assert claimed.status == 'processing'
    worker = ProcessingWorker(catalog_engine, interval=.02); worker.start()
    try:
        value = await wait_status(api, created['id'], 'error')
        assert value['error_code'] == 'interrupted' and value['attempts'] == 1
        assert not processing.finish(catalog_engine, claimed, processing.prepare(catalog_engine, claimed))
        assert (await api.post(f"/api/v1/jobs/{created['id']}/retry")).status_code == 202
        value = await wait_status(api, created['id'], 'completed')
        assert value['attempts'] == 2
        assert not processing.finish(catalog_engine, claimed, failed=True)
    finally:
        worker.stop()


async def test_changed_input_is_stale_before_claim_and_after_processing(client, catalog_engine):
    api, _ = client
    identity = await imported(api)
    first = processing.enqueue(catalog_engine, identity)
    with catalog_engine.begin() as connection:
        connection.execute(track.update().where(track.c.id == identity).values(revision=first['input_version'] + 1, title='Cambio'))
    assert processing.claim(catalog_engine) is None
    value = (await api.get(f"/api/v1/jobs/{first['id']}")).json()
    assert value['status'] == 'stale' and value['attempts'] == 0
    assert (await api.post(f"/api/v1/jobs/{first['id']}/retry")).status_code == 409
    second = processing.enqueue(catalog_engine, identity)
    assert second['id'] != first['id'] and second['input_version'] == first['input_version'] + 1
    claimed = processing.claim(catalog_engine)
    result = processing.prepare(catalog_engine, claimed)
    with catalog_engine.begin() as connection:
        connection.execute(track.update().where(track.c.id == identity).values(revision=second['input_version'] + 1))
    assert processing.finish(catalog_engine, claimed, result)
    stale = (await api.get(f"/api/v1/jobs/{second['id']}")).json()
    assert stale['status'] == 'stale' and stale['result'] is None


async def test_atomic_claim_and_late_attempt_cannot_overwrite_retry(client, catalog_engine):
    api, _ = client
    identity = await imported(api)
    created = processing.enqueue(catalog_engine, identity)
    attempts = await asyncio.gather(*[asyncio.to_thread(processing.claim, catalog_engine) for _ in range(5)])
    claimed = [a for a in attempts if a is not None]
    assert len(claimed) == 1
    old = claimed[0]
    processing.finish(catalog_engine, old, failed=True)
    processing.retry(catalog_engine, created['id'])
    new = processing.claim(catalog_engine)
    assert new.attempts == 2
    assert not processing.finish(catalog_engine, old, processing.prepare(catalog_engine, old))
    assert processing.finish(catalog_engine, new, processing.prepare(catalog_engine, new))
    assert (await api.get(f"/api/v1/jobs/{created['id']}")).json()['status'] == 'completed'


async def test_second_worker_does_not_recover_live_owner(client, catalog_engine, monkeypatch):
    api, _ = client
    from threading import Event
    entered, release = Event(), Event()
    real = processing.prepare
    def slow(engine, claimed):
        entered.set(); release.wait(5)
        return real(engine, claimed)
    monkeypatch.setattr(processing, 'prepare', slow)
    identity = await imported(api); created = processing.enqueue(catalog_engine, identity)
    one = ProcessingWorker(catalog_engine, interval=.02); two = ProcessingWorker(catalog_engine, interval=.02)
    one.start()
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        two.start(); await asyncio.sleep(.1)
        current = (await api.get(f"/api/v1/jobs/{created['id']}")).json()
        assert current['status'] == 'processing' and current['attempts'] == 1
        release.set(); await wait_status(api, created['id'], 'completed')
    finally:
        release.set(); one.stop()
        if two.thread.ident is not None:
            two.stop()


async def test_downgrade_guard_preserves_jobs_and_catalog(client, catalog_engine):
    api, _ = client
    identity = await imported(api); created = processing.enqueue(catalog_engine, identity)
    with pytest.raises(RuntimeError, match='historial'):
        migrate(catalog_engine, command.downgrade, '0005_album_walls')
    assert (await api.get(f"/api/v1/jobs/{created['id']}")).status_code == 200
    assert (await api.get(f'/api/v1/tracks/{identity}')).status_code == 200
