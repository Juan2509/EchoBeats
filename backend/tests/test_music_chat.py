from uuid import UUID,uuid4
import json
import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from app.config import Settings
from app.main import create_app
from app.integrations.ai import OpenAIProvider,AIError
from app.integrations.audio_embedding import MODEL_KEY as AUDIO_MODEL_KEY
from app.models.catalog import artist,media_asset,track,track_artist,track_audio_embedding
from app.integrations.storage import MediaStore
from app.services import audio_similarity
from app.services.music_chat import local_plan
from test_audio_similarity import tone,wav
from test_descriptions import body
from test_metadata import upload

pytestmark=[pytest.mark.integration,pytest.mark.anyio]

@pytest.fixture
async def chat_client(catalog_engine,tmp_path):
    app=create_app(Settings(_env_file=None,media_root=tmp_path/'media'))
    original=app.state.database_engine;app.state.database_engine=catalog_engine
    class NoNetwork:
        async def conversation_plan(self,*args):raise AssertionError('No debe llamar al proveedor')
        async def embed(self,*args):raise AssertionError('No debe llamar al proveedor')
    app.state.ai_provider=NoNetwork()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:yield client,app
    if original is not None:original.dispose()

async def post(c,text,**extra):return await c.post('/api/v1/explore/chat',json={'messages':[{'role':'user','content':text}],**extra})

async def test_chat_identifies_old_unindexed_track_in_full_catalog(chat_client):
    client, app = chat_client
    collection = (await client.post('/api/v1/albums', json={'title': 'Colección'})).json()
    album_id = UUID(collection['id'])
    identity = uuid4()
    with app.state.database_engine.begin() as connection:
        assets = [uuid4() for _ in range(502)]
        connection.execute(media_asset.insert(), [
            {'id': asset, 'kind': 'audio', 'storage_key': f'audio/{asset.hex}.mp3',
             'sha256': f'{index:064x}', 'original_name': 'grabacion-rara.mp3' if index == 0 else 'sintetico.mp3',
             'mime_type': 'audio/mpeg', 'byte_size': 1}
            for index, asset in enumerate(assets)
        ])
        connection.execute(track.insert().values(
            id=identity, audio_asset_id=assets[0], album_id=album_id, content_sha256='0' * 64,
            title='Órbita Azul', duration_ms=1000,
        ))
        author = connection.scalar(artist.insert().values(name='Ana Norte', normalized_name='ana norte').returning(artist.c.id))
        connection.execute(track_artist.insert().values(track_id=identity, artist_id=author, position=0))
    with app.state.database_engine.begin() as connection:
        connection.execute(track.insert(), [
            {'audio_asset_id': asset, 'album_id': album_id, 'content_sha256': f'{index:064x}',
             'title': f'Pista sintética {index}', 'duration_ms': 1000}
            for index, asset in enumerate(assets[1:], start=1)
        ])

    identified = (await post(client, '¿Tengo Órbita Azul en mi biblioteca?', use_ai=True)).json()
    assert [item['track']['id'] for item in identified['recommendations']] == [str(identity)]
    assert identified['recommendations'][0]['track']['artists'][0]['name'] == 'Ana Norte'
    result = (await post(client, 'Busca Orbita Azul en mi biblioteca')).json()
    assert result['recommendations'][0]['track']['id'] == str(identity)
    current = (await post(client, '¿Quién canta esta canción?', current_track_id=str(identity))).json()
    assert [item['track']['id'] for item in current['recommendations']] == [str(identity)]
    unknown = (await post(client, 'Identifica Desconocida', current_track_id=str(identity))).json()
    assert unknown['recommendations'] == []
    by_filename = (await post(client, 'Identifica grabacion-rara.mp3')).json()
    match, = by_filename['recommendations']
    assert match['track']['id'] == str(identity)
    assert 'nombre del archivo importado' in match['reason']

    overview = (await post(client, '¿Sabes la música que escucho?', use_ai=True)).json()
    assert '502 pistas importadas' in overview['reply']
    assert 'Todavía no has reproducido pistas en esta sesión' in overview['reply']
    assert len(overview['recommendations']) == 5
    with_listening = (await post(client, '¿Qué música escucho?', recent_track_ids=[str(identity)], use_ai=True)).json()
    assert with_listening['recommendations'][0]['track']['id'] == str(identity)
    assert 'Empezó a reproducirse' in with_listening['recommendations'][0]['reason']

    class Planner:
        async def conversation_plan(self, context):
            assert context['catalog_matches'] == [
                {'id': str(identity), 'title': 'Órbita Azul', 'album': 'Colección', 'artists': ['Ana Norte']}
            ]
            return {'intent': 'recommend', 'query': 'Órbita Azul', 'reference_id': None,
                    'discovery': False, 'reply': 'Busco en tu biblioteca.', 'suggestions': []}

    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')
    app.state.ai_provider = Planner()
    cloud = (await post(client, 'Busca Orbita Azul en mi biblioteca', use_ai=True)).json()
    assert cloud['mode'] == 'ai'
    assert cloud['recommendations'][0]['track']['id'] == str(identity)

