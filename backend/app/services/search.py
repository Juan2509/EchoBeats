"""Recuperación exacta, filtros y fusión de rangos; no genera explicaciones."""
from sqlalchemy import select, func, cast, Text, Float, bindparam, or_, not_
from sqlalchemy.dialects.postgresql import JSONPATH
from starlette.concurrency import run_in_threadpool
from app.models.catalog import track, album, artist, track_artist, playlist, playlist_track
from app.models.catalog import track_description as description, description_revision as revision, track_embedding as embedding
from app.models.vector import Vector1536
from app.integrations.ai import OpenAIProvider, AIError
from app.services import indexing, metadata

WINDOW = 100
RRF_K = 60


def track_filters(connection, album_id, playlist_id, exclude=None):
    conditions=[]
    if album_id is not None:
        metadata.require_album(connection,album_id)
        conditions.append(track.c.album_id==album_id)
    if playlist_id is not None:
        if connection.scalar(select(playlist.c.id).where(playlist.c.id==playlist_id)) is None:
            raise metadata.MetadataError('playlist_not_found','No existe esa playlist.',404)
        conditions.append(track.c.id.in_(select(playlist_track.c.track_id).where(playlist_track.c.playlist_id==playlist_id)))
    if exclude is not None: conditions.append(track.c.id!=exclude)
    return conditions


def eligible(settings, conditions=()):
    derived=or_(description.c.source=='metadata',description.c.features.contains([{'source':'metadata'}]))
    basis=revision.c.snapshot['input_track_revision'].astext
    return select(track.c.id.label('track_id'),description.c.id.label('description_id'),description.c.version,
        description.c.content_hash,description.c.text,description.c.features,description.c.source,description.c.source_details,
        embedding.c.id.label('embedding_id')).select_from(track.join(description,description.c.track_id==track.c.id)
        .join(revision,(revision.c.description_id==description.c.id)&(revision.c.version==description.c.version))
        .join(embedding,(embedding.c.description_id==description.c.id)&(embedding.c.description_version==description.c.version)&(embedding.c.content_hash==description.c.content_hash)))\
        .where(embedding.c.model_key==indexing.model_key(settings),embedding.c.input_format==indexing.INPUT_FORMAT,
               func.length(func.trim(description.c.text))>0,or_(not_(derived),basis==cast(track.c.revision,Text)),*conditions)


def envelope(settings, query, mode, limit, status, reason=None, **extra):
    return {'query':query,'mode':mode,'limit':limit,'status':status,'reason':reason,
        'model_key':indexing.model_key(settings),'results':[],
        'distance_limit':settings.search_max_cosine_distance,
        'relevance':'candidates_only','warnings':['Ranking de candidatos; la pertinencia y el umbral aún requieren evaluación con P17. Los scores no son porcentajes de confianza.'],**extra}


def preflight(engine, settings, query, mode, limit, album_id, playlist_id):
    indexing.configured(settings)
    with engine.connect() as connection:
        filters=track_filters(connection,album_id,playlist_id)
        if not connection.scalar(select(func.count()).select_from(track)):
            return envelope(settings,query,mode,limit,'no_library')
        if not connection.scalar(select(func.count()).select_from(track).where(*filters)):
            return envelope(settings,query,mode,limit,'no_matches','empty_filter')
        if not connection.scalar(select(func.count()).select_from(eligible(settings,filters).subquery())):
            return envelope(settings,query,mode,limit,'no_indexed_tracks')
    return None


def lexical_score(query):
    names=select(func.string_agg(artist.c.name,' ')).select_from(artist.join(track_artist,artist.c.id==track_artist.c.artist_id)).where(track_artist.c.track_id==track.c.id).correlate(track).scalar_subquery()
    collection=select(album.c.title).where(album.c.id==track.c.album_id).correlate(track).scalar_subquery()
    values=cast(func.jsonb_path_query_array(description.c.features,cast('$[*].value',JSONPATH)),Text)
    document=func.concat_ws(' ',track.c.title,collection,names,description.c.text,values)
    return func.ts_rank_cd(func.to_tsvector('simple',document),func.plainto_tsquery('simple',query))


