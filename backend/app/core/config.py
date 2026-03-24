from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "AI 3D Tumor Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tumor_user:tumor_secret@localhost:5432/tumor_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "./storage"

    # Model paths
    MODEL_WEIGHTS_DIR: str = "./models/weights"
    SEGMENTATION_MODEL_PATH: str = "./models/weights/unet3d_best.pth"
    CLASSIFICATION_MODEL_PATH: str = "./models/weights/classifier_best.pth"
    PREDICTION_MODEL_PATH: str = "./models/weights/lstm_best.pth"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Notifications
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