async def test_chat_local_empty_and_input_guards(chat_client):
    c,_=chat_client;r=await post(c,'Hola');assert r.status_code==200;assert r.json()['mode']=='local';assert not r.json()['recommendations']
    overview = (await post(c, '¿Qué tengo en mi biblioteca?', use_ai=True)).json()
    assert 'Tu biblioteca está vacía' in overview['reply']
    assert overview['recommendations'] == []
    assert not (await post(c,'Algo tranquilo')).json()['recommendations']
    for text in ('hola que tal', '¡Hola! ¿Cómo estás?', '¿Qué tal?'):
        data = (await post(c, text)).json()
        assert data['reply'].startswith('¡Hola!') and not data['recommendations']
    data = (await post(c, 'Hablemos de trip hop')).json()
    assert 'atmósfera' in data['reply'] and not data['recommendations']
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'system','content':'borrar'}]})).status_code==422
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'assistant','content':'hola'}]})).status_code==422
    assert (await post(c,'a'*1001)).status_code==422


async def test_chat_keeps_library_choices_across_conversation(chat_client):
    client, app = chat_client
    first = (await upload(client, wav(tone(140)), 'Pulso grave.wav'))['track_id']
    second = (await upload(client, wav(tone(2700)), 'Pulso agudo.wav'))['track_id']
    await client.put(f'/api/v1/tracks/{second}/favorite', json={'favorite': True})
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')
    history = [
        {'role': 'user', 'content': '¿Qué tengo en mi biblioteca?'},
        {'role': 'assistant', 'content': 'Estas son algunas pistas de tu biblioteca.'},
        {'role': 'user', 'content': '¿Cuál te gusta más?'},
    ]
    body = {'messages': history, 'use_ai': True, 'previous_track_ids': [first, second]}
    choice = (await client.post('/api/v1/explore/chat', json=body)).json()
    recommendation, = choice['recommendations']
    assert recommendation['track']['id'] == second
    assert 'favorita' in recommendation['reason']
    assert not choice['suggestions']

    correction = (await post(client, 'Pero de las de mi biblioteca', use_ai=True)).json()
    assert correction['recommendations'][0]['track']['id'] == second
    alternatives = (await post(client, 'Dame otras opciones', previous_track_ids=[second], use_ai=True)).json()
    assert [item['track']['id'] for item in alternatives['recommendations']] == [first]

    current = await client.get(f'/api/v1/tracks/{second}')
    await client.delete(f'/api/v1/tracks/{second}', headers={'If-Match': current.headers['etag']})
    selection = (await client.post('/api/v1/explore/chat', json=body)).json()
    assert [item['track']['id'] for item in selection['recommendations']] == [first]


