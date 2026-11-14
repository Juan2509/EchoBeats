"""Indexación versionada. Ningún vector de prueba se inserta en la biblioteca real."""
import asyncio
import json
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.integrations.ai import OpenAIProvider, AIError, checked_text, usage, MESSAGES
from app.models.catalog import track_description as description, track_embedding as embedding, processing_job as job
from app.models.vector import Vector1536
from app.services import descriptions, processing
from app.services.metadata import MetadataError, require_track

INPUT_FORMAT = 'description-v1'


def model_key(settings):
    return f'{OpenAIProvider(settings).model_key}:{INPUT_FORMAT}'


def configured(settings):
    if settings.ai_embedding_dimensions != 1536:
        raise MetadataError('embedding_dimensions_incompatible', 'El esquema requiere 1536 dimensiones. Un cambio de espacio exige migración y reindexación explícitas.', 409)


def input_text(record):
    text = json.dumps({key: record[key] for key in ('text','features','source','source_details')}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    try:
        checked_text(text, 6000)
    except AIError:
        raise MetadataError('description_too_large', 'La ficha supera el presupuesto de 6000 bytes UTF-8 para indexación. Revisa su extensión sin perder las evidencias necesarias.', 422) from None
    return text


def matching(record, row, key):
    return record['can_index'] and record['version'] == row.input_version and record['content_hash'] == row.input_hash and row.model_key == key


def state(connection, track_id, settings, record=None):
    if record is None:
        if descriptions.find(connection, track_id) is None:
            require_track(connection, track_id)
            return {'status':'missing_description','model_key':model_key(settings),'job':None}
        record=descriptions.data(connection,track_id)[0]
    key=model_key(settings)
    found=connection.execute(select(embedding.c.id).where(embedding.c.description_id==record['id'],embedding.c.description_version==record['version'],embedding.c.content_hash==record['content_hash'],embedding.c.model_key==key)).first()
    latest=connection.execute(select(job).where(job.c.track_id==track_id,job.c.operation=='index_description',job.c.input_version==record['version'],job.c.model_key==key)).first()
    old=connection.scalar(select(embedding.c.id).where(embedding.c.description_id==record['id']).limit(1))
    status = ('stale' if record['metadata_stale'] else 'incomplete_description') if not record['can_index'] else 'ready' if found and settings.ai_embedding_dimensions==1536 else latest.status if latest is not None and latest.status!='completed' else 'stale' if old else 'not_indexed'
    return {'status':status,'model_key':key,'description_version':record['version'],'content_hash':record['content_hash'],
        'job':processing.public(latest,record['version']) if latest else None}


def enqueue(engine, track_id, settings):
    configured(settings)
    with engine.begin() as connection:
        require_track(connection,track_id,lock=True)
        record=descriptions.data(connection,track_id)[0]
        if not record['can_index']:
            raise MetadataError('description_not_indexable','Completa o revisa la ficha antes de indexar.',409)
        input_text(record)
        existing=connection.execute(select(job).where(job.c.track_id==track_id,job.c.operation=='index_description',job.c.input_version==record['version'],job.c.model_key==model_key(settings))).first()
        if existing is not None:
            return processing.public(existing,record['version'])
        if not settings.ai_enabled or not settings.openai_api_key.get_secret_value().strip():
            raise MetadataError('ai_unavailable','Habilita el proveedor con créditos disponibles antes de solicitar indexación. No se envió la ficha.',503)
        row=connection.execute(job.insert().values(id=uuid4(),track_id=track_id,operation='index_description',input_version=record['version'],input_hash=record['content_hash'],model_key=model_key(settings)).returning(job)).first()
        return processing.public(row,record['version'])


def retry(engine, job_id, settings):
    configured(settings)
    with engine.begin() as connection:
        previous=processing.require_job(connection,job_id)
        require_track(connection,previous.track_id,lock=True)
        row=processing.require_job(connection,job_id,lock=True)
        record=descriptions.data(connection,row.track_id)[0]
        if not matching(record,row,model_key(settings)):
            raise MetadataError('index_input_changed','La ficha o el espacio vectorial cambió. Solicita una indexación de la entrada actual.',409)
        if row.status not in {'error','stale'} or row.attempts>=3:
            raise MetadataError('job_not_retryable','El trabajo no admite otro intento para esta entrada.',409)
        if not settings.ai_enabled or not settings.openai_api_key.get_secret_value().strip():
            raise MetadataError('ai_unavailable','El proveedor no está habilitado. No se reintentó.',503)
        return processing.public(connection.execute(job.update().where(job.c.id==row.id).values(status='pending',error_code=None,result=None,started_at=None,finished_at=None,updated_at=func.now()).returning(job)).first(),record['version'])


def claim(engine, settings):
    if settings is None or not settings.ai_enabled or not settings.openai_api_key.get_secret_value().strip() or settings.ai_embedding_dimensions!=1536:
        return None
    with engine.begin() as connection:
        candidates=connection.execute(select(job.c.id,job.c.track_id).where(job.c.operation=='index_description',job.c.status=='pending').order_by(job.c.created_at,job.c.id).limit(32)).all()
        for candidate in candidates:
            from app.models.catalog import track
            if connection.execute(select(track.c.id).where(track.c.id==candidate.track_id).with_for_update(skip_locked=True)).first() is None:
                continue
            row=connection.execute(select(job).where(job.c.id==candidate.id,job.c.status=='pending').with_for_update(skip_locked=True)).first()
            if row is None: continue
            record=descriptions.data(connection,row.track_id)[0]
            if not matching(record,row,model_key(settings)):
                connection.execute(job.update().where(job.c.id==row.id).values(status='stale',error_code='index_input_changed',finished_at=func.now(),updated_at=func.now()))
                continue
            return connection.execute(job.update().where(job.c.id==row.id).values(status='processing',attempts=row.attempts+1,started_at=func.now(),error_code=None,finished_at=None,updated_at=func.now()).returning(job)).first()
    return None


def prepare(engine, claimed, settings, provider_factory=OpenAIProvider):
    with engine.connect() as connection:
        record=descriptions.data(connection,claimed.track_id)[0]
        if not matching(record,claimed,model_key(settings)):
            raise AIError('ai_input_invalid')
        text=input_text(record)
    # La conexión/transacción terminó antes de la llamada externa.
    result = asyncio.run(provider_factory(settings).embed(text))
    if result.get('model_key') != OpenAIProvider(settings).model_key:
        raise AIError('ai_invalid_response')
    return {**result, 'model_key': model_key(settings)}


def finish(engine, claimed, settings, result=None, error_code=None):
    with engine.begin() as connection:
        require_track(connection,claimed.track_id,lock=True)
        row=processing.require_job(connection,claimed.id,lock=True)
        if row.status!='processing' or row.attempts!=claimed.attempts: return False
        record=descriptions.data(connection,row.track_id)[0]
        stale=not matching(record,row,model_key(settings))
        status='stale' if stale else 'error' if error_code else 'completed'
        if status=='completed':
            if result is None or result.get('model_key')!=row.model_key:
                raise AIError('ai_invalid_response')
            try:
                Vector1536().bind_processor(None)(result['vector'])
            except (ValueError,KeyError,TypeError):
                raise AIError('ai_invalid_response') from None
            safe_usage = usage(result.get('usage'))
            connection.execute(insert(embedding).values(id=uuid4(),description_id=record['id'],description_version=record['version'],content_hash=record['content_hash'],model_key=row.model_key,input_format=INPUT_FORMAT,embedding=result['vector'],usage=safe_usage).on_conflict_do_nothing(index_elements=['description_id','description_version','model_key']))
        safe_error='index_input_changed' if stale else error_code if error_code in MESSAGES else 'processing_failed' if error_code else None
        connection.execute(job.update().where(job.c.id==row.id).values(status=status,error_code=safe_error,
            result={'description_id':str(record['id']),'description_version':record['version'],'model_key':row.model_key,'input_hash':row.input_hash} if status=='completed' else None,
            finished_at=func.now(),updated_at=func.now()))
        return True
