from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "reconwebapp",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.tasks.sample"],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_max_tasks_per_child=100,
    result_expires=86400,
    timezone="UTC",
)
