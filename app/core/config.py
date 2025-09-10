import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
load_dotenv(override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce Microservice"
    ENV: str = "dev"

    # PostgreSQL (individual components)
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ecomdb"
    POSTGRES_USER: str = "ecomuser"
    POSTGRES_PASSWORD: str = "ecompass"

    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # MongoDB
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "ecomdb"

    # Auth
    JWT_SECRET: str = "changeme"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS S3
    AWS_S3_BUCKET: str = "ecom-bucket-1"
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str 
    AWS_SECRET_ACCESS_KEY: str

    # Email (SMTP or AWS SES)
    EMAIL_FROM: str
    EMAIL_BACKEND: str = "smtp" # or "aws_ses"
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    HTTPS_ONLY: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"



settings = Settings()