def ranked(connection, settings, conditions, query, mode, vector, limit):
    base=eligible(settings,conditions)
    distance=embedding.c.embedding.op('<=>',return_type=Float)(bindparam('query_vector',type_=Vector1536())) if vector is not None else None
    parameters={'query_vector':vector} if vector is not None else {}
    if distance is not None and settings.search_max_cosine_distance is not None:
        base=base.where(distance<=settings.search_max_cosine_distance)
    candidates={}
    if mode in {'semantic','hybrid','reference'}:
        rows=connection.execute(base.add_columns(distance.label('distance')).order_by(distance,track.c.id).limit(WINDOW),parameters).all()
        for rank,row in enumerate(rows,1):candidates[row.track_id]={'row':row,'semantic_rank':rank,'lexical_rank':None,'distance':float(row.distance)}
    if mode in {'lexical','hybrid'}:
        score=lexical_score(query)
        statement=base.add_columns(score.label('lexical_score'))
        if distance is not None:statement=statement.add_columns(distance.label('distance'))
        rows=connection.execute(statement.where(score>0).order_by(score.desc(),track.c.id).limit(WINDOW),parameters).all()
        for rank,row in enumerate(rows,1):
            if row.track_id not in candidates:candidates[row.track_id]={'row':row,'semantic_rank':None,'lexical_rank':None,'distance':float(row.distance) if distance is not None else None}
            candidates[row.track_id]['lexical_rank']=rank
    for item in candidates.values():
        item['score']=sum(1/(RRF_K+item[key]) for key in ('semantic_rank','lexical_rank') if item[key] is not None)
    if mode in {'semantic','reference'}:
        ordered=sorted(candidates.values(),key=lambda c:(c['distance'],str(c['row'].track_id)))
    else:
        ordered=sorted(candidates.values(),key=lambda c:(-c['score'],c['distance'] if c['distance'] is not None else 3,str(c['row'].track_id)))
    results=[]
    for item in ordered[:limit]:
        row=item['row']
        results.append({'track':metadata.track_data(connection,row.track_id)[0],
            'description':{'id':row.description_id,'version':row.version,'content_hash':row.content_hash,'text':row.text,'features':row.features,'source':row.source,'source_details':row.source_details},
            'distance':item['distance'],'fusion_score':item['score'] if mode=='hybrid' else None,
            'semantic_rank':item['semantic_rank'],'lexical_rank':item['lexical_rank'],
            'evidence':[{'source_id':str(row.description_id),'version':row.version,'field':'text','quote':row.text[:300]}],
            'explanation_source':'recorded'})
    return results


def retrieve(engine,settings,query,mode,limit,album_id,playlist_id,vector):
    # Nueva instantánea después del proveedor: excluye fichas que cambiaron en vuelo.
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection,connection.begin():
        filters=track_filters(connection,album_id,playlist_id)
        results=ranked(connection,settings,filters,query,mode,vector,limit)
        return envelope(settings,query,mode,limit,'ok' if results else 'no_matches',results=results)


async def search(engine,settings,provider,query,mode,limit,album_id=None,playlist_id=None):
    empty=await run_in_threadpool(preflight,engine,settings,query,mode,limit,album_id,playlist_id)
    if empty is not None:return empty
    vector=None;consumption=None
    if mode!='lexical':
        if not settings.ai_enabled:raise AIError('ai_disabled')
        if not settings.openai_api_key.get_secret_value().strip():raise AIError('ai_not_configured')
        result=await provider.embed(query)
        if result.get('model_key')!=OpenAIProvider(settings).model_key:raise AIError('ai_invalid_response')
        try:Vector1536().bind_processor(None)(result['vector'])
        except (KeyError,ValueError,TypeError,OverflowError):raise AIError('ai_invalid_response') from None
        vector=result['vector'];consumption=result.get('usage')
    value=await run_in_threadpool(retrieve,engine,settings,query,mode,limit,album_id,playlist_id,vector)
    value['query_usage']=consumption
    return value


def similar(engine,settings,track_id,limit,album_id=None,playlist_id=None):
    indexing.configured(settings)
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection,connection.begin():
        metadata.require_track(connection,track_id)
        reference=connection.execute(eligible(settings,[track.c.id==track_id]).add_columns(embedding.c.embedding)).first()
        if reference is None:raise metadata.MetadataError('reference_not_indexed','La pista de referencia necesita una ficha y un vector vigentes del modelo activo.',409)
        filters=track_filters(connection,album_id,playlist_id,exclude=track_id)
        results=ranked(connection,settings,filters,None,'reference',reference.embedding,limit)
        return envelope(settings,None,'reference',limit,'ok' if results else 'no_matches',reference_track_id=track_id,query_usage=None,results=results)
