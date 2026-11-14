"""SQL/pgvector reales, embeddings simulados en BD aislada; sin saldo ni red."""
from uuid import UUID,uuid4
import pytest
from app.integrations.ai import OpenAIProvider,AIError
from app.services import indexing,descriptions
from test_metadata import client,tagged,upload
from test_descriptions import body
from test_indexing import config,result

pytestmark=[pytest.mark.integration,pytest.mark.anyio]


def vec(a,b=0):return [a,b]+[0.0]*1534


class Fake:
    def __init__(self,settings):self.settings=settings;self.calls=[]
    async def embed(self,query):
        self.calls.append(query)
        return {'vector':vec(1),'model_key':OpenAIProvider(self.settings).model_key,'usage':{'prompt_tokens':5,'total_tokens':5}}


def enable(app,**kwargs):
    settings=config(**kwargs);provider=Fake(settings)
    app.state.settings=settings;app.state.ai_provider=provider
    return settings,provider


async def add(api,engine,settings,title,description,vector,collection='Colección búsqueda',source='verified'):
    identity=UUID((await upload(api,tagged(title=title,collection=collection)))['track_id'])
    saved=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-None-Match':'*'},json=body(text=description,source=source))
    assert saved.status_code==200,saved.text
    indexing.enqueue(engine,identity,settings);claimed=indexing.claim(engine,settings)
    indexing.finish(engine,claimed,settings,{**result(settings),'vector':vector})
    return identity,saved


async def test_empty_and_unindexed_library_do_not_call_provider(client):
    api,app=client;_,provider=enable(app)
    empty=await api.post('/api/v1/explore/search',json={'query':'tranquilo'})
    assert empty.status_code==200 and empty.json()['status']=='no_library'
    identity=(await upload(api,tagged()))['track_id']
    value=await api.post('/api/v1/explore/search',json={'query':'tranquilo'})
    assert value.json()['status']=='no_indexed_tracks' and not provider.calls
    assert (await api.get(f'/api/v1/tracks/{identity}/similar')).status_code==409


async def test_exact_cosine_ranking_lexical_and_hybrid_are_grounded(client,catalog_engine):
    api,app=client;settings,provider=enable(app)
    a,_=await add(api,catalog_engine,settings,'Órbita lenta','Sintetizador sinusoidal sin percusión.',vec(1))
    b,_=await add(api,catalog_engine,settings,'Campanas al sol','Campanas sintetizadas a pulso medio.',vec(.8,.6))
    await add(api,catalog_engine,settings,'Impulso','Percusión sintetizada rápida.',vec(0,1))
    response=await api.post('/api/v1/explore/search',json={'query':'tono puro','mode':'semantic','limit':2})
    assert response.status_code==200,response.text
    data=response.json();assert [r['track']['id'] for r in data['results']]==[str(a),str(b)]
    assert data['results'][0]['distance']==pytest.approx(0,abs=1e-6)
    assert data['results'][1]['distance']==pytest.approx(.2,abs=1e-6)
    assert data['relevance']=='candidates_only' and data['warnings']
    assert len(provider.calls)==1 and data['query_usage']['total_tokens']==5
    lexical=await api.post('/api/v1/explore/search',json={'query':'Campanas al sol','mode':'lexical'})
    assert lexical.status_code==200,lexical.text
    assert lexical.json()['results'][0]['track']['id']==str(b) and len(provider.calls)==1
    hybrid=await api.post('/api/v1/explore/search',json={'query':'Campanas al sol','mode':'hybrid'})
    item=hybrid.json()['results'][0]
    assert item['track']['id']==str(b) and item['fusion_score']>0
    assert item['evidence'][0]['version']==item['description']['version']
    assert 'embedding' not in item and item['explanation_source']=='recorded'
    assert (await api.get(item['track']['audio_url'])).status_code==200


async def test_album_playlist_filters_reference_exclusion_and_no_external_reference_call(client,catalog_engine):
    api,app=client;settings,provider=enable(app)
    a,_=await add(api,catalog_engine,settings,'Referencia','Tono estable',vec(1),'Disco A')
    b,_=await add(api,catalog_engine,settings,'Vecina','Tono similar',vec(.9,.1),'Disco B')
    c,_=await add(api,catalog_engine,settings,'Otra','Ritmo diferente',vec(0,1),'Disco C')
    album=(await api.get(f'/api/v1/tracks/{b}')).json()['album_id']
    value=(await api.get(f'/api/v1/tracks/{a}/similar',params={'album_id':album})).json()
    assert [r['track']['id'] for r in value['results']]==[str(b)] and not provider.calls
    created=await api.post('/api/v1/playlists',json={'name':'Filtro'})
    assert created.status_code==201,created.text
    pid=created.json()['id']
    saved=await api.put(f'/api/v1/playlists/{pid}/tracks',headers={'If-Match':created.headers['etag']},json={'track_ids':[str(c)]})
    assert saved.status_code==200,saved.text
    found=await api.post('/api/v1/explore/search',json={'query':'tono','playlist_id':pid,'limit':20})
    assert [r['track']['id'] for r in found.json()['results']]==[str(c)]
    similar=(await api.get(f'/api/v1/tracks/{a}/similar')).json()
    assert str(a) not in [r['track']['id'] for r in similar['results']]
    assert (await api.post('/api/v1/explore/search',json={'query':'x','playlist_id':str(uuid4())})).status_code==404


