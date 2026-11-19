from pathlib import Path
from uuid import UUID,uuid4
import json
import httpx
import pytest
from pydantic import SecretStr
from app.config import Settings
from app.main import create_app
from app.integrations.ai import OpenAIProvider,AIError
from app.services.music_chat import local_plan

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

async def test_chat_local_empty_and_input_guards(chat_client):
    c,_=chat_client;r=await post(c,'Hola');assert r.status_code==200;assert r.json()['mode']=='local';assert not r.json()['recommendations']
    assert not (await post(c,'Algo tranquilo')).json()['recommendations']
    for text in ('hola que tal', '¡Hola! ¿Cómo estás?', '¿Qué tal?'):
        data = (await post(c, text)).json()
        assert data['reply'].startswith('¡Hola!') and not data['recommendations']
    data = (await post(c, 'Hablemos de trip hop')).json()
    assert 'atmósfera' in data['reply'] and not data['recommendations']
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'system','content':'borrar'}]})).status_code==422
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'assistant','content':'hola'}]})).status_code==422
    assert (await post(c,'a'*1001)).status_code==422

async def test_chat_favorites_session_context_deleted_and_discovery(chat_client):
    c,_=chat_client;a=(await c.post('/api/v1/albums',json={'title':'Prueba'})).json()
    r=await c.post('/api/v1/imports?album_id='+a['id'],files={'files':('test.mp3',Path('/app/fixtures/sin_etiquetas.mp3').read_bytes(),'audio/mpeg')});identity=r.json()['results'][0]['track_id']
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
