from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    storage_path: str = "./storage"
    google_application_credentials: str = ""

    class Config:
        env_file = ".env"


settings = Settings()