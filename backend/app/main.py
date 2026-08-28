from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, auth, seller, categories, category_requests, products, uploads, orders
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)

is_dev = settings.ENV == "development" or settings.DEBUG
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_dev else settings.CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?" if is_dev else None,
    allow_credentials=False if is_dev else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(seller.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(category_requests.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(uploads.router, prefix=settings.API_V1_PREFIX)
app.include_router(orders.router, prefix=settings.API_V1_PREFIX)

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