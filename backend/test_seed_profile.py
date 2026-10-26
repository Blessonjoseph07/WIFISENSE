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
            "tomy@wifisense.com", "mathew.varghese@wifisense.com", "john@wifisense.com", "payer@wifisense.com"}


def run():
    with TestClient(app) as client:
        with Session(engine) as s:
            emails = {u.email for u in s.exec(select(User)).all()}
            assert emails == EXPECTED, emails ^ EXPECTED
            roles = s.exec(select(UserRole)).all()
            assert len(roles) == 8, len(roles)
            orphans = s.execute(text("select count(*) from user_roles where user_id not in (select id from users)")).scalar()
            assert orphans == 0
            assert s.execute(text("select count(*) from family_connections where family_user_id not in (select id from users)")).scalar() == 0
            assert s.execute(text("select count(*) from residents")).scalar() > 0, "residents and rooms must be kept"
            from app.models.entities import FamilySubscription, Organization
            payer = s.exec(select(User).where(User.email == "payer@wifisense.com")).first()
            assert s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == payer.id)).first() is None, "the payment test account must have no plan"
            assert s.exec(select(Organization).where(Organization.type == "ELDER_CARE")).first().contact_phone, "the care home needs a helpline to show"
        print("[PASS] exactly the 7 role users plus the payment test account remain, no dangling rows, residents untouched, helpline present")

        for email in sorted(EXPECTED):
            r = client.post("/auth/login", json={"email": email, "password": SECRET})
            assert r.status_code == 200, (email, r.text)
        old = client.post("/auth/login", json={"email": "blesson@wifisense.com", "password": "blessonpassword"})
        assert old.status_code in (400, 401), old.status_code
        print("[PASS] every remaining account logs in with SEED_PASSWORD; the well-known password no longer works")

    # A database that already had accounts (migrated, or seeded before SEED_PASSWORD was set or changed): on the next start
    # every demo account must still end up with SEED_PASSWORD, not only the ones created then.
    from app.core.security import hash_password
    with Session(engine) as s:
        for email in ("elizabeth@wifisense.com", "mary@wifisense.com"):
            u = s.exec(select(User).where(User.email == email)).first()
            u.password_hash = hash_password(email.split("@")[0] + "password")
            s.add(u)
        s.commit()
    with TestClient(app) as client:                      # a restart runs the startup hook again (not a first run any more)
        for email in ("elizabeth@wifisense.com", "mary@wifisense.com"):   # few logins: the login rate limit is 15 a minute
            r = client.post("/auth/login", json={"email": email, "password": SECRET})
            assert r.status_code == 200, (email, r.text)
        assert client.post("/auth/login", json={"email": "elizabeth@wifisense.com", "password": "elizabethpassword"}).status_code in (400, 401)
    print("[PASS] after a restart on an existing database, accounts with an old password get SEED_PASSWORD too")

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
