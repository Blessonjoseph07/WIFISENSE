from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

# For SQLite, connect_args={"check_same_thread": False} is required
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    # Set expire_on_commit=False globally as per project requirements
    with Session(engine, expire_on_commit=False) as session:
        yield session