async def test_stale_versions_metadata_and_wrong_spaces_are_excluded(client,catalog_engine):
    api,app=client;settings,provider=enable(app)
    identity,saved=await add(api,catalog_engine,settings,'Vieja','Datos originales',vec(1))
    await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-Match':saved.headers['etag']},json=body(text='Actualizada'))
    value=(await api.post('/api/v1/explore/search',json={'query':'datos'})).json()
    assert value['status']=='no_indexed_tracks' and not provider.calls
    # Otro model_key no permite rescatar el vector histórico.
    app.state.settings=settings.model_copy(update={'ai_embedding_dimensions':512})
    assert (await api.post('/api/v1/explore/search',json={'query':'x'})).status_code==409


async def test_edit_during_provider_wait_is_rechecked_in_new_snapshot(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    identity,saved=await add(api,catalog_engine,settings,'Concurrente','Información previa',vec(1))
    class Editing(Fake):
        async def embed(self,query):
            assert catalog_engine.pool.checkedout()==0
            descriptions.save(catalog_engine,identity,body(text='Información corregida'),saved.headers['etag'],None)
            return await super().embed(query)
    app.state.ai_provider=Editing(settings)
    value=(await api.post('/api/v1/explore/search',json={'query':'información'})).json()
    assert value['status']=='no_matches' and value['results']==[]


async def test_optional_distance_limit_and_lexical_absence_do_not_invent_matches(client,catalog_engine):
    api,app=client;settings,provider=enable(app,search_max_cosine_distance=.1)
    identity,_=await add(api,catalog_engine,settings,'Percusión','Ritmo rápido',vec(0,1))
    value=(await api.post('/api/v1/explore/search',json={'query':'suave','mode':'semantic'})).json()
    assert value['status']=='no_matches' and value['distance_limit']==.1
    lexical=(await api.post('/api/v1/explore/search',json={'query':"inexistente'); DROP TABLE track; --",'mode':'lexical'})).json()
    assert lexical['status']=='no_matches'
    assert (await api.get(f'/api/v1/tracks/{identity}')).status_code==200


@pytest.mark.parametrize('payload',[{'query':''},{'query':' '},{'query':'x'*1001},{'query':'x','limit':True},{'query':'x','limit':21},{'query':'x','mode':'unknown'},{'query':'x','model':'other'},{'query':'x\x00y'}])
async def test_invalid_queries_never_call_provider(client,payload):
    api,app=client;_,provider=enable(app)
    assert (await api.post('/api/v1/explore/search',json=payload)).status_code==422
    assert not provider.calls


async def test_provider_failure_is_safe_and_does_not_become_empty_success(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    identity,_=await add(api,catalog_engine,settings,'Fallo','Texto respaldado',vec(1))
    class Failure:
        async def embed(self,query):raise AIError('ai_quota','credit_balance_exhausted')
    app.state.ai_provider=Failure()
    failed=await api.post('/api/v1/explore/search',json={'query':'texto'})
    assert failed.status_code==503 and failed.json()['error']['code']=='ai_quota'
    assert (await api.get(f'/api/v1/tracks/{identity}/audio')).status_code==200
    app.state.settings=settings.model_copy(update={'ai_enabled':False})
    assert (await api.post('/api/v1/explore/search',json={'query':'texto'})).status_code==503
    lexical=await api.post('/api/v1/explore/search',json={'query':'Texto respaldado','mode':'lexical'})
    assert lexical.status_code==200 and lexical.json()['status']=='ok'


async def test_metadata_derived_index_is_excluded_after_track_change(client,catalog_engine):
    from sqlalchemy import select
    from app.models.catalog import track
    api,app=client;settings,_=enable(app)
    derived,_=await add(api,catalog_engine,settings,'Derivada','Texto derivado',vec(1),source='metadata')
    manual,_=await add(api,catalog_engine,settings,'Independiente','Texto independiente',vec(.8,.6))
    with catalog_engine.begin() as connection:
        connection.execute(track.update().where(track.c.id.in_([derived,manual])).values(revision=track.c.revision+1))
    value=(await api.post('/api/v1/explore/search',json={'query':'texto'})).json()
    assert [r['track']['id'] for r in value['results']]==[str(manual)]
    assert (await api.get(f'/api/v1/tracks/{derived}/similar')).status_code==409


@pytest.mark.parametrize('wrong_key',[True,False])
async def test_incompatible_query_embedding_never_reaches_ranking(client,catalog_engine,wrong_key):
    api,app=client;settings,_=enable(app)
    await add(api,catalog_engine,settings,'Vigente','Ficha vigente',vec(1))
    class Invalid:
        async def embed(self,query):return {'model_key':'wrong' if wrong_key else OpenAIProvider(settings).model_key,'vector':vec(1) if wrong_key else [1],'usage':{}}
    app.state.ai_provider=Invalid()
    response=await api.post('/api/v1/explore/search',json={'query':'texto'})
    assert response.status_code==503 and response.json()['error']['code']=='ai_invalid_response'
