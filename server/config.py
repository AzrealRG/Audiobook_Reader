from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    storage_path: str = "./storage"
    google_application_credentials: str = ""

    postgres_user: str
    postgres_password: str
    postgres_db: str

    database_url: str
    sync_database_url: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra="ignore",
    )


settings = Settings()