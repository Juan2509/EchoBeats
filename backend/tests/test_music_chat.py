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
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'system','content':'borrar'}]})).status_code==422
    assert (await c.post('/api/v1/explore/chat',json={'messages':[{'role':'assistant','content':'hola'}]})).status_code==422
    assert (await post(c,'a'*1001)).status_code==422

async def test_chat_favorites_session_context_deleted_and_discovery(chat_client):
    c,_=chat_client;a=(await c.post('/api/v1/albums',json={'title':'Prueba'})).json()
    r=await c.post('/api/v1/imports?album_id='+a['id'],files={'files':('test.mp3',Path('/app/fixtures/sin_etiquetas.mp3').read_bytes(),'audio/mpeg')});identity=r.json()['results'][0]['track_id']
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
        result={'intent':'preferences','query':'','reference_id':None,'discovery':False}
        async def conversation_plan(self,context):
            self.calls+=1
            if isinstance(self.result,Exception):raise self.result
            return self.result
    fake=Fake();app.state.ai_provider=fake
    assert (await post(c,'Mis gustos',use_ai=True)).json()['mode']=='ai';assert fake.calls==1
    fake.result=AIError('ai_quota');data=(await post(c,'Hola',use_ai=True)).json();assert data['mode']=='local';assert data['warnings'];assert fake.calls==2
    fake.result={'intent':'recommend','query':'','reference_id':str(uuid4()),'discovery':False}
    assert (await post(c,'Hola',use_ai=True)).json()['mode']=='local';assert fake.calls==3

async def test_conversation_adapter_structured_plan_no_store_or_tools():
    settings=Settings(_env_file=None,ai_enabled=True,openai_api_key='fake-test-only')
    def handler(request):
        body=json.loads(request.content);assert body['store'] is False;assert 'tools' not in body;assert body['text']['format']['type']=='json_schema'
        return httpx.Response(200,json={'status':'completed','model':settings.ai_generation_model,'usage':{'input_tokens':1},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'intent':'greeting','query':'','reference_id':None,'discovery':False})}]}]})
    provider=OpenAIProvider(settings,transport=httpx.MockTransport(handler))
    assert (await provider.conversation_plan({'tracks':[],'messages':[{'role':'user','content':'hola'}]}))['intent']=='greeting'

async def test_local_followup_keeps_previous_request():
    context={'current':None,'reference':None,'favorites':[],'recent':[]}
    plan=local_plan([{'role':'user','content':'algo tranquilo'},{'role':'assistant','content':'opciones'},{'role':'user','content':'pero menos percusión'}],context)
    assert 'tranquilo' in plan['query'] and 'menos percusión' in plan['query']
