"""Conversación acotada: plan opcional de IA, recuperación real y razones comprobables."""
import re
import unicodedata
from uuid import UUID
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.integrations.ai import AIError,ConversationPlan
from pydantic import ValidationError
from app.models.catalog import track,favorite,track_description
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

def local_plan(messages,context):
    text=messages[-1]['content'].strip();plain=normalized(text)
    if plain in {'hola','buenas','hey','buenos dias','buenas tardes'}:return {'intent':'greeting','query':'','reference_id':None,'discovery':False}
    if any(p in plain for p in ['mis gustos','que me gusta','que sabes de mi']):return {'intent':'preferences','query':'','reference_id':None,'discovery':False}
    prior=[m['content'] for m in messages[:-1] if m['role']=='user']
    query=(' '.join([prior[-1],text]) if prior and any(p in plain for p in ['mas ','menos ','otra','pero ','tambien']) else text)[-700:]
    ref=context['reference'] or (context['current'] if any(p in plain for p in ['como esta','lo que escucho','parecid','esta cancion']) else None)
    if not ref and context['recent'] and 'lo que escucho' in plain:ref=context['recent'][0]
    return {'intent':'recommend','query':query,'reference_id':ref,'discovery':any(p in plain for p in ['descubrir','diferente','sin favoritos','algo nuevo'])}

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
            reason='Coincide con palabras del título, artista o álbum.' if matches else 'La marcaste como favorita.' if fav else 'Pertenece a un álbum de tus favoritos o reproducciones de esta sesión.' if same else 'Está en tu biblioteca; todavía no tengo una señal musical suficiente para asegurar que encaje.'
            ranked.append((matches*20+int(fav)*5+int(same)*3,-index,{'track':item,'reason':reason,'evidence':[]}))
        ranked.sort(key=lambda row:(row[0],row[1]),reverse=True)
        return [row[2] for row in ranked[:limit]],len(candidates)>=500

async def respond(engine,settings,provider,messages,current,recent,reference,use_ai,previous=()):
    context=await run_in_threadpool(context_for,engine,current,recent,reference)
    warnings=[];plan=local_plan(messages,context);used_ai=False
    if reference and not context['reference']:
        raise metadata.MetadataError('track_not_found','La pista de referencia ya no está en la biblioteca.',404)
    if use_ai:
        try:
            if not settings.ai_enabled:raise AIError('ai_disabled')
            if not settings.openai_api_key.get_secret_value().strip():raise AIError('ai_not_configured')
            generated=await provider.conversation_plan({'messages':messages,**context})
            plan=ConversationPlan.model_validate(generated).model_dump()
            if plan['reference_id'] and plan['reference_id'] not in {t['id'] for t in context['tracks']}:raise AIError('ai_invalid_response')
            used_ai=True
        except (AIError,ValidationError):
            plan=local_plan(messages,context)
            warnings.append('No se pudo usar la IA. Continúo con la alternativa local, sin repetir la llamada.')
    mode='ai' if used_ai else 'local';recommendations=[]
    exclude=previous if any(word in normalized(messages[-1]['content']) for word in ['otras','otra opcion','mas opciones','diferentes','diferente']) else ()
    if plan['intent']=='greeting':reply='Hola. Cuéntame qué te apetece escuchar: un ánimo, una actividad o algo parecido a la canción actual.'
    elif plan['intent']=='preferences':reply=f"Ahora puedo tomar como referencia {len(context['favorites'])} favoritos y {len(context['recent'])} reproducciones recientes de esta sesión. No tengo un historial completo ni conozco tus gustos fuera de EchoBeats."
    elif plan['intent']=='clarify':reply='Cuéntame qué te apetece escuchar o qué quieres cambiar de las recomendaciones anteriores.'
    else:
        data=None
        try:
            if plan['reference_id']:data=await run_in_threadpool(search.similar,engine,settings,UUID(plan['reference_id']),5,None,None,'discovery' if plan['discovery'] else 'favorites')
            else:data=await search.search(engine,settings,provider,plan['query'] or messages[-1]['content'],'hybrid' if used_ai else 'lexical',5,preferences='discovery' if plan['discovery'] else 'favorites')
            for item in (data or {}).get('results',[]):
                if item['track']['id'] in exclude:continue
                saved=exploration.recorded(item)
                recommendations.append({'track':item['track'],'reason':'Su ficha guardada contiene estos fragmentos.','evidence':saved['evidence']})
        except (AIError,metadata.MetadataError):
            warnings.append('No pude completar la búsqueda por fichas. Estas opciones usan el catálogo y tus señales explícitas.')
        if not recommendations:
            recommendations,truncated=await run_in_threadpool(catalog_fallback,engine,plan['query'],context,plan['discovery'],plan['reference_id'],exclude)
            if truncated:warnings.append('La alternativa local examinó las 500 pistas añadidas más recientemente.')
        reply='Te propongo estas canciones de tu biblioteca. Puedes decirme qué cambiar o marcar un corazón para orientar próximas recomendaciones.' if recommendations else 'No encontré pistas disponibles con estas condiciones. Puedes añadir música en Biblioteca o pedirme otra cosa.'
    return {'reply':reply,'mode':mode,'recommendations':recommendations,'warnings':warnings,'context':{'favorites':len(context['favorites']),'recent':len(context['recent']),'current':context['current']}}
