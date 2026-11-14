"""Regla P25 comprobada con SQL real y datos artificiales, no calibración musical."""
import pytest
from test_metadata import client
from test_search import add, enable, vec, Fake
from test_exploration import Selecting

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def ids(data): return [item['track']['id'] for item in data['results']]


async def save(api, identity, desired=True):
    response = await api.put(f'/api/v1/tracks/{identity}/favorite', json={'favorite': desired})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize('mode', ['lexical', 'semantic', 'hybrid'])
async def test_only_adjacent_pairs_change_preserving_candidates_and_query_scores(client, catalog_engine, mode):
    api, app = client; settings, provider = enable(app)
    tracks = []
    for index, name in enumerate(['Alfa', 'Beta', 'Gamma', 'Delta', 'Final']):
        identity, _ = await add(api, catalog_engine, settings, name, 'Tono común.', vec(1, index * .15))
        tracks.append(identity)
    base = (await api.post('/api/v1/explore/search', json={'query': 'tono', 'mode': mode})).json()
    baseline = ids(base)
    await save(api, baseline[1]); await save(api, baseline[3])
    original = (await api.post('/api/v1/explore/search', json={'query': 'tono', 'mode': mode, 'preferences': 'off'})).json()
    adjusted = (await api.post('/api/v1/explore/search', json={'query': 'tono', 'mode': mode, 'preferences': 'favorites'})).json()
    assert ids(original) == baseline
    assert ids(adjusted) == [baseline[1], baseline[0], baseline[3], baseline[2], baseline[4]]
    assert adjusted['preferences']['baseline_order'] == baseline and adjusted['preferences']['reordered']
    by_id = {item['track']['id']: item for item in original['results']}
    for item in adjusted['results']:
        before = by_id[item['track']['id']]
        for key in ['distance', 'fusion_score', 'semantic_rank', 'lexical_rank', 'description', 'evidence']:
            assert item[key] == before[key]
        assert abs(item['preference']['rank'] - item['preference']['base_rank']) <= 1
        assert 'confianza' not in item['preference']['reason']
    assert len(provider.calls) == (0 if mode == 'lexical' else 3)
    # Sin ranking acumulativo: cada consulta parte de la intención original.
    again = (await api.post('/api/v1/explore/search', json={'query': 'tono', 'mode': mode, 'preferences': 'favorites'})).json()
    assert ids(again) == ids(adjusted)


async def test_no_favorites_unrelated_favorites_and_top_k_are_not_expanded(client, catalog_engine):
    api, app = client; settings, provider = enable(app)
    a, _ = await add(api, catalog_engine, settings, 'Uno', 'Campanas sintetizadas.', vec(1))
    b, _ = await add(api, catalog_engine, settings, 'Dos', 'Campanas sintetizadas.', vec(.9,.1))
    unrelated, _ = await add(api, catalog_engine, settings, 'Ajena', 'Ruido de prueba.', vec(0,1))
    request = {'query': 'campanas', 'mode': 'lexical', 'preferences': 'favorites', 'limit': 1}
    without = (await api.post('/api/v1/explore/search', json=request)).json()
    assert not without['preferences']['reordered']
    await save(api, unrelated); await save(api, b if ids(without) == [str(a)] else a)
    with_saved = (await api.post('/api/v1/explore/search', json=request)).json()
    assert ids(with_saved) == ids(without) and str(unrelated) not in ids(with_saved)
    assert not provider.calls


async def test_discovery_excludes_before_limit_keeps_filters_and_all_saved_is_empty_without_api(client, catalog_engine):
    api, app = client; settings, provider = enable(app)
    a, _ = await add(api, catalog_engine, settings, 'Alfa', 'Tono.', vec(1), 'Dentro')
    b, _ = await add(api, catalog_engine, settings, 'Beta', 'Tono.', vec(.9,.1), 'Dentro')
    c, _ = await add(api, catalog_engine, settings, 'Gamma', 'Tono.', vec(.8,.2), 'Dentro')
    outside, _ = await add(api, catalog_engine, settings, 'Fuera', 'Tono.', vec(1), 'Fuera')
    album = (await api.get(f'/api/v1/tracks/{a}')).json()['album_id']
    await save(api, a); await save(api, b)
    data = (await api.post('/api/v1/explore/search', json={'query':'tono','preferences':'discovery','album_id':album,'limit':1})).json()
    assert ids(data) == [str(c)] and not data['results'][0]['preference']['favorite']
    assert str(outside) not in ids(data) and len(provider.calls) == 1
    await save(api,c)
    empty = (await api.post('/api/v1/explore/search', json={'query':'tono','preferences':'discovery','album_id':album})).json()
    assert empty['status'] == 'no_matches' and empty['reason'] == 'empty_filter'
    assert not empty['results'] and len(provider.calls) == 1


