"""
HEALTH ENDPOINT TEST (in-process, throwaway database)
=====================================================
GET /health is public so hosting platforms can use it, and must reveal nothing sensitive: only whether the database answers,
whether the detection model loaded, the payment mode and the environment name.
"""
import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="health_test_"), "t.db").replace("\\", "/")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def run():
    with TestClient(app) as client:
        r = client.get("/health")
        body = r.json()
        assert r.status_code == 200 and body["status"] == "ok", (r.status_code, body)
        assert body["database"] == "ok" and body["detection_model"] == "loaded" and body["payments_mode"] == "sandbox", body
        assert set(body) == {"status", "database", "detection_model", "payments_mode", "environment"}, f"unexpected fields: {set(body)}"
        blob = r.text.lower()
        for secret_word in ("secret", "password", "token", "key", "sqlite", "postgres"):
            assert secret_word not in blob, f"/health must not mention {secret_word!r}"
        print("[PASS] /health is public, reports database, detection model and payment mode, and exposes nothing sensitive")


if __name__ == "__main__":
    print("=== HEALTH TEST ===")
    try:
        run()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
    print("\nALL HEALTH TESTS PASSED")
