from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth, health, projects, scans, users
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import SessionLocal
from app.services.auth_service import ensure_bootstrap_admin


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(projects.router)
    app.include_router(scans.router)

    @app.on_event("startup")
    def bootstrap_admin() -> None:
        db = SessionLocal()
        try:
            ensure_bootstrap_admin(db)
        finally:
            db.close()

    return app


app = create_app()
