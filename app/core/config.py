import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file, allowing them to be overridden
load_dotenv(override=True)

class Settings(BaseSettings):
    """
    Manages application-wide settings, loading from environment variables.
    """
    PROJECT_NAME: str = "FastAPI_Cloud_Microservice"
    ENV: str = "dev"

    # --- PostgreSQL Settings ---
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ecomdb"
    POSTGRES_USER: str = "ecomuser"
    POSTGRES_PASSWORD: str = "ecompass"
    
    # These are constructed by the validator below
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_SYNC: Optional[str] = None
    
    # --- MongoDB Settings ---
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "ecomdb"

    # --- Test Database Settings ---
    # Read from env vars (set in docker-compose.yml), default to 'localhost' for local runs
    TEST_POSTGRES_HOST: str = "localhost"
    TEST_MONGO_HOST: str = "localhost"
    
    # These are constructed by the validator below
    TEST_DATABASE_URL: Optional[str] = None
    TEST_MONGO_URI: Optional[str] = None

    # --- Authentication Settings ---
    JWT_SECRET: str = "supersecret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- AWS S3 Settings ---
    AWS_S3_BUCKET: str = "my-ecom-bucket-1"
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    # --- Email Settings ---
    EMAIL_FROM: str
    EMAIL_BACKEND: str = "smtp"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # --- HTTPS Settings ---
    HTTPS_ONLY: bool = False
    
    # --- CORS Settings ---
    CORS_ORIGINS: List[str] = ["*"]

    @model_validator(mode='after')
    def assemble_db_urls(self) -> 'Settings':
        """
        Constructs full database URLs from their components after all other
        settings have been loaded from the environment.
        """
        # For async application connection
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        # For sync connection (used by Alembic)
        if not self.DATABASE_URL_SYNC:
            self.DATABASE_URL_SYNC = (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        # For async test connection
        if not self.TEST_DATABASE_URL:
            self.TEST_DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.TEST_POSTGRES_HOST}:{self.POSTGRES_PORT}/ecomdb_test"
            )
        # For mongo test connection
        if not self.TEST_MONGO_URI:
            self.TEST_MONGO_URI = f"mongodb://{self.TEST_MONGO_HOST}:27017"
        return self

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

