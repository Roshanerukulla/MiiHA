from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    database_name: str
    cohere_api_key: str
    secret_key: str = "your-secret-key"

    class Config:
        env_file = ".env"
        env_file_encoding="utf-8"

settings = Settings()
