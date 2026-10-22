"""
Reduce a SQLite database to ONE user per role (and per organization context for facility managers), for presentations.

  python tools/keep_one_user_per_role.py --db backend/hardware_test.db --yes

What it does
  * Keeps exactly the users listed in KEEP (by email) and deletes every other user together with everything that
    depends on them (roles, tokens, subscriptions, family connections, doctor profile and its assignments/messages, ...).
    Dependents are found from the database's own foreign keys, so nothing is left dangling.
  * Rows that merely point at a deleted user through an OPTIONAL column (for example "approved by") keep existing and
    that column is cleared. Audit log entries are kept as history.
  * Residents, rooms, devices, alerts and sensing data are not touched.
  * Writes a timestamped backup next to the database first, verifies the result (one user per role, no dangling
    references, integrity check) and rolls back if anything is off.

It refuses to touch the project's main database, wifisense.db, unless --allow-main is given. It only works on SQLite files.
The test scripts and CI rely on the full seed, so this is a tool for a presentation database, not a change to the seed.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import time

KEEP = {
    "system_admin": "blesson@wifisense.com",
    "facility_manager (care)": "elizabeth@wifisense.com",
    "facility_manager (corporate)": "abhinand@wifisense.com",
    "caregiver": "mary@wifisense.com",
    "corporate_staff": "tomy@wifisense.com",
    "doctor": "mathew.varghese@wifisense.com",
    "family_member": "john@wifisense.com",
}


def table_info(conn, table):
    return conn.execute(f'PRAGMA table_info("{table}")').fetchall()


def pk_column(conn, table):
    pks = [r[1] for r in table_info(conn, table) if r[5]]
    return pks[0] if len(pks) == 1 else None


def build_children(conn):
    """parent table -> [(child table, child column, parent column, child column is NOT NULL)]"""
    tables = [r[0] for r in conn.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")]
    kids = {}
    for t in tables:
        notnull = {r[1]: bool(r[3]) for r in table_info(conn, t)}
        for fk in conn.execute(f'PRAGMA foreign_key_list("{t}")').fetchall():
            parent, col, to = fk[2], fk[3], fk[4]
            kids.setdefault(parent, []).append((t, col, to, notnull.get(col, False)))
    return kids


def delete_rows(conn, kids, table, ids, stats):
    """Delete rows of `table` whose primary key is in ids, after removing or detaching everything that depends on them."""
    ids = list(ids)
    if not ids:
        return
    pk = pk_column(conn, table)
    if pk is None:
        raise SystemExit(f"cannot cascade through {table}: no single-column primary key")
    marks = ",".join("?" * len(ids))
    for child, col, to, notnull in kids.get(table, []):
        if to != pk:
            raise SystemExit(f"unsupported foreign key {child}.{col} -> {table}.{to}")
        if notnull:
            cpk = pk_column(conn, child)
            if cpk is None:
                n = conn.execute(f'delete from "{child}" where "{col}" in ({marks})', ids).rowcount
                stats[child] = stats.get(child, 0) + n
            else:
                child_ids = [r[0] for r in conn.execute(f'select "{cpk}" from "{child}" where "{col}" in ({marks})', ids)]
                delete_rows(conn, kids, child, child_ids, stats)
        else:
            conn.execute(f'update "{child}" set "{col}" = NULL where "{col}" in ({marks})', ids)
    n = conn.execute(f'delete from "{table}" where "{pk}" in ({marks})', ids).rowcount
    stats[table] = stats.get(table, 0) + n


def role_listing(conn):
    return conn.execute("""
        select r.name, coalesce(o.type, '-'), u.email from users u
        left join user_roles ur on ur.user_id = u.id left join roles r on r.id = ur.role_id
        left join organizations o on o.id = ur.organization_id order by r.name, o.type, u.email""").fetchall()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True, help="path to a SQLite database file")
    ap.add_argument("--yes", action="store_true", help="actually delete (without it, only shows what would happen)")
    ap.add_argument("--allow-main", action="store_true", help="allow wifisense.db (the project's main database)")
    a = ap.parse_args()
    path = os.path.abspath(a.db)
    if not os.path.isfile(path):
        sys.exit(f"{path} is not a file")
    if os.path.basename(path).lower() == "wifisense.db" and not a.allow_main:
        sys.exit("Refusing to modify wifisense.db (the main database). Use a copy, or pass --allow-main if you really mean it.")

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = OFF")
    users = {r[1]: r[0] for r in conn.execute("select id, email from users")}
    missing = [e for e in KEEP.values() if e not in users]
    if missing:
        sys.exit(f"These users to keep do not exist in the database: {missing}")
    keep_ids = {users[e] for e in KEEP.values()}
    drop = [(uid, email) for email, uid in users.items() if uid not in keep_ids]
    print(f"{len(users)} users now; keeping {len(keep_ids)}, removing {len(drop)}:")
    for uid, email in sorted(drop, key=lambda x: x[1]):
        print("  remove", email)
    if not a.yes:
        print("\nDry run only. Add --yes to apply (a backup is written first).")
        return

    backup = f"{path}.before_user_cleanup_{time.strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, backup)
    print("backup:", backup)

    kids = build_children(conn)
    stats = {}
    baseline = set(conn.execute("PRAGMA foreign_key_check").fetchall())   # problems that existed before this tool ran
    try:
        conn.execute("BEGIN")
        delete_rows(conn, kids, "users", [uid for uid, _ in drop], stats)
        left = role_listing(conn)
        keys = [(r[0], r[1]) for r in left]
        assert len(left) == len(KEEP) and len(set(keys)) == len(keys), f"expected one user per role, got {left}"
        new_bad = set(conn.execute("PRAGMA foreign_key_check").fetchall()) - baseline
        assert not new_bad, f"this cleanup left dangling references: {sorted(new_bad)[:5]}"
        if baseline:
            print(f"note: {len(baseline)} dangling reference(s) already existed before the cleanup and were left alone")
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
        assert ok == "ok", ok
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        sys.exit(f"ROLLED BACK, nothing changed: {exc}")
    print("rows removed per table:", {k: v for k, v in sorted(stats.items())})
    print("\nremaining users:")
    for role, ctx, email in role_listing(conn):
        print(f"  {role:18s} {ctx:10s} {email}")
    conn.close()


if __name__ == "__main__":
    main()
