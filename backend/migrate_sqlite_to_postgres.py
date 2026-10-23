"""
Controlled SQLite -> PostgreSQL data migration.

  # 1. look first: reads the source, checks everything, writes NOTHING to PostgreSQL
  python migrate_sqlite_to_postgres.py --source hardware_test.db --target "postgresql://user:pass@host/db"

  # 2. then do it
  python migrate_sqlite_to_postgres.py --source hardware_test.db --target "postgresql://user:pass@host/db" --yes

The target can also come from the TARGET_DATABASE_URL environment variable, so the password never has to appear on a command line.

What it does
  * Reads a COPY of the source (SQLite's own backup API), never the file itself, and upgrades that copy to the current
    schema with Alembic if it is behind. The source file is not modified. It works on wifisense.db too, for the same reason.
  * Builds the PostgreSQL schema with `alembic upgrade head`, the same migrations the app runs. It does not use create_all.
  * Requires the target to hold no data (an empty database), so a migration can never silently mix two datasets.
  * Copies tables in foreign-key order inside ONE transaction: if anything fails, PostgreSQL is left exactly as it was.
  * Skips raw_csi_telemetry by default. Raw packets are a rolling window (see the retention rule), they are large, and the
    detection results that matter live in sensing_events. --include-raw-csi N copies only the newest N packets.
  * SQLite does not enforce foreign keys, PostgreSQL does. Rows that point at a parent that does not exist are listed.
    --orphans abort (default) stops; --orphans skip drops them (and, in turn, anything that pointed at them) and says so;
    an optional reference to a missing parent is set to NULL and counted.
  * Afterwards: resets every integer id sequence, compares row counts table by table, and prints a report
    (--report FILE also writes it as JSON).

It never prints the database password.
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from typing import Any, Dict, List, Set

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

BACKEND = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND)

SKIP_BY_DEFAULT = {"raw_csi_telemetry"}
# Lookup tables that the schema migrations may pre-fill. They are replaced by the source's rows inside the transaction.
REFERENCE_TABLES = {"roles", "activity_types"}
CHUNK = 2000


def masked(url: str) -> str:
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:  # noqa: BLE001
        return "<unparseable url>"


def alembic_upgrade(url: str) -> None:
    """Run the app's migrations against `url` in a child process, so this script's own settings are not disturbed."""
    import subprocess
    env = dict(os.environ, DATABASE_URL=url)
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"alembic upgrade failed on {masked(url)}:\n{r.stdout[-800:]}\n{r.stderr[-1500:]}")


def snapshot_sqlite(path: str) -> str:
    """Consistent copy of the source made with SQLite's backup API (safe even if the app is running)."""
    tmp = os.path.join(tempfile.mkdtemp(prefix="wifisense_migrate_"), "source_copy.db")
    src = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    return tmp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="path to the SQLite database file")
    ap.add_argument("--target", default=os.getenv("TARGET_DATABASE_URL", ""), help="PostgreSQL URL (or set TARGET_DATABASE_URL)")
    ap.add_argument("--yes", action="store_true", help="actually write to PostgreSQL (without it nothing is written)")
    ap.add_argument("--orphans", choices=["abort", "skip"], default="abort")
    ap.add_argument("--include-raw-csi", type=int, default=0, metavar="N", help="also copy the newest N raw CSI packets (default: none)")
    ap.add_argument("--report", help="write the report as JSON to this file")
    a = ap.parse_args()

    if not os.path.isfile(a.source):
        sys.exit(f"{a.source} is not a file")
    target_url = a.target
    if target_url.startswith("postgres://"):
        target_url = "postgresql://" + target_url[len("postgres://"):]
    if not target_url.startswith("postgresql"):
        sys.exit("--target (or TARGET_DATABASE_URL) must be a postgresql:// URL")

    started = time.time()
    print(f"source : {os.path.abspath(a.source)} (read through a copy; the file is not modified)")
    print(f"target : {masked(target_url)}")
    print(f"mode   : {'WRITE' if a.yes else 'DRY RUN (nothing is written to PostgreSQL)'}")

    # ---- 1. source: consistent copy, brought to the current schema -------------------------------------------
    copy_path = snapshot_sqlite(os.path.abspath(a.source))
    copy_url = "sqlite:///" + copy_path.replace("\\", "/")
    alembic_upgrade(copy_url)
    src = create_engine(copy_url)

    # ---- 2. target: schema from Alembic, must be empty of data ------------------------------------------------
    pg = create_engine(target_url, connect_args={"options": "-c timezone=utc"})
    if a.yes:
        alembic_upgrade(target_url)
    else:
        with pg.connect() as c:
            have = inspect(c).get_table_names()
        if "alembic_version" not in have:
            print("note   : the target has no schema yet; a real run will create it with `alembic upgrade head`.")

    from sqlmodel import SQLModel
    import app.models.entities  # noqa: F401  (registers every table)
    tables = list(SQLModel.metadata.sorted_tables)       # parents before children
    names = {t.name for t in tables}
    referenced = {fk.column.table.name for t in tables for fk in t.foreign_keys}

    src_tables = set(inspect(src).get_table_names()) - {"alembic_version"}
    unknown = sorted(src_tables - names)
    if unknown:
        print(f"WARNING: tables in the source that the app does not define (not copied): {unknown}")

    if a.yes:
        with pg.connect() as c:
            dirty = {t.name: c.execute(text(f'select count(*) from "{t.name}"')).scalar() for t in tables}
        dirty = {k: v for k, v in dirty.items() if v and k not in REFERENCE_TABLES}
        if dirty:
            sys.exit(f"STOPPED: the target already contains data ({dirty}). Use an empty database so two datasets are never mixed.")

    # ---- 3. plan: counts, orphans -------------------------------------------------------------------------------
    plan: List[Dict[str, Any]] = []
    copied_pks: Dict[str, Set[Any]] = {}
    report: Dict[str, Any] = {"tables": {}, "skipped_tables": [], "orphan_rows_skipped": {}, "optional_refs_nulled": {}}
    raw_limit = a.include_raw_csi

    with src.connect() as sc:
        for t in tables:
            if t.name not in src_tables:
                report["tables"][t.name] = {"source": 0, "copied": 0, "note": "absent in source"}
                continue
            total = sc.execute(text(f'select count(*) from "{t.name}"')).scalar()
            if t.name in SKIP_BY_DEFAULT and raw_limit <= 0:
                report["skipped_tables"].append({"table": t.name, "rows_in_source": total,
                                                 "reason": "raw packets are a rolling window; detections are kept in sensing_events"})
                continue
            plan.append({"table": t, "total": total})

        # ---- 4. copy (one transaction) -------------------------------------------------------------------------
        pg_conn = pg.connect() if a.yes else None
        trans = pg_conn.begin() if pg_conn else None
        try:
            if pg_conn:
                for ref in sorted(REFERENCE_TABLES & names):
                    pg_conn.execute(text(f'delete from "{ref}"'))
            for item in plan:
                t = item["table"]
                pk_cols = [c.name for c in t.primary_key.columns]
                # foreign keys that point at a single-column primary key of another table: those can be checked
                checks = [(fk.parent.name, fk.column.table.name, fk.parent.nullable) for fk in t.foreign_keys
                          if [c.name for c in fk.column.table.primary_key.columns] == [fk.column.name]]
                if t.name in referenced:
                    copied_pks[t.name] = set()
                query = t.select()
                if t.name == "raw_csi_telemetry":
                    query = query.order_by(t.c.id.desc()).limit(raw_limit)
                elif pk_cols:
                    query = query.order_by(*[t.c[c] for c in pk_cols])
                copied = skipped = nulled = 0
                batch: List[Dict[str, Any]] = []
                for row in sc.execute(query).mappings():
                    rec = dict(row)
                    drop = False
                    for col, parent, nullable in checks:
                        val = rec.get(col)
                        if val is None or val in copied_pks.get(parent, ()):
                            continue
                        if nullable:
                            rec[col] = None
                            nulled += 1
                        else:
                            drop = True
                            break
                    if drop:
                        if a.orphans == "abort":
                            sys.exit(f"STOPPED: {t.name} has a row whose required parent does not exist (primary key {[rec.get(c) for c in pk_cols]}). "
                                     "SQLite did not enforce this; PostgreSQL does. Re-run with --orphans skip to drop such rows and report them.")
                        skipped += 1
                        continue
                    if t.name in copied_pks and len(pk_cols) == 1:
                        copied_pks[t.name].add(rec[pk_cols[0]])
                    batch.append(rec)
                    if len(batch) >= CHUNK:
                        if pg_conn:
                            pg_conn.execute(t.insert(), batch)
                        copied += len(batch)
                        batch = []
                if batch:
                    if pg_conn:
                        pg_conn.execute(t.insert(), batch)
                    copied += len(batch)
                entry = {"source": item["total"], "copied": copied, "orphan_rows_skipped": skipped, "optional_refs_nulled": nulled}
                report["tables"][t.name] = entry
                if skipped:
                    report["orphan_rows_skipped"][t.name] = skipped
                if nulled:
                    report["optional_refs_nulled"][t.name] = nulled
                print(f"  {t.name:34s} source={item['total']:>7}  copied={copied:>7}" + (f"  orphans_skipped={skipped}" if skipped else "")
                      + (f"  refs_nulled={nulled}" if nulled else ""), flush=True)
            if trans:
                trans.commit()
        except BaseException:
            if trans:
                trans.rollback()
            raise
        finally:
            if pg_conn:
                pg_conn.close()

    # ---- 5. after: sequences, verification --------------------------------------------------------------------
    verified = None
    if a.yes:
        from app.core.database import sync_postgres_sequences
        report["sequences_reset"] = sync_postgres_sequences(pg)
        with pg.connect() as c:
            c.execute(text("ANALYZE"))
            bad = []
            for item in plan:
                n = c.execute(text(f'select count(*) from "{item["table"].name}"')).scalar()
                exp = report["tables"][item["table"].name]["copied"]
                if n != exp:
                    bad.append((item["table"].name, exp, n))
        verified = not bad
        report["verified_counts_match"] = verified
        if bad:
            print(f"VERIFICATION FAILED (table, expected, found): {bad}")

    report["seconds"] = round(time.time() - started, 1)
    skipped_total = sum(report["orphan_rows_skipped"].values())
    print("\n--- summary ---")
    for s in report["skipped_tables"]:
        print(f"  skipped table {s['table']} ({s['rows_in_source']} rows): {s['reason']}")
    print(f"  tables copied: {len(plan)}   rows copied: {sum(v['copied'] for v in report['tables'].values())}   "
          f"orphan rows skipped: {skipped_total}   optional refs set to NULL: {sum(report['optional_refs_nulled'].values())}")
    if a.yes:
        print(f"  id sequences reset: {report.get('sequences_reset')}   row counts match: {verified}")
    else:
        print("  DRY RUN: nothing was written. Add --yes to migrate.")
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        print(f"  report written to {a.report}")
    shutil.rmtree(os.path.dirname(copy_path), ignore_errors=True)
    if a.yes and not verified:
        sys.exit(1)


if __name__ == "__main__":
    main()
