from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Scalpex AI"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    jwt_secret: str = "change-me-to-a-secure-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: List[str] = ["http://localhost:4200"]
    rate_limit_max: int = 60
    rate_limit_window: int = 60
    max_request_size_mb: int = 10
    admin_password: str = "admin"

    # OpenRouter
    openrouter_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Market data
    supported_symbols: List[str] = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"
    ]
    supported_timeframes: List[str] = [
        "1m", "3m", "5m", "15m", "1h", "4h"
    ]
    default_timeframe: str = "5m"
    candle_limit: int = 500

    # WebSocket
    ws_reconnect_delay: float = 1.0
    ws_max_reconnect_delay: float = 60.0
    ws_ping_interval: int = 20
    ws_ping_timeout: int = 10

    # Cache
    cache_ttl_seconds: int = 300
    max_cache_entries: int = 10000

    # Exchanges
    binance_ws_base: str = "wss://stream.binance.com:9443/ws"
    binance_rest_base: str = "https://api.binance.com"
    bybit_ws_base: str = "wss://stream.bybit.com/v5/public/linear"
    bybit_rest_base: str = "https://api.bybit.com"
    hyperliquid_ws_base: str = "wss://api.hyperliquid.xyz/ws"
    hyperliquid_rest_base: str = "https://api.hyperliquid.xyz"

    class Config:
        env_file = ".env"
        env_prefix = "SCALPEX_"


settings = Settings()
