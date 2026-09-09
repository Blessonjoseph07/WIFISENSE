@echo off
echo Starting Wi-Fi Sense Focus...

echo Starting Backend Server on http://127.0.0.1:8000 ...
start "WiFiSense-Backend" cmd /k "cd /d %~dp0backend && .\venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting Frontend Server on http://localhost:5173 ...
start "WiFiSense-Frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo Both services launched!
echo Backend Docs: http://127.0.0.1:8000/docs
echo Frontend App: http://localhost:5173
pause
