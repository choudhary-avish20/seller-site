import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, auth, categories, products, uploads, orders, sellers, wishlist, addresses, reviews, coupons, settings as settings_routes
from app.core.config import settings

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations on startup so every deploy is always up to date.
    Safe to call repeatedly — Alembic is idempotent (skips already-applied migrations)."""
    try:
        from alembic import command
        from alembic.config import Config

        # alembic.ini lives in backend/ (one level above app/)
        alembic_cfg_path = Path(__file__).resolve().parents[1] / "alembic.ini"
        alembic_cfg = Config(str(alembic_cfg_path))
        # Override script_location to absolute path so it works regardless of
        # the working directory the process starts from (important on Render).
        alembic_cfg.set_main_option(
            "script_location", str(Path(__file__).resolve().parents[1] / "alembic")
        )
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied successfully.")
    except Exception:
        logger.exception("Alembic migration failed — server will still start, check logs.")


app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)


@app.on_event("startup")
async def startup_event() -> None:
    run_migrations()

is_dev = settings.ENV == "development" or settings.DEBUG
app.add_middleware(
    CORSMiddleware,
    # In dev: wildcard origin is used so allow_credentials must be False (browser enforces this).
    # In prod: explicit origins are listed so credentials (Authorization headers, cookies) are allowed.
    allow_origins=["*"] if is_dev else settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?" if is_dev else None,
    allow_credentials=not is_dev,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(uploads.router, prefix=settings.API_V1_PREFIX)
app.include_router(orders.router, prefix=settings.API_V1_PREFIX)
app.include_router(sellers.router, prefix=settings.API_V1_PREFIX)
app.include_router(wishlist.router, prefix=settings.API_V1_PREFIX)
app.include_router(addresses.router, prefix=settings.API_V1_PREFIX)
app.include_router(reviews.router, prefix=settings.API_V1_PREFIX)
app.include_router(coupons.router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_routes.router, prefix=settings.API_V1_PREFIX)

# Static for uploaded product images
# backend/uploads/products -> /uploads/products/*
uploads_dir = Path(__file__).resolve().parents[1] / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Frontend — plain HTML/CSS/JS (no frameworks) — matches centrumhurt screenshots, replaces Next.js+vanilla
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    # Serve at / (homepage) and keep /vanilla alias for backward compat
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    vanilla_dir = Path(__file__).resolve().parents[2] / "vanilla"
    if vanilla_dir.exists():
        app.mount("/vanilla", StaticFiles(directory=str(vanilla_dir), html=True), name="vanilla")

    @app.get("/")
    def root():
        return {"message": settings.PROJECT_NAME, "status": "running"}