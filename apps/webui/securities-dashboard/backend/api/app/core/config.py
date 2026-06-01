"""Application configuration using pydantic-settings"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    app_name: str = "证券看板 API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]

    # Data Provider Settings
    tushare_token: str
    tushare_enabled: bool = True
    akshare_enabled: bool = True  # 作为备用

    # Database Settings
    database_url: str = "postgresql+asyncpg://securities_user:securities_pass@localhost:5432/securities_db"
    database_echo: bool = False

    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 60  # 缓存过期时间（秒）

    # WebSocket Settings
    ws_heartbeat_interval: int = 30  # 心跳间隔（秒）

    # Market Data Settings
    default_timeframe: str = "daily"  # 默认K线周期
    supported_timeframes: list[str] = ["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"]

    # Rate Limiting
    rate_limit_per_minute: int = 100

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Backtest Settings (future)
    backtest_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
