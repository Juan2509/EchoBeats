"""Respaldar y restaurar PostgreSQL local usando los clientes de su contenedor.

Restaurar siempre crea una base nueva: nunca limpia ni reemplaza una existente.
No imprime contraseñas ni incorpora valores de .env a comandos del host.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "exec", "-T", "postgres"]


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(arguments, **kwargs):
    result = subprocess.run(COMPOSE + arguments, cwd=ROOT, stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        raise SystemExit("Falló la operación de PostgreSQL. Verifica servicio, permisos y espacio; no se reemplazó ninguna base existente.")
    return result


def query(sql):
    return run([
        "sh", "-c", 'exec psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -v ON_ERROR_STOP=1 -c "$1"',
        "query", sql,
    ], stdout=subprocess.PIPE).stdout.decode().strip()


def backup():
    destination = ROOT / "backups"
    destination.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = destination / f"echobeats_{stamp}_{uuid4().hex[:8]}.dump"
    partial = path.with_suffix(".dump.part")
    try:
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            run(["sh", "-c", 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl'], stdout=stream)
        metadata = {
            "format": "pg_dump_custom", "file": path.name, "sha256": checksum(partial),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "postgresql": query("SHOW server_version"),
            "pgvector": query("SELECT extversion FROM pg_extension WHERE extname = 'vector'"),
            "migration": query("SELECT version_num FROM public.alembic_version ORDER BY version_num"),
            "includes_media": False,
        }
        partial.rename(path)
        path.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    finally:
        if partial.exists():
            partial.unlink()
    print(f"Respaldo de BD creado: {path.relative_to(ROOT)}")
    print("Conserva también MEDIA_ROOT; el dump no contiene audios ni imágenes.")


def restore(path, database):
    if not re.fullmatch(r"echobeats_restore_[a-z0-9_]{1,40}", database):
        raise SystemExit("La base nueva debe llamarse echobeats_restore_<nombre>, usando minúsculas, números o _.")
    path = path.resolve()
    if not path.is_file():
        raise SystemExit("No existe el archivo de respaldo.")
    manifest = path.with_suffix(".json")
    if not manifest.is_file():
        raise SystemExit("Falta el manifiesto JSON del respaldo.")
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if metadata.get("sha256") != checksum(path):
        raise SystemExit("El hash del respaldo no coincide. No se creó ninguna base.")
    if query("SELECT current_database()") == database:
        raise SystemExit("No se puede restaurar sobre la base activa.")
    # Nombre validado antes de interpolarlo como literal SQL.
    if query(f"SELECT 1 FROM pg_database WHERE datname = '{database}'"):
        raise SystemExit("La base destino ya existe; elige un nombre nuevo. No se modificó.")
    run(["sh", "-c", 'exec createdb -U "$POSTGRES_USER" -- "$1"', "create", database])
    with path.open("rb") as stream:
        run([
            "sh", "-c", 'exec pg_restore -U "$POSTGRES_USER" --dbname="$1" --no-owner --no-acl --exit-on-error',
            "restore", database,
        ], stdin=stream)
    print(f"Respaldo restaurado en la base nueva {database}. La base activa no cambió.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("respaldar")
    restore_parser = commands.add_parser("restaurar")
    restore_parser.add_argument("archivo", type=Path)
    restore_parser.add_argument("--base", required=True)
    options = parser.parse_args()
    if options.operation == "respaldar":
        backup()
    else:
        restore(options.archivo, options.base)


if __name__ == "__main__":
    main()
