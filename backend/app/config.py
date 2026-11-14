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
    import_max_files: int = Field(default=20, ge=1, le=20)
    import_max_file_bytes: int = Field(default=50 * 1024 * 1024, ge=1)
    import_max_request_bytes: int = Field(default=200 * 1024 * 1024, ge=1)
    processing_worker_enabled: bool = True
    ai_enabled: bool = False
    openai_api_key: SecretStr = SecretStr('')
    ai_embedding_model: str = Field(default='text-embedding-3-small', pattern=r'^text-embedding-3-small$')
    ai_embedding_dimensions: int = Field(default=1536, ge=1, le=1536)
    ai_generation_model: str = Field(default='gpt-6-luna', pattern=r'^gpt-6-luna$')
    ai_timeout_seconds: float = Field(default=20, ge=1, le=60)
    ai_rate_limit_retries: int = Field(default=0, ge=0, le=1)
    search_max_cosine_distance: float | None = Field(default=None, ge=0, le=2, allow_inf_nan=False)

    def hosts(self) -> list[str]:
        return [value.strip() for value in self.allowed_hosts.split(",") if value.strip()]

    def origins(self) -> set[str]:
        return {value.strip() for value in self.allowed_origins.split(",") if value.strip()}
