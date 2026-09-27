import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "ABYSSEYE Sonar Evidence Engine"
    API_V1_STR: str = "/api/v1"
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = os.path.join("data", "raw")
    PROCESSED_DIR: str = os.path.join("data", "processed")
    MODELS_DIR: str = "models"
    CORS_ORIGINS: list = ["*"]

settings = Settings()
