import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "wifisense.db").replace("\\", "/")


class Settings:
    PROJECT_NAME: str = "Wi-Fi Sense Focus"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3d162fc8cd92b516f863efbd4cfbd892abf4857b29a8a72")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "0") == "1"
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    BOOTSTRAP_ADMIN_EMAIL: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "")
    BOOTSTRAP_ADMIN_PASSWORD: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", self.ENVIRONMENT)
        self.DATABASE_URL = os.getenv("DATABASE_URL", self.DATABASE_URL)
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY == "b3d162fc8cd92b516f863efbd4cfbd892abf4857b29a8a72":
                raise RuntimeError(
                    "CRITICAL SECURITY SAFEGUARD: Production environment cannot use default or hardcoded SECRET_KEY! "
                    "Configure a cryptographically random SECRET_KEY in the environment."
                )
            if self.DATABASE_URL.startswith("sqlite"):
                raise RuntimeError(
                    "CRITICAL PRODUCTION SAFEGUARD: Production environment cannot run on SQLite file database. "
                    "Configure a production PostgreSQL DATABASE_URL."
                )



settings = Settings()


