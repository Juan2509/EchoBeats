"""Cola durable P18. Solo prepara metadatos existentes: no analiza sonido ni usa IA."""
from uuid import uuid4
from sqlalchemy import select, func
from app.models.catalog import processing_job as job, track, artist, track_artist
from app.services.metadata import MetadataError, require_track

MAX_ATTEMPTS = 3
MESSAGES = {
    'interrupted': 'El servidor se detuvo durante el trabajo. Puedes reintentarlo.',
    'input_changed': 'Los metadatos cambiaron. Inicia una preparación con la versión actual.',
    'processing_failed': 'No se pudo preparar la información. Puedes reintentar sin importar de nuevo.',
}
from app.integrations.ai import MESSAGES as AI_MESSAGES
MESSAGES.update(AI_MESSAGES)
MESSAGES['index_input_changed'] = 'La ficha o el modelo cambió; solicita la indexación actual.'


def public(row, current_version=None):
    value = dict(row._mapping)
    value['error_message'] = MESSAGES.get(row.error_code)
    value['status_url'] = f'/api/v1/jobs/{row.id}'
    if current_version is not None:
        value['is_current'] = row.input_version == current_version
    return value


def require_job(connection, job_id, lock=False):
    statement = select(job).where(job.c.id == job_id)
    row = connection.execute(statement.with_for_update() if lock else statement).first()
    if row is None:
        raise MetadataError('job_not_found', 'No existe ese trabajo.', 404)
    return row


def enqueue(engine, track_id):
    with engine.begin() as connection:
        current = require_track(connection, track_id, lock=True)
        existing = connection.execute(select(job).where(job.c.track_id == track_id, job.c.operation == 'prepare_metadata', job.c.input_version == current.revision)).first()
        if existing is not None:
            return public(existing, current.revision)
        row = connection.execute(job.insert().values(id=uuid4(), track_id=track_id, operation='prepare_metadata', input_version=current.revision).returning(job)).first()
        return public(row, current.revision)


def retry(engine, job_id):
    with engine.begin() as connection:
        previous = require_job(connection, job_id)
        current = require_track(connection, previous.track_id, lock=True)
        row = require_job(connection, job_id, lock=True)
        if row.status not in {'error', 'stale'}:
            raise MetadataError('job_not_retryable', 'Solo se reintentan trabajos fallidos o desactualizados.', 409)
        if current.revision != row.input_version:
            raise MetadataError('input_changed', MESSAGES['input_changed'], 409)
        if row.attempts >= MAX_ATTEMPTS:
            raise MetadataError('attempt_limit', 'Se alcanzaron tres intentos para esta versión. Revisa el problema antes de continuar.', 409)
        return public(connection.execute(job.update().where(job.c.id == job_id).values(status='pending', error_code=None, result=None, started_at=None, finished_at=None, updated_at=func.now()).returning(job)).first(), current.revision)


def claim(engine):
    """Adquisición atómica; orden de bloqueos pista → trabajo, igual que retry."""
    with engine.begin() as connection:
        candidates = connection.execute(select(job.c.id, job.c.track_id).where(job.c.status == 'pending', job.c.operation == 'prepare_metadata').order_by(job.c.created_at, job.c.id).limit(32)).all()
        for candidate in candidates:
            current = connection.execute(select(track).where(track.c.id == candidate.track_id).with_for_update(skip_locked=True)).first()
            if current is None:
                continue
            row = connection.execute(select(job).where(job.c.id == candidate.id, job.c.status == 'pending').with_for_update(skip_locked=True)).first()
            if row is None:
                continue
            if row.input_version != current.revision:
                connection.execute(job.update().where(job.c.id == row.id).values(status='stale', error_code='input_changed', finished_at=func.now(), updated_at=func.now()))
                continue
            return connection.execute(job.update().where(job.c.id == row.id).values(status='processing', attempts=row.attempts + 1, started_at=func.now(), finished_at=None, error_code=None, result=None, updated_at=func.now()).returning(job)).first()
    return None


def prepare(engine, claimed):
    with engine.connect() as connection:
        current = require_track(connection, claimed.track_id)
        names = list(connection.scalars(select(artist.c.name).join(track_artist, artist.c.id == track_artist.c.artist_id).where(track_artist.c.track_id == current.id).order_by(track_artist.c.position)))
        return {'source': 'metadata', 'track_revision': current.revision, 'title': current.title,
                'artist_names': names, 'duration_ms': current.duration_ms,
                'metadata_sources': current.metadata_sources,
                'content_sha256': current.content_sha256,
                'notice': 'Resumen de metadatos existentes; sin análisis acústico, ficha musical ni embedding.'}


def finish(engine, claimed, result=None, failed=False):
    """CAS por estado/intento: un ejecutor antiguo nunca publica sobre un reintento."""
    with engine.begin() as connection:
        current = require_track(connection, claimed.track_id, lock=True)
        row = require_job(connection, claimed.id, lock=True)
        if row.status != 'processing' or row.attempts != claimed.attempts:
            return False
        stale = current.revision != claimed.input_version or (result is not None and result.get('track_revision') != claimed.input_version)
        state = 'stale' if stale else 'error' if failed else 'completed'
        connection.execute(job.update().where(job.c.id == row.id).values(status=state,
            result=result if state == 'completed' else None,
            error_code='input_changed' if stale else 'processing_failed' if failed else None,
            finished_at=func.now(), updated_at=func.now()))
        return True


def recover(engine):
    """Solo el trabajador dueño del bloqueo global debe llamar a esta recuperación."""
    with engine.begin() as connection:
        return connection.execute(job.update().where(job.c.status == 'processing').values(status='error', error_code='interrupted', result=None, finished_at=func.now(), updated_at=func.now())).rowcount
