"""Conversación acotada: plan opcional de IA, recuperación real y razones comprobables."""
import re
import unicodedata
from heapq import nlargest
from uuid import UUID
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool
from app.integrations.ai import AIError,ConversationPlan
from pydantic import ValidationError
from app.models.catalog import album, artist, media_asset, track, track_artist, favorite, track_description
from app.services import audio_similarity,metadata,search,exploration,library_dialogue

def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))

def context_for(engine,current,recent,reference,previous=()):
    with engine.connect() as connection:
        favorites=list(connection.scalars(select(favorite.c.track_id).join(track,track.c.id==favorite.c.track_id).where(track.c.deleted_at.is_(None)).order_by(favorite.c.created_at.desc()).limit(8)))
        requested=list(dict.fromkeys([identity for identity in [reference,current,*recent,*favorites] if identity]))[:24]
        valid=list(connection.scalars(select(track.c.id).where(track.c.id.in_(requested),track.c.deleted_at.is_(None))))
        acoustic=[];neighbor_ids=[]
        for seed in valid[:4]:
            candidates=audio_similarity.nearest_audio(connection,seed,3)
            if not candidates:continue
            neighbors=[{'track_id':str(item.id),'distance':round(float(item.distance),6)} for item in candidates]
            acoustic.append({'seed_track_id':str(seed),'neighbors':neighbors})
            neighbor_ids.extend(item.id for item in candidates)
        valid=list(dict.fromkeys([*valid,*neighbor_ids]))[:24]
        data=metadata.tracks_data(connection,valid)
        previous_data=metadata.tracks_data(connection,list(dict.fromkeys(previous))[:5])
        profile_ids = list(dict.fromkeys([*(item['id'] for item in previous_data), *valid[:4]]))
        profiles = audio_similarity.acoustic_profiles(connection, profile_ids)
        # IDs vienen del cliente, pero títulos/autor/fichas se resuelven en servidor.
        desc=dict(connection.execute(select(track_description.c.track_id,track_description.c.text).where(track_description.c.track_id.in_(valid))).all())
        rows=[{'id':str(item['id']),'title':item['title'],'album':item['album_title'],'artists':[a['name'] for a in item['artists']], 'description':desc.get(item['id'],'')[:180]} for item in data]
        return {'tracks':rows,'previous':[str(item['id']) for item in previous_data],
            'previous_tracks':[{'id':str(item['id']), 'title':item['title'], 'album':item['album_title'],
                                'artists':[artist['name'] for artist in item['artists']]} for item in previous_data],
            'favorites':[str(i) for i in favorites if i in valid], 'recent':[str(i) for i in recent if i in valid], 'current':str(current) if current in valid else None,'reference':str(reference) if reference in valid else None,
            'acoustic':{'method':'local_first_30_seconds_rank_v1','raw_audio_sent':False,'distance_is_confidence':False,
                        'seeds':acoustic, 'profiles':{str(identity): profile for identity, profile in profiles.items()}}}


