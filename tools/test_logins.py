import urllib.request
import json

creds = [
    ('blesson@wifisense.com', 'blessonpassword'),
    ('mary@wifisense.com', 'marypassword'),
    ('elizabeth@wifisense.com', 'elizabethpassword'),
    ('abhinand@wifisense.com', 'abhinandpassword'),
    ('tomy@wifisense.com', 'tomypassword'),
    ('john@wifisense.com', 'johnpassword'),
]

for email, pwd in creds:
    data = json.dumps({'email': email, 'password': pwd}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/auth/login', data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            out = json.loads(res.read().decode())
            print(f"SUCCESS: {email} | Role: {out.get('role')} | Context: {out.get('application_context')} | User: {out.get('user', {}).get('first_name')}")
    except Exception as e:
        print(f"FAIL: {email} | Error: {e}")
