"""Conversación acotada: plan opcional de IA, recuperación real y razones comprobables."""
import re
import unicodedata
from uuid import UUID
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool
from app.integrations.ai import AIError,ConversationPlan
from pydantic import ValidationError
from app.models.catalog import artist, track, track_artist, favorite, track_description
from app.services import metadata,search,exploration

def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def context_for(engine,current,recent,reference):
    with engine.connect() as connection:
        favorites=list(connection.scalars(select(favorite.c.track_id).join(track,track.c.id==favorite.c.track_id).where(track.c.deleted_at.is_(None)).order_by(favorite.c.created_at.desc()).limit(8)))
        requested=list(dict.fromkeys([identity for identity in [reference,current,*recent,*favorites] if identity]))[:24]
        valid=list(connection.scalars(select(track.c.id).where(track.c.id.in_(requested),track.c.deleted_at.is_(None))))
        data=metadata.tracks_data(connection,valid)
        # IDs vienen del cliente, pero títulos/autor/fichas se resuelven en servidor.
        desc=dict(connection.execute(select(track_description.c.track_id,track_description.c.text).where(track_description.c.track_id.in_(valid))).all())
        rows=[{'id':str(item['id']),'title':item['title'],'album':item['album_title'],'artists':[a['name'] for a in item['artists']], 'description':desc.get(item['id'],'')[:180]} for item in data]
        return {'tracks':rows,'favorites':[str(i) for i in favorites if i in valid], 'recent':[str(i) for i in recent if i in valid], 'current':str(current) if current in valid else None,'reference':str(reference) if reference in valid else None}

def local_discussion(messages, *, clarify):
    user_messages = [m['content'] for m in messages if m['role'] == 'user']
    topic = user_messages[-2] if clarify and len(user_messages) > 1 else user_messages[-1]
    if re.search(r'\b(?:videojuegos?|video juegos?|videogames?)\b', normalized(topic)):
        if clarify:
            return ('Me refiero a cómo la música acompaña lo que haces en el juego. '
                    'Por ejemplo, una melodía tranquila puede acompañar la exploración, '
                    'y una percusión más intensa puede anunciar un combate.')
        return ('Las bandas sonoras de videojuegos tienen algo especial: una melodía puede '
                'hacerte recordar un lugar del juego. ¿Te atrae más la música tranquila '
                'de exploración o la intensidad de los combates?')
    if clarify:
        return ('Si te refieres al modo local, puedo buscar canciones que ya tengas en EchoBeats. '
                'Para comentar géneros, discos o tus gustos con más detalle, hace falta habilitar la IA.')
    return ('¿Qué es lo que más te gusta de esa música: el ritmo, la instrumentación o la atmósfera? '
            'En modo local puedo usar lo que me cuentes como punto de partida para buscar en tu biblioteca.')


SWITCH_FORCE_REFERENCE = {
    'title': 'Mighty Switch Force 2 OST',
    'artist': 'Jake Kaufman',
    'work': 'Mighty Switch Force! 2',
    'match': 'approximate',
    'reason': 'Es la secuela musical del mismo compositor y comparte el cruce de chiptune, electro y house. Es otra banda sonora, con temas distintos.',
    'source_url': 'https://virt.bandcamp.com/album/mighty-switch-force-2-ost',
}


NON_GAME_REFERENCES = (
    {'title': 'D.A.N.C.E.', 'artist': 'Justice', 'work': None, 'match': 'approximate',
     'reason': 'Mantiene la energía del electro bailable y añade un coro pop.',
     'source_url': 'https://etjusticepourtous.bandcamp.com/track/d-a-n-c-e'},
    {'title': 'Digital Love', 'artist': 'Daft Punk', 'work': 'Discovery', 'match': 'approximate',
     'reason': 'Conserva el pulso de baile y los sintetizadores melódicos, con un aire más disco.',
     'source_url': 'https://daftpunk.com/discovery/'},
)


SWITCH_FORCE_NAME = r'\bmight(?:y)? switch force\b'


def excludes_game_music(messages):
    previous = [normalized(m['content']) for m in messages if m['role'] == 'user']
    games = r'(?:video\s*juegos?|videogames?|juegos?)'
    exclusion = (rf'\b(?:sin|ni|fuera de)\s+(?:(?:musica|bandas sonoras?) de\s+)?{games}\b'
                 rf'|\b(?:no|nada)\b[^.!?;]{{0,55}}\b(?:de|a)\s+{games}\b')
    inclusion = rf'\b(?:si quiero|volvamos a|ahora (?:quiero|si)|incluye|puedes incluir)\b[^.!?;]{{0,55}}\b{games}\b'
    latest = previous[-1]
    if re.search(exclusion, latest):
        return True
    followup = re.search(r'\b(?:otra|otras|otro|otros|opciones|parecid[oa]s?|algo mas)\b|^(?:mas|menos|pero)\b', latest)
    follows_style = re.search(r'\b(?:estilo|sonido|ritmo|atmosfera|sintetizadores|pulso|melodia)\b', latest)
    if not (followup or follows_style or re.search(SWITCH_FORCE_NAME, latest)):
        return False
    for text in reversed(previous):
        if re.search(exclusion, text):
            return True
        if re.search(inclusion, text):
            return False
    return False


