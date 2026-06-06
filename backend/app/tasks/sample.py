from app.core.celery_app import celery_app


@celery_app.task(name="sample.ping")
def ping() -> str:
    """Task de fumaça para validar broker + worker na Fase 0."""
    return "pong"
