import os


class Settings:
    PROJECT_NAME: str = "Wi-Fi Sense Focus"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wifisense.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "0") == "1"
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

    def __init__(self):
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


settings = Settings()