def acoustic_recommendations(engine,reference,exclude,discovery=False):
    if not reference:return []
    try:data=audio_similarity.similar_audio(engine,UUID(reference),5,exclude=exclude,discovery=discovery)
    except metadata.MetadataError:return []
    return [{'track':item['track'],
        'reason':'Su comienzo tiene uno de los perfiles acústicos más cercanos en el análisis local de los primeros 30 segundos.',
        'evidence':[]} for item in data['results']]

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
    if re.fullmatch(r'(?:muy )?bien(?: gracias)? y tu|y tu como estas',phrase):
        return {'intent':'check_in','query':'','reference_id':None,'discovery':False}
    if re.fullmatch(r'(?:muchas )?gracias(?: por (?:la ayuda|las recomendaciones))?|genial|perfecto',phrase):
        return {'intent':'thanks','query':'','reference_id':None,'discovery':False}
    if re.fullmatch(r'(?:a )?que te refieres(?: con eso)?|que quieres decir(?: con eso)?|como asi|no (?:te )?entiend[oa]|no (?:te )?entendi|puedes explicarlo',phrase):
        return {'intent':'clarify','query':'','reference_id':None,'discovery':False}
    prior=[m['content'] for m in messages[:-1] if m['role']=='user']
    query=(' '.join([prior[-1],text]) if prior and any(p in plain for p in ['mas ','menos ','otra','pero ','tambien']) else text)[-700:]
    ref=context['reference'] or (context['current'] if any(p in plain for p in ['como esta','lo que escucho','parecid','esta cancion']) else None)
    if any(p in plain for p in ['fuera de mi biblioteca','fuera de la biblioteca','fuera de echobeats','no esten en mi biblioteca','no busques en mi biblioteca','no busques en la biblioteca']):
        return {'intent':'discover','query':query,'reference_id':None,'discovery':True}
    if (
        re.search(r'\b(?:la musica que escucho|que musica escucho)\b', phrase)
        or re.search(r'\b(?:que tengo en (?:mi|la) biblioteca|(?:que|cuantos?|cuantas?) (?:musica|canciones|pistas|archivos)\b.*\b(?:tengo|hay))\b', phrase)
        or re.fullmatch(r'(?:muestrame|revisa|consulta|explora) (?:(?:mi|la) biblioteca|mis (?:archivos|canciones|pistas))', phrase)
    ):
        return {'intent':'catalog_overview','query':'','reference_id':None,'discovery':False}
    if any(p in plain for p in ['mis gustos','que me gusta','que sabes de mi']):return {'intent':'preferences','query':'','reference_id':None,'discovery':False}
    if re.fullmatch(r'(?:puedes decirme )?(?:que (?:(?:cancion|pista|musica) (?:es|suena|esta sonando)|esta sonando|estoy escuchando)(?: (?:ahora|aqui))?|quien (?:canta|interpreta) (?:esto|esta cancion))', phrase):
        return {'intent':'identify','query':query,'reference_id':context['reference'] or context['current'],'discovery':False}
    if (
        re.search(r'\b(?:identifica(?:r|me)?|quien canta|quien interpreta|de quien es|como se llama|que (?:cancion|pista) es|esta en mi biblioteca)\b|^tengo\b', phrase)
        or re.search(r'\.(?:mp3|wav|flac|ogg|opus)\b', plain)
    ):
        return {'intent':'identify','query':query,'reference_id':context['reference'],'discovery':False}
    if not ref and context['recent'] and 'lo que escucho' in plain:ref=context['recent'][0]
    library_requested = ref or re.search(r'\b(?:biblioteca|favoritos|mi catalogo|mis canciones|mis pistas|mis archivos|nombre del archivo|escuchar aqui|reproducir aqui)\b', phrase)
    if library_requested:
        return {'intent':'recommend','query':query,'reference_id':ref,'discovery':'sin favoritos' in phrase}
    if re.match(r'^soy (?:gei|gay|queer|lesbiana|bisexual|trans)\b', phrase):
        return {'intent':'acknowledge','query':'','reference_id':None,'discovery':False}
    if re.search(r'\b(?:gei|gay|queer|lgbtq?)\b', phrase):
        return {'intent':'discover','query':query,'reference_id':None,'discovery':True}
    if re.match(r'(?:hablemos (?:de|sobre)|charlemos|que opinas|que piensas|que distingue|por que me gusta|cual es la diferencia|me (?:gusta|encanta))\b',phrase):
        return {'intent':'discuss','query':'','reference_id':None,'discovery':False}
    return {'intent':'discover','query':query,'reference_id':None,'discovery':True}


CATALOG_STOP_WORDS = frozenset(
    'algo aqui archivo archivos busca buscame biblioteca cancion canciones catalogo como cual dame de del donde el en '
    'encuentra es esta estan estas este estoy escuchar favorita favoritos identifica identificar la las los '
    'identificame interpreta llama mas mi mis musica nombre opcion opciones otra otras para pista pistas puedes '
    'que quien quiero recomienda recomiendame saber son suena tengo un una uno ver canta autor artista'.split()
)


