from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., description="postgresql+psycopg://...")

    JWT_SECRET: str = Field(..., description="JWT signing secret")
    JWT_ALG: str = Field(default="HS256")
    JWT_EXPIRES_MIN: int = Field(default=60)

    ADDRESS_SECRET: str = Field(..., description="HMAC secret for address generation")

    ADMIN_SEED_ENABLED: bool = Field(default=False)
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    # Optional: SMTP if you have OTP already; keep if exists in your project
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    EMAIL_FROM: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()