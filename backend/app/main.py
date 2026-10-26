from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from app.core.config import settings
from app.core.database import init_db, engine, sync_postgres_sequences
from app.core.seed import seed_database
from app.core.bootstrap import bootstrap_system_admin
from app.core.demo_profile import apply_demo_profile, ensure_demo_extras, sync_demo_passwords
from app.services.retention import start_background_pruner
from app.services.detection import close_stale_live_fall_alerts
from app.models.entities import Organization
from app.routers import auth, crud, sensing, occupancy, alerts, analytics, family_portal, users, care_records, doctor_portal, replay, payments, bookings

app = FastAPI(
    title="Wi-Fi Sense Focus API",
    description="Backend services for indoor human activity and fall monitoring using Wi-Fi CSI telemetry.",
    version="1.0.0"
)

# CORS Configuration for Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(crud.router)
app.include_router(care_records.router)
app.include_router(doctor_portal.router)
app.include_router(replay.router)
app.include_router(payments.router)
app.include_router(bookings.router)
app.include_router(sensing.router)
app.include_router(occupancy.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(family_portal.router)
app.include_router(users.router)
app.include_router(users.uploads_router)

@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        if settings.SEED_DEMO_DATA:
            first_run = session.exec(select(Organization)).first() is None
            seed_database(session)
            if first_run:
                apply_demo_profile(session)
            ensure_demo_extras(session)
            sync_demo_passwords(session)
        bootstrap_system_admin(session)
        close_stale_live_fall_alerts(session)
    sync_postgres_sequences()
    start_background_pruner(engine)

@app.get("/health", tags=["Health"])
def health():
    """Liveness and readiness for hosting platforms and for humans. Public, and it reveals nothing sensitive:
    only whether the database answers, whether the detection model loaded, and which payment mode is configured."""
    from sqlalchemy import text
    from app.services import fall_model
    db_ok = True
    try:
        with Session(engine) as session:
            session.exec(text("select 1"))
    except Exception:  # noqa: BLE001 - any failure means "not ready"
        db_ok = False
    info = fall_model.model_info()
    model_ok = bool(info.get("available"))
    ready = db_ok and model_ok
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ok" if ready else "degraded",
            "database": "ok" if db_ok else "unreachable",
            "detection_model": "loaded" if model_ok else "unavailable",
            "payments_mode": settings.PAYMENTS_MODE,
            "environment": settings.ENVIRONMENT,
        },
    )


@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "project": "Wi-Fi Sense Focus",
        "phase": 1,
        "docs_url": "/docs"
    }
