"""Backfill the acoustic index from the current catalog without modifying media."""

import argparse
import shutil

from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.database import database_readiness, make_database_engine
from app.integrations.audio_embedding import AudioEmbeddingError
from app.integrations.storage import MediaStore
from app.services.audio_similarity import index_audio, pending_tracks


def main() -> int:
    parser = argparse.ArgumentParser(description="Indexar el audio importado en pgvector.")
    parser.parse_args()
    if not shutil.which("ffmpeg"):
        parser.exit(2, "FFmpeg no está instalado.\n")
    settings = Settings()
    engine = make_database_engine(settings)
    if engine is None:
        parser.exit(2, "Configura PostgreSQL antes de indexar.\n")
    store = MediaStore(settings.media_root)
    cursor = None
    indexed = failed = 0
    try:
        if set(database_readiness(engine).values()) != {"ok"}:
            parser.exit(2, "PostgreSQL, pgvector y las migraciones deben estar listos.\n")
        while True:
            with engine.connect() as connection:
                candidates = pending_tracks(connection, cursor)
            if not candidates:
                break
            for candidate in candidates:
                try:
                    indexed += index_audio(engine, store, candidate)
                except (AudioEmbeddingError, ValueError) as exc:
                    failed += 1
                    print(f"{candidate.id}: {exc}")
            cursor = candidates[-1].id
    except SQLAlchemyError:
        parser.exit(2, "Se interrumpió la indexación por un error de base de datos.\n")
    finally:
        engine.dispose()
    print(f"Vectores nuevos: {indexed}. Pistas con error: {failed}.")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
