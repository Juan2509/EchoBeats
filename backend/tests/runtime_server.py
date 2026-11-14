"""Servidor HTTP efímero exclusivo de P26; nunca acepta la base principal."""
import os
from pathlib import Path
import re
import socket
import uvicorn
from pydantic import SecretStr
from app.config import Settings
from app.main import create_app


def main():
    name = os.environ['P26_DATABASE']
    if not re.fullmatch(r'echobeats_test_[0-9a-f]{32}', name):
        raise RuntimeError('P26 exige una base aislada creada por pytest.')
    settings = Settings(_env_file=None, database_url=SecretStr(''), postgres_db=name,
        media_root=Path(os.environ['P26_MEDIA']), processing_worker_enabled=False,
        ai_enabled=False, openai_api_key=SecretStr(''))
    app = create_app(settings)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        Path(os.environ['P26_PORT_FILE']).write_text(str(listener.getsockname()[1]), encoding='ascii')
        server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))
        server.run(sockets=[listener])


if __name__ == '__main__':
    main()
