from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app.core.database import init_db, engine
from app.core.seed import seed_database
import os
from fastapi.staticfiles import StaticFiles
from app.routers import auth, crud, sensing, alerts, analytics, family_portal, users

app = FastAPI(
    title="Wi-Fi Sense Focus API",
    description="Backend services for indoor human activity and fall monitoring using Wi-Fi CSI telemetry.",
    version="1.0.0"
)

# CORS Configuration for Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Uploads directory
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(crud.router)
app.include_router(sensing.router)
app.include_router(alerts.router)
app.include_router(analytics.router)
app.include_router(family_portal.router)
app.include_router(users.router)

@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        seed_database(session)

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "project": "Wi-Fi Sense Focus",
        "phase": 1,
        "docs_url": "/docs"
    }
