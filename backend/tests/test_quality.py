"""P27: presupuestos observables, contrato de datos y recursos en bases aisladas."""
import json
from pathlib import Path
from time import perf_counter
from uuid import UUID
from sqlalchemy import event, select
import pytest
from app.models.catalog import media_asset
from app.integrations.storage import MediaStore
from test_metadata import client, tagged, upload, png
from test_visuals import animation
from test_walls import composition, element
from test_search import add, enable, vec
from test_exploration import Selecting

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_collection_query_budgets_and_resource_sizes(client,catalog_engine,record_testsuite_property):
    api,_=client
    identities=[]
    for index in range(24):
        identities.append((await upload(api,tagged(title=f'Calidad {index:02}',collection=f'Disco {index:02}',names=['Uno','Dos'])))['track_id'])
    metrics={}
    for name,path in [('tracks_24','/api/v1/tracks?limit=24'),('albums_24','/api/v1/albums?limit=24&include_empty_system=false')]:
        statements=[]
        def count(_connection,_cursor,statement,_params,_context,_many): statements.append(statement)
        event.listen(catalog_engine,'before_cursor_execute',count)
        started=perf_counter()
        try: response=await api.get(path)
        finally: event.remove(catalog_engine,'before_cursor_execute',count)
        assert response.status_code==200 and len(response.json()['items'])==24
        metrics[name]={'sql_statements':len(statements),'milliseconds':round((perf_counter()-started)*1000,3),'response_bytes':len(response.content)}
        assert len(statements)<=4, f'{name}: se superó el presupuesto de cuatro consultas por página'
        if name=='tracks_24':
            for item in response.json()['items']:
                assert item==(await api.get('/api/v1/tracks/'+item['id'])).json()
        else:
            for item in response.json()['items']:
                assert item==(await api.get('/api/v1/albums/'+item['id'])).json()
    picture=await api.post('/api/v1/assets',files={'file':('calidad.png',png(),'image/png')},data={'purpose':'wall'})
    gif=await api.post('/api/v1/assets',files={'file':('calidad.gif',animation(3),'image/gif')},data={'purpose':'wall'})
    assert picture.status_code==gif.status_code==201
    track=(await api.get('/api/v1/tracks/'+identities[0])).json()
    wall_url='/api/v1/albums/'+track['album_id']+'/wall'
    initial=await api.get(wall_url)
    objects=[element(gif.json()['id'] if index%2 else picture.json()['id'],kind='gif' if index%2 else 'poster',z_index=index) for index in range(30)]
    saved=await api.put(wall_url,headers={'If-Match':initial.headers['etag']},json=composition(*objects))
    assert saved.status_code==200,saved.text
    resources={}
    for obj in saved.json()['elements']:
        for url in [obj['content_url'],obj['static_preview_url']]:
            if url and url not in resources:
                response=await api.get(url)
                assert response.status_code==200
                resources[url]=len(response.content)
    metrics['wall_30']={'json_bytes':len(saved.content),'unique_resource_urls':len(resources),'unique_resource_bytes':sum(resources.values())}
    audio_url=track['audio_url']
    response=await api.get(audio_url,headers={'Range':'bytes=100-199'})
    assert response.status_code==206 and len(response.content)==100
    metrics['audio_range']={'bytes':len(response.content),'content_range':response.headers['content-range']}
    record_testsuite_property('p27_measurements',json.dumps(metrics,sort_keys=True))


