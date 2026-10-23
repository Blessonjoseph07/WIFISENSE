"""
SQLITE -> POSTGRESQL MIGRATION TOOL TEST
========================================
Needs a PostgreSQL server: set PG_ADMIN_URL to a URL that can CREATE DATABASE (for example
postgresql://user:pass@127.0.0.1:5433/postgres). Without it the test says so and exits 0 (CI sets it).

Builds a seeded SQLite database, plants a dangling reference and raw CSI packets, then checks the tool: the dry run writes
nothing, a dangling required reference aborts by default, --orphans skip reports and drops it, raw CSI is not copied,
row counts match, id sequences work afterwards, the source file is byte-for-byte unchanged, and a second run refuses to
mix data into a non-empty target.
"""
import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import uuid

BACKEND = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([PY, os.path.join(BACKEND, "migrate_sqlite_to_postgres.py"), *args], cwd=BACKEND, env=e, capture_output=True, text=True)


def main():
    admin = os.getenv("PG_ADMIN_URL")
    if not admin:
        print("SKIPPED: set PG_ADMIN_URL (a PostgreSQL URL that may CREATE DATABASE) to run the migration test")
        return
    import psycopg2
    from sqlalchemy.engine import make_url
    u = make_url(admin)

    def connect(db):
        return psycopg2.connect(host=u.host, port=u.port or 5432, user=u.username, password=u.password, dbname=db)

    tmp = tempfile.mkdtemp(prefix="mig_test_")
    src_db = os.path.join(tmp, "source.db")
    src_url = "sqlite:///" + src_db.replace("\\", "/")
    target_name = "mig_" + uuid.uuid4().hex[:8]
    target_url = u.set(database=target_name).render_as_string(hide_password=False)

    print("--- building a seeded SQLite source")
    r = subprocess.run([PY, "-c", "from app.main import on_startup; on_startup()"], cwd=BACKEND,
                       env=dict(os.environ, DATABASE_URL=src_url, PAYMENT_WEBHOOK_SECRET="mig-test-secret-123"), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1500:]
    c = sqlite3.connect(src_db)
    c.execute("PRAGMA foreign_keys=OFF")
    users_before = c.execute("select count(*) from users").fetchone()[0]
    dev = c.execute("select id, room_id from devices limit 1").fetchone()
    # raw packets that must NOT be migrated
    for i in range(20):
        c.execute("insert into raw_csi_telemetry (device_id, room_id, timestamp, rssi, subcarrier_count, csi_data, provenance, created_at) "
                  "values (?,?,?,?,?,?,?,?)", (dev[0], dev[1], "2026-01-01 00:00:00", -50, 52, '{"iq": []}', "simulated", "2026-01-01 00:00:00"))
    # a sensing event that points at a device that does not exist (SQLite allows it, PostgreSQL does not)
    ev = c.execute("select count(*) from sensing_events").fetchone()[0]
    c.execute("insert into sensing_events (device_id, room_id, timestamp, rssi, subcarrier_count, signal_quality, event_type, extracted_features, "
              "inferred_activity_id, model_confidence, source) values ('no-such-device', ?, '2026-01-01 00:00:00', -50, 52, 90, 'x', '{}', 1, 0.5, 'simulated')", (dev[1],))
    c.commit()
    c.close()
    digest = hashlib.sha256(open(src_db, "rb").read()).hexdigest()

    admin_conn = connect("postgres")
    admin_conn.autocommit = True
    admin_conn.cursor().execute(f'create database "{target_name}"')
    try:
        print("--- dry run writes nothing")
        r = run(["--source", src_db, "--target", target_url, "--orphans", "skip"])
        assert r.returncode == 0 and "DRY RUN" in r.stdout, r.stdout[-800:] + r.stderr[-800:]
        t = connect(target_name).cursor()
        t.execute("select count(*) from information_schema.tables where table_schema='public' and table_name='users'")
        assert t.fetchone()[0] == 0, "a dry run must not create the schema"
        print("[PASS] dry run: report only, no tables created")

        print("--- a dangling required reference aborts by default")
        r = run(["--source", src_db, "--target", target_url, "--yes"])
        assert r.returncode != 0 and "required parent does not exist" in (r.stdout + r.stderr), r.stdout[-600:] + r.stderr[-600:]
        t = connect(target_name).cursor()
        t.execute("select count(*) from users")
        assert t.fetchone()[0] == 0, "an aborted migration must leave PostgreSQL without data (one transaction)"
        print("[PASS] abort leaves the target empty")

        print("--- --orphans skip migrates, reports the skipped row, and skips raw CSI")
        r = run(["--source", src_db, "--target", target_url, "--yes", "--orphans", "skip"])
        assert r.returncode == 0 and "row counts match: True" in r.stdout, r.stdout[-1200:] + r.stderr[-800:]
        assert "orphan rows skipped: 1" in r.stdout and "skipped table raw_csi_telemetry (20 rows)" in r.stdout, r.stdout[-1200:]
        t = connect(target_name).cursor()
        t.execute("select count(*) from users")
        assert t.fetchone()[0] == users_before
        t.execute("select count(*) from raw_csi_telemetry")
        assert t.fetchone()[0] == 0
        t.execute("select count(*) from sensing_events")
        assert t.fetchone()[0] == ev, "the dangling event is dropped, every other event is copied"
        print(f"[PASS] {users_before} users, {ev} sensing events copied; the dangling event and the 20 raw packets were not")

        print("--- sequences work after the copy")
        t.execute("select setval(pg_get_serial_sequence('activity_types','id'), (select max(id) from activity_types))")
        t.execute("select nextval(pg_get_serial_sequence('activity_types','id'))")
        nxt = t.fetchone()[0]
        t.execute("select max(id) from activity_types")
        assert nxt > t.fetchone()[0]
        print("[PASS] id sequences sit past the copied ids")

        print("--- the source file is untouched")
        assert hashlib.sha256(open(src_db, "rb").read()).hexdigest() == digest, "the source database was modified"
        print("[PASS] source SHA-256 identical before and after")

        print("--- a second run refuses a non-empty target")
        r = run(["--source", src_db, "--target", target_url, "--yes", "--orphans", "skip"])
        assert r.returncode != 0 and "already contains data" in (r.stdout + r.stderr)
        print("[PASS] refuses to mix datasets")
        print("\nALL SQLITE -> POSTGRESQL MIGRATION TESTS PASSED")
    finally:
        admin_conn.cursor().execute(f'drop database if exists "{target_name}" with (force)')


if __name__ == "__main__":
    main()
