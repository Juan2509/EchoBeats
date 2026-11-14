"""Selección de citas, alternativa registrada y verificación posterior a generación."""
import json
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError
from app.integrations.ai import AIError, Explanation, usage
from app.models.catalog import track
from app.services import search, metadata, preferences


def recorded(item):
    desc=item['description']
    quote=desc['text'][:300]
    return {**item,'explanation_source':'recorded','explanation':f'Descripción guardada: «{quote}»',
        'evidence':[{'source_id':str(desc['id']),'version':desc['version'],'field':'text','quote':quote}]}


def sources_for(query,items):
    sources=[]
    for item in items[:5]:
        desc=item['description']
        text=desc['text'].encode('utf-8')[:1600].decode('utf-8',errors='ignore')
        source={'source_id':str(desc['id']),'version':desc['version'],'text':text}
        candidate=sources+[source]
        if len(json.dumps({'query':query,'sources':candidate},ensure_ascii=False).encode('utf-8'))<=12000:
            sources=candidate
    return sources


def current_results(engine,settings,data,album_id,playlist_id):
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection,connection.begin():
        if data.get('reference_track_id'):
            reference=connection.execute(search.eligible(settings,[track.c.id==data['reference_track_id']])).first()
            if reference is None or reference.version!=data['reference_description_version'] or reference.content_hash!=data['reference_content_hash']:
                raise metadata.MetadataError('reference_changed','La referencia cambió mientras se preparaban las citas. Vuelve a consultar su versión actual.',409)
        preference_mode=data.get('preferences',{}).get('mode','off')
        filters=search.track_filters(connection,album_id,playlist_id,exclude=data.get('reference_track_id'),preferences=preference_mode)
        ids=[item['track']['id'] for item in data['results']]
        rows=connection.execute(search.eligible(settings,[*filters,track.c.id.in_(ids)])).all()
        valid={(str(row.track_id),str(row.description_id),row.version,row.content_hash) for row in rows}
        results=[]
        for item in data['results']:
            desc=item['description']
            key=(str(item['track']['id']),str(desc['id']),desc['version'],desc['content_hash'])
            if key in valid:
                results.append({**item,'track':metadata.track_data(connection,item['track']['id'])[0]})
        return preferences.apply(connection,results,preference_mode)


async def explain(engine,settings,provider,data,requested,album_id=None,playlist_id=None):
    data={**data,'results':[recorded(item) for item in data['results']],
        'warnings':list(data['warnings']),'explanations_requested':requested,
        'explanation_policy':'literal_quotes_only','generation_usage':None}
    if not requested or not data['results']:return data
    query=data['query'] or 'Selecciona evidencia registrada para describir posibles pistas similares, sin afirmar coincidencia demostrada.'
    sources=sources_for(query,data['results'])
    allowed={(s['source_id'],s['version']):s['text'] for s in sources}
    try:
        if not settings.ai_enabled:raise AIError('ai_disabled')
        if not settings.openai_api_key.get_secret_value().strip():raise AIError('ai_not_configured')
        if not sources:raise AIError('ai_input_invalid')
        generated=await provider.generate(query,sources)
        output=Explanation.model_validate(generated['output'])
        model=generated.get('model')
        if not isinstance(model,str) or not (model==settings.ai_generation_model or model.startswith(settings.ai_generation_model+'-')):
            raise AIError('ai_invalid_response')
        consumption=usage(generated.get('usage'))
        grouped={};seen=set()
        for citation in output.evidence:
            key=(citation.source_id,citation.version)
            if key not in allowed or citation.quote not in allowed[key] or (key,citation.quote) in seen:
                raise AIError('ai_invalid_response')
            seen.add((key,citation.quote))
            grouped.setdefault(key,[]).append({'source_id':citation.source_id,'version':citation.version,'field':'text','quote':citation.quote})
        # La prosa libre del modelo no se publica: solo citas comprobadas.
        for item in data['results']:
            key=(str(item['description']['id']),item['description']['version'])
            if key in grouped:
                item.update(explanation_source='generated_selection',evidence=grouped[key],
                    explanation='Fragmentos de la ficha: '+' · '.join(f'«{c["quote"]}»' for c in grouped[key]))
        data['generation_usage']=consumption
        data['generation_model']=model
        data['warnings'].append('La IA seleccionó citas; no se muestra su prosa libre ni se garantiza pertinencia por esa selección. Los demás resultados conservan su descripción registrada.')
    except (AIError,ValidationError,KeyError,TypeError,ValueError):
        data['warnings'].append('No se pudo validar la selección de citas con IA. Se conservan las descripciones guardadas; no se reintentó ni se inventaron explicaciones.')
    refreshed,details=await run_in_threadpool(current_results,engine,settings,data,album_id,playlist_id)
    if data.get('preferences')!=details:
        data['warnings'].append('El orden y los favoritos se comprobaron de nuevo después de la generación; la comparación corresponde a los candidatos que siguen vigentes.')
    data['preferences']=details
    if len(refreshed)!=len(data['results']):
        data['warnings'].append('Se excluyeron resultados que cambiaron o dejaron de pertenecer al filtro durante la generación.')
    data['results']=refreshed
    data['status']='ok' if refreshed else 'no_matches'
    return data
