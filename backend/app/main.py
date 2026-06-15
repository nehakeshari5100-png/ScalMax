import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import SecurityHeadersMiddleware, DebugModeMiddleware
from services.vision.router import router as vision_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=None,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(DebugModeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

app.include_router(
    vision_router,
    prefix="/api/v1/vision",
    tags=["Vision"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
