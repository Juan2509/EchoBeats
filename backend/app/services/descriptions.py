"""Fichas explícitas, versionadas y trazables; nunca inferidas de títulos."""
import hashlib
import json
from uuid import uuid4
from sqlalchemy import select, func
from app.models.catalog import track_description as description, description_revision
from app.services.metadata import MetadataError, require_track


def token(row):
    return f'"description-{row.id}-{row.version}"'


def find(connection, track_id):
    return connection.execute(select(description).where(description.c.track_id == track_id)).first()


def serialize(row, basis, current_revision):
    value = dict(row._mapping)
    value['can_index'] = bool(row.text.strip())
    value['index_status'] = 'not_indexed'
    value['needs_indexing'] = bool(row.text.strip())
    value['index_notice'] = 'Sin embedding. Una ficha nueva o corregida deberá indexarse cuando se habilite P21.'
    value['input_track_revision'] = basis
    derived = row.source == 'metadata' or any(f['source'] == 'metadata' for f in row.features)
    value['metadata_stale'] = derived and basis != current_revision
    if value['metadata_stale']:
        value['can_index'] = False
        value['needs_indexing'] = False
    return value


def data(connection, track_id):
    current = require_track(connection, track_id)
    row = find(connection, track_id)
    if row is None:
        raise MetadataError('description_missing', 'Esta pista todavía no tiene ficha musical.', 404)
    snapshot = connection.scalar(select(description_revision.c.snapshot).where(description_revision.c.description_id == row.id, description_revision.c.version == row.version))
    return serialize(row, snapshot.get('input_track_revision') if snapshot else None, current.revision), token(row)


def history(connection, track_id, version):
    require_track(connection, track_id)
    row = find(connection, track_id)
    saved = connection.scalar(select(description_revision.c.snapshot).where(description_revision.c.description_id == row.id, description_revision.c.version == version)) if row else None
    if saved is None:
        raise MetadataError('description_version_missing', 'No existe esa versión de la ficha.', 404)
    # Es evidencia histórica, nunca un estado de indexación actual.
    return {**saved, 'historical': True}, f'"description-{row.id}-{version}"'


def save(engine, track_id, values, expected, create_condition):
    with engine.begin() as connection:
        current = require_track(connection, track_id, lock=True)
        row = find(connection, track_id)
        if expected is not None and create_condition is not None:
            raise MetadataError('invalid_precondition', 'Usa una sola condición de creación o actualización.', 422)
        if row is None:
            if create_condition != '*' or expected is not None:
                raise MetadataError('creation_condition_required', 'Para crear la ficha se necesita If-None-Match: *.', 428)
        elif create_condition is not None or expected != token(row):
            if expected is None and create_condition is None:
                raise MetadataError('revision_required', 'Recarga la ficha antes de guardar.', 428)
            raise MetadataError('revision_conflict', 'La ficha cambió en otra pestaña. Conserva tu borrador y recarga antes de guardar.', 412, current_revision=row.version, current_etag=token(row))
        canonical = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if row is not None and row.content_hash == digest:
            return data(connection, track_id)
        updated = {**values, 'content_hash': digest, 'version': row.version + 1 if row else 1}
        if row is None:
            saved = connection.execute(description.insert().values(id=uuid4(), track_id=track_id, **updated).returning(description)).first()
        else:
            saved = connection.execute(description.update().where(description.c.id == row.id).values(**updated, updated_at=func.now()).returning(description)).first()
        snapshot = {key: str(value) if key in {'id', 'track_id'} else value for key, value in dict(saved._mapping).items() if key not in {'created_at', 'updated_at'}}
        snapshot['input_track_revision'] = current.revision
        connection.execute(description_revision.insert().values(description_id=saved.id, version=saved.version, snapshot=snapshot))
        return serialize(saved, current.revision, current.revision), token(saved)
