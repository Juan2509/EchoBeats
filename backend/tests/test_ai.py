"""Solo MockTransport. Nunca usa claves reales, red ni saldo de proveedor."""
import asyncio
import json
import math
from httpx import ASGITransport, AsyncClient
import httpx
import pytest
from pydantic import SecretStr
from app.config import Settings
from app.integrations.ai import AIError, OpenAIProvider, status, validate_library_answer
from app.main import create_app

pytestmark = pytest.mark.anyio


def config(**changes):
    return Settings(_env_file=None, ai_enabled=True, openai_api_key=SecretStr('fake-test-key'), ai_embedding_dimensions=3, **changes)


def vector(**changes):
    return {'model': 'text-embedding-3-small', 'data': [{'index': 0, 'embedding': [.1,.2,.3]}], 'usage': {'prompt_tokens': 4, 'total_tokens': 4}, **changes}


def generated(**changes):
    return {'status': 'completed', 'model': 'gpt-6-luna', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps({'text':'Sin voces según la fuente.', 'evidence':[{'source_id':'a','version':1,'quote':'sin voces'}]})}]}], 'usage': {'input_tokens':10,'output_tokens':15,'total_tokens':25}, **changes}


SOURCES = [{'source_id':'a','version':1,'text':'Fragmento sintético sin voces.'}]


async def test_library_conversation_explains_the_previous_choice_from_available_evidence():
    candidates = [{'id': 'a', 'title': 'Tally Screen', 'artists': ['Jake Kaufman'],
                   'acoustic': {'summary': 'Predominan los graves en el comienzo.'}}]
    messages = [{'role': 'user', 'content': '¿Cuál te gusta más?'},
                {'role': 'assistant', 'content': 'Elegiría Tally Screen para empezar.'},
                {'role': 'user', 'content': '¿Y por qué te gusta más esa?'}]
    answer = {'reply': 'Elegí Tally Screen por el peso de los graves en el comienzo. '
                       'Si lo que buscas es un grave presente desde el arranque, empezaría por esa.',
              'selections': [{'track_id': 'a', 'reason': 'El comienzo medido da más peso a los graves.'}]}

    def handle(request):
        body = json.loads(request.content)
        assert body['input'][1:] == messages
        data = json.loads(body['input'][0]['content'].split(': ', 1)[1])
        assert data == {'action': 'explain', 'candidates': candidates}
        assert body['store'] is False and 'tools' not in body
        spec = body['text']['format']
        assert spec['name'] == 'library_conversation' and spec['strict'] is True
        assert spec['schema']['$defs']['LibrarySelection']['properties']['track_id']['enum'] == ['a']
        output = generated()
        output['output'][0]['content'][0]['text'] = json.dumps(answer)
        output['output'].insert(0, {'type': 'reasoning', 'summary': []})
        return httpx.Response(200, json=output)

    provider = OpenAIProvider(config(), httpx.MockTransport(handle))
    assert await provider.library_conversation(messages, candidates, 'explain') == answer


def test_library_conversation_accepts_discussion_and_rejects_unknown_or_repeated_tracks():
    candidates = [{'id': 'a'}]
    discussion = {'reply': 'Solo consta el título de esa grabación.', 'selections': []}
    assert validate_library_answer(discussion, candidates) == discussion
    for ids in (['outside'], ['a', 'a']):
        invalid = {**discussion, 'selections': [{'track_id': identity, 'reason': 'Para empezar.'} for identity in ids]}
        with pytest.raises(AIError) as failure:
            validate_library_answer(invalid, candidates)
        assert failure.value.code == 'ai_invalid_response'


@pytest.mark.parametrize('source', ['previous_tracks', 'catalog_matches'])
async def test_conversation_accepts_references_returned_by_catalog_lookup(source):
    plan = {'intent': 'recommend', 'query': '', 'reference_id': 'catalog-id', 'discovery': False,
            'reply': 'Buscaré pistas cercanas a esa.', 'suggestions': []}
    envelope = generated()
    envelope['output'][0]['content'][0]['text'] = json.dumps(plan)
    provider = OpenAIProvider(config(), httpx.MockTransport(lambda _: httpx.Response(200, json=envelope)))
    context = {'tracks': [], source: [{'id': 'catalog-id'}], 'library_requested': True,
               'messages': [{'role': 'user', 'content': 'Algo similar a esa.'}]}
    assert await provider.conversation_plan(context) == plan
    context[source] = []
    with pytest.raises(AIError) as failure:
        await provider.conversation_plan(context)
    assert failure.value.code == 'ai_invalid_response'


async def test_embedding_uses_exact_model_dimensions_and_private_authorization():
    def handler(request):
        assert str(request.url) == 'https://api.openai.com/v1/embeddings'
        assert request.headers['Authorization'] == 'Bearer fake-test-key'
        body = json.loads(request.content)
        assert body == {'model':'text-embedding-3-small','dimensions':3,'encoding_format':'float','input':'Texto controlado'}
        return httpx.Response(200,json=vector())
    provider=OpenAIProvider(config(),httpx.MockTransport(handler))
    result=await provider.embed('Texto controlado')
    assert len(result['vector']) == 3 and 'dimensions=3' in result['model_key']


