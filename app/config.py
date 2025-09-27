import os
from decouple import config

class Settings:
    # Environment
    ENVIRONMENT: str = config("ENVIRONMENT", default="dev")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    
    # Database
    DATABASE_URL: str = config("DATABASE_URL", default="postgresql://postgres:password@localhost:5432/mony_db")
    
    # Security
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-change-in-production")
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", default="your-jwt-secret-change-in-production")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    
    # Azure (for production)
    AZURE_STORAGE_CONNECTION_STRING: str = config("AZURE_STORAGE_CONNECTION_STRING", default="")
    AZURE_CONTAINER_NAME: str = config("AZURE_CONTAINER_NAME", default="receipts")

settings = Settings()