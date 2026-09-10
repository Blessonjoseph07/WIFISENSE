# Wi-Fi Sense Focus 📡

Wi-Fi Sense Focus is an indoor human activity and fall monitoring system powered by Wi-Fi CSI (Channel State Information) telemetry, FastAPI backend, and a React + Vite dashboard.

---

## 🚀 Quick Start

### 1. Backend Service (FastAPI)
The backend uses Python 3.8+ and SQLite (or PostgreSQL).

```bash
# Navigate to backend directory
cd backend

# Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat

# Install dependencies (already installed in venv)
pip install -r requirements.txt

# Configure the environment (SECRET_KEY is required; the server refuses to start without it)
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"  # paste into SECRET_KEY

# Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Redoc**: `http://127.0.0.1:8000/redoc`

---

### 2. Frontend Application (React + Vite)
The frontend dashboard is built with React and Tailwind CSS.

```bash
# Navigate to frontend directory
cd frontend

# Run the development server (use npm.cmd on Windows PowerShell if execution policies block npm)
npm run dev
# or:
npm.cmd run dev
```
- **Frontend Dashboard**: `http://localhost:5173`

---

## ⚙️ Configuration

Backend settings come from the environment (see `backend/.env.example`):

| Variable | Required | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | yes | – | JWT signing key. Startup fails if unset. |
| `DATABASE_URL` | no | `sqlite:///./wifisense.db` | Database connection string. |
| `ALLOWED_ORIGINS` | no | `http://localhost:5173` | Comma-separated CORS origins. |
| `SEED_DEMO_DATA` | no | `0` | Set to `1` to seed demo data on startup. |
| `MAX_UPLOAD_BYTES` | no | `5242880` | Profile photo size limit. |

The frontend reads `VITE_API_BASE` (see `frontend/.env.example`), defaulting to `http://localhost:8000`.

---

## 👥 Accounts

Self-registration via `POST /auth/register` always creates an unprivileged `emergency_contact`
account. A system administrator grants staff roles and scopes through `POST /auth/assign-role`.

For local development only, start the backend with `SEED_DEMO_DATA=1` to create sample
facilities, devices, residents and demo logins (their passwords are in `backend/app/core/seed.py`).
Never enable demo seeding on a deployed instance.

---

## 📁 Project Architecture

- `backend/app/`
  - `main.py`: Application entry point, CORS config, router registration, DB initialization.
  - `core/`: Database engine, security (JWT, bcrypt), settings, database seeder.
  - `models/entities.py`: SQLModel relational entities.
  - `schemas/schemas.py`: Pydantic input/output validation schemas.
  - `routers/`: API endpoints for authentication, sensing events, alerts, analytics, family portal, and user profile management.
- `frontend/src/`
  - `App.jsx`: Main interactive dashboard and monitoring UI.
  - `main.jsx`: React entry point.
- `database/`
  - `schema.sql`: Full SQL DDL schema reference.
  - `database_design_document.md`: Comprehensive database architecture & specifications.
- `docs/`
  - UI prototypes and design specifications.
