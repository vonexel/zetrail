from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix = "ZETRAIL_", env_file = ".env", extra = "ignore")


    token: SecretStr = SecretStr("")
    token_file: Path | None = None
    data_dir: Path = Path(".data")
    host: str = "127.0.0.1"
    port: int = Field(default = 8765, ge = 1, le = 65535)

    clickhouse_host: str = "127.0.0.1"
    clickhouse_port: int = 8123
    clickhouse_user: str = "zetrail"
    clickhouse_password: SecretStr = SecretStr("")
    clickhouse_password_file: Path | None = None
    clickhouse_database: str = Field(default = "zetrail", pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    embedding_provider: Literal["ollama", "sentence_transformers"] = "ollama"
    embedding_model: str = "nomic-embed-text"
    embedding_revision: str = "local"
    ollama_url: str = "https://127.0.0.1:11434"
    llm_model: str = ""
    reranker_model: str = ""

    max_upload_mb: int = Field(default = 64, ge = 1, le = 256)
    max_pages: int = Field(default = 2000, ge = 1)
    max_text_chars: int = Field(default = 20000000, ge = 1000)
    queue_limit: int = Field(default = 100, ge = 1, le = 10000)
    allowed_hosts: list[str] = ["127.0.0.1", "localhost", "[testserver]", "[::1]"]

    @model_validator(mode = "after")
    def local_policy(self) -> "Settings":
        url = urlparse(self.ollama_url)
        if url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1", "host.docker.internal", "ollama"}:
            raise ValueError("Model runtime must be local; remote providers are not enabled")
        if url.username or url.password or url.query or url.fragment:
            raise ValueError("Invalid model runtime URL")
        if self.token_file:
            self.token = SecretStr(self.token_file.read_text().strip())
        if self.clickhouse_password_file:
            self.clickhouse_password = SecretStr(self.clickhouse_password_file.read_text().strip())
        return self

    def require_token(self) -> str:
        value = self.token.get_secret_value()
        if len(value) < 32:
            raise ValueError("Set ZETRAIL_TOKEN to a random token with at least 32 characters (zetrail init)")
        return value