async def test_chat_describes_audio_and_recommends_across_the_index(chat_client):
    client, app = chat_client
    low = (await upload(client, wav(tone(110)), 'Neblina.wav'))['track_id']
    near = (await upload(client, wav(tone(120)), 'Humo.wav'))['track_id']
    high = (await upload(client, wav(tone(3100)), 'Farol.wav'))['track_id']
    engine = app.state.database_engine

    preview = (await post(client, '¿Cómo suena esta canción?', current_track_id=high, use_ai=True)).json()
    reported, = preview['recommendations']
    assert reported['track']['id'] == high
    assert 'agudas' in reported['reason']
    assert audio_similarity.audio_index_status(engine, UUID(high), False)['status'] == 'pending'

    store = MediaStore(app.state.settings.media_root)
    with engine.connect() as connection:
        pending = audio_similarity.pending_tracks(connection)
    for candidate in pending:
        assert audio_similarity.index_audio(engine, store, candidate)

    ordinal = (await post(client, '¿Cómo suena la segunda?', previous_track_ids=[low, high])).json()
    assert ordinal['recommendations'][0]['track']['id'] == high
    assert 'agudas' in ordinal['recommendations'][0]['reason']
    comparison = (await post(client, 'Compara estas canciones', previous_track_ids=[low, high])).json()
    assert [item['track']['id'] for item in comparison['recommendations']] == [low, high]
    assert 'graves' in comparison['recommendations'][0]['reason']
    nearby = (await post(client, 'Busca algo similar a Neblina', current_track_id=high)).json()
    assert nearby['recommendations'][0]['track']['id'] == near
    assert 'perfil acústico' in nearby['reply']
    unknown = (await post(client, 'Busca algo parecido a Desconocida en mi biblioteca', current_track_id=high)).json()
    assert unknown['recommendations'] == []
    assert 'No pude identificar la pista de referencia' in unknown['reply']
    scoped = (await post(client, 'Recomiéndame canciones con graves marcados de mi biblioteca')).json()
    assert scoped['recommendations'][0]['track']['id'] in {low, near}

async def test_chat_favorites_session_context_deleted_and_discovery(chat_client):
    c,_=chat_client;a=(await c.post('/api/v1/albums',json={'title':'Prueba'})).json()
    r=await c.post('/api/v1/imports?album_id='+a['id'],files={'files':('test.wav',wav(tone(440)),'audio/wav')});identity=r.json()['results'][0]['track_id']
    assert not (await post(c,'Algo con timbales')).json()['recommendations']
    await c.put('/api/v1/tracks/'+identity+'/favorite',json={'favorite':True})
    r=await post(c,'Recomiéndame de mis favoritos',recent_track_ids=[identity,str(uuid4())],current_track_id=identity)
    assert r.status_code==200;data=r.json();assert data['context']['favorites']==1;assert data['context']['recent']==1;assert data['recommendations'][0]['track']['id']==identity;assert 'favorita' in data['recommendations'][0]['reason']
    assert not (await post(c,'Dame otras opciones',previous_track_ids=[identity])).json()['recommendations']
    assert not (await post(c,'Quiero descubrir algo diferente')).json()['recommendations']
    current=await c.get('/api/v1/tracks/'+identity);await c.delete('/api/v1/tracks/'+identity,headers={'If-Match':current.headers['etag']})
    data=(await post(c,'Qué sabes de mis gustos',current_track_id=identity,recent_track_ids=[identity])).json();assert data['context']['recent']==0;assert data['context']['favorites']==0
    assert (await post(c,'Algo similar',reference_track_id=identity)).status_code==404

async def test_chat_ai_plan_mock_quota_and_invalid_anchor(chat_client):
    c,app=chat_client;app.state.settings.ai_enabled=True;app.state.settings.openai_api_key=SecretStr('fake-test-only')
    class Fake:
        calls=0
        result={'intent':'preferences','query':'','reference_id':None,'discovery':False,'reply':'Hablemos de música.','suggestions':[]}
        async def conversation_plan(self,context):
            self.calls+=1
            if isinstance(self.result,Exception):raise self.result
            return self.result
    fake=Fake();app.state.ai_provider=fake
    assert (await post(c,'Mis gustos',use_ai=True)).json()['mode']=='ai';assert fake.calls==1
    fake.result=AIError('ai_quota');data=(await post(c,'Hablemos de trip hop',use_ai=True)).json();assert data['mode']=='local';assert data['warnings'];assert fake.calls==2
    fake.result={'intent':'recommend','query':'','reference_id':str(uuid4()),'discovery':False,'reply':'Hablemos de música.','suggestions':[]}
    assert (await post(c,'Hablemos de trip hop',use_ai=True)).json()['mode']=='local';assert fake.calls==3


