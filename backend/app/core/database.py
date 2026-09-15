import os
from sqlmodel import create_engine, Session
from alembic import command
from alembic.config import Config
from app.core.config import BASE_DIR, settings

# For SQLite, connect_args={"check_same_thread": False} is required
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def run_migrations():
    """Apply all pending database migrations up to head via Alembic."""
    ini_path = os.path.join(BASE_DIR, "alembic.ini")
    alembic_cfg = Config(ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(BASE_DIR, "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

def init_db():
    """Authoritative schema management entry point: runs Alembic migrations."""
    run_migrations()

def get_session():
    # Set expire_on_commit=False globally as per project requirements
    with Session(engine, expire_on_commit=False) as session:
        yield session