def discovery_without_games(messages):
    user_text = ' '.join(normalized(m['content']) for m in messages if m['role'] == 'user')
    if re.search(SWITCH_FORCE_NAME, user_text) or re.search(r'\b(?:chiptune|electro|sintetizadores)\b', user_text):
        shown = ' '.join(normalized(m['content']) for m in messages if m['role'] == 'assistant')
        item = next((item for item in NON_GAME_REFERENCES if normalized(item['title']) not in shown), None)
        if item:
            return 'Fuera de los videojuegos, esta opción conserva parte del pulso electrónico que buscas.', [item]
    return ('Dejemos fuera las bandas sonoras de videojuegos. ¿Qué quieres conservar del sonido: el pulso bailable, '
            'los sintetizadores o la melodía?'), []


def local_discovery(messages):
    latest = normalized(messages[-1]['content'])
    topics = latest
    if re.match(r'^(?:mas|menos|algo mas|otra|otras|pero|ese|esa|atmosfera|ambiente)\b', latest):
        topics = ' '.join(normalized(m['content']) for m in messages if m['role'] == 'user'
                          and not normalized(m['content']).startswith('soy '))
    queer_music = r'\b(?:gei|gay|queer|lgbtq?)\b'
    if re.search(queer_music, latest) or (
        re.search(queer_music, topics) and re.search(r'\b(?:atmosfera|tematica|ambiente)\b', latest)
    ):
        return 'Si buscas algo bailable con temática queer, tengo un ejemplo local de synth-pop.', [
            {'title': 'Smalltown Boy', 'artist': 'Bronski Beat', 'work': None, 'match': 'direct',
             'reason': 'Combina un pulso de pista de baile con una letra sobre el rechazo y la búsqueda de un lugar propio.'},
        ]
    if re.search(r'\b(?:videojuegos?|video juegos?|videogames?|celeste)\b', topics):
        return 'El ejemplo local que más se acerca viene de Celeste. Si tenías en mente otro juego o una escena concreta, dime cuál.', [
            {'title': 'First Steps', 'artist': 'Lena Raine', 'work': 'Celeste', 'match': 'approximate',
             'reason': 'Sus sintetizadores y el ritmo ágil evocan exploración y movimiento. Es una referencia de ese ambiente; si buscas combate orquestal, el carácter es distinto.'},
        ]
    return ('Para darte ejemplos concretos de ese sonido necesito la IA. '
            'Si quieres, dime un juego, una escena o algún rasgo como «sintetizadores lentos» para precisar la búsqueda.'), []


def local_plan(messages,context):
    text=messages[-1]['content'].strip();plain=normalized(text)
    phrase=' '.join(re.findall(r'\w+',plain))
    greeting=r'hola|buenas|hey|buenos dias|buenas tardes|buenas noches'
    check_in=r'que tal|como estas|como va|como te va|que hay'
    if re.fullmatch(rf'(?:{greeting})(?: (?:{check_in}))?|(?:{check_in})',phrase):
        return {'intent':'greeting','query':'','reference_id':None,'discovery':False}
    if re.fullmatch(r'(?:muchas )?gracias(?: por (?:la ayuda|las recomendaciones))?|genial|perfecto',phrase):
        return {'intent':'thanks','query':'','reference_id':None,'discovery':False}
    if re.fullmatch(r'(?:a )?que te refieres(?: con eso)?|que quieres decir(?: con eso)?|como asi|no (?:te )?entendi|puedes explicarlo',phrase):
        return {'intent':'clarify','query':'','reference_id':None,'discovery':False}
    if any(p in plain for p in ['mis gustos','que me gusta','que sabes de mi']):return {'intent':'preferences','query':'','reference_id':None,'discovery':False}
    prior=[m['content'] for m in messages[:-1] if m['role']=='user']
    query=(' '.join([prior[-1],text]) if prior and any(p in plain for p in ['mas ','menos ','otra','pero ','tambien']) else text)[-700:]
    ref=context['reference'] or (context['current'] if any(p in plain for p in ['como esta','lo que escucho','parecid','esta cancion']) else None)
    if any(p in plain for p in ['fuera de mi biblioteca','fuera de la biblioteca','fuera de echobeats','no esten en mi biblioteca','no busques en mi biblioteca','no busques en la biblioteca']):
        return {'intent':'discover','query':query,'reference_id':None,'discovery':True}
    if not ref and context['recent'] and 'lo que escucho' in plain:ref=context['recent'][0]
    library_requested = ref or re.search(r'\b(?:biblioteca|favoritos|mi catalogo|mis canciones|mis pistas|escuchar aqui|reproducir aqui)\b', phrase)
    if library_requested:
        return {'intent':'recommend','query':query,'reference_id':ref,'discovery':'sin favoritos' in phrase}
    if re.match(r'^soy (?:gei|gay|queer|lesbiana|bisexual|trans)\b', phrase):
        return {'intent':'acknowledge','query':'','reference_id':None,'discovery':False}
    if re.search(r'\b(?:gei|gay|queer|lgbtq?)\b', phrase):
        return {'intent':'discover','query':query,'reference_id':None,'discovery':True}
    if re.match(r'(?:hablemos (?:de|sobre)|charlemos|que opinas|que piensas|que distingue|por que me gusta|cual es la diferencia|me (?:gusta|encanta))\b',phrase):
        return {'intent':'discuss','query':'','reference_id':None,'discovery':False}
    return {'intent':'discover','query':query,'reference_id':None,'discovery':True}