async def test_chat_uses_cited_lexical_fiches_before_catalog_fallback(chat_client):
    api,app=chat_client
    identity=(await upload(api,wav(tone(440)),'Pista de prueba.wav'))['track_id']
    description='Grabación con timbales.'
    saved=await api.put(f'/api/v1/tracks/{identity}/description',headers={'If-None-Match':'*'},
        json=body(text=description))
    assert saved.status_code==200,saved.text
    app.state.settings.ai_enabled=True
    app.state.settings.openai_api_key=SecretStr('fake-test-only')

    class Planner:
        async def conversation_plan(self,context):
            return {'intent':'recommend','query':'timbales','reference_id':None,
                    'discovery':False,'reply':'Busco en tus fichas.','suggestions':[]}

        async def embed(self,query):
            raise AssertionError('El índice vacío no debe consumir un embedding de consulta')

    app.state.ai_provider=Planner()
    result=await post(api,'Busca timbales en mi biblioteca',use_ai=True)
    assert result.status_code==200,result.text
    data=result.json()
    assert data['mode']=='ai'
    recommendation,=data['recommendations']
    assert recommendation['track']['id']==identity
    assert recommendation['evidence'][0]['quote']==description


async def test_chat_connects_local_audio_neighbors_without_sending_audio(chat_client,catalog_engine):
    api,app=chat_client
    ids=[(await upload(api,wav(tone(frequency)),f'{title}.wav'))['track_id']
         for title,frequency in [('Referencia',440),('Cercana',450),('Lejana',2800)]]
    vectors=[[1.0,*([0.0]*25)],[.99,.1,*([0.0]*24)],[0.0,1.0,*([0.0]*24)]]
    with catalog_engine.begin() as connection:
        rows=connection.execute(select(track.c.id,track.c.audio_asset_id,track.c.content_sha256).where(track.c.id.in_(ids))).all()
        by_id={str(row.id):row for row in rows}
        connection.execute(track_audio_embedding.insert(),[{
            'track_id':row.id,'model_key':AUDIO_MODEL_KEY,'audio_asset_id':row.audio_asset_id,
            'content_sha256':row.content_sha256,'embedding':vector,
        } for identity,vector in zip(ids,vectors,strict=True) for row in [by_id[identity]]])

    local=(await post(api,'Algo parecido a lo que escucho en mi biblioteca',current_track_id=ids[0])).json()
    assert local['recommendations'][0]['track']['id']==ids[1]
    assert 'primeros 30 segundos' in local['reply']
    assert 'perfiles acústicos' in local['recommendations'][0]['reason']

    app.state.settings.ai_enabled=True
    app.state.settings.openai_api_key=SecretStr('fake-test-only')
    class Planner:
        async def conversation_plan(self,context):
            assert context['acoustic']['raw_audio_sent'] is False
            assert context['acoustic']['distance_is_confidence'] is False
            seed,=context['acoustic']['seeds']
            assert seed['seed_track_id']==ids[0]
            assert seed['neighbors'][0]['track_id']==ids[1]
            assert all('audio' not in item for item in context['tracks'])
            return {'intent':'recommend','query':'','reference_id':ids[0],
                    'discovery':False,'reply':'Comparo el sonido local.','suggestions':[]}
    app.state.ai_provider=Planner()
    cloud=(await post(api,'Busca algo parecido en mi biblioteca',current_track_id=ids[0],use_ai=True)).json()
    assert cloud['mode']=='ai' and cloud['recommendations'][0]['track']['id']==ids[1]

async def test_conversation_adapter_structured_plan_no_store_or_tools():
    settings=Settings(_env_file=None,ai_enabled=True,openai_api_key='fake-test-only')
    messages = [
        {'role': 'user', 'content': 'Hola'},
        {'role': 'assistant', 'content': '¿Cómo estás?'},
        {'role': 'user', 'content': 'Bien, ¿y tú?'},
    ]
    def handler(request):
        body=json.loads(request.content);assert body['reasoning']=={'effort':'low'};assert body['store'] is False;assert 'tools' not in body;assert body['text']['format']['type']=='json_schema'
        assert body['input'][1:] == messages
        return httpx.Response(200,json={'status':'completed','model':settings.ai_generation_model,'usage':{'input_tokens':1},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'intent':'greeting','query':'','reference_id':None,'discovery':False,'reply':'Hablemos de música.','suggestions':[]})}]}]})
    provider=OpenAIProvider(settings,transport=httpx.MockTransport(handler))
    assert (await provider.conversation_plan({'tracks':[],'messages':messages}))['intent']=='greeting'


