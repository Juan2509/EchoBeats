"""Compose a library answer from live catalog evidence and the conversation."""
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.integrations.ai import AIError, validate_library_answer
from app.models.catalog import favorite, track
from app.services import audio_similarity, metadata, search


def snapshot(engine, settings, cards, context, previews, discovery):
    ids = [card['track']['id'] for card in cards]
    supplied = {card['track']['id']: card for card in cards}
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
        documents = metadata.tracks_data(connection, ids)
        favorites = set(connection.scalars(select(favorite.c.track_id).where(favorite.c.track_id.in_(ids))))
        profiles = audio_similarity.acoustic_profiles(connection, ids)
        records = {row.track_id: row for row in connection.execute(
            search.eligible(settings, [track.c.id.in_(ids)], require_embedding=False)
        )}

    candidates, active_cards = [], {}
    for doc in documents:
        identity = doc['id']
        if discovery and identity in favorites:
            continue
        card = supplied[identity]
        if doc['content_sha256'] != card['track']['content_sha256']:
            continue
        record = records.get(identity)
        description = record.text[:600] if record else ''
        evidence = []
        if record:
            evidence = [{'source_id': str(record.description_id), 'version': record.version,
                         'field': 'text', 'quote': record.text[:300]}]
        key = str(identity)
        candidates.append({
            'id': key, 'title': doc['title'], 'artists': [a['name'][:160] for a in doc['artists'][:8]],
            'album': doc['album_title'], 'duration_ms': doc['duration_ms'],
            'description': description, 'description_source': record.source if record else None,
            'features': [
                {field: (value[:160] if isinstance(value, str) else value)
                 for field, value in feature.items() if field in {'name','value','source','interpretation','evidence'}}
                for feature in (record.features[:5] if record else [])
            ],
            'acoustic': profiles.get(identity) or previews.get(identity),
            'favorite': identity in favorites, 'recent': key in context['recent'],
            'current': key == context['current'], 'previous': key in context['previous'],
            'retrieval_reason': card['reason'],
        })
        active_cards[key] = {'track': doc, 'reason': card['reason'], 'evidence': evidence}
    return candidates, active_cards


def local_answer(action, candidates, cards, default_reply):
    if action not in {'choose', 'explain', 'discuss', 'describe', 'conversation'} or not candidates:
        return default_reply, list(cards.values())[:5]
    # Keep the referent of an explanation. Only a new choice may reorder the options.
    item = candidates[0]
    if action == 'choose':
        item = max(candidates, key=lambda c: (c['favorite'], c['recent'], bool(c['description']), bool(c['acoustic'])))
    title = '«' + item['title'] + '»'
    if len(candidates) > 1 and action in {'explain', 'discuss', 'conversation'}:
        names = ', '.join('«' + c['title'] + '»' for c in candidates)
        return f'Entre {names}, ¿de cuál quieres que hable?', list(cards.values())
    card = cards[item['id']]
    if item['description']:
        detail = f'Su ficha dice «{item["description"][:180]}».'
    elif item['acoustic']:
        detail = item['acoustic']['summary']
    elif item['favorite']:
        detail = 'La marcaste como favorita.'
    elif item['recent']:
        detail = 'Empezó a sonar en esta sesión.'
    else:
        artists = ', '.join(item['artists'])
        credit = f' de {artists}' if artists else ''
        detail = f'La tengo registrada{credit} en el álbum «{item["album"]}».'
        return f'{title}. {detail} Con esos datos todavía no puedo decir qué la distingue musicalmente.', [card]
    lead = f'Empezaría por {title}.' if action == 'choose' else f'En el caso de {title}:'
    if item['acoustic'] and not item['description'] and action in {'choose', 'explain'}:
        band = max(item['acoustic']['frequency_weights'], key=item['acoustic']['frequency_weights'].get)
        emphasis = {'bass':'el peso de los graves', 'mid':'la presencia de las frecuencias medias',
                    'treble':'el brillo de los agudos'}[band]
        return f'De {title} destacaría {emphasis} en su comienzo. Es el rasgo que me llevaría a sugerírtela si buscas ese sonido.', [{**card, 'reason': detail}]
    return f'{lead} {detail}', [{**card, 'reason': detail}]


async def answer(engine, settings, provider, messages, context, use_ai, action, cards, default_reply,
                 *, previews=None, warnings=(), discovery=False):
    notices = list(warnings)
    previews = previews or {}
    cards = cards[:10]
    candidates, active = await run_in_threadpool(snapshot, engine, settings, cards, context, previews, discovery)
    selections = None
    if use_ai and candidates:
        try:
            if not settings.ai_enabled:
                raise AIError('ai_disabled')
            if not settings.openai_api_key.get_secret_value().strip():
                raise AIError('ai_not_configured')
            result = await provider.library_conversation(messages, candidates, action)
            result = validate_library_answer(result, candidates)
        except AIError as error:
            result = None
            notices.append(f'{error} Seguí con la información local de estas pistas.')
        current, active = await run_in_threadpool(snapshot, engine, settings, cards, context, previews, discovery)
        if current != candidates:
            candidates = current
            notices.append('La biblioteca cambió durante la consulta. Actualicé las pistas disponibles.')
        elif result is not None:
            selections = [{**active[item['track_id']], 'reason': item['reason']} for item in result['selections']]
            reply = result['reply']
    generated = selections is not None
    if not generated:
        if cards and not active:
            default_reply = 'Las pistas de esa consulta ya no están disponibles.'
        reply, selections = local_answer(action, candidates, active, default_reply)
    return {
        'reply': reply, 'mode': 'ai' if generated else 'local', 'provider': 'openai' if generated else None,
        'recommendations': selections, 'suggestions': [], 'warnings': notices,
        'context': {'favorites': len(context['favorites']), 'recent': len(context['recent']), 'current': context['current']},
    }
