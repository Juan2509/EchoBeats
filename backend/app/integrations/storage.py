"""Archivos gestionados: nombres generados, sin acceso por rutas del cliente."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
from uuid import uuid4


class FileTooLarge(Exception):
    pass


class MediaStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def path_for(self, key: str) -> Path:
        if not re.fullmatch(r"(audio|images)/[0-9a-f]{32}\.(mp3|wav|flac|ogg|opus|png|jpg|jpeg|gif)", key):
            raise ValueError("Referencia de recurso no válida.")
        path = self.root / key
        if not path.resolve().is_relative_to(self.root) or path.is_symlink():
            raise ValueError("Referencia de recurso fuera del almacenamiento.")
        return path

    @contextmanager
    def stage(self, stream, max_bytes: int):
        directory = self.root / ".staging"
        directory.mkdir(parents=True, exist_ok=True)
        if directory.is_symlink():
            raise ValueError("Directorio temporal no válido.")
        path = directory / f"{uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        try:
            with path.open("xb") as destination:
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise FileTooLarge
                    destination.write(chunk)
                    digest.update(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            yield path, digest.hexdigest(), size
        finally:
            path.unlink(missing_ok=True)

    def publish(self, staged: Path, key: str) -> Path:
        destination = self.path_for(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Mismo filesystem; link falla si ya existe, sin sobrescribir archivos.
        os.link(staged, destination)
        staged.unlink()
        return destination
