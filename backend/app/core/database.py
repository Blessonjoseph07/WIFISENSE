import os
from sqlmodel import create_engine, Session
from alembic import command
from alembic.config import Config
from app.core.config import BASE_DIR, settings

# For SQLite, connect_args={"check_same_thread": False} is required
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.DATABASE_URL.startswith("postgres"):
    # Timestamps are stored as UTC in timezone-less columns. Pinning the session to UTC keeps comparisons between those
    # columns and timezone-aware values correct whatever timezone the database server itself is set to.
    connect_args = {"options": "-c timezone=utc"}
else:
    connect_args = {}

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


def sync_postgres_sequences(target=None):
    """PostgreSQL only: move every integer primary-key sequence past the largest id in its table.

    The seed inserts roles and activity types with fixed ids. SQLite then keeps handing out the next free id by
    itself, but a PostgreSQL sequence does not know about those rows and would hand out an id that already exists.
    This is also needed after copying rows from another database. It is idempotent and a no-op on SQLite."""
    from sqlalchemy import Integer, text
    from sqlmodel import SQLModel
    target = target or engine
    if target.dialect.name != "postgresql":
        return 0
    fixed = 0
    with target.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            pks = list(table.primary_key.columns)
            if len(pks) != 1 or not isinstance(pks[0].type, Integer):
                continue
            col = pks[0].name
            seq = conn.execute(text("select pg_get_serial_sequence(:t, :c)"), {"t": table.name, "c": col}).scalar()
            if not seq:
                continue
            conn.execute(
                text(f'select setval(:seq, coalesce((select max("{col}") from "{table.name}"), 1), '
                     f'(select max("{col}") from "{table.name}") is not null)'),
                {"seq": seq},
            )
            fixed += 1
    return fixed