def catalog_fallback(engine,query,context,discovery,reference,exclude=(),limit=5):
    """Alternativa sin vectores: solo coincidencias registradas y señales explícitas."""
    with engine.connect() as connection:
        favorites=set(connection.scalars(select(favorite.c.track_id)))
        seeds=[UUID(i) for i in [context['current'],*context['recent'],*context['favorites']] if i]
        albums=set(connection.scalars(select(track.c.album_id).where(track.c.id.in_(seeds),track.c.deleted_at.is_(None))))
        candidates=connection.scalars(select(track.c.id).where(track.c.deleted_at.is_(None),track.c.id.not_in(exclude),*( [track.c.id.not_in(favorites)] if discovery else []),*( [track.c.id!=UUID(reference)] if reference else [])).order_by(track.c.id.in_(seeds).desc(),track.c.created_at.desc(),track.c.id).limit(500)).all()
        rows=metadata.tracks_data(connection,candidates)
        words={w for w in re.findall(r'\w+',normalized(query)) if len(w)>3} - {'quiero','musica','recomienda','recomiendame','algo','como','para','escuchar','favoritos','estoy','puedes','tengo'}
        ranked=[]
        for index,item in enumerate(rows):
            hay=normalized(' '.join([item['title'],item['album_title'],*[a['name'] for a in item['artists']]]))
            matches=sum(word in hay for word in words);fav=item['id'] in favorites;same=item['album_id'] in albums
            if not (matches or fav or same):
                continue
            reason='Coincide con palabras del título, artista o álbum.' if matches else 'La marcaste como favorita.' if fav else 'Pertenece a un álbum de tus favoritos o reproducciones de esta sesión.'
            ranked.append((matches*20+int(fav)*5+int(same)*3,-index,{'track':item,'reason':reason,'evidence':[]}))
        ranked.sort(key=lambda row:(row[0],row[1]),reverse=True)
        return [row[2] for row in ranked[:limit]],len(candidates)>=500

def new_suggestions(engine, suggestions):
    if not suggestions:
        return []
    titles = [item['title'].lower() for item in suggestions]
    with engine.connect() as connection:
        existing = connection.execute(
            select(track.c.title, artist.c.name)
            .join(track_artist, track_artist.c.track_id == track.c.id)
            .join(artist, artist.c.id == track_artist.c.artist_id)
            .where(track.c.deleted_at.is_(None), func.lower(track.c.title).in_(titles))
        )
        seen = {(normalized(title), normalized(name)) for title, name in existing}
    result = []
    for item in suggestions:
        key = (normalized(item['title']), normalized(item['artist'] or item['work'] or ''))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


