import json
import urllib.request
import urllib.error
import time

API_BASE = "http://127.0.0.1:8000"

def api_call(endpoint, method="GET", data=None, token=None):
    url = f"{API_BASE}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed

def run_tests():
    print("=== RUNNING PHASE 1 SECURITY & PRODUCTION FOUNDATION TESTS ===")

    # 1. Test Login & Refresh Token Issuance
    print("\n--- 1. Testing Login & Refresh Token Issuance ---")
    status, login_res = api_call("/auth/login", method="POST", data={"email": "blesson@wifisense.com", "password": "blessonpassword"})
    assert status == 200, f"Login failed: {status} {login_res}"
    assert "access_token" in login_res, "Missing access_token"
    assert "refresh_token" in login_res and login_res["refresh_token"] is not None, "Missing refresh_token"
    assert login_res["role"] == "system_admin"
    print("[PASS] Login successfully issued access_token and rotating refresh_token.")
    sys_access = login_res["access_token"]
    sys_refresh = login_res["refresh_token"]

    # 2. Test Refresh Token Rotation
    print("\n--- 2. Testing Refresh Token Rotation ---")
    status, refresh_res = api_call("/auth/refresh", method="POST", data={"refresh_token": sys_refresh})
    assert status == 200, f"Token refresh failed: {status} {refresh_res}"
    assert "access_token" in refresh_res
    assert "refresh_token" in refresh_res
    new_access = refresh_res["access_token"]
    new_refresh = refresh_res["refresh_token"]
    assert new_refresh != sys_refresh, "Refresh token was not rotated to a new secret!"
    print("[PASS] Token refresh rotated to new refresh_token successfully.")

    # 3. Test Refresh Token Reuse Detection
    print("\n--- 3. Testing Refresh Token Reuse Detection ---")
    status, reuse_res = api_call("/auth/refresh", method="POST", data={"refresh_token": sys_refresh})
    assert status == 401, f"Expected 401 on reused refresh token, got {status}: {reuse_res}"
    print("[PASS] Reusing old refresh token was blocked with HTTP 401 (compromised token reuse detection active).")

    # 4. Test Server-side Logout & Access Token Revocation
    print("\n--- 4. Testing Server-side Logout & Revocation List ---")
    # First verify new_access works
    status, me_res = api_call("/auth/me", method="GET", token=new_access)
    assert status == 200, f"GET /auth/me failed: {status}"

    # Now logout
    status, logout_res = api_call("/auth/logout", method="POST", data={"refresh_token": new_refresh}, token=new_access)
    assert status == 200, f"Logout failed: {status} {logout_res}"
    print("[PASS] POST /auth/logout completed successfully.")

    # Verify access token is revoked server-side
    status, me_revoked = api_call("/auth/me", method="GET", token=new_access)
    assert status == 401, f"Expected 401 for revoked access token, got {status}: {me_revoked}"
    print("[PASS] Revoked access token was blocked with HTTP 401 Unauthorized.")

    # 5. Test Audit Logging
    print("\n--- 5. Testing Structured Audit Logging (WHO, WHAT, WHEN, RESOURCE, RESULT) ---")
    # Log back in as sysadmin to inspect audit logs
    status, fresh_login = api_call("/auth/login", method="POST", data={"email": "blesson@wifisense.com", "password": "blessonpassword"})
    assert status == 200
    admin_token = fresh_login["access_token"]

    status, logs = api_call("/auth/audit-logs", method="GET", token=admin_token)
    assert status == 200, f"Failed to fetch audit logs: {status} {logs}"
    assert isinstance(logs, list) and len(logs) > 0, "Expected non-empty audit log list"

    # Verify structured attributes on latest log entry
    latest = logs[0]
    assert "who_user_id" in latest or "who_email" in latest
    assert "what_action" in latest
    assert "resource_type" in latest
    assert "result" in latest
    assert "created_at" in latest

    actions = [log["what_action"] for log in logs]
    assert "AUTH_LOGIN_SUCCESS" in actions, f"AUTH_LOGIN_SUCCESS not in actions: {actions[:5]}"
    assert "AUTH_LOGOUT" in actions, f"AUTH_LOGOUT not in actions: {actions[:5]}"
    print(f"[PASS] Audit logs verified ({len(logs)} entries recorded with full WHO, WHAT, WHEN, RESOURCE, RESULT schema).")

    # 6. Test Production Safeguards (Direct Unit Check)
    print("\n--- 6. Testing Production Safeguards ---")
    from app.core.config import Settings
    import os
    
    old_env = os.environ.get("ENVIRONMENT")
    try:
        os.environ["ENVIRONMENT"] = "production"
        failed = False
        try:
            Settings()
        except RuntimeError as e:
            failed = True
            assert "CRITICAL SECURITY SAFEGUARD" in str(e)
        assert failed, "Production safeguard failed to block hardcoded default secret in production mode!"
        print("[PASS] Production safeguard successfully blocked default credentials in production mode.")
    finally:
        if old_env is not None:
            os.environ["ENVIRONMENT"] = old_env
        else:
            os.environ.pop("ENVIRONMENT", None)

    print("\n>>> ALL PHASE 1 SECURITY & PRODUCTION FOUNDATION TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    run_tests()
