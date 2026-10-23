"""
DEMO SEED PROFILE TEST (in-process, throwaway database)
=======================================================
SEED_PROFILE=minimal keeps one user per role and removes everything that depended on the others; SEED_PASSWORD replaces the
well-known demo passwords; production refuses to seed demo accounts without a strong SEED_PASSWORD.
"""
import os
import sys
import tempfile

SECRET = "Demo-Only-Strong-Pass-2026"
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="seed_profile_"), "t.db").replace("\\", "/")
os.environ["SEED_PROFILE"] = "minimal"
os.environ["SEED_PASSWORD"] = SECRET

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.entities import User, UserRole  # noqa: E402

EXPECTED = {"blesson@wifisense.com", "elizabeth@wifisense.com", "abhinand@wifisense.com", "mary@wifisense.com",
            "tomy@wifisense.com", "mathew.varghese@wifisense.com", "john@wifisense.com"}


def run():
    with TestClient(app) as client:
        with Session(engine) as s:
            emails = {u.email for u in s.exec(select(User)).all()}
            assert emails == EXPECTED, emails ^ EXPECTED
            roles = s.exec(select(UserRole)).all()
            assert len(roles) == 7, len(roles)
            orphans = s.execute(text("select count(*) from user_roles where user_id not in (select id from users)")).scalar()
            assert orphans == 0
            assert s.execute(text("select count(*) from family_connections where family_user_id not in (select id from users)")).scalar() == 0
            assert s.execute(text("select count(*) from residents")).scalar() > 0, "residents and rooms must be kept"
        print("[PASS] exactly the 7 demo users remain, no dangling role or family rows, residents untouched")

        for email in sorted(EXPECTED):
            r = client.post("/auth/login", json={"email": email, "password": SECRET})
            assert r.status_code == 200, (email, r.text)
        old = client.post("/auth/login", json={"email": "blesson@wifisense.com", "password": "blessonpassword"})
        assert old.status_code in (400, 401), old.status_code
        print("[PASS] every remaining account logs in with SEED_PASSWORD; the well-known password no longer works")

    # production guard (a new Settings() reads the environment)
    from app.core.config import Settings
    saved = dict(os.environ)
    try:
        os.environ.update({"ENVIRONMENT": "production", "SECRET_KEY": "x" * 40, "DATABASE_URL": "postgresql://u:p@h/db",
                           "PAYMENT_WEBHOOK_SECRET": "y" * 20, "SEED_DEMO_DATA": "1", "SEED_PASSWORD": ""})
        try:
            Settings()
            raise AssertionError("production must refuse to seed demo accounts without SEED_PASSWORD")
        except RuntimeError as exc:
            assert "SEED_PASSWORD" in str(exc)
        os.environ["SEED_PASSWORD"] = "short"
        try:
            Settings()
            raise AssertionError("a short SEED_PASSWORD must be refused")
        except RuntimeError:
            pass
        os.environ["SEED_PASSWORD"] = SECRET
        Settings()
        os.environ["SEED_PASSWORD"] = ""
        os.environ["SEED_DEMO_DATA"] = "0"
        Settings()
        os.environ["SEED_PROFILE"] = "bogus"
        try:
            Settings()
            raise AssertionError("an unknown SEED_PROFILE must be refused")
        except RuntimeError:
            pass
    finally:
        os.environ.clear()
        os.environ.update(saved)
    print("[PASS] production refuses demo seeding without a strong SEED_PASSWORD (or SEED_DEMO_DATA=0); bad profile refused")


if __name__ == "__main__":
    print("=== DEMO SEED PROFILE TEST ===")
    try:
        run()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
    print("\nALL SEED PROFILE TESTS PASSED")
