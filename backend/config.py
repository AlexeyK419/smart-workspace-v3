from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = "postgresql://postgres:12345@localhost:5432/workspace_db"

    # Admin bootstrap
    admin_email: str = "admin@gmail.com"
    admin_password: str = ""

    # RouterAI (OpenAI-compatible)
    routerai_api_key: str = ""
    routerai_base_url: str = "https://routerai.ru/api/v1"
    routerai_model: str = "google/gemma-4-31b-it"
    routerai_embedding_model: str = ""
    routerai_timeout_sec: int = 60
    ai_embeddings_enabled: bool = True

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost,http://127.0.0.1"

    # Uploads
    upload_dir: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin for origin in (item.strip() for item in self.cors_origins.split(",")) if origin]

    @property
    def upload_dir_path(self) -> str:
        path = Path(self.upload_dir)
        if path.is_absolute():
            return str(path)
        return str((Path(__file__).resolve().parent / path).resolve())


settings = Settings()
