import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "wifisense.db")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "supabase_data.sql")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

def get_insert_sql(table):
    cur.execute(f"PRAGMA table_info({table});")
    col_infos = cur.fetchall()
    cols = [col[1] for col in col_infos]
    col_types = {col[1]: col[2].upper() for col in col_infos}
    
    cur.execute(f"SELECT * FROM {table};")
    rows = cur.fetchall()
    if not rows:
        return ""
    lines = []
    for r in rows:
        vals = []
        for col_name, val in zip(cols, r):
            col_type = col_types.get(col_name, "")
            if val is None:
                vals.append("NULL")
            elif col_type == "BOOLEAN":
                vals.append("TRUE" if val else "FALSE")
            elif isinstance(val, (int, float)):
                vals.append(str(val))
            else:
                s = str(val).replace("'", "''")
                vals.append(f"'{s}'")
        lines.append(f"({', '.join(vals)})")
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n" + ",\n".join(lines) + ";"
    return sql

order = [
    "activity_types",
    "roles",
    "organizations",
    "buildings",
    "floors",
    "rooms",
    "users",
    "user_roles",
    "caregiver_profiles",
    "residents",
    "health_conditions",
    "sharing_policies",
    "devices",
    "sensing_events",
    "alerts",
    "alert_acknowledgements",
    "access_requests"
]

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for t in order:
        stmt = get_insert_sql(t)
        if stmt:
            f.write(f"-- Table {t}\n{stmt}\n\n")

print(f"Exported {OUTPUT_PATH} successfully")
con.close()
