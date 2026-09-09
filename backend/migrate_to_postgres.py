import os
import sys
from sqlmodel import SQLModel, create_engine, Session, select
from app.models.entities import (
    Role, User, UserRole, Organization, Building, Floor, Room,
    SensingDevice, Resident, HealthCondition, ActivityType, SensingEvent,
    Alert, AlertAcknowledgement, AccessRequest, SharingPolicy, CaregiverProfile
)

# SQLite Source
SQLITE_URL = "sqlite:///./wifisense.db"
sqlite_engine = create_engine(SQLITE_URL, echo=False)

def migrate(postgres_url="postgresql://postgres:postgres@localhost:5432/wifisensedb"):
    print("=" * 70)
    print(" MIGRATING WIFISENSE DATA: SQLite -> PostgreSQL")
    print("=" * 70)
    print(f"Source: {SQLITE_URL}")
    print(f"Target: {postgres_url}\n")

    try:
        pg_engine = create_engine(postgres_url, echo=False)
        with pg_engine.connect() as conn:
            print("[+] Successfully connected to PostgreSQL!")
    except Exception as e:
        print(f"[-] Could not connect to PostgreSQL: {e}")
        print("    Ensure PostgreSQL service is running and credentials/database name are correct.")
        return False

    # 1. Create all tables in PostgreSQL
    print("[+] Creating schema tables in PostgreSQL...")
    SQLModel.metadata.create_all(pg_engine)
    print("[+] Schema creation completed successfully.")

    # 2. Ordered migration of all entities
    models_to_migrate = [
        Role,
        ActivityType,
        Organization,
        Building,
        Floor,
        Room,
        User,
        UserRole,
        CaregiverProfile,
        Resident,
        HealthCondition,
        SharingPolicy,
        SensingDevice,
        SensingEvent,
        Alert,
        AlertAcknowledgement,
        AccessRequest
    ]

    with Session(sqlite_engine) as src_session, Session(pg_engine) as dest_session:
        for model in models_to_migrate:
            table_name = model.__tablename__
            rows = src_session.exec(select(model)).all()
            print(f" -> Migrating {table_name}: {len(rows)} records...", end=" ")
            
            # Clear target table first to avoid duplicate primary key errors
            dest_session.query(model).delete()
            dest_session.commit()

            for row in rows:
                data = row.dict()
                dest_session.add(model(**data))
            dest_session.commit()
            print("DONE.")

    print("\n" + "=" * 70)
    print(" [SUCCESS] All 17 tables migrated to PostgreSQL!")
    print(" Open pgAdmin 4 -> Databases -> wifisensedb -> Schemas -> public -> Tables")
    print("=" * 70)
    return True

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/wifisensedb")
    migrate(url)
