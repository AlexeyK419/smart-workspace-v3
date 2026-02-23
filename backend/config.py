from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = "postgresql://postgres:12345@localhost:5432/workspace_db"


    gigachat_client_id: str = "0c181eec-4297-42c9-b737-46ddcaa54fc0"
    gigachat_auth_key: str = "MGMxODFlZWMtNDI5Ny00MmM5LWI3MzctNDZkZGNhYTU0ZmMwOmQ1N2Y1NWNlLWEyN2YtNGEyZC1iZjY5LTU4ZTNjMjQ0MWNjMw=="
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat"

    # GigaChat endpoints
    gigachat_auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    gigachat_api_url: str = "https://gigachat.devices.sberbank.ru/api/v1"

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