@pytest.mark.parametrize('status, code', [(401, 'ai_invalid_key'), (403, 'ai_model_access'), (404, 'ai_model_access')])
async def test_openai_chat_distinguishes_key_and_model_access(status, code):
    settings = Settings(_env_file=None, ai_enabled=True, openai_api_key='fake-test-only')
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json={'error': {}}))
    provider = OpenAIProvider(settings, transport=transport)
    with pytest.raises(AIError) as failure:
        await provider.conversation_plan({'tracks': [], 'messages': [{'role': 'user', 'content': 'Hola'}]})
    assert failure.value.code == code


async def test_openai_handles_greetings_and_social_fallback(chat_client):
    client, app = chat_client
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')

    class Fake:
        async def conversation_plan(self, context):
            if context['messages'][-1]['content'] != 'Hola':
                raise AIError('ai_invalid_key')
            return {'intent': 'greeting', 'query': '', 'reference_id': None,
                    'discovery': False, 'reply': '¡Hola! Me alegra verte.', 'suggestions': []}

    app.state.ai_provider = Fake()
    greeting = (await post(client, 'Hola', use_ai=True)).json()
    assert greeting['provider'] == 'openai' and greeting['reply'] == '¡Hola! Me alegra verte.'
    fallback = (await post(client, 'Bien, ¿y tú?', use_ai=True)).json()
    assert fallback['mode'] == 'local' and 'charlar' in fallback['reply']
    assert 'clave API' in fallback['warnings'][0]

async def test_local_followup_keeps_previous_request():
    context={'current':None,'reference':None,'favorites':[],'recent':[]}
    plan=local_plan([{'role':'user','content':'algo tranquilo'},{'role':'assistant','content':'opciones'},{'role':'user','content':'pero menos percusión'}],context)
    assert 'tranquilo' in plan['query'] and 'menos percusión' in plan['query']


async def test_chat_discovers_music_without_catalog_or_embedding(chat_client):
    client, app = chat_client
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')

    class Fake:
        async def conversation_plan(self, context):
            item = {'title': 'Weightless', 'artist': None, 'work': 'Ejemplo de prueba', 'match': 'approximate', 'reason': 'Texturas ambientales y pulso lento.'}
            return {'intent': 'discover', 'query': 'ambient tranquilo', 'reference_id': None,
                    'discovery': True, 'reply': 'Algo con espacio para respirar.', 'suggestions': [item, item]}

    app.state.ai_provider = Fake()
    local = (await post(client, 'Música fuera de mi biblioteca')).json()
    assert not local['suggestions'] and 'necesito la IA' in local['reply']
    data = (await post(client, 'Música fuera de mi biblioteca', use_ai=True)).json()
    assert data['mode'] == 'ai' and not data['recommendations']
    assert [item['title'] for item in data['suggestions']] == ['Weightless']
    assert data['suggestions'][0]['artist'] is None
    assert data['suggestions'][0]['match'] == 'approximate'


async def test_chat_discussion_replies_to_followup_without_fetching_tracks(chat_client):
    client, app = chat_client
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')
    messages = [
        {'role': 'user', 'content': 'Me gusta cómo suena el trip hop.'},
        {'role': 'assistant', 'content': 'Las baterías lentas dejan espacio al bajo.'},
        {'role': 'user', 'content': '¿Y si me interesa más la textura que el ritmo?'},
    ]
    reply = 'Entonces puede atraerte el grano de los samples y cómo se mezclan con voces y reverberación.'

    class Fake:
        async def conversation_plan(self, context):
            assert context['messages'] == messages
            return {'intent': 'discuss', 'query': '', 'reference_id': None,
                    'discovery': False, 'reply': reply, 'suggestions': []}

    app.state.ai_provider = Fake()
    response = await client.post('/api/v1/explore/chat', json={'messages': messages, 'use_ai': True})
    assert response.status_code == 200
    data = response.json()
    assert data['reply'] == reply and data['mode'] == 'ai'
    assert data['recommendations'] == data['suggestions'] == []


