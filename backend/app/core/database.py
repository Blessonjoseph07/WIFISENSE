from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

# For SQLite, connect_args={"check_same_thread": False} is required
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

from sqlalchemy import text

def init_db():
    SQLModel.metadata.create_all(engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN hardware_token VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN classification VARCHAR"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE residents ADD COLUMN resident_status VARCHAR DEFAULT 'Active'"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE sensing_events ADD COLUMN signal_quality INTEGER DEFAULT 94"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE sensing_events ADD COLUMN event_type VARCHAR DEFAULT 'SensingTelemetry'"))
            conn.commit()
        except Exception:
            pass

def get_session():
    # Set expire_on_commit=False globally as per project requirements
    with Session(engine, expire_on_commit=False) as session:
        yield session
