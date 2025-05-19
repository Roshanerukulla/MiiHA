from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    database_name: str
    cohere_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