@pytest.mark.parametrize('bad', [
    vector(data=[]), vector(data=[{'index':0,'embedding':[1,2]}]),
    vector(data=[{'index':0,'embedding':[True,1,2]}]),
    vector(data=[{'index':0,'embedding':[0,0,0]}]),
    vector(data=[{'index':0,'embedding':[1,math.inf,2]}]),
    vector(model='other-space'), vector(usage={'total_tokens':-1}),
])
async def test_rejects_invalid_or_incompatible_vectors(bad):
    # json.dumps permite construir explícitamente una respuesta NaN/Infinity defectuosa.
    provider=OpenAIProvider(config(),httpx.MockTransport(lambda _:httpx.Response(200,content=json.dumps(bad).encode())))
    with pytest.raises(AIError) as err: await provider.embed('Texto')
    assert err.value.code == 'ai_invalid_response'


async def test_structured_generation_no_tools_no_storage_and_quotes_verified():
    def handler(request):
        body=json.loads(request.content)
        assert body['store'] is False and body['max_output_tokens']==512
        assert 'tools' not in body and body['text']['format']['strict'] is True
        assert body['reasoning']=={'effort':'none'}
        return httpx.Response(200,json=generated())
    result=await OpenAIProvider(config(),httpx.MockTransport(handler)).generate('¿Qué consta?',SOURCES)
    assert result['output']['evidence'][0]['source_id']=='a'


@pytest.mark.parametrize('change', [
    {'status':'incomplete'}, {'output':[]},
    {'output':[{'type':'message','content':[{'type':'refusal','refusal':'No.'}]}]},
    {'output':[{'type':'message','content':[{'type':'output_text','text':'no-json'}]}]},
    {'model':'otro-modelo'},
])
async def test_generation_handles_refusal_incomplete_and_invalid_json(change):
    provider=OpenAIProvider(config(),httpx.MockTransport(lambda _:httpx.Response(200,json=generated(**change))))
    with pytest.raises(AIError) as err: await provider.generate('Consulta',SOURCES)
    assert err.value.code in {'ai_refusal','ai_invalid_response'}


@pytest.mark.parametrize('citation',[{'source_id':'ajena','version':1,'quote':'sin voces'},{'source_id':'a','version':2,'quote':'sin voces'},{'source_id':'a','version':1,'quote':'con guitarra'}])
async def test_rejects_foreign_citations_versions_or_invented_quotes(citation):
    value=generated();value['output'][0]['content'][0]['text']=json.dumps({'text':'Explicación','evidence':[citation]})
    provider=OpenAIProvider(config(),httpx.MockTransport(lambda _:httpx.Response(200,json=value)))
    with pytest.raises(AIError) as err: await provider.generate('Consulta',SOURCES)
    assert err.value.code=='ai_invalid_response'


@pytest.mark.parametrize('code,expected',[(401,'ai_authentication'),(403,'ai_authentication'),(429,'ai_rate_limit'),(500,'ai_unavailable')])
async def test_provider_errors_do_not_leak_secret_body_or_retry_uncertain_calls(code,expected):
    calls=[]
    def handler(request):
        calls.append(1);return httpx.Response(code,json={'error':{'message':'fake-test-key /ruta/privada'}})
    with pytest.raises(AIError) as err: await OpenAIProvider(config(),httpx.MockTransport(handler)).embed('Texto')
    assert err.value.code==expected and 'fake-test-key' not in str(err.value) and len(calls)==1


async def test_quota_never_retries_and_rate_limit_retry_is_bounded():
    calls=[]
    def rate(request):
        calls.append(1);return httpx.Response(429,json={'error':{'code':'rate_limit_exceeded'}},headers={'Retry-After':'0'})
    with pytest.raises(AIError) as err: await OpenAIProvider(config(ai_rate_limit_retries=1),httpx.MockTransport(rate)).embed('Texto')
    assert len(calls)==2 and err.value.code=='ai_rate_limit'
    calls.clear()
    def quota(request):
        calls.append(1);return httpx.Response(429,json={'error':{'code':'insufficient_quota'}})
    with pytest.raises(AIError) as err: await OpenAIProvider(config(ai_rate_limit_retries=1),httpx.MockTransport(quota)).embed('Texto')
    assert len(calls)==1 and err.value.code=='ai_quota'


async def test_timeout_never_retries_and_concurrency_is_one():
    async def timeout(request): raise httpx.ReadTimeout('private',request=request)
    with pytest.raises(AIError) as err: await OpenAIProvider(config(),httpx.MockTransport(timeout)).embed('Texto')
    assert err.value.code=='ai_timeout'
    entered,release=asyncio.Event(),asyncio.Event()
    async def slow(request):
        entered.set();await release.wait();return httpx.Response(200,json=vector())
    provider=OpenAIProvider(config(),httpx.MockTransport(slow))
    task=asyncio.create_task(provider.embed('Texto'));await entered.wait()
    try:
        with pytest.raises(AIError) as err: await provider.embed('Otro')
        assert err.value.code=='ai_busy'
    finally: release.set();await task