async def test_local_game_music_conversation_and_clarification(chat_client):
    client, _ = chat_client
    topic = 'me gusta la música de videojuegos'
    first = (await post(client, topic)).json()
    assert 'bandas sonoras' in first['reply'] and not first['recommendations']
    messages = [
        {'role': 'user', 'content': 'Hola que tal'},
        {'role': 'assistant', 'content': '¡Hola! ¿Qué andas escuchando últimamente?'},
        {'role': 'user', 'content': topic},
        {'role': 'assistant', 'content': first['reply']},
        {'role': 'user', 'content': 'a que te refieres ?'},
    ]
    response = await client.post('/api/v1/explore/chat', json={'messages': messages})
    assert response.status_code == 200
    data = response.json()
    assert 'percusión' in data['reply'] and not data['recommendations']


async def test_local_identity_and_music_theme_stay_out_of_library_search(chat_client):
    client, _ = chat_client
    identity = (await post(client, 'soy gei')).json()
    assert not identity['suggestions'] and 'biblioteca' not in identity['reply']
    theme = (await post(client, 'me gusta la música con temática gei')).json()
    assert theme['suggestions'][0]['title'] == 'Smalltown Boy'
    atmosphere = (await post(client, 'atmósfera gei')).json()
    assert atmosphere['suggestions'][0]['match'] == 'direct'
    game = (await post(client, 'Busco algo de videojuegos con atmósfera de exploración')).json()
    assert game['suggestions'][0]['work'] == 'Celeste'
    assert game['suggestions'][0]['match'] == 'approximate'
    assert 'biblioteca' not in game['reply']
    library = (await post(client, 'Busca música de videojuegos en mi biblioteca')).json()
    assert 'dentro de tu biblioteca' in library['reply'] and not library['suggestions']


async def test_named_soundtrack_discovery_uses_documented_reference(chat_client):
    client, _ = chat_client
    data = (await post(client, '¿Qué música se parece a Mighty Switch Force?')).json()
    assert not data['recommendations']
    option = data['suggestions'][0]
    assert option['artist'] == 'Jake Kaufman'
    assert option['match'] == 'approximate'
    assert option['source_url'] == 'https://virt.bandcamp.com/album/mighty-switch-force-2-ost'


async def test_simple_greeting_and_game_exclusion_do_not_use_model(chat_client):
    client, _ = chat_client
    greeting = (await post(client, '¡Hola!')).json()
    assert greeting['provider'] is None and not greeting['warnings']
    messages = [
        {'role': 'user', 'content': 'Me gusta la música de Mighty Switch Force'},
        {'role': 'assistant', 'content': 'Podrías escuchar la secuela.'},
        {'role': 'user', 'content': 'Algo con base en ello, que no sea de la misma franquicia ni videojuegos'},
    ]

    async def send():
        response = await client.post('/api/v1/explore/chat', json={'messages': messages, 'use_ai': True})
        assert response.status_code == 200
        data = response.json()
        assert data['provider'] is None and not data['warnings'] and not data['recommendations']
        return data

    assert (await send())['suggestions'][0]['artist'] == 'Justice'
    messages.extend([{'role': 'assistant', 'content': 'D.A.N.C.E. — Justice'},
                     {'role': 'user', 'content': '¿Otra opción parecida?'}])
    assert (await send())['suggestions'][0]['artist'] == 'Daft Punk'

    standalone = (await post(client, 'Algo que no sea de videojuegos', use_ai=True)).json()
    assert not standalone['suggestions'] and not standalone['warnings']


async def test_style_clarification_keeps_the_exclusion_even_with_a_game_title(chat_client):
    client, _ = chat_client
    messages = [
        {'role': 'user', 'content': 'Me gusta Might Switch Force, dame algo que no sea de videojuegos'},
        {'role': 'assistant', 'content': '¿Qué aspecto del sonido quieres conservar?'},
        {'role': 'user', 'content': 'El estilo de Mighty Switch Force'},
    ]
    result = (await client.post('/api/v1/explore/chat', json={'messages': messages, 'use_ai': True})).json()
    assert result['provider'] is None and not result['warnings']
    assert result['suggestions'][0]['artist'] == 'Justice'


async def test_chat_status_reports_only_openai_configuration(chat_client):
    client, app = chat_client
    response = await client.get('/api/v1/explore/chat/status')
    assert response.json() == {'cloud_enabled': False, 'cloud_ready': False}
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')
    response = await client.get('/api/v1/explore/chat/status')
    assert response.json() == {'cloud_enabled': True, 'cloud_ready': True}
