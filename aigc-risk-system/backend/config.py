import os
from pathlib import Path


class Config:
    """系统配置。开发时默认使用 SQLite，部署时可切换为 MySQL。"""

    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent

    SECRET_KEY = os.getenv("SECRET_KEY", "graduation-design-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///aigc_risk.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    SAMPLE_DATA_PATH = os.getenv(
        "SAMPLE_DATA_PATH",
        str(PROJECT_ROOT / "sample_data" / "aigc_usage_data.csv"),
    )
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))
    JSON_AS_ASCII = False
