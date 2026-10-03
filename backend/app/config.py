from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kinetix API"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8787
    client_origin: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = "postgresql://kinetix:kinetix@localhost:5432/kinetix"
    redis_url: str = "redis://localhost:6379/0"
    amadeus_client_id: str | None = None
    amadeus_client_secret: str | None = None
    amadeus_host: str = "https://test.api.amadeus.com"
    mapbox_token: str | None = None
    tomorrow_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    pinecone_api_key: str | None = None
    pinecone_index: str = "kinetix-vibes"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.client_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
