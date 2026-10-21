# Git workflow for WiFi Sense

`master` is the stable, demonstrable version. Nothing is committed to it directly.

## Everyday flow
1. Branch from an up-to-date `master`: `feat/<topic>`, `fix/<topic>` or `docs/<topic>`.
2. Make small commits with messages that say what changed and why.
3. Run the backend test scripts and the frontend build. Keep the real output.
4. Push the branch and open a pull request into `master` (the template asks for the test output and a data-provenance check).
5. Merge only when the CI check is green. Use a **merge commit** so each feature's commits stay visible in the git log.
6. Delete the merged branch.

## Stacked branches
When one branch builds on another (for example `feat/b` was cut from `feat/a`), open ONE pull request from the top
branch into `master`, or merge them bottom-up and re-point each next pull request at `master` before merging it.
Never merge a stacked branch ahead of the one underneath it.

## Running the checks locally (Windows, Git Bash)
```bash
cd backend
export DATABASE_URL="sqlite:///./test_run.db" SEED_DEMO_DATA=1     # a throwaway database, never your real one
venv/Scripts/python.exe -c "from app.core.database import init_db, engine; from sqlmodel import Session; from app.core.seed import seed_database; init_db(); seed_database(Session(engine))"
venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 &       # leave running
for t in test_boundaries test_master_phases test_phase1_security test_device_ingestion test_care_records test_alert_verification test_doctor_workflow; do
  venv/Scripts/python.exe $t.py || break
done
cd ../frontend && npm run build
```
The test scripts talk to the running server on port 8000 and use the same `DATABASE_URL` for setup and cleanup.

## Protecting `master` (GitHub settings, done once by the repository admin)
Settings -> Rules -> Rulesets -> New branch ruleset (or Settings -> Branches -> Add branch protection rule), target `master`:

| Setting | Value |
|---|---|
| Require a pull request before merging | On |
| Required approvals | 0 for a solo repository (set to 1 only if a second person with write access reviews) |
| Require status checks to pass | On, and select **Backend Boundary & Regression Tests** (the CI job) |
| Require branches to be up to date before merging | On |
| Block force pushes | On |
| Restrict deletions | On |
| Require linear history | Off (merge commits are used on purpose) |
| Do not allow bypassing | On, so the rule also applies to the owner |

The status check only appears in the dropdown after CI has run once on a pull request.

## Rules that never bend
- Do not commit `.env` files, database files, tokens or real personal data.
- Do not describe simulated or replayed data as live ESP32 capture, in the UI, the report or a commit message.
- Reports (testing report, project report) state only what was actually run, including failures that were found and fixed.
