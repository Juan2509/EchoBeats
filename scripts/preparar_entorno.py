"""Prepara configuración local sin imprimir ni sobrescribir secretos existentes."""

import os
from pathlib import Path
import secrets


ROOT = Path(__file__).resolve().parents[1]


def main():
    destino = ROOT / ".env"
    if destino.exists():
        print("Se conserva el .env existente. Verifica POSTGRES_* según .env.example.")
        return
    contenido = (ROOT / ".env.example").read_text(encoding="utf-8")
    contenido = contenido.replace("POSTGRES_PASSWORD=\n", f"POSTGRES_PASSWORD={secrets.token_hex(32)}\n")
    descriptor = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    print(".env local creado con contraseña aleatoria. Su contenido no se muestra ni se versiona.")


if __name__ == "__main__":
    main()
