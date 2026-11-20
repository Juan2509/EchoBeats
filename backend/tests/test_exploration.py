"""P23: recuperación y citas en BD aislada; nunca utiliza API real."""
import json
from uuid import UUID
import pytest
from app.integrations.ai import AIError
from app.services import descriptions
from app.services.exploration import sources_for
from test_metadata import client,tagged,upload
from test_search import add,enable,vec,Fake
from test_descriptions import body

pytestmark=[pytest.mark.integration,pytest.mark.anyio]


class Selecting(Fake):
    def __init__(self,settings):super().__init__(settings);self.generations=[]
    async def generate(self,query,sources):
        self.generations.append((query,sources))
        source=sources[0]
        return {'output':{'text':'IMAGINADO: interpreta una cantante famosa.', 'evidence':[{'source_id':source['source_id'],'version':source['version'],'quote':source['text']}]},
            'model':'gpt-6-luna','usage':{'input_tokens':20,'output_tokens':30,'total_tokens':50}}


async def test_generation_selects_literal_evidence_without_publishing_free_claims(client,catalog_engine):
    api,app=client;settings,_=enable(app);provider=Selecting(settings);app.state.ai_provider=provider
    a,_=await add(api,catalog_engine,settings,'Tono','Onda sinusoidal sin voces.',vec(1))
    await add(api,catalog_engine,settings,'Campanas','Campanas sintetizadas.',vec(.8,.6))
    value=await api.post('/api/v1/explore/search',json={'query':'tono','mode':'semantic','explain':True})
    assert value.status_code==200,value.text
    data=value.json();assert len(provider.calls)==1 and len(provider.generations)==1
    assert data['results'][0]['explanation_source']=='generated_selection'
    assert data['results'][1]['explanation_source']=='recorded'
    assert 'IMAGINADO' not in value.text and 'cantante famosa' not in value.text
    assert data['generation_usage']['total_tokens']==50 and data['explanation_policy']=='literal_quotes_only'
    assert (await api.get(data['results'][0]['track']['audio_url'])).status_code==200
    assert set(provider.generations[0][1][0])=={'source_id','version','text'}


@pytest.mark.parametrize('code',['ai_quota','ai_timeout','ai_invalid_response','ai_refusal'])
async def test_generation_failure_keeps_results_and_recorded_alternative(client,catalog_engine,code):
    api,app=client;settings,_=enable(app)
    identity,_=await add(api,catalog_engine,settings,'Dato','Información con procedencia.',vec(1))
    class Failure(Fake):
        async def generate(self,query,sources):raise AIError(code)
    provider=Failure(settings);app.state.ai_provider=provider
    response=await api.post('/api/v1/explore/search',json={'query':'dato','explain':True})
    assert response.status_code==200,response.text
    data=response.json();assert data['results'][0]['track']['id']==str(identity)
    assert data['results'][0]['explanation_source']=='recorded' and data['generation_usage'] is None
    assert any('No se pudo validar' in w for w in data['warnings']) and len(provider.calls)==1


@pytest.mark.parametrize('change',[{'source_id':'ajena'},{'version':999},{'quote':'Hay guitarra y voz humana.'}])
async def test_invalid_citations_do_not_become_generated_explanation(client,catalog_engine,change):
    api,app=client;settings,_=enable(app)
    await add(api,catalog_engine,settings,'Verificada','Sin voz humana.',vec(1))
    class Invalid(Selecting):
        async def generate(self,query,sources):
            value=await super().generate(query,sources)
            value['output']['evidence'][0].update(change)
            return value
    app.state.ai_provider=Invalid(settings)
    value=(await api.post('/api/v1/explore/search',json={'query':'voz','mode':'lexical','explain':True})).json()
    assert value['results'][0]['explanation_source']=='recorded'
    assert value['results'][0]['evidence'][0]['quote']=='Sin voz humana.'