def catalog_fallback(engine,query,context,discovery,reference,exclude=(),limit=5,*,identify=False,exact=False):
    """Rank active tracks by metadata and hydrate only the selected IDs."""
    phrase = ' '.join(re.findall(r'\w+', normalized(query)))
    words = {word for word in phrase.split() if len(word) > 1} - CATALOG_STOP_WORDS
    with engine.connect() as connection:
        favorite_track = select(favorite.c.track_id).where(favorite.c.track_id == track.c.id).exists()
        names = select(func.string_agg(artist.c.name, ' ')).select_from(
            track_artist.join(artist, artist.c.id == track_artist.c.artist_id)
        ).where(track_artist.c.track_id == track.c.id).correlate(track).scalar_subquery()
        seeds=[UUID(i) for i in [context['current'],*context['recent'],*context['favorites']] if i]
        albums=set(connection.scalars(select(track.c.album_id).where(track.c.id.in_(seeds),track.c.deleted_at.is_(None))))
        statement = select(track.c.id, track.c.title, track.c.album_id, album.c.title, names, favorite_track,
                           media_asset.c.original_name).select_from(
            track.join(album, album.c.id == track.c.album_id).join(media_asset, media_asset.c.id == track.c.audio_asset_id)
        ).where(track.c.deleted_at.is_(None), track.c.id.not_in(exclude))
        if discovery:
            statement = statement.where(~favorite_track)
        if reference:
            statement = statement.where(track.c.id != UUID(reference))
        statement = statement.order_by(track.c.id.in_(seeds).desc(), track.c.created_at.desc(), track.c.id)

        def scored_rows(rows):
            for index, (identity, title, album_id, album_title, artists, fav, original_name) in enumerate(rows):
                title_words = re.findall(r'\w+', normalized(title))
                title_phrase = ' '.join(title_words)
                catalog_words = set(title_words + re.findall(r'\w+', normalized(f'{album_title} {artists or ""}')))
                matches = len(words & catalog_words)
                filename_words = re.findall(r'\w+', normalized(original_name.rsplit('.', 1)[0]))
                filename_phrase = ' '.join(filename_words)
                filename_matches = len(words.intersection(filename_words))
                exact_filename = bool(filename_matches and f' {filename_phrase} ' in f' {phrase} ')
                exact_title = bool(title_phrase and (
                    phrase == title_phrase or (words.intersection(title_words) and f' {title_phrase} ' in f' {phrase} ')
                ))
                if exact and not (exact_title or exact_filename):
                    continue
                same_album = album_id in albums
                if exact_title:
                    reason = 'Coincide con el título guardado.'
                elif exact_filename or (filename_matches and not matches):
                    reason = 'Coincide con el nombre del archivo importado.'
                elif matches:
                    reason = 'Coincide con palabras del título, artista o álbum.'
                elif identify or not (fav or same_album):
                    continue
                else:
                    reason = 'La marcaste como favorita.' if fav else 'Pertenece a un álbum de tus favoritos o reproducciones de esta sesión.'
                score = 1000 * exact_title + 500 * exact_filename + 20 * matches + 10 * filename_matches
                if not identify:
                    score += 5 * fav + 3 * same_album
                yield score, -index, identity, reason

        with connection.execute(statement.execution_options(yield_per=250)) as result:
            ranked = nlargest(limit, scored_rows(result))
        items = metadata.tracks_data(connection, [identity for _, _, identity, _ in ranked])
        reasons = {identity: reason for _, _, identity, reason in ranked}
        return [{'track': item, 'reason': reasons[item['id']], 'evidence': []} for item in items]


def identified_track(engine, identity):
    with engine.connect() as connection:
        return [
            {'track': item, 'reason': 'Es la pista seleccionada en EchoBeats.', 'evidence': []}
            for item in metadata.tracks_data(connection, [identity])
        ]


