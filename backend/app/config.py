"""Configuración del servidor; no se transmite al navegador."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    allowed_hosts: str = "localhost,127.0.0.1,backend"
    allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )
    media_root: Path = Path(__file__).resolve().parents[2] / "data" / "media"
    database_url: SecretStr = SecretStr("")
    postgres_host: str = "127.0.0.1"
    postgres_port: int = Field(default=5433, ge=1, le=65535)
    postgres_db: str = "echobeats"
    postgres_user: str = "echobeats"
    postgres_password: SecretStr = SecretStr("")

    def hosts(self) -> list[str]:
        return [value.strip() for value in self.allowed_hosts.split(",") if value.strip()]

    def origins(self) -> set[str]:
        return {value.strip() for value in self.allowed_origins.split(",") if value.strip()}