async def test_reference_excludes_itself_filters_playlist_and_uses_no_provider(client, catalog_engine):
    api, app = client; settings, provider = enable(app)
    ref, _ = await add(api,catalog_engine,settings,'Referencia','Tono.',vec(1))
    a, _ = await add(api,catalog_engine,settings,'Alfa','Tono.',vec(.9,.1))
    b, _ = await add(api,catalog_engine,settings,'Beta','Tono.',vec(.8,.2))
    await save(api,b); await save(api,ref)
    playlist = await api.post('/api/v1/playlists',json={'name':'Comparación'})
    pid=playlist.json()['id']
    await api.put(f'/api/v1/playlists/{pid}/tracks',headers={'If-Match':playlist.headers['etag']},json={'track_ids':[str(ref),str(a),str(b)]})
    data = (await api.post('/api/v1/explore/similar',json={'track_id':str(ref),'preferences':'favorites','playlist_id':pid})).json()
    assert ids(data)==[str(b),str(a)] and data['preferences']['baseline_order']==[str(a),str(b)]
    discovery = (await api.get(f'/api/v1/tracks/{ref}/similar',params={'preferences':'discovery','playlist_id':pid})).json()
    assert ids(discovery)==[str(a)] and not provider.calls


async def test_preferences_changed_during_embedding_are_read_after_network(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    a,_=await add(api,catalog_engine,settings,'Alfa','Tono.',vec(1))
    b,_=await add(api,catalog_engine,settings,'Beta','Tono.',vec(.9,.1))
    class Updating(Fake):
        async def embed(self,query):
            assert catalog_engine.pool.checkedout()==0
            await save(api,b)
            return await super().embed(query)
    app.state.ai_provider=Updating(settings)
    data=(await api.post('/api/v1/explore/search',json={'query':'tono','preferences':'favorites'})).json()
    assert ids(data)==[str(b),str(a)]


async def test_generation_revalidates_favorites_and_rebuilds_comparison_without_sending_preferences(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    tracks=[]
    for index in range(4):
        identity,_=await add(api,catalog_engine,settings,f'Tono {index}','Tono registrado.',vec(1,index*.2))
        tracks.append(identity)
    await save(api,tracks[1])
    class Updating(Selecting):
        async def generate(self,query,sources):
            assert catalog_engine.pool.checkedout()==0
            assert all(set(source)=={'source_id','version','text'} for source in sources)
            await save(api,tracks[1],False);await save(api,tracks[3])
            return await super().generate(query,sources)
    app.state.ai_provider=Updating(settings)
    response=await api.post('/api/v1/explore/search',json={'query':'tono','mode':'semantic','preferences':'favorites','explain':True})
    assert response.status_code==200,response.text
    data=response.json()
    assert ids(data)==[str(tracks[0]),str(tracks[1]),str(tracks[3]),str(tracks[2])]
    assert data['preferences']['baseline_order']==list(map(str,tracks))
    assert any('comprobaron de nuevo' in w for w in data['warnings'])
    assert 'IMAGINADO' not in response.text


async def test_discovery_removes_new_favorite_during_generation_without_second_api_call(client,catalog_engine):
    api,app=client;settings,_=enable(app)
    identity,_=await add(api,catalog_engine,settings,'Tono','Tono registrado.',vec(1))
    class Updating(Selecting):
        async def generate(self,query,sources):
            await save(api,identity)
            return await super().generate(query,sources)
    provider=Updating(settings);app.state.ai_provider=provider
    data=(await api.post('/api/v1/explore/search',json={'query':'tono','preferences':'discovery','explain':True})).json()
    assert data['status']=='no_matches' and not data['results']
    assert data['preferences']['baseline_order']==[] and len(provider.calls)==len(provider.generations)==1


async def test_invalid_mode_and_empty_library_are_explicit_without_provider(client):
    api,app=client;_,provider=enable(app)
    for value in ['automatic',True,None,{'mode':'favorites'}]:
        assert (await api.post('/api/v1/explore/search',json={'query':'tono','preferences':value})).status_code==422
    empty=(await api.post('/api/v1/explore/search',json={'query':'tono','preferences':'favorites'})).json()
    assert empty['status']=='no_library' and empty['preferences']['mode']=='favorites' and not provider.calls
