import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "wifisense.db").replace("\\", "/")


class Settings:
    PROJECT_NAME: str = "Wi-Fi Sense Focus"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_SQLITE_PATH}"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3d162fc8cd92b516f863efbd4cfbd892abf4857b29a8a72")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "1") == "1"
    # "full" keeps the complete demo data set (needed by the test scripts). "minimal" keeps one user per role.
    SEED_PROFILE: str = os.getenv("SEED_PROFILE", "full").strip().lower()
    # When set, every seeded demo account gets this password instead of its well-known one.
    SEED_PASSWORD: str = os.getenv("SEED_PASSWORD", "")
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    BOOTSTRAP_ADMIN_EMAIL: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "")
    BOOTSTRAP_ADMIN_PASSWORD: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    # Raw CSI retention. raw_csi_telemetry is by far the largest table (about 4.8 GB a day at 90 packets/s), so it is a rolling
    # window: packets already analysed are deleted after RAW_CSI_RETENTION_HOURS, and the oldest analysed packets go first when
    # the table passes RAW_CSI_MAX_ROWS. Detection results, alerts and audit history are never touched. 0 disables a limit.
    # The fall model was trained on a public dataset (WiFall), not in your rooms. On live hardware it is OFF by default: in a busy
    # room it flags constantly, and a false "possible fall" is worse than none. Presence/movement is what live hardware shows.
    # Set LIVE_FALL_DETECTION=1 only for experiments; dataset replay is unaffected.
    LIVE_FALL_DETECTION: bool = False
    RAW_CSI_RETENTION_HOURS: float = 24.0
    RAW_CSI_MAX_ROWS: int = 300000
    RAW_CSI_PRUNE_INTERVAL_SECONDS: int = 600

    # SMTP Configuration for Alert Notifications
    SMTP_HOST: str = os.getenv("SMTP_HOST", "127.0.0.1")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))  # Default to MailHog/Mailpit for local dev
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "alerts@wifisense.com")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Payments. Only the SANDBOX provider exists: it simulates a payment provider, no real money moves and no card or
    # payment details are ever collected or stored. The price below is a placeholder for the sandbox, not a business decision.
    PAYMENTS_MODE: str = os.getenv("PAYMENTS_MODE", "sandbox").lower()
    PAYMENT_WEBHOOK_SECRET: str = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
    CARE_MONTHLY_PRICE_MINOR: int = int(os.getenv("CARE_MONTHLY_PRICE_MINOR", "49900"))   # 499.00
    CARE_MONTHLY_CURRENCY: str = os.getenv("CARE_MONTHLY_CURRENCY", "INR")
    SUBSCRIPTION_PERIOD_DAYS: int = int(os.getenv("SUBSCRIPTION_PERIOD_DAYS", "30"))
    SUBSCRIPTION_GRACE_DAYS: int = int(os.getenv("SUBSCRIPTION_GRACE_DAYS", "3"))
    WEBHOOK_TOLERANCE_SECONDS: int = int(os.getenv("WEBHOOK_TOLERANCE_SECONDS", "300"))
    PAYMENTS_SANDBOX_SIMULATOR_ENABLED: bool = True

    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", self.ENVIRONMENT)
        self.DATABASE_URL = os.getenv("DATABASE_URL") or self.DATABASE_URL
        # Some hosts hand out "postgres://", which SQLAlchemy no longer accepts.
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = "postgresql://" + self.DATABASE_URL[len("postgres://"):]
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)
        if not self.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        self.PAYMENTS_MODE = os.getenv("PAYMENTS_MODE", self.PAYMENTS_MODE).lower()
        if self.PAYMENTS_MODE != "sandbox":
            raise RuntimeError("PAYMENTS_MODE must be 'sandbox': no real payment provider is implemented.")
        sim_env = os.getenv("PAYMENTS_SANDBOX_SIMULATOR_ENABLED")
        if sim_env is not None:
            self.PAYMENTS_SANDBOX_SIMULATOR_ENABLED = sim_env.strip().lower() in ("1", "true", "yes", "on")
        else:
            self.PAYMENTS_SANDBOX_SIMULATOR_ENABLED = (self.ENVIRONMENT.lower() != "production")
        self.PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
        if not self.PAYMENT_WEBHOOK_SECRET:
            # Sandbox only: a random per-process secret, never written anywhere. External callers (tests, a future real
            # provider) must set PAYMENT_WEBHOOK_SECRET so that they can sign.
            if self.ENVIRONMENT.lower() == "production":
                raise RuntimeError("PAYMENT_WEBHOOK_SECRET is required in production.")
            self.PAYMENT_WEBHOOK_SECRET = secrets.token_urlsafe(32)
        self.LIVE_FALL_DETECTION = os.getenv("LIVE_FALL_DETECTION", "0").strip().lower() in ("1", "true", "yes", "on")
        self.RAW_CSI_RETENTION_HOURS = float(os.getenv("RAW_CSI_RETENTION_HOURS", self.RAW_CSI_RETENTION_HOURS))
        self.RAW_CSI_MAX_ROWS = int(os.getenv("RAW_CSI_MAX_ROWS", self.RAW_CSI_MAX_ROWS))
        self.RAW_CSI_PRUNE_INTERVAL_SECONDS = int(os.getenv("RAW_CSI_PRUNE_INTERVAL_SECONDS", self.RAW_CSI_PRUNE_INTERVAL_SECONDS))
        # Demo data is on by default for development and off by default in production (an explicit opt-in there).
        self.SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "0" if self.ENVIRONMENT.lower() == "production" else "1") == "1"
        self.SEED_PROFILE = os.getenv("SEED_PROFILE", "full").strip().lower()
        self.SEED_PASSWORD = os.getenv("SEED_PASSWORD", "")
        if self.SEED_PROFILE not in ("full", "minimal"):
            raise RuntimeError("SEED_PROFILE must be 'full' or 'minimal'.")
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
        if self.ENVIRONMENT.lower() == "production" and self.SEED_DEMO_DATA and len(self.SEED_PASSWORD) < 12:
            raise RuntimeError(
                "Refusing to seed demo accounts in production with their well-known passwords. "
                "Set SEED_PASSWORD (12+ characters, known only to you) or set SEED_DEMO_DATA=0."
            )


settings = Settings()


