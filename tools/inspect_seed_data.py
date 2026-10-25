import sqlite3

con = sqlite3.connect('backend/wifisense.db')
cur = con.cursor()

print("=== USERS & ROLES ===")
query = """
SELECT u.id, u.email, u.first_name, u.last_name, u.is_active, r.name as role_name, ur.organization_id, o.name as org_name, o.type as org_type
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
LEFT JOIN organizations o ON ur.organization_id = o.id
"""
for r in cur.execute(query).fetchall():
    print(r)

print("\n=== RESIDENTS ===")
for r in cur.execute("SELECT id, full_name, room_id, organization_id, status FROM residents").fetchall():
    print(r)

print("\n=== ROOMS ===")
for r in cur.execute("SELECT id, name, room_type, organization_id FROM rooms").fetchall():
    print(r)

print("\n=== DEVICES ===")
for r in cur.execute("SELECT id, device_code, status, room_id, organization_id FROM devices").fetchall():
    print(r)

print("\n=== ALERTS (Recent 5) ===")
for r in cur.execute("SELECT id, alert_type, severity, status, room_id, resident_id, organization_id, created_at FROM alerts ORDER BY created_at DESC LIMIT 5").fetchall():
    print(r)

con.close()