async def test_disabled_missing_key_and_invalid_input_never_touch_transport():
    calls=[]
    def handler(request): calls.append(1);raise AssertionError('No debe llamar')
    for settings,expected in [(config().model_copy(update={'ai_enabled':False}),'ai_disabled'),(config().model_copy(update={'openai_api_key':SecretStr('')}),'ai_not_configured')]:
        with pytest.raises(AIError) as err: await OpenAIProvider(settings,httpx.MockTransport(handler)).embed('Texto')
        assert err.value.code==expected
    provider=OpenAIProvider(config(),httpx.MockTransport(handler))
    for text in ['', 'x'*6001]:
        with pytest.raises(AIError): await provider.embed(text)
    with pytest.raises(AIError): await provider.generate('Consulta',[])
    assert not calls


async def test_status_endpoint_is_configuration_only_and_redacts_key():
    app=create_app(config())
    try:
        async with AsyncClient(transport=ASGITransport(app),base_url='http://localhost') as api:
            response=await api.get('/api/v1/ai/status')
        assert response.status_code==200 and response.json()['verification']=='not_checked'
        assert 'fake-test-key' not in response.text and 'OPENAI_API_KEY' not in response.text
    finally:
        if app.state.database_engine is not None: app.state.database_engine.dispose()


async def test_real_probe_missing_key_never_creates_success_receipt(tmp_path):
    from app.ai_check import probe
    settings=config().model_copy(update={'openai_api_key':SecretStr(''), 'media_root':tmp_path / 'media'})
    with pytest.raises(AIError) as err: await probe(settings)
    assert err.value.code=='ai_not_configured' and not (tmp_path / 'ai_checks').exists()


async def test_openai_key_save_applies_immediately_and_survives_restart(tmp_path):
    settings = config(media_root=tmp_path / 'media')
    app = create_app(settings)
    key = 'sk-synthetic-for-test'
    async with AsyncClient(transport=ASGITransport(app), base_url='http://localhost') as api:
        denied = await api.put('/api/v1/ai/key', json={'key': key})
        assert denied.status_code == 403
        invalid = await api.put('/api/v1/ai/key', json={'key': 'invalid'}, headers={'Origin': 'http://localhost:5173'})
        assert invalid.status_code == 422
        assert not (tmp_path / '.openai-key').exists()
        response = await api.put('/api/v1/ai/key', json={'key': key}, headers={'Origin': 'http://localhost:5173'})
        assert response.status_code == 200
        assert response.json()['available']
        assert key not in response.text
        assert (await api.get('/api/v1/explore/chat/status')).json()['cloud_ready']
    assert app.state.ai_provider.settings.openai_api_key.get_secret_value() == key
    restarted = create_app(config(media_root=settings.media_root))
    assert restarted.state.settings.openai_api_key.get_secret_value() == key
    remote = create_app(config(media_root=settings.media_root, ai_key_editable=False))
    async with AsyncClient(transport=ASGITransport(remote), base_url='http://localhost') as api:
        denied = await api.put('/api/v1/ai/key', json={'key': 'sk-another-test'}, headers={'Origin': 'http://localhost:5173'})
        assert denied.status_code == 403
    assert remote.state.settings.openai_api_key.get_secret_value() == 'fake-test-key'


async def test_input_evidence_invalid_and_oversized_response_are_rejected():
    provider=OpenAIProvider(config(),httpx.MockTransport(lambda _:httpx.Response(200,content=b'x' * 1_000_001)))
    with pytest.raises(AIError) as err: await provider.embed('Texto')
    assert err.value.code=='ai_invalid_response'
    for evidence in [[*SOURCES,*SOURCES],[{'source_id':'a','version':0,'text':'Texto'}]]:
        with pytest.raises(AIError) as err: await provider.generate('Consulta',evidence)
        assert err.value.code=='ai_input_invalid'


async def test_total_deadline_is_enforced():
    async def slow(request):
        await asyncio.sleep(2)
        return httpx.Response(200,json=vector())
    provider=OpenAIProvider(config(ai_timeout_seconds=1),httpx.MockTransport(slow))
    with pytest.raises(AIError) as err: await provider.embed('Texto')
    assert err.value.code=='ai_timeout' and provider.busy is False


@pytest.mark.parametrize('provider_code',['credit_balance_exhausted','organization_spend_limit_exceeded','project_spend_limit_exceeded','organization_usage_limit_exceeded'])
async def test_current_billing_codes_never_retry(provider_code):
    calls=[]
    def handler(request):
        calls.append(1);return httpx.Response(429,json={'error':{'code':provider_code}})
    with pytest.raises(AIError) as err: await OpenAIProvider(config(ai_rate_limit_retries=1),httpx.MockTransport(handler)).embed('Texto')
    assert err.value.code=='ai_quota' and err.value.provider_code==provider_code and len(calls)==1
