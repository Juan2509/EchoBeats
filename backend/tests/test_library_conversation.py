"""Conversaciones sobre pistas gestionadas, con proveedor simulado y catálogo aislado."""

from pydantic import SecretStr
import pytest

from app.integrations.ai import AIError
from app.integrations.storage import MediaStore
from app.services import audio_similarity
from test_audio_similarity import tone, wav
from test_descriptions import body as description_body
from test_metadata import upload
from test_music_chat import chat_client


pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def enable_provider(app, provider):
    app.state.settings.ai_enabled = True
    app.state.settings.openai_api_key = SecretStr('fake-test-only')
    app.state.ai_provider = provider


async def ask(client, messages, previous=()):
    result = await client.post('/api/v1/explore/chat', json={
        'messages': messages, 'previous_track_ids': list(previous), 'use_ai': True,
    })
    assert result.status_code == 200, result.text
    return result.json()


async def test_model_chooses_and_explains_a_real_library_track(chat_client):
    client, app = chat_client
    low = (await upload(client, wav(tone(110)), 'Umbral.wav'))['track_id']
    high = (await upload(client, wav(tone(2600)), 'Destello.wav'))['track_id']
    description = 'Entrada breve que contrasta con la pista anterior.'
    saved = await client.put(f'/api/v1/tracks/{high}/description', headers={'If-None-Match': '*'},
                             json=description_body(text=description))
    assert saved.status_code == 200, saved.text
    engine = app.state.database_engine
    store = MediaStore(app.state.settings.media_root)
    with engine.connect() as connection:
        pending = audio_similarity.pending_tracks(connection)
    for candidate in pending:
        assert audio_similarity.index_audio(engine, store, candidate)

    chosen_reply = 'Elegiría Destello para empezar por el contraste con el registro grave de Umbral.'
    reason = 'En el comienzo analizado predominan las frecuencias agudas.'
    followup_reply = 'Elegí Destello porque su entrada destaca en agudos y ofrece el contraste que pediste.'

    class Provider:
        def __init__(self):
            self.actions = []

        async def library_conversation(self, messages, candidates, action):
            self.actions.append(action)
            by_id = {item['id']: item for item in candidates}
            selected = by_id[high]
            assert selected['title'] == 'Destello'
            assert selected['acoustic']['frequency_weights']['treble'] > selected['acoustic']['frequency_weights']['bass']
            assert description in str(selected['description'])
            assert 'storage_key' not in selected
            if action == 'choose':
                assert set(by_id) == {low, high}
                reply = chosen_reply
            else:
                assert action == 'explain'
                assert messages[-1]['content'] == '¿Y por qué te gusta más esa?'
                assert any(chosen_reply in message['content'] for message in messages if message['role'] == 'assistant')
                reply = followup_reply
            return {'reply': reply, 'selections': [{'track_id': high, 'reason': reason}]}

    provider = Provider()
    enable_provider(app, provider)
    history = [
        {'role': 'user', 'content': '¿Qué tengo en mi biblioteca?'},
        {'role': 'assistant', 'content': 'Aquí tienes las dos pistas importadas.'},
        {'role': 'user', 'content': '¿Cuál te gusta más? Quiero contraste.'},
    ]
    choice = await ask(client, history, [low, high])
    assert choice['mode'] == 'ai' and choice['provider'] == 'openai'
    assert choice['reply'] == chosen_reply
    assert [item['track']['id'] for item in choice['recommendations']] == [high]
    assert choice['recommendations'][0]['reason'] == reason
    history.extend([
        {'role': 'assistant', 'content': choice['reply']},
        {'role': 'user', 'content': '¿Y por qué te gusta más esa?'},
    ])
    followup = await ask(client, history, [high])
    assert provider.actions == ['choose', 'explain']
    assert followup['mode'] == 'ai'
    assert followup['reply'] == followup_reply
    assert not followup['suggestions'] and not followup['warnings']


async def test_library_followup_survives_provider_failure_without_an_acoustic_profile(chat_client):
    client, app = chat_client
    identity = (await upload(client, wav(bytes(16000)), 'Silencio.wav'))['track_id']

    class Rejected:
        async def library_conversation(self, messages, candidates, action):
            assert action == 'explain'
            assert [item['id'] for item in candidates] == [identity]
            assert not candidates[0].get('acoustic')
            raise AIError('ai_unavailable')

    enable_provider(app, Rejected())
    result = await ask(client, [
        {'role': 'user', 'content': 'Elige una pista de la biblioteca'},
        {'role': 'assistant', 'content': 'Empezaría por Silencio.'},
        {'role': 'user', 'content': '¿Y por qué te gusta más esa?'},
    ], [identity])
    assert result['mode'] == 'local' and result['warnings']
    assert 'Silencio' in result['reply']
    assert not result['suggestions']
    assert 'dime un juego' not in result['reply'].lower()


async def test_visible_cards_do_not_redirect_unrelated_topics_into_library(chat_client):
    client, app = chat_client
    identity = (await upload(client, wav(tone(200)), 'Eco.wav'))['track_id']
    general_reply = 'La luna refleja la luz del sol.'

    class GeneralProvider:
        async def conversation_plan(self, context):
            assert not context['library_requested']
            return {'intent': 'discuss', 'query': '', 'reference_id': None, 'discovery': False,
                    'reply': general_reply, 'suggestions': []}

    enable_provider(app, GeneralProvider())
    answer = await ask(client, [
        {'role': 'user', 'content': 'Elige una de mi biblioteca.'},
        {'role': 'assistant', 'content': 'Elegiría Eco.'},
        {'role': 'user', 'content': 'Cambiando de tema, ¿por qué brilla la luna?'},
    ], [identity])
    assert answer['reply'] == general_reply
    assert not answer['recommendations']


@pytest.mark.parametrize('provider_fails', [False, True])
async def test_choice_revalidates_tracks_after_provider_returns(chat_client, provider_fails):
    client, app = chat_client
    retiring = (await upload(client, wav(tone(160)), 'Niebla.wav'))['track_id']
    kept = (await upload(client, wav(tone(240)), 'Brisa.wav'))['track_id']
    stale_reply = 'Elegiría Niebla, que puedes reproducir ahora.'

    class ConcurrentRemoval:
        async def library_conversation(self, messages, candidates, action):
            track_url = f'/api/v1/tracks/{retiring}'
            current = await client.get(track_url)
            retired = await client.delete(track_url, headers={'If-Match': current.headers['etag']})
            assert retired.is_success, retired.text
            if provider_fails:
                raise AIError('ai_timeout')
            return {'reply': stale_reply, 'selections': [
                {'track_id': retiring, 'reason': 'Era una de las pistas mostradas.'},
            ]}

    enable_provider(app, ConcurrentRemoval())
    result = await ask(client, [{'role': 'user', 'content': '¿Cuál te gusta más?'}], [retiring, kept])
    assert (await client.get(f'/api/v1/tracks/{retiring}')).status_code == 404
    assert result['reply'] != stale_reply
    assert all(item['track']['id'] != retiring for item in result['recommendations'])
