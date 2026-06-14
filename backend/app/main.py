from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.middleware import SecurityHeadersMiddleware, DebugModeMiddleware
from app.security import get_current_user, rate_limit
from services.auth.router import router as auth_router
from services.market_data.router import router as market_data_router
from services.market_data.exchange_manager import ExchangeManager
from services.indicators.router import router as indicators_router
from services.liquidity.router import router as liquidity_router
from services.confluence.router import router as confluence_router
from services.calibration.router import router as calibration_router
from services.backtesting.router import router as backtesting_router
from services.vision.router import router as vision_router
from services.decision.router import router as decision_router
from services.signals.router import router as signals_router
from services.integration.router import router as integration_router
from services.papertrading.router import router as papertrading_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    exchange_manager = ExchangeManager.get_instance()
    await exchange_manager.start()
    yield
    await exchange_manager.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)

# Security middleware (order matters — headers first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(DebugModeMiddleware)

# CORS — locked to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

# Auth router (no auth required)
app.include_router(auth_router)

# Protected API routers — require valid JWT + rate limit
app.include_router(
    market_data_router,
    prefix="/api/market",
    tags=["Market Data"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    indicators_router,
    prefix="/api/indicators",
    tags=["Indicators"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    liquidity_router,
    prefix="/api/v1/liquidity",
    tags=["Liquidity"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    confluence_router,
    prefix="/api/v1/confluence",
    tags=["Confluence"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    calibration_router,
    prefix="/api/v1/calibration",
    tags=["Calibration"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    backtesting_router,
    prefix="/api/v1/backtesting",
    tags=["Backtesting"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    vision_router,
    prefix="/api/v1/vision",
    tags=["Vision"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    decision_router,
    prefix="/api/v1/decision",
    tags=["Decision"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    signals_router,
    prefix="/api/v1/signals",
    tags=["Signals"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    integration_router,
    prefix="/api/v1/pipeline",
    tags=["Integration"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)
app.include_router(
    papertrading_router,
    prefix="/api/v1/papertrading",
    tags=["Paper Trading"],
    dependencies=[Depends(get_current_user), Depends(rate_limit)],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}
