"""Composiciones por álbum: reemplazo atómico y control optimista de revisión."""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.models.catalog import WALL_DEFAULT_BACKGROUND, media_asset, wall, wall_element
from app.services.metadata import MetadataError, check_revision, etag, require_album


def create_initial(connection, album_id):
    """Se llama dentro de la misma transacción que crea el álbum."""
    connection.execute(wall.insert().values(album_id=album_id))


def require_wall(connection, album_id, lock=False):
    require_album(connection, album_id)
    statement = select(wall).where(wall.c.album_id == album_id)
    row = connection.execute(statement.with_for_update() if lock else statement).first()
    if row is None:
        raise MetadataError('wall_missing', 'Falta el muro de este álbum. Comprueba las migraciones.', 503)
    return row


def data(connection, album_id):
    row = require_wall(connection, album_id)
    fields = ('id', 'asset_id', 'kind', 'cx', 'cy', 'width', 'height', 'rotation_deg', 'z_index')
    elements = [{**{key: getattr(element, key) for key in fields},
                 'content_url': f'/api/v1/assets/{element.asset_id}/content',
                 'static_preview_url': f'/api/v1/assets/{element.static_preview_id}/content' if element.static_preview_id else None}
                for element in connection.execute(select(wall_element, media_asset.c.static_preview_id).join(media_asset, media_asset.c.id == wall_element.c.asset_id).where(wall_element.c.wall_id == row.id)
                                                  .order_by(wall_element.c.z_index, wall_element.c.id))]
    return {**{key: getattr(row, key) for key in ('id', 'album_id', 'schema_version', 'revision', 'background_color', 'updated_at')},
            'elements': elements}, etag('wall', row)


def validate_assets(connection, elements, store):
    ids = {element['asset_id'] for element in elements}
    assets = {asset.id: asset for asset in connection.execute(select(media_asset).where(media_asset.c.id.in_(ids)))}
    for element in elements:
        asset = assets.get(element['asset_id'])
        if asset is None:
            raise MetadataError('invalid_wall_asset', 'Uno de los recursos visuales no existe.')
        compatible = (asset.kind == 'gif' and asset.mime_type == 'image/gif' and asset.frame_count is not None and 1 <= asset.frame_count <= 200
                      if element['kind'] == 'gif' else asset.kind in {'cover', 'image'} and asset.mime_type in {'image/png', 'image/jpeg'})
        if (not compatible or not asset.width_px or not asset.height_px or
                max(asset.width_px, asset.height_px) > 4096 or asset.width_px * asset.height_px > 16_000_000 or asset.byte_size > 5 * 1024 * 1024):
            raise MetadataError('invalid_wall_asset', 'El recurso no es compatible con este elemento o supera los límites visuales.')
        try:
            path = store.path_for(asset.storage_key)
            available = path.is_file() and path.stat().st_size == asset.byte_size
        except (ValueError, OSError):
            available = False
        if not available:
            raise MetadataError('wall_asset_missing', 'No se encuentra uno de los archivos visuales. El muro anterior se conserva.')


def replace(engine, store, album_id, values, expected):
    try:
        with engine.begin() as connection:
            row = require_wall(connection, album_id, lock=True)
            check_revision('wall', row, expected)
            elements = values['elements']
            ids = [element['id'] for element in elements]
            foreign = connection.scalar(select(wall_element.c.id).where(wall_element.c.id.in_(ids), wall_element.c.wall_id != row.id).limit(1))
            if foreign is not None:
                raise MetadataError('wall_element_conflict', 'Un elemento pertenece al muro de otro álbum. Usa un ID nuevo.')
            validate_assets(connection, elements, store)
            connection.execute(wall_element.delete().where(wall_element.c.wall_id == row.id))
            if elements:
                connection.execute(wall_element.insert(), [dict(element, wall_id=row.id) for element in sorted(elements, key=lambda value: str(value["id"]))])
            connection.execute(wall.update().where(wall.c.id == row.id).values(
                background_color=values['background_color'], schema_version=values['schema_version'],
                revision=row.revision + 1, updated_at=func.now()))
            return data(connection, album_id)
    except IntegrityError as exc:
        # Dos muros distintos pueden intentar publicar el mismo ID nuevo a la vez.
        if getattr(getattr(exc.orig, 'diag', None), 'constraint_name', '') == 'pk_wall_element':
            raise MetadataError('wall_element_conflict', 'El ID de un elemento ya está en uso. Recarga el muro antes de guardar.') from None
        raise


def reset(engine, store, album_id, expected):
    return replace(engine, store, album_id, {'schema_version': 1, 'background_color': WALL_DEFAULT_BACKGROUND, 'elements': []}, expected)
