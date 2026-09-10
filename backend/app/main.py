from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app.core.config import settings
from app.core.database import init_db, engine
from app.core.seed import seed_database
from app.core.bootstrap import bootstrap_system_admin
from app.routers import auth, crud, sensing, alerts, analytics, family_portal, users

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
app.include_router(sensing.router)
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
            seed_database(session)
        bootstrap_system_admin(session)

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "project": "Wi-Fi Sense Focus",
        "phase": 1,
        "docs_url": "/docs"
    }
