# Running Wi-Fi Sense with Docker

The hosted API on Render runs in Docker, built from `backend/Dockerfile`. The same image runs the whole project on one
laptop with `docker compose`: Postgres, the API and the website, each in its own container, with one command.

| Setup | Uses Docker? | Ports |
|---|---|---|
| Hosted API (Render) | Yes. `render.yaml` has `runtime: docker` and builds `backend/Dockerfile`; Render sets `$PORT` | — |
| Hosted website (Vercel) | No. Vercel builds the static site from `package.json` | — |
| `start-live.bat` / `start-all.bat` (local, with the boards) | No. `backend\venv` + `npm run dev` | API 8000, website 5173 |
| `docker compose` (this page) | Yes | website **8081**, API **8080** (Postgres stays inside Docker) |

The Docker ports are different on purpose, so both local setups can run at the same time. They also avoid the ranges
Windows reserves for Hyper-V (check with `netsh interface ipv4 show excludedportrange protocol=tcp`).

## Start

Docker Desktop must be running (whale icon in the taskbar). In PowerShell:

```powershell
cd D:\Wifisense
docker compose up --build -d
```

The first build takes a few minutes; later starts take seconds. Then open **http://localhost:8081**.

The Docker database starts empty and is seeded with the demo accounts (`SEED_PROFILE=minimal`, one user per role) using
their well-known development passwords. To give every demo account your own password instead:

```powershell
$env:SEED_PASSWORD = "your-12+-character-password"; docker compose up -d
```

## Everyday commands

```powershell
docker compose ps                 # what is running, and health
docker compose logs -f api        # API log (Ctrl+C to stop following)
docker compose down               # stop everything; the database is kept
docker compose down -v            # stop and DELETE the Docker database and uploads
docker compose up --build -d      # rebuild after changing code
```

## What is inside

- `backend/Dockerfile`: Python 3.10 slim, `pip install -r requirements.txt`, runs `uvicorn` as a non-root user on `$PORT`
  (8000 when unset), with a health check on `/health`. CI builds it and starts it in production mode on every pull
  request (the "Docker image (API)" check), so a change that would break the Render build fails there first.
- `frontend/Dockerfile`: builds the site with Node 22 (`VITE_API_BASE=http://localhost:8080`), then serves it with nginx
  (`frontend/nginx.conf`, same page fallback as `vercel.json`).
- `docker-compose.yml`: `db` (Postgres 16, data in the `pgdata` volume, not published), `api`, `web`. The published
  ports are bound to `127.0.0.1`, so nothing is reachable from other machines on the network.
- `.dockerignore` files keep `venv`, `node_modules`, every `*.db`, `.env` files and uploads out of the images, so your
  local databases and secrets never end up inside a container image.

## Live hardware with Docker (optional)

The serial bridge still runs on Windows (containers on Windows cannot open COM ports easily). Point it at the Docker API
with a token from the Docker site (Devices & Service Desk, RESET TOKEN):

```powershell
.\backend\venv\Scripts\python tools\csi_serial_bridge.py --port COM4 --api http://localhost:8080 --token $t
```

For the panel, keep using the hosted site or `start-live.bat`: the board is registered there.
