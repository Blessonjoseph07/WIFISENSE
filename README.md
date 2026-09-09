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

## 👥 Seeded Demo Accounts

The database is pre-seeded with sample facilities, devices, residents, and the following accounts:

| Email | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `blesson@wifisense.com` | `blessonpassword` | System Administrator | Full administrative system access |
| `abhinand@wifisense.com` | `abhinandpassword` | Facility Manager | Amal Jyothi College of Engineering (Corporate) |
| `tomy@wifisense.com` | `tomypassword` | Corporate Staff | AJCE Computer Applications |
| `abhinanth@wifisense.com` | `abhinanthpassword` | Caregiver | St. Peter's Elder Care Home (Ward 101) |
| `mary@wifisense.com` | `marypassword` | Caregiver | St. Peter's Elder Care Home (Wing Beta) |
| `elizabeth@wifisense.com` | `elizabethpassword` | Facility Manager | St. Peter's Elder Care Home |
| `john@wifisense.com` | `johnpassword` | Emergency Contact | Family portal linked to Annamma Joseph |
| `susan@wifisense.com` | `susanpassword` | Emergency Contact | Family portal access pending |

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
