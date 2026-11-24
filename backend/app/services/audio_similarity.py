"""Index managed audio and retrieve candidates in the matching pgvector space."""

from sqlalchemy import Float, and_, select
from sqlalchemy.dialects.postgresql import insert

from app.integrations.audio_embedding import AudioEmbeddingError, MODEL_KEY, embed_file
from app.integrations.storage import MediaStore
from app.models.catalog import audio_index_attempt as attempt
from app.models.catalog import media_asset, track, track_audio_embedding as audio_index
from app.services.metadata import MetadataError, require_track, tracks_data


CURRENT_AUDIO = and_(
    audio_index.c.track_id == track.c.id,
    audio_index.c.model_key == MODEL_KEY,
    audio_index.c.audio_asset_id == track.c.audio_asset_id,
    audio_index.c.content_sha256 == track.c.content_sha256,
)


CURRENT_ATTEMPT = and_(
    attempt.c.track_id == track.c.id,
    attempt.c.model_key == MODEL_KEY,
    attempt.c.content_sha256 == track.c.content_sha256,
)


def pending_tracks(connection, after=None, *, automatic=False):
    query = (
        select(track.c.id, track.c.audio_asset_id, track.c.content_sha256, media_asset.c.storage_key)
        .select_from(track.join(media_asset, media_asset.c.id == track.c.audio_asset_id)
                     .outerjoin(audio_index, CURRENT_AUDIO))
        .where(track.c.deleted_at.is_(None), audio_index.c.track_id.is_(None))
        .order_by(track.c.id).limit(100)
    )
    if automatic:
        query = query.outerjoin(attempt, CURRENT_ATTEMPT).where(attempt.c.track_id.is_(None)).limit(1)
    if after is not None:
        query = query.where(track.c.id > after)
    return connection.execute(query).all()


def index_audio(engine, store, candidate):
    vector = embed_file(store.path_for(candidate.storage_key))
    with engine.begin() as connection:
        current = connection.execute(
            select(track.c.id).where(
                track.c.id == candidate.id,
                track.c.deleted_at.is_(None),
                track.c.audio_asset_id == candidate.audio_asset_id,
                track.c.content_sha256 == candidate.content_sha256,
            ).with_for_update()
        ).scalar_one_or_none()
        if current is None:
            return False
        statement = insert(audio_index).values(
            track_id=current, model_key=MODEL_KEY, audio_asset_id=candidate.audio_asset_id,
            content_sha256=candidate.content_sha256, embedding=vector,
        )
        upsert = statement.on_conflict_do_update(
            index_elements=[audio_index.c.track_id, audio_index.c.model_key],
            set_={
                "audio_asset_id": statement.excluded.audio_asset_id,
                "content_sha256": statement.excluded.content_sha256,
                "embedding": statement.excluded.embedding,
                "indexed_at": statement.excluded.indexed_at,
            },
            where=(audio_index.c.audio_asset_id != statement.excluded.audio_asset_id)
                  | (audio_index.c.content_sha256 != statement.excluded.content_sha256),
        ).returning(audio_index.c.track_id)
        return connection.scalar(upsert) is not None


def attempt_key(candidate):
    return dict(track_id=candidate.id, model_key=MODEL_KEY, content_sha256=candidate.content_sha256)


def attempt_for(candidate):
    return and_(*(attempt.c[key] == value for key, value in attempt_key(candidate).items()))


def recover_audio_attempts(engine):
    with engine.begin() as connection:
        connection.execute(attempt.delete().where(attempt.c.status == "processing"))


def process_next_audio(engine, media_root):
    with engine.begin() as connection:
        candidates = pending_tracks(connection, automatic=True)
        if not candidates:
            return False
        candidate = candidates[0]
        connection.execute(attempt.insert().values(**attempt_key(candidate), status="processing"))
    try:
        index_audio(engine, MediaStore(media_root), candidate)
    except AudioEmbeddingError as exc:
        error = str(exc)
    except (OSError, ValueError):
        error = "No se pudo leer el archivo de audio gestionado."
    else:
        error = None
    with engine.begin() as connection:
        statement = attempt.delete() if error is None else attempt.update().values(status="failed", error=error)
        connection.execute(statement.where(attempt_for(candidate), attempt.c.status == "processing"))
    return True


def audio_index_status(engine, track_id, worker_enabled):
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection, connection.begin():
        require_track(connection, track_id)
        state = connection.execute(
            select(audio_index.c.track_id.label("indexed"), attempt.c.status, attempt.c.error)
            .select_from(track.outerjoin(audio_index, CURRENT_AUDIO).outerjoin(attempt, CURRENT_ATTEMPT))
            .where(track.c.id == track_id)
        ).one()
        status = "ready" if state.indexed is not None else state.status or "pending"
        return {
            "status": status,
            "worker_enabled": worker_enabled,
            "error": state.error if status == "failed" else None,
        }


def retry_audio_index(engine, track_id, worker_enabled):
    if not worker_enabled:
        raise MetadataError("audio_worker_disabled", "El análisis de audio en segundo plano está desactivado.", 409)
    with engine.begin() as connection:
        current = require_track(connection, track_id)
        # An uncertain or repeated POST cannot clear an active attempt.
        connection.execute(attempt.delete().where(attempt_for(current), attempt.c.status == "failed"))
    return audio_index_status(engine, track_id, worker_enabled)


def nearest_audio(connection, track_id, limit):
    """Return ranked local candidates, or None when the reference is not indexed."""
    reference = connection.scalar(
        select(audio_index.c.embedding).select_from(track.join(audio_index, CURRENT_AUDIO))
        .where(track.c.id == track_id)
    )
    if reference is None:
        return None
    distance = audio_index.c.embedding.op("<=>", return_type=Float)(reference)
    return connection.execute(
        select(track.c.id, distance.label("distance"))
        .select_from(track.join(audio_index, CURRENT_AUDIO))
        .where(track.c.deleted_at.is_(None), track.c.id != track_id)
        .order_by(distance, track.c.id)
        .limit(limit)
    ).all()


def similar_audio(engine, track_id, limit):
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection, connection.begin():
        require_track(connection, track_id)
        candidates = nearest_audio(connection, track_id, limit)
        if candidates is None:
            raise MetadataError(
                "audio_not_indexed", "Esta canción aún no está lista para buscar por sonido.", 409,
            )
        documents = tracks_data(connection, [candidate.id for candidate in candidates])
        return {
            "model_key": MODEL_KEY,
            "results": [
                {"track": document, "distance": float(candidate.distance)}
                for document, candidate in zip(documents, candidates, strict=True)
            ],
        }