ORDINAL = re.compile(r'\b(primer[oa]?|segund[oa]|tercer[oa]?|cuart[oa]|quint[oa])\b')
LIBRARY = re.compile(r'\b(?:biblioteca|mi catalogo|mis (?:canciones|pistas|archivos))\b')
PICK = re.compile(
    r'\b(?:cual(?:es)?\b.*\b(?:gusta|gustaria|elegirias|escogerias|recomiendas|prefieres|pondrias)'
    r'|con cual te quedas|elige una|escoge una|pero de las de (?:mi|la) biblioteca)\b'
)
SOUND = re.compile(r'\b(?:como suena[n]?|como es su sonido|describe (?:como suena|el sonido)|que sonido tiene)\b')
SIMILAR = re.compile(r'\b(?:parecid[oa]s?|se parece[n]? a|similar(?:es)?|suena[n]? como|del mismo sonido)\b')
NAMED_SIMILAR = re.compile(
    r'\b(?:(?:parecid[oa]s?|se parece[n]?|similar(?:es)?) a|suena[n]? como) '
    r'(?!esta\b|esa\b|la actual\b|lo que\b|(?:la|el) (?:primera|segunda|tercera|cuarta|quinta)\b)'
)
COMPARE = re.compile(r'\b(?:compara(?:las)?|diferencia(?:s)? entre|en que se diferencian)\b')
ALTERNATIVES = re.compile(r'\b(?:otra(?:s)?(?: opcion(?:es)?)?|mas opciones|diferentes?)\b')
BROAD_RECOMMENDATION = re.compile(
    r'^(?:recomiendame|sugiereme|dame|elige|pon|quiero escuchar) '
    r'(?:(?:algo|mas|otra|una|una cancion|musica|opciones|otras opciones) )?'
    r'(?:de|en) (?:mi|la) (?:biblioteca|catalogo)$'
)
FOLLOWUP_RECOMMENDATION = re.compile(r'^(?:y )?(?:recomiendame|sugiereme|dame)(?: algo| una| una cancion| una recomendacion)$')
WHY_CHOSEN = re.compile(
    r'^(?:y |pero )?(?:por que(?: (?:esa|esta|justo esa|esa cancion|esa pista))?|por que lo dices|en que te basas)$'
    r'|\b(?:por que|que te hizo)\b.*\b(?:eliges|elegiste|elegir|escogiste|prefieres|gusta|recomiendas|recomendaste)\b'
    r'|\b(?:que le ves|que (?:la|lo) hace especial|que destacarias|por que esa y no)\b'
)
MUSIC_DISCUSSION = re.compile(
    r'\b(?:hablame|cuentame|que (?:piensas|opinas|sabes)|conoces|que te parece|'
    r'que (?:estilo|genero|instrumentos)|que (?:la|lo) caracteriza|que transmite|que te llama la atencion)\b'
)


def mentioned_track(engine, query, context, previous, *, allow_implicit):
    """Resolve optional references using active catalog IDs and original card order."""
    phrase = normalized(query)
    matches = catalog_fallback(engine, query, context, False, None, limit=2, identify=True, exact=True)
    if len(matches) == 1:
        return str(matches[0]['track']['id'])
    if len(matches) > 1:
        shown = [str(match['track']['id']) for match in matches if str(match['track']['id']) in context['previous']]
        return shown[0] if len(shown) == 1 else None
    ordinal = ORDINAL.search(phrase)
    if ordinal:
        prefixes = ('primer', 'segund', 'tercer', 'cuart', 'quint')
        position = next(index for index, prefix in enumerate(prefixes) if ordinal[0].startswith(prefix))
        candidate = str(previous[position]) if position < len(previous) else None
        return candidate if candidate in context['previous'] else None
    if allow_implicit and (context['reference'] or context['current']):
        return context['reference'] or context['current']
    if allow_implicit and len(context['previous']) == 1:
        return context['previous'][0]
    return None


def describe_candidates(engine, track_ids, media_root=None):
    identities = [UUID(identity) for identity in track_ids]
    with engine.connect() as connection:
        items = metadata.tracks_data(connection, identities)
        profiles = audio_similarity.acoustic_profiles(connection, identities)
    if media_root is not None and len(identities) == 1 and items and not profiles:
        preview = audio_similarity.preview_acoustic_profile(engine, media_root, identities[0])
        if preview:
            profiles[identities[0]] = preview
    return [
        {'track': item, 'reason': profiles[item['id']]['summary'] if item['id'] in profiles
         else 'Todavía no hay un análisis acústico disponible para esta pista.',
         'evidence': []}
        for item in items
    ], profiles


def catalog_overview(engine, context, *, exclude=(), limit=5):
    recent = [UUID(identity) for identity in context['recent']]
    favorites = [UUID(identity) for identity in context['favorites']]
    playing = UUID(context['current']) if context['current'] else None
    active = (track.c.deleted_at.is_(None), track.c.id.not_in(exclude))
    with engine.connect() as connection:
        count = connection.scalar(select(func.count()).select_from(track).where(*active))
        ids = connection.scalars(
            select(track.c.id).where(*active).order_by(
                track.c.id.in_([playing] if playing else []).desc(),
                track.c.id.in_(recent).desc(), track.c.id.in_(favorites).desc(),
                track.c.created_at.desc(), track.c.id,
            ).limit(limit)
        ).all()
        items = metadata.tracks_data(connection, ids)

    if not items:
        return 'Tu biblioteca está vacía. Cuando importes música, podré consultar los datos de esos archivos.', []
    reply = f'Tu biblioteca tiene {count} {"pista importada" if count == 1 else "pistas importadas"}.'
    if recent:
        reply += ' Las tarjetas indican qué pistas empezaron a reproducirse durante esta sesión.'
    else:
        reply += ' Todavía no has reproducido pistas en esta sesión.'
    reply += ' También puedo buscar por título, artista, álbum o nombre del archivo.'
    return reply, [
        {'track': item, 'reason': (
            'Empezó a reproducirse en esta sesión.' if item['id'] in recent
            else 'Es la pista seleccionada en el reproductor.' if item['id'] == playing
            else 'La marcaste como favorita.' if item['id'] in favorites
            else 'Está importada en tu biblioteca.'
        ), 'evidence': []}
        for item in items
    ]


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


