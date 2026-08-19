import os

class Settings:
    PROJECT_NAME: str = "Wi-Fi Sense Focus"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wifisense.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3d162fc8cd92b516f863efbd4cfbd892abf4857b29a8a72") # Dev default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours

settings = Settings()