async def respond(engine,settings,provider,messages,current,recent,reference,use_ai,previous=(),*,local_provider=None,requested_provider=None):
    context=await run_in_threadpool(context_for,engine,current,recent,reference)
    warnings=[];plan=local_plan(messages,context);used_ai=False;suggestions=[]
    switch_force = bool(re.search(SWITCH_FORCE_NAME + r'(?!\s*!?\s*2)', normalized(messages[-1]['content'])))
    use_ollama = requested_provider == 'ollama' or (requested_provider is None and local_provider is not None)
    if reference and not context['reference']:
        raise metadata.MetadataError('track_not_found','La pista de referencia ya no está en la biblioteca.',404)
    exclude_games = plan['intent'] not in {'greeting', 'thanks'} and excludes_game_music(messages)
    if use_ai and not exclude_games and plan['intent'] not in {'greeting', 'thanks'}:
        library_requested=plan['intent']=='recommend'
        try:
            if use_ollama:
                if local_provider is None:raise AIError('local_model_unavailable')
            else:
                if not settings.ai_enabled:raise AIError('ai_disabled')
                if not settings.openai_api_key.get_secret_value().strip():raise AIError('ai_not_configured')
            generator=local_provider if use_ollama else provider
            grounding = {'related_soundtrack': SWITCH_FORCE_REFERENCE} if switch_force else {}
            generated=await generator.conversation_plan({'messages':messages,'library_requested':library_requested,**context,**grounding})
            plan=ConversationPlan.model_validate(generated).model_dump()
            if plan['intent']=='recommend' and not library_requested:raise AIError('ai_invalid_response')
            if plan['reference_id'] and plan['reference_id'] not in {t['id'] for t in context['tracks']}:raise AIError('ai_invalid_response')
            used_ai=True
        except (AIError,ValidationError) as error:
            plan=local_plan(messages,context)
            if isinstance(error,AIError) and error.code=='ai_quota':
                warnings.append('OpenAI rechazó la solicitud por cuota. Para descubrir música con IA, revisa el saldo de la cuenta configurada.')
            else:
                warnings.append(f'{error} Seguí en modo local.' if isinstance(error,AIError) else 'La IA devolvió una respuesta no válida. Seguí en modo local.')
    mode='ai' if used_ai else 'local';recommendations=[]
    exclude=previous if any(word in normalized(messages[-1]['content']) for word in ['otras','otra opcion','mas opciones','diferentes','diferente']) else ()
    if exclude_games:
        reply,suggestions=discovery_without_games(messages)
    elif used_ai and plan['intent'] in {'discuss','greeting','preferences','clarify'}:
        reply=plan['reply']
    elif plan['intent']=='greeting':reply='¡Hola! ¿Cómo va todo?'
    elif plan['intent']=='thanks':reply='¡De nada!'
    elif plan['intent']=='acknowledge':reply='Gracias por contármelo. ¿Qué música te gusta?'
    elif plan['intent']=='discuss':reply=local_discussion(messages,clarify=False)
    elif plan['intent']=='preferences':reply=f"Ahora puedo tomar como referencia {len(context['favorites'])} favoritos y {len(context['recent'])} reproducciones recientes de esta sesión. No tengo un historial completo ni conozco tus gustos fuera de EchoBeats."
    elif plan['intent']=='clarify':reply=local_discussion(messages,clarify=True)
    elif plan['intent']=='discover':
        if switch_force:
            reply='Por la mezcla de electro y chiptune de Mighty Switch Force, empezaría por la banda sonora de la secuela. Es la referencia más cercana que tengo documentada.'
            suggestions=[SWITCH_FORCE_REFERENCE]
        elif used_ai:
            suggestions=await run_in_threadpool(new_suggestions,engine,plan['suggestions'])
            reply=plan['reply'] if suggestions else 'No tengo una sugerencia concreta para esa petición. Si me dices un juego, una escena o el tipo de sonido, puedo acotar la búsqueda.'
        else:
            reply,suggestions=local_discovery(messages)
    else:
        data=None
        try:
            if plan['reference_id']:data=await run_in_threadpool(search.similar,engine,settings,UUID(plan['reference_id']),5,None,None,'discovery' if plan['discovery'] else 'favorites')
            else:data=await search.search(engine,settings,provider,plan['query'] or messages[-1]['content'],'hybrid' if used_ai and not use_ollama else 'lexical',5,preferences='discovery' if plan['discovery'] else 'favorites')
            for item in (data or {}).get('results',[]):
                if item['track']['id'] in exclude:continue
                saved=exploration.recorded(item)
                recommendations.append({'track':item['track'],'reason':'Su ficha guardada contiene estos fragmentos.','evidence':saved['evidence']})
        except (AIError,metadata.MetadataError):
            warnings.append('No pude completar la búsqueda por fichas. Estas opciones usan el catálogo y tus señales explícitas.')
        if not recommendations:
            recommendations,truncated=await run_in_threadpool(catalog_fallback,engine,plan['query'],context,plan['discovery'],plan['reference_id'],exclude)
            if truncated:warnings.append('La alternativa local revisó hasta 500 pistas, priorizando las señales de contexto y las incorporaciones recientes.')
        reply='Estas son las pistas de tu biblioteca con las señales más cercanas. Cada tarjeta indica por qué apareció; el parecido musical es orientativo.' if recommendations else 'En la búsqueda que pediste dentro de tu biblioteca no encontré resultados con señales suficientes. Si quieres, puedo explorar música en general.'
    return {'reply':reply,'mode':mode,'provider':('ollama' if use_ollama else 'openai') if used_ai else None,'recommendations':recommendations,'suggestions':suggestions,'warnings':warnings,'context':{'favorites':len(context['favorites']),'recent':len(context['recent']),'current':context['current']}}
