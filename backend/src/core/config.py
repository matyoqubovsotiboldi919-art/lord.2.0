from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "sotiboldi22"

    INITIAL_USER_BALANCE: float = 1000.0

    # comma separated or *
    ALLOWED_ORIGINS: str = "*"

    # Frontend folder (relative to backend/src)
    FRONTEND_DIR: str = "../../frontend"

    class Config:
        env_file = ".env"


settings = Settings()