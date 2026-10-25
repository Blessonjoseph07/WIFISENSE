import sqlite3
import os

for path in ['backend/wifisense.db', 'wifisense.db', 'backend/hardware_test.db']:
    if os.path.exists(path):
        con = sqlite3.connect(path)
        cur = con.cursor()
        print(f"=== DB: {path} ===")
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("Tables:", tables)
        if 'user' in tables:
            users = cur.execute("SELECT id, email, full_name, role, org_id, is_active FROM user").fetchall()
            print("Users count:", len(users))
            for u in users:
                print("  ", u)
        if 'organization' in tables:
            orgs = cur.execute("SELECT id, name, context_type FROM organization").fetchall()
            print("Organizations:", orgs)
        con.close()