async def test_visual_delivery_checks_size_permissions_and_symlink_without_private_errors(client,catalog_engine,monkeypatch,tmp_path):
    api,app=client
    uploaded=await api.post('/api/v1/assets',files={'file':('imagen.png',png(),'image/png')},data={'purpose':'wall'})
    assert uploaded.status_code==201
    url=uploaded.json()['content_url']
    with catalog_engine.connect() as connection:
        key=connection.scalar(select(media_asset.c.storage_key).where(media_asset.c.id==UUID(uploaded.json()['id'])))
    path=MediaStore(app.state.settings.media_root).path_for(key)
    original=path.read_bytes()
    path.write_bytes(b'bad')
    broken=await api.get(url)
    assert broken.status_code==404 and broken.json()['error']['code']=='media_missing'
    path.write_bytes(original)
    real_open=Path.open
    def denied(target,*args,**kwargs):
        if target==path: raise PermissionError('/private/path DO_NOT_EXPOSE')
        return real_open(target,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path,'open',denied)
        unavailable=await api.get(url)
        assert unavailable.status_code==503 and unavailable.json()['error']['code']=='media_unavailable'
        assert 'DO_NOT_EXPOSE' not in unavailable.text and '/private' not in unavailable.text
    assert (await api.get(url)).content==original
    path.unlink()
    secret=tmp_path/'outside.png';secret.write_bytes(b'DO_NOT_EXPOSE')
    path.symlink_to(secret)
    assert (await api.get(url)).status_code==404


async def test_batch_reads_preserve_manual_cover_and_inherited_cover(client):
    api,_=client
    first=await upload(api,tagged(title='Heredada',collection='Portadas'))
    second=await upload(api,tagged(title='Manual',collection='Portadas'))
    original=await api.get('/api/v1/tracks/'+first['track_id'])
    album_url='/api/v1/albums/'+original.json()['album_id']
    album=await api.get(album_url)
    cover=await api.post('/api/v1/assets',files={'file':('portada.png',png(),'image/png')},data={'purpose':'cover'})
    assert (await api.patch(album_url,headers={'If-Match':album.headers['etag']},json={'cover_asset_id':cover.json()['id']})).status_code==200
    manual=await api.get('/api/v1/tracks/'+second['track_id'])
    assert (await api.patch('/api/v1/tracks/'+second['track_id'],headers={'If-Match':manual.headers['etag']},json={'cover_asset_id':None})).status_code==200
    page=(await api.get('/api/v1/tracks')).json()
    values={item['id']:item for item in page['items']}
    assert values[first['track_id']]['cover_source']=='album' and values[first['track_id']]['cover_url']==cover.json()['content_url']
    assert values[second['track_id']]['cover_source']=='manual' and values[second['track_id']]['cover_url'] is None
    assert [artist['name'] for artist in values[first['track_id']]['artists']]==['Artista de prueba']


async def test_exploration_provider_budget_is_bounded_and_never_sends_audio(client,catalog_engine,record_testsuite_property):
    api,app=client;settings,_=enable(app)
    for index in range(6):
        await add(api,catalog_engine,settings,f'Ficha {index}','Campanas sintéticas con fuente.',vec(1,index*.1))
    class Measured(Selecting):
        async def embed(self,query):
            assert catalog_engine.pool.checkedout()==0
            return await super().embed(query)
        async def generate(self,query,sources):
            assert catalog_engine.pool.checkedout()==0
            assert len(sources)<=5 and all(set(source)=={'source_id','version','text'} for source in sources)
            return await super().generate(query,sources)
    provider=Measured(settings);app.state.ai_provider=provider
    started=perf_counter()
    response=await api.post('/api/v1/explore/search',json={'query':'campanas','mode':'semantic','limit':6,'explain':True})
    assert response.status_code==200 and len(response.json()['results'])==6
    assert len(provider.calls)==len(provider.generations)==1
    sources=provider.generations[0][1]
    record_testsuite_property('p27_exploration',json.dumps({'milliseconds_simulated':round((perf_counter()-started)*1000,3),
        'response_bytes':len(response.content),'embedding_calls_simulated':len(provider.calls),
        'generation_calls_simulated':len(provider.generations),'context_sources':len(sources),
        'context_bytes':len(json.dumps({'query':'campanas','sources':sources},ensure_ascii=False).encode())},sort_keys=True))
