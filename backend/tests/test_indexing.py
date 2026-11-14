"""pgvector real con proveedor falso solo en BD aislada; no acredita API real."""
import asyncio
from time import monotonic
from uuid import UUID
from pydantic import SecretStr
from sqlalchemy import select, func, text
import pytest
from alembic import command
from app.config import Settings
from app.models.catalog import track_embedding, track_description, processing_job
from app.processing_worker import ProcessingWorker
from app.services import indexing, processing, descriptions
from app.integrations.ai import AIError, OpenAIProvider
from test_metadata import client, tagged, upload
from test_descriptions import body
from test_database import migrate

pytestmark=[pytest.mark.integration,pytest.mark.anyio]


def config(**changes):
    return Settings(_env_file=None,ai_enabled=True,openai_api_key=SecretStr('fake-test-key'),**changes)


async def target(api):
    identity=UUID((await upload(api,tagged()))['track_id'])
    saved=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-None-Match':'*'},json=body())
    assert saved.status_code==200,saved.text
    return identity,saved


def result(settings):
    return {'model_key':indexing.model_key(settings),'vector':[1.0]+[0.0]*1535,'usage':{'prompt_tokens':12,'total_tokens':12}}


async def test_atomic_dedup_and_pgvector_persistence_without_regeneration(client,catalog_engine):
    api,app=client;settings=config();app.state.settings=settings
    identity,saved=await target(api)
    jobs=await asyncio.gather(*[asyncio.to_thread(indexing.enqueue,catalog_engine,identity,settings) for _ in range(5)])
    assert len({j['id'] for j in jobs})==1
    claimed=indexing.claim(catalog_engine,settings);assert claimed.attempts==1
    assert indexing.finish(catalog_engine,claimed,settings,result(settings))
    assert not indexing.finish(catalog_engine,claimed,settings,result(settings))
    repeated=indexing.enqueue(catalog_engine,identity,settings)
    assert repeated['id']==jobs[0]['id'] and repeated['status']=='completed'
    assert (await api.get(f'/api/v1/tracks/{identity}/index-status')).json()['status']=='ready'
    assert (await api.get(f'/api/v1/tracks/{identity}/description')).json()['index_status']=='ready'
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(track_embedding))==1
        vector=connection.scalar(select(track_embedding.c.embedding))
        assert len(vector)==1536 and vector[0]==1
        assert connection.scalar(text('SELECT vector_dims(embedding) FROM track_embedding'))==1536
    assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code==200


async def test_edit_and_model_change_cannot_publish_old_vector(client,catalog_engine):
    api,app=client;settings=config();app.state.settings=settings
    identity,saved=await target(api);indexing.enqueue(catalog_engine,identity,settings)
    claimed=indexing.claim(catalog_engine,settings)
    corrected=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':saved.headers['etag']},json=body(text='Descripción corregida'))
    assert indexing.finish(catalog_engine,claimed,settings,result(settings))
    assert (await api.get(f'/api/v1/jobs/{claimed.id}')).json()['status']=='stale'
    with catalog_engine.connect() as connection: assert connection.scalar(select(func.count()).select_from(track_embedding))==0
    new=indexing.enqueue(catalog_engine,identity,settings);assert new['input_version']==corrected.json()['version']
    current=indexing.claim(catalog_engine,settings)
    indexing.finish(catalog_engine,current,settings,result(settings))
    app.state.settings=settings.model_copy(update={'ai_embedding_dimensions':512})
    assert (await api.get(f'/api/v1/tracks/{identity}/index-status')).json()['status']=='stale'
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs')).status_code==409


async def test_stale_existing_vector_and_retry_version_guards(client,catalog_engine):
    api,app=client;settings=config();app.state.settings=settings
    identity,saved=await target(api);indexing.enqueue(catalog_engine,identity,settings)
    old=indexing.claim(catalog_engine,settings);indexing.finish(catalog_engine,old,settings,result(settings))
    await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':saved.headers['etag']},json=body(text='Versión nueva'))
    state=(await api.get(f'/api/v1/tracks/{identity}/index-status')).json()
    assert state['status']=='stale'
    assert (await api.post(f'/api/v1/jobs/{old.id}/retry')).status_code==409
    assert (await api.get(f'/api/v1/tracks/{identity}/description')).json()['needs_indexing'] is True


