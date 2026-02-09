from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "cleair_gateway",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["gateway"])