async def respond(engine,settings,provider,messages,current,recent,reference,use_ai,previous=()):
    context=await run_in_threadpool(context_for,engine,current,recent,reference,previous)
    warnings=[];plan=local_plan(messages,context);used_ai=False;suggestions=[]
    latest = normalized(messages[-1]['content'])
    phrase = ' '.join(re.findall(r'\w+', latest))
    switch_force = bool(re.search(SWITCH_FORCE_NAME + r'(?!\s*!?\s*2)', latest))
    alternatives = bool(ALTERNATIVES.search(phrase))
    exclude = previous if alternatives else ()
    explicit_library = bool(LIBRARY.search(phrase))
    external = plan['intent'] == 'discover' and any(
        fragment in latest for fragment in ('fuera de', 'no esten en mi biblioteca', 'no busques en')
    )
    context_summary = {'favorites':len(context['favorites']),'recent':len(context['recent']),'current':context['current']}

    def local_result(reply, matches):
        return {'reply':reply,'mode':'local','provider':None,'recommendations':matches,'suggestions':[],'warnings':[],
                'context':context_summary}

    async def answer_about(action, matches, fallback, **kwargs):
        return await library_dialogue.answer(engine, settings, provider, messages, context, use_ai,
                                             action, matches, fallback, **kwargs)

    if reference and not context['reference']:
        raise metadata.MetadataError('track_not_found','La pista de referencia ya no está en la biblioteca.',404)
    explain = bool(WHY_CHOSEN.search(phrase))
    choose = bool(PICK.search(phrase))
    if not external and (explain or choose) and (previous or explicit_library or context['current'] or reference):
        targets = [i for i in context['previous'] if UUID(i) not in exclude]
        if explain and not targets and not previous:
            targets = [i for i in [context['reference'] or context['current']] if i]
        if targets:
            matches, profiles = await run_in_threadpool(describe_candidates, engine, targets)
        elif previous or explain:
            return local_result('¿A qué canción te refieres? No encuentro la pista de esa elección entre las opciones vigentes.', [])
        else:
            _, matches = await run_in_threadpool(catalog_overview, engine, context, exclude=exclude, limit=10)
            profiles = {}
        return await answer_about('explain' if explain else 'choose', matches,
                                  'No encontré una pista disponible para esa elección.', previews=profiles)
    if not external and (SOUND.search(phrase) or (COMPARE.search(phrase) and len(context['previous']) > 1)):
        compare = bool(COMPARE.search(phrase) and len(context['previous']) > 1)
        if compare:
            targets = context['previous']
        else:
            implicit = bool(re.search(r'\b(?:esta cancion|esta pista|la actual|lo que suena|la que suena|la que escucho)\b', phrase)
                            or re.fullmatch(r'como suena|como suenan|como es su sonido', phrase))
            identity = await run_in_threadpool(mentioned_track, engine, latest, context, previous, allow_implicit=implicit)
            targets = [identity] if identity else []
        if not targets:
            return local_result('Dime el título o el nombre del archivo, o reproduce una pista y pregunta «¿Cómo suena esta canción?».', [])
        matches, profiles = await run_in_threadpool(describe_candidates, engine, targets, settings.media_root)
        reply = ('Estas observaciones salen del análisis local de hasta los primeros 30 segundos. En cada tarjeta indico qué rango de frecuencias predomina.'
                 if profiles else 'Aún no hay un análisis acústico disponible para estas pistas. Su título, artista y álbum sí se pueden consultar.')
        return await answer_about('compare' if compare else 'describe', matches, reply, previews=profiles)

    named_similarity = bool(NAMED_SIMILAR.search(phrase))
    if not external and SIMILAR.search(phrase) and (not plan['reference_id'] or named_similarity):
        identity = await run_in_threadpool(mentioned_track, engine, latest, context, previous,
                                           allow_implicit=bool(re.search(r'\b(?:a esta|como esta|a esa|como esa)\b', phrase)))
        if identity:
            plan = {'intent':'recommend','query':latest,'reference_id':identity,'discovery':'sin favoritos' in phrase}
        elif named_similarity and explicit_library:
            return local_result('No pude identificar la pista de referencia en tu biblioteca. Indica el título o el nombre del archivo para buscar por sonido.', [])
        elif named_similarity and not reference and plan['reference_id']:
            plan = {'intent':'discover','query':latest,'reference_id':None,'discovery':True}
    if not external and alternatives and context['previous'] and plan['intent'] == 'discover':
        plan = {'intent':'recommend','query':plan['query'],'reference_id':None,'discovery':False}
    criterion = audio_similarity.acoustic_criterion(latest) if not external and plan['intent'] in {'recommend', 'discover'} else None
    if criterion:
        matches = await run_in_threadpool(audio_similarity.recommend_by_profile, engine, criterion, exclude,
                                           discovery=plan['discovery'] if explicit_library else 'sin favoritos' in phrase)
        reply = ('Estas pistas son las que más se acercan al rasgo acústico pedido en el análisis local del comienzo.'
                 if matches else 'No encontré pistas con análisis acústico vigente que pueda recomendar para ese criterio.')
        return await answer_about('recommend', matches, reply, discovery='sin favoritos' in phrase)
    if plan['intent'] in {'catalog_overview', 'identify'}:
        if plan['intent'] == 'catalog_overview':
            reply, matches = await run_in_threadpool(catalog_overview, engine, context)
        elif plan['reference_id']:
            matches = await run_in_threadpool(identified_track, engine, UUID(plan['reference_id']))
            reply = 'La pista ya no está disponible en tu biblioteca.'
        else:
            matches = await run_in_threadpool(catalog_fallback, engine, plan['query'], context, False, None, identify=True)
            reply = ('Estas pistas de tu biblioteca coinciden con los datos que diste. Revisa el título, artista y álbum de cada una.'
                     if matches else 'No encontré una pista con esos datos. Dime un título, artista, álbum o nombre del archivo importado.')
        if plan['intent'] == 'identify' and len(matches) == 1:
            doc = matches[0]['track']
            artists = ', '.join(credit['name'] for credit in doc['artists']) or 'artista sin registrar'
            reply = f'En tu biblioteca figura «{doc["title"]}», de {artists}, en el álbum «{doc["album_title"]}».'
        return local_result(reply, matches)
    if BROAD_RECOMMENDATION.fullmatch(phrase) or (context['previous'] and (
        FOLLOWUP_RECOMMENDATION.fullmatch(phrase) or phrase in {'dame otras opciones', 'dame otras', 'dame otra', 'mas opciones', 'otra'}
    )):
        _, matches = await run_in_threadpool(catalog_overview, engine, context, exclude=exclude)
        return await answer_about('recommend', matches, 'Estas son algunas pistas de tu biblioteca que puedes escuchar ahora.'
                                  if matches else 'No encontré más pistas disponibles en tu biblioteca.')
    exclude_games = plan['intent'] not in {'greeting', 'thanks', 'recommend'} and excludes_game_music(messages)
    if not external and not exclude_games and MUSIC_DISCUSSION.search(phrase) and plan['intent'] != 'preferences':
        named = await run_in_threadpool(catalog_fallback, engine, latest, context, False, None, identify=True, exact=True)
        if named:
            return await answer_about('discuss', named, 'Encontré estas pistas en tu biblioteca.')
    if (not external and not exclude_games and context['previous'] and plan['intent'] in {'discuss','clarify','discover'}
            and not re.search(r'\b(?:cambiando de tema|otro tema|en general|fuera de|otro asunto)\b', phrase)):
        matches, profiles = await run_in_threadpool(describe_candidates, engine, context['previous'])
        return await answer_about('conversation', matches, '¿Qué te interesa de las pistas que acabamos de ver?', previews=profiles)

    library_requested = plan['intent'] == 'recommend'
    if use_ai and not exclude_games and not library_requested:
        try:
            if not settings.ai_enabled:raise AIError('ai_disabled')
            if not settings.openai_api_key.get_secret_value().strip():raise AIError('ai_not_configured')
            grounding = {'related_soundtrack': SWITCH_FORCE_REFERENCE} if switch_force else {}
            generated=await provider.conversation_plan({'messages':messages,'library_requested':library_requested,**context,**grounding})
            generated_plan=ConversationPlan.model_validate(generated).model_dump()
            if generated_plan['intent']=='recommend':raise AIError('ai_invalid_response')
            allowed_ids = {t['id'] for t in [*context['tracks'], *context['previous_tracks']]}
            if generated_plan['reference_id'] and generated_plan['reference_id'] not in allowed_ids:raise AIError('ai_invalid_response')
            plan = generated_plan
            used_ai=True
        except (AIError,ValidationError) as error:
            if isinstance(error,AIError) and error.code=='ai_quota':
                warnings.append('OpenAI rechazó la solicitud por cuota. Para descubrir música con IA, revisa el saldo de la cuenta configurada.')
            else:
                warnings.append(f'{error} Seguí en modo local.' if isinstance(error,AIError) else 'La IA devolvió una respuesta no válida. Seguí en modo local.')
    mode='ai' if used_ai else 'local';recommendations=[]
    if exclude_games:
        reply,suggestions=discovery_without_games(messages)
    elif used_ai and plan['intent'] in {'discuss','greeting','preferences','clarify'}:
        reply=plan['reply']
    elif plan['intent']=='greeting':reply='¡Hola! ¿Cómo va todo?'
    elif plan['intent']=='check_in':reply='¡Me alegra que estés bien! Aquí estoy para charlar contigo.'
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
            if plan['reference_id']:
                recommendations=await run_in_threadpool(acoustic_recommendations,engine,plan['reference_id'],exclude,plan['discovery'])
                if not recommendations:
                    warnings.append('La comparación acústica no devolvió candidatos. Las fichas o los datos del catálogo disponibles se mostrarán con su propia razón.')
                    data=await run_in_threadpool(search.similar,engine,settings,UUID(plan['reference_id']),5,None,None,'discovery' if plan['discovery'] else 'favorites')
            else:
                query=plan['query'] or messages[-1]['content']
                preference_mode='discovery' if plan['discovery'] else 'favorites'
                if use_ai and settings.ai_enabled and settings.openai_api_key.get_secret_value().strip():
                    try:
                        data=await search.search(engine,settings,provider,query,'hybrid',5,preferences=preference_mode)
                    except AIError:
                        warnings.append('La búsqueda vectorial no estuvo disponible. Busqué coincidencias por texto en las fichas.')
                if not data or not data['results']:
                    terms = [w for w in re.findall(r'\w+', normalized(query)) if w not in CATALOG_STOP_WORDS]
                    data=await search.search(engine,settings,provider,' '.join(terms) or query,'lexical',5,preferences=preference_mode)
            for item in (data or {}).get('results',[]):
                if item['track']['id'] in exclude:continue
                saved=exploration.recorded(item)
                recommendations.append({'track':item['track'],'reason':'Su ficha guardada contiene estos fragmentos.','evidence':saved['evidence']})
        except (AIError,metadata.MetadataError):
            warnings.append('No pude completar la búsqueda por fichas. Estas opciones usan el catálogo y tus señales explícitas.')
        if not recommendations:
            recommendations=await run_in_threadpool(catalog_fallback,engine,plan['query'],context,plan['discovery'],plan['reference_id'],exclude)
        if recommendations and plan['reference_id'] and any('acústic' in item['reason'] for item in recommendations):
            reply='Estas son las pistas con el perfil acústico más cercano al comienzo de tu referencia. Es una comparación local y orientativa de los primeros 30 segundos.'
        else:
            reply='Estas son las pistas de tu biblioteca con las señales más cercanas. Cada tarjeta indica por qué apareció; el parecido musical es orientativo.' if recommendations else 'En la búsqueda que pediste dentro de tu biblioteca no encontré resultados con señales suficientes. Si quieres, puedo explorar música en general.'
        return await answer_about('recommend', recommendations, reply, warnings=warnings, discovery=plan['discovery'])
    return {'reply':reply,'mode':mode,'provider':'openai' if used_ai else None,'recommendations':recommendations,'suggestions':suggestions,'warnings':warnings,'context':context_summary}
