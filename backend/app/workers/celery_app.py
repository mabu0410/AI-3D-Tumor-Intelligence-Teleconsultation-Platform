from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tumor_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.segmentation_tasks",
        "app.workers.tasks.reconstruction_tasks",
        "app.workers.tasks.feature_tasks",
        "app.workers.tasks.classification_tasks",
        "app.workers.tasks.prediction_tasks",
        "app.workers.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.segmentation_tasks.*": {"queue": "ai_heavy"},
        "app.workers.tasks.reconstruction_tasks.*": {"queue": "ai_heavy"},
        "app.workers.tasks.classification_tasks.*": {"queue": "ai_heavy"},
        "app.workers.tasks.prediction_tasks.*": {"queue": "ai_heavy"},
        "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    beat_schedule={},
)
