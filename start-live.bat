@echo off
rem Live hardware session: API on the hardware database, the website, and the serial bridge for the ESP32-S3 receiver.
rem   start-live.bat            uses COM4
rem   start-live.bat COM3       uses another port
rem The bridge needs the receiver's device token in the WIFISENSE_DEVICE_TOKEN environment variable. Set it once with
rem   setx WIFISENSE_DEVICE_TOKEN "TK-ESP32-..."
rem then open a NEW terminal (setx only affects terminals opened afterwards). See docs/RUNBOOK.md.

set "RX_PORT=%~1"
if "%RX_PORT%"=="" set "RX_PORT=COM4"

rem The live receiver is registered in hardware_test.db (start-all.bat uses the main wifisense.db). Windows started below
rem inherit this setting.
set "DATABASE_URL=sqlite:///./hardware_test.db"

echo Starting the API on the hardware database (http://127.0.0.1:8000) ...
start "WiFiSense-API (hardware DB)" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Starting the website (http://localhost:5173) ...
start "WiFiSense-Website" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

if not defined WIFISENSE_DEVICE_TOKEN (
  echo.
  echo No WIFISENSE_DEVICE_TOKEN set, so the bridge was NOT started.
  echo   1. Open http://localhost:5173, sign in as blesson@wifisense.com, Devices ^& Service Desk.
  echo   2. Press RESET TOKEN on 7c:4f:ad:26:05:78 and copy the token.
  echo   3. setx WIFISENSE_DEVICE_TOKEN "the token"   then open a new terminal and run start-live.bat again.
  pause
  exit /b 0
)

echo Waiting for the API before starting the bridge on %RX_PORT% ...
timeout /t 10 /nobreak >nul
start "WiFiSense-Bridge (%RX_PORT%)" cmd /k "cd /d %~dp0 && backend\venv\Scripts\python.exe tools\csi_serial_bridge.py --port %RX_PORT% --api http://127.0.0.1:8000"

echo.
echo Started: API, website and bridge. Open http://localhost:5173  (Sensing Monitor - LIVE HARDWARE)
echo If the receiver is unplugged the bridge window stops: plug it back in and run this file again.
pause
