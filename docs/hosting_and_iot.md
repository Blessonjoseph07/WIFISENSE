# Hosting the demo (Render API + Neon Postgres + Vercel frontend)

Status: the files here are prepared but **have not been deployed**. The application has only been run on SQLite so far; the first
deploy is the first run on PostgreSQL. Read the Render logs of that first start.

## Why the settings look strict
- `ENVIRONMENT=production` refuses SQLite and the built-in SECRET_KEY (so you need a Postgres database).
- Demo data creates user accounts with passwords written in the repository. In production the app therefore **refuses to seed demo
  accounts unless `SEED_PASSWORD` (12+ characters) is set**. That password replaces the well-known ones for every demo account.
- `SEED_PROFILE=minimal` keeps one user per role (7 accounts) and the residents, rooms and devices they need.

## Steps you do (accounts and secrets stay with you)
1. **Neon** (free Postgres): create a project, copy the connection string. Make sure it ends with `?sslmode=require`.
2. **Render**: New > Blueprint, connect this GitHub repo (`render.yaml`). In the dashboard set:
   - `DATABASE_URL` = the Neon string
   - `ALLOWED_ORIGINS` = your Vercel URL (set after step 3, then redeploy)
   - `SEED_PASSWORD` = a password only you know (12+ characters)
3. **Vercel**: import the repo, root directory `frontend`, build env `VITE_API_BASE=https://<your-service>.onrender.com`.
4. Open the Vercel URL and log in with the demo emails below and your `SEED_PASSWORD`.

Demo emails: `blesson@wifisense.com` (system admin), `elizabeth@wifisense.com` (care facility manager), `abhinand@wifisense.com`
(corporate facility manager), `mary@wifisense.com` (caregiver), `tomy@wifisense.com` (corporate staff),
`mathew.varghese@wifisense.com` (doctor), `john@wifisense.com` (family member).

## Things to know
- Render's free web service sleeps after about 15 minutes idle (a cold start takes 30-60 s). Open the API URL before presenting.
- Seeding runs once, when the database is empty. Changing `SEED_PASSWORD` later does not change existing accounts.
- Payments are a sandbox; no real money is involved.

## Connecting the ESP32-S3 boards to the hosted API
The receiver is read over USB by `tools/csi_serial_bridge.py` on the PC beside it; point the bridge at the hosted API:

    python tools/csi_serial_bridge.py --port COM4 --api https://<your-service>.onrender.com --token <device token>

Register the receiver on the hosted site first (Devices page, source "live") to get its token, which is shown once.
Use HTTPS; never put the token in the firmware or the repository. The wire format is in `docs/firmware_contract.md`.
