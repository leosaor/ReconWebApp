from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: a aplicação está de pé."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness: a aplicação consegue falar com Postgres e Redis."""
    checks: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # noqa: BLE001
        checks["database"] = "error"

    try:
        connection = celery_app.broker_connection()
        connection.ensure_connection(max_retries=1)
        connection.release()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        checks["redis"] = "error"

    dependencies_ok = all(value == "ok" for value in checks.values())
    checks["status"] = "ok" if dependencies_ok else "degraded"
    return checks