async def test_disabled_empty_missing_and_large_input_do_not_queue(client,catalog_engine):
    api,app=client;settings=config().model_copy(update={'ai_enabled':False});app.state.settings=settings
    identity,saved=await target(api)
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs')).status_code==503
    value=body(text='',features=[])
    changed=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':saved.headers['etag']},json=value)
    assert (await api.get(f'/api/v1/tracks/{identity}/index-status')).json()['status']=='incomplete_description'
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs')).status_code==409
    app.state.settings=config()
    await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':changed.headers['etag']},json=body(text='á'*5999))
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs')).status_code==422
    with catalog_engine.connect() as connection: assert connection.scalar(select(func.count()).select_from(processing_job))==0


async def test_worker_false_provider_real_db_and_retry_after_quota(client,catalog_engine):
    api,app=client;settings=config();app.state.settings=settings
    identity,_=await target(api);created=indexing.enqueue(catalog_engine,identity,settings)
    calls=[]
    class Fake:
        def __init__(self,settings):pass
        async def embed(self,text):
            calls.append(text)
            if len(calls)==1:raise AIError('ai_quota','credit_balance_exhausted')
            return {**result(settings),'model_key':OpenAIProvider(settings).model_key}
    worker=ProcessingWorker(catalog_engine,interval=.02,settings=settings,provider_factory=Fake);worker.start()
    async def wait(expected):
        until=monotonic()+8
        while monotonic()<until:
            value=(await api.get(f"/api/v1/jobs/{created['id']}")).json()
            if value['status']==expected:return value
            await asyncio.sleep(.02)
        raise AssertionError(value)
    try:
        failure=await wait('error');assert failure['error_code']=='ai_quota' and len(calls)==1
        await asyncio.sleep(.1);assert len(calls)==1
        assert (await api.post(f"/api/v1/jobs/{created['id']}/retry")).status_code==202
        completed=await wait('completed');assert completed['attempts']==2 and len(calls)==2
        assert 'vector' not in completed['result']
    finally:worker.stop()


async def test_interrupted_old_attempt_and_invalid_vector_never_publish(client,catalog_engine):
    api,app=client;settings=config();app.state.settings=settings
    identity,_=await target(api);created=indexing.enqueue(catalog_engine,identity,settings)
    old=indexing.claim(catalog_engine,settings);processing.recover(catalog_engine)
    indexing.retry(catalog_engine,created['id'],settings);new=indexing.claim(catalog_engine,settings)
    assert not indexing.finish(catalog_engine,old,settings,result(settings))
    with pytest.raises(AIError):indexing.finish(catalog_engine,new,settings,{'model_key':indexing.model_key(settings),'vector':[1.0],'usage':{}})
    indexing.finish(catalog_engine,new,settings,error_code='ai_invalid_response')
    with catalog_engine.connect() as connection:assert connection.scalar(select(func.count()).select_from(track_embedding))==0


async def test_downgrade_preserves_vectors_jobs_and_fichas(client,catalog_engine):
    api,_=client;settings=config();identity,_=await target(api)
    indexing.enqueue(catalog_engine,identity,settings);claimed=indexing.claim(catalog_engine,settings)
    indexing.finish(catalog_engine,claimed,settings,result(settings))
    with pytest.raises(RuntimeError,match='historial'):
        migrate(catalog_engine,command.downgrade,'0007_track_descriptions')
    assert (await api.get(f'/api/v1/tracks/{identity}/description')).status_code==200


async def test_metadata_revision_change_rejects_historical_index_and_claim_is_single(client,catalog_engine):
    from app.models.catalog import track
    api,app=client;settings=config();app.state.settings=settings
    identity,saved=await target(api)
    saved=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':saved.headers['etag']},json=body(source='metadata'))
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs',json={'model':'arbitrary'})).status_code==422
    queued=indexing.enqueue(catalog_engine,identity,settings)
    claims=await asyncio.gather(*[asyncio.to_thread(indexing.claim,catalog_engine,settings) for _ in range(5)])
    claimed=[row for row in claims if row is not None];assert len(claimed)==1
    indexing.finish(catalog_engine,claimed[0],settings,result(settings))
    with catalog_engine.begin() as connection:connection.execute(track.update().where(track.c.id==identity).values(revision=track.c.revision+1))
    assert (await api.get(f'/api/v1/tracks/{identity}/index-status')).json()['status']=='stale'
    assert (await api.get(f"/api/v1/jobs/{queued['id']}")).json()['is_current'] is False
    assert (await api.post(f'/api/v1/tracks/{identity}/index-jobs')).status_code==409
