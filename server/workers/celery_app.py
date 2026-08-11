from celery import Celery

from server.config import settings

celery_app = Celery(
    "audiobook_reader",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=60 * 60 * 24 # lasts a day
)

celery_app.autodiscover_tasks(["server"])