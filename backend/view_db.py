import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "wifisense.db")

def show_database(filter_table=None):
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    if filter_table:
        tables = [filter_table]
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cur.fetchall()]

    print("=" * 75)
    print(f" DATABASE VIEWER: {os.path.abspath(DB_PATH)}")
    print("=" * 75)
    print(f"Total Tables: {len(tables)}\n")

    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            
            cur.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cur.fetchall()]

            print(f"[*] Table: {table}  (Rows: {count})")
            print(f"    Columns: {', '.join(columns)}")
            
            cur.execute(f"SELECT * FROM {table} LIMIT 4;")
            rows = cur.fetchall()
            if rows:
                for r in rows:
                    formatted_vals = [str(val)[:24] if val is not None else "NULL" for val in r]
                    print(f"    - {formatted_vals}")
            else:
                print("    (Empty table)")
            print("-" * 75)
        except Exception as e:
            print(f"    Error reading table {table}: {e}")

    con.close()

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    show_database(arg)
