# Presentation runbook (hosted demo)

Rule one: **nothing risky happens live.** Load all data the day before. During the presentation you only look at pages.

## The day before
1. Run the dataset replay once, from your PC, until it finishes (it retries on 502/500 and can resume):
   `python tools\replay_wifall.py --data-dir <WiFall folder> --limit 32` and, if it stopped, the same command with `--skip N`
   (N = clips already done, shown in its output). Use a node registered with **Dataset replay**.
2. Open the hosted site as `blesson@` and check **Sensing Monitor > Dataset Replay** and **Evidence & Limits**.
3. Consider the Render **Starter** plan (about 7 USD a month, check the current price) for presentation week. The free plan sleeps when
   idle and has very little CPU, which is what caused the 502 errors. You can go back to free afterwards.

## Keep it awake (free, 2 minutes)
Create a free monitor (for example UptimeRobot, HTTP, every 5 minutes) for `https://wifisense-api.onrender.com/health`. A pinged
service does not fall asleep. This is optional if you use the Starter plan.

## 15 minutes before
    python tools\presentation_preflight.py --api https://wifisense-api.onrender.com --web https://wifisense-ecru.vercel.app
It must print READY. Then log in once in the browser you will present from and leave that tab open.

## Backup plan (if the internet or Render fails)
Run the local copy, which does not need the internet: backend `uvicorn app.main:app --port 8000` on `hardware_test.db` and
`npm run dev` in `frontend`, at `http://localhost:5173`. Decide the switch before you start; do not debug in front of the audience.

## What not to do live
- Do not run the replay, register devices, or reset the database.
- Do not change environment variables in Render (every change redeploys and takes a minute or two).
