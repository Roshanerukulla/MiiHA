from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    database_name: str
    cohere_api_key: str
    jwt_secret_key: str

    class Config:
        env_file = ".env"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v in ("your-secret-key", "") or len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be a strong secret of at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("cohere_api_key")
    @classmethod
    def validate_cohere_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("COHERE_API_KEY must be set in the environment")
        return v


settings = Settings()