async def test_ficha_changed_while_generation_waits_is_excluded(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    identity,saved=await add(api,catalog_engine,settings,'Concurrente','Ficha inicial.',vec(1))
    class Editing(Selecting):
        async def generate(self,query,sources):
            assert catalog_engine.pool.checkedout()==0
            descriptions.save(catalog_engine,identity,body(text='Ficha nueva.'),saved.headers['etag'],None)
            return await super().generate(query,sources)
    app.state.ai_provider=Editing(settings)
    value=(await api.post('/api/v1/explore/search',json={'query':'ficha','explain':True})).json()
    assert value['status']=='no_matches' and value['results']==[]
    assert any('cambiaron' in w for w in value['warnings'])


async def test_reference_explanation_opt_in_and_reference_change_guard(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    a,saved=await add(api,catalog_engine,settings,'Referencia','Tono original.',vec(1))
    b,_=await add(api,catalog_engine,settings,'Vecina','Tono vecino.',vec(.8,.6))
    provider=Selecting(settings);app.state.ai_provider=provider
    response=await api.post('/api/v1/explore/similar',json={'track_id':str(a)})
    assert response.status_code==200 and response.json()['results'][0]['track']['id']==str(b)
    assert not provider.calls and not provider.generations
    class Editing(Selecting):
        async def generate(self,query,sources):
            descriptions.save(catalog_engine,a,body(text='Referencia nueva.'),saved.headers['etag'],None)
            return await super().generate(query,sources)
    app.state.ai_provider=Editing(settings)
    response=await api.post('/api/v1/explore/similar',json={'track_id':str(a),'explain':True})
    assert response.status_code==409 and response.json()['error']['code']=='reference_changed'


async def test_lexical_sources_without_embeddings_with_and_without_generation(client):
    api,app=client;settings,_=enable(app)
    identity=(await upload(api,tagged(title='Local')))['track_id']
    saved=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-None-Match':'*'},
        json=body(text='Dato local registrado.'))
    assert saved.status_code==200,saved.text
    provider=Selecting(settings);app.state.ai_provider=provider
    app.state.settings=settings.model_copy(update={'ai_enabled':False,'ai_embedding_dimensions':512})
    value=(await api.post('/api/v1/explore/search',json={'query':'local','mode':'lexical','explain':True})).json()
    assert value['results'][0]['track']['id']==identity
    assert value['results'][0]['explanation_source']=='recorded' and not provider.calls and not provider.generations
    app.state.settings=settings
    value=(await api.post('/api/v1/explore/search',json={'query':'local','mode':'lexical','explain':True})).json()
    assert value['results'][0]['explanation_source']=='generated_selection'
    assert value['results'][0]['evidence'][0]['quote']=='Dato local registrado.'
    assert not provider.calls and len(provider.generations)==1
    semantic=(await api.post('/api/v1/explore/search',json={'query':'local','mode':'semantic'})).json()
    assert semantic['status']=='no_indexed_tracks' and not provider.calls
    assert (await api.post('/api/v1/explore/search',json={'query':'local','explain':'yes'})).status_code==422


def test_context_budget_preserves_ids_versions_and_utf8_without_audio():
    items=[{'description':{'id':str(i),'version':1,'text':'á'*3000}} for i in range(20)]
    sources=sources_for('🟢'*1000,items)
    assert 1<=len(sources)<=5
    assert len(json.dumps({'query':'🟢'*1000,'sources':sources},ensure_ascii=False).encode())<=12000
    assert all(set(s)=={'source_id','version','text'} for s in sources)


@pytest.mark.parametrize('invalid',[{'model':'other-model'},{'usage':{'total_tokens':-1}}])
async def test_bad_model_or_consumption_does_not_publish_selection(client,catalog_engine,invalid):
    api,app=client;settings,_=enable(app)
    await add(api,catalog_engine,settings,'Respaldada','Ficha documentada.',vec(1))
    class Invalid(Selecting):
        async def generate(self,query,sources):
            value=await super().generate(query,sources);value.update(invalid);return value
    app.state.ai_provider=Invalid(settings)
    value=(await api.post('/api/v1/explore/search',json={'query':'ficha','mode':'lexical','explain':True})).json()
    assert value['results'][0]['explanation_source']=='recorded' and value['generation_usage'] is None


async def test_playlist_change_during_generation_removes_results(client,catalog_engine):
    from app.models.catalog import playlist_track
    api,app=client;settings,_=enable(app)
    identity,_=await add(api,catalog_engine,settings,'Filtro','Ficha de filtro.',vec(1))
    created=await api.post('/api/v1/playlists',json={'name':'Selección'})
    pid=created.json()['id']
    await api.put(f'/api/v1/playlists/{pid}/tracks',headers={'If-Match':created.headers['etag']},json={'track_ids':[str(identity)]})
    class Editing(Selecting):
        async def generate(self,query,sources):
            with catalog_engine.begin() as connection:connection.execute(playlist_track.delete().where(playlist_track.c.playlist_id==UUID(pid)))
            return await super().generate(query,sources)
    app.state.ai_provider=Editing(settings)
    value=(await api.post('/api/v1/explore/search',json={'query':'filtro','playlist_id':pid,'explain':True})).json()
    assert value['results']==[] and value['status']=='no_matches'


async def test_no_results_does_not_generate_even_with_opt_in(client):
    api,app=client;settings,_=enable(app);provider=Selecting(settings);app.state.ai_provider=provider
    value=(await api.post('/api/v1/explore/search',json={'query':'cualquier cosa','explain':True})).json()
    assert value['status']=='no_library' and value['results']==[]
    assert not provider.calls and not provider.generations
