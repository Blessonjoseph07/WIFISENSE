#!/usr/bin/env bash
# Seeds a fresh database, starts the API and runs every backend test script. Used by CI for SQLite and PostgreSQL.
# The database comes from DATABASE_URL (unset = the default SQLite file).
set -u
cd "$(dirname "$0")"
PORT="${API_PORT:-8000}"
export API_BASE="http://127.0.0.1:$PORT"

python -c "from app.core.database import init_db, engine, sync_postgres_sequences; from sqlmodel import Session; from app.core.seed import seed_database; init_db(); session=Session(engine); seed_database(session); session.close(); sync_postgres_sequences()"

python -m uvicorn app.main:app --host 127.0.0.1 --port $PORT > uvicorn.log 2>&1 &
UVICORN_PID=$!
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:$PORT/health > /dev/null; then echo "API is up (PID $UVICORN_PID)."; break; fi
  echo "Waiting for the API ($i/60)..."; sleep 1
done
if ! kill -0 $UVICORN_PID 2>/dev/null; then echo "uvicorn died:"; cat uvicorn.log; exit 1; fi

FAILED=""
for t in test_boundaries test_master_phases test_phase1_security test_device_ingestion test_care_records \
         test_alert_verification test_doctor_workflow test_dataset_replay test_audit_scoping test_family_subscription \
         test_business_logic test_global_admin_alert_access test_ui_flow_sharing_policy test_live_stream test_room_bookings \
         test_csi_serial_bridge test_fall_doctor_notify test_health test_seed_profile test_retention test_ingest_delivery test_room_picker test_movement test_occupancy \
         test_migrate_sqlite_to_postgres; do
  echo "=== $t ==="
  if ! python $t.py; then FAILED="$FAILED $t"; fi
done

kill $UVICORN_PID 2>/dev/null || true
if [ -n "$FAILED" ]; then echo "FAILED:$FAILED"; echo "--- uvicorn.log (tail) ---"; tail -40 uvicorn.log; exit 1; fi
echo "ALL BACKEND TESTS PASSED"
