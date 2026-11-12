"""Informe de medios sin modificar archivos: ejecutar con importaciones detenidas."""

import json

from sqlalchemy import select

from app.config import Settings
from app.database import make_database_engine
from app.integrations.storage import MediaStore
from app.models.catalog import media_asset


def audit(engine, store):
    with engine.connect() as connection:
        records = connection.execute(select(media_asset.c.id, media_asset.c.storage_key)).all()
    known = {record.storage_key for record in records}
    missing = []
    for record in records:
        try:
            exists = store.path_for(record.storage_key).is_file()
        except ValueError:
            exists = False
        if not exists:
            missing.append(str(record.id))
    orphans = []
    for folder in ("audio", "images"):
        directory = store.root / folder
        if directory.is_dir() and not directory.is_symlink():
            orphans.extend(f"{folder}/{path.name}" for path in directory.iterdir() if path.is_file() and f"{folder}/{path.name}" not in known)
    staging = store.root / ".staging"
    return {
        "missing_asset_ids": missing, "unreferenced_files": sorted(orphans),
        "staging_files": sorted(path.name for path in staging.glob("*.part")) if not staging.is_symlink() else [],
        "modified_files": 0,
    }


def main():
    settings = Settings()
    engine = make_database_engine(settings)
    if engine is None:
        raise SystemExit("Configura la conexión antes de comprobar medios.")
    try:
        print(json.dumps(audit(engine, MediaStore(settings.media_root)), indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
