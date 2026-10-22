"""
Family subscription lifecycle tests (SANDBOX payment provider).

Runs against a live seeded server (API_BASE, default http://127.0.0.1:8000) using the same DATABASE_URL, and the SAME
PAYMENT_WEBHOOK_SECRET as the server (export it for both; outside production a server without one picks a random
secret that the test cannot know).

What is checked: checkout needs an approved connection; signed webhooks (missing / forged / stale signature refused);
idempotency; amount and checkout validation; a checkout completes once; renewal; cancellation at period end and resume;
past due, grace and expiry; an administrator hold that a payment cannot lift; staff scope; emergency visibility that never
depends on a subscription; no payment details stored; audit attribution.
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import timedelta

from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.core.timeutil import as_utc, utcnow
from app.models.entities import (
    Alert, AuditLog, FamilyConnection, FamilySubscription, PaymentEvent, RefreshToken, Resident, User, UserRole,
)
from app.services.payments import sandbox, signing

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


def call(endpoint, method="GET", data=None, token=None, raw=None, headers=None):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(f"{API_BASE}{endpoint}", data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            txt = resp.read().decode()
            return resp.status, json.loads(txt) if txt else None
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


def login(email, password):
    st, res = call("/auth/login", "POST", {"email": email, "password": password})
    assert st == 200, f"login failed {email}: {st} {res}"
    return res["access_token"]


def post_event(event_type, data, created=None, event_id=None, header=None, tamper=False):
    body, sig = sandbox.build_signed_event(event_type, data, created=created, event_id=event_id)
    if tamper:
        body = body.replace(b"payment", b"paymenX", 1)
    return call("/payments/webhooks/sandbox", "POST", raw=body, headers={"X-Sandbox-Signature": sig if header is None else header})


def db_sub(sub_id):
    with Session(engine) as s:
        row = s.get(FamilySubscription, sub_id)
        s.expunge(row)
        return row


def set_sub(sub_id, **fields):
    with Session(engine) as s:
        row = s.get(FamilySubscription, sub_id)
        for k, v in fields.items():
            setattr(row, k, v)
        s.add(row)
        s.commit()


def run_tests():
    print("=== RUNNING FAMILY SUBSCRIPTION (SANDBOX) TESTS ===")
    assert os.getenv("PAYMENT_WEBHOOK_SECRET") or settings.PAYMENT_WEBHOOK_SECRET, "PAYMENT_WEBHOOK_SECRET must be set"
    stamp = str(int(time.time()))
    pw = "FamilyTestPass#1"
    staff = login("anjali@wifisense.com", "anjalipassword")           # elder-care facility manager
    corp_fm = login("abhinand@wifisense.com", "abhinandpassword")      # corporate organization
    sysadmin = login("blesson@wifisense.com", "blessonpassword")

    with Session(engine) as s:
        mary = next(r for r in s.exec(select(Resident)).all() if r.first_name == "Mary")
        mary_id, mary_room = mary.id, mary.room_id

    users, alerts = [], []
    try:
        def new_family(tag):
            email = f"fam_{tag}_{stamp}@example.com"
            st, res = call("/auth/register", "POST", {"email": email, "password": pw, "first_name": "Fam", "last_name": tag})
            assert st == 201, (st, res)
            users.append(res["id"])
            return res["id"], login(email, pw)

        uid1, fam1 = new_family("one")
        uid2, fam2 = new_family("two")          # never gets a connection

        # -------------------------------------------------------------- 1. checkout needs an approved connection
        print("\n--- 1. Checkout requires an approved connection ---")
        st, res = call("/payments/checkout", "POST", token=fam1)
        assert st == 403, (st, res)
        with Session(engine) as s:
            s.add(FamilyConnection(resident_id=mary_id, family_user_id=uid1, relationship="Son", status="pending"))
            s.commit()
        st, res = call("/payments/checkout", "POST", token=fam1)
        assert st == 403, "a PENDING connection must not allow checkout"
        with Session(engine) as s:
            c = s.exec(select(FamilyConnection).where(FamilyConnection.family_user_id == uid1)).first()
            c.status = "approved"
            c.approved_at = utcnow()
            s.add(c)
            s.commit()
        print("[PASS] No connection or a pending one: checkout refused (403). Paying cannot create access.")

        st, res = call("/payments/subscription", token=fam1)
        assert st == 200 and res["mode"] == "SANDBOX" and "No real money" in res["sandbox_notice"] and res["subscription"] is None, res
        print("[PASS] Every payments response is labelled SANDBOX.")

        # -------------------------------------------------------------- 2. before paying: optional features off, emergency on
        print("\n--- 2. Before paying ---")
        st, rs = call("/family/resident-status", token=fam1)
        assert st == 200 and rs["linked"] and rs["has_active_subscription"] is False, rs
        assert rs["emergency"]["available_without_subscription"] is True and "presence_status" not in rs, rs
        print("[PASS] Not subscribed: optional features gated, emergency block present.")

        # -------------------------------------------------------------- 3. checkout
        print("\n--- 3. Checkout ---")
        st, res = call("/payments/checkout", "POST", token=fam1)
        assert st == 201 and res["subscription"]["status"] == "PENDING", (st, res)
        sub_id = res["subscription"]["id"]
        checkout_id = res["checkout"]["id"]
        price = res["plan"]
        assert res["checkout"]["mode"] == "SANDBOX" and price["amount_minor"] == settings.CARE_MONTHLY_PRICE_MINOR
        st, _ = call(f"/payments/sandbox/checkout/{checkout_id}/complete", "POST", {"outcome": "success"}, token=fam2)
        assert st == 404, "another user must not complete my checkout"
        st, _ = call(f"/payments/sandbox/checkout/{checkout_id}/complete", "POST", {"outcome": "success"}, token=staff)
        assert st == 403, "staff cannot use family sandbox controls"
        print(f"[PASS] Checkout started (PENDING, {price['amount_minor']} {price['currency']} minor units). Not completable by others.")

        # -------------------------------------------------------------- 4. webhook authenticity
        print("\n--- 4. Webhook signatures ---")
        good = {"subscription_ref": sub_id, "checkout_id": checkout_id, "provider_subscription_id": "sbx_sub_x",
                "amount_minor": price["amount_minor"], "currency": price["currency"]}
        body, sig = sandbox.build_signed_event("payment.succeeded", good)
        st, _ = call("/payments/webhooks/sandbox", "POST", raw=body)
        assert st == 400, "no signature header must be refused"
        st, _ = post_event("payment.succeeded", good, header=f"t={int(time.time())},v1=abc")
        assert st == 400, "forged signature must be refused"
        st, _ = post_event("payment.succeeded", good, tamper=True)
        assert st == 400, "body changed after signing must be refused"
        old_ts = int(time.time()) - 3600
        st, _ = post_event("payment.succeeded", good, header=signing.sign(settings.PAYMENT_WEBHOOK_SECRET, body, old_ts))
        assert st == 400, "a correctly signed but old request (replay) must be refused"
        wrong_secret = signing.sign("not-the-secret", body)
        st, _ = call("/payments/webhooks/sandbox", "POST", raw=body, headers={"X-Sandbox-Signature": wrong_secret})
        assert st == 400
        assert db_sub(sub_id).status == "PENDING"
        print("[PASS] Missing / forged / tampered / replayed-old / wrong-secret webhooks: all 400, subscription unchanged.")
        assert signing.verify("k", b"x", signing.sign("k", b"x") + ",v1=00", 300) > 0
        print("[PASS] Signature check unit: extra v1 values (key rotation) accepted when one matches.")

        # -------------------------------------------------------------- 5. validation of genuine, signed events
        print("\n--- 5. Signed but invalid events ---")
        st, r = post_event("payment.succeeded", {**good, "amount_minor": 1})
        assert st == 200 and r["outcome"] == "REJECTED_AMOUNT_MISMATCH", r
        st, r = post_event("payment.succeeded", {**good, "currency": "USD"})
        assert r["outcome"] == "REJECTED_AMOUNT_MISMATCH", r
        st, r = post_event("payment.succeeded", {**good, "checkout_id": "sbx_cs_other"})
        assert r["outcome"] == "REJECTED_UNKNOWN_CHECKOUT", r
        st, r = post_event("payment.succeeded", {**good, "subscription_ref": "no-such-subscription"})
        assert r["outcome"] == "REJECTED_UNKNOWN_SUBSCRIPTION", r
        st, r = post_event("invoice.something_new", {"subscription_ref": sub_id})
        assert r["outcome"] == "IGNORED_UNKNOWN_TYPE", r
        assert db_sub(sub_id).status == "PENDING"
        print("[PASS] Wrong amount, wrong currency, foreign checkout, unknown subscription, unknown type: none activate anything.")

        # -------------------------------------------------------------- 6. failed payment then success
        print("\n--- 6. Payment outcomes ---")
        st, res = call(f"/payments/sandbox/checkout/{checkout_id}/complete", "POST", {"outcome": "failure"}, token=fam1)
        assert st == 200 and res["subscription"]["status"] == "PENDING" and res["subscription"]["last_payment_status"] == "FAILED", res
        print("[PASS] Failed first payment: stays PENDING, failure recorded.")
        st, res = call(f"/payments/sandbox/checkout/{checkout_id}/complete", "POST", {"outcome": "success"}, token=fam1)
        sub = res["subscription"]
        assert st == 200 and sub["status"] == "ACTIVE" and sub["entitled"] and res["webhook_outcome"] == "PROCESSED", res
        t0, t1 = sub["current_period_start"], sub["current_period_end"]
        days = (as_utc(db_sub(sub_id).end_date) - as_utc(db_sub(sub_id).start_date)).days
        assert days == settings.SUBSCRIPTION_PERIOD_DAYS, days
        print(f"[PASS] Successful payment (arrived as a signed webhook): ACTIVE, paid period {days} days.")

        st, rs = call("/family/resident-status", token=fam1)
        assert rs["has_active_subscription"] and rs["subscription_status"] == "ACTIVE" and "presence_status" in rs, rs
        print("[PASS] Optional features unlocked and resident-status reports the REAL status.")

        st, r = call(f"/payments/sandbox/checkout/{checkout_id}/complete", "POST", {"outcome": "success"}, token=fam1)
        assert st == 404, "a completed checkout no longer exists for the sandbox"
        prov = db_sub(sub_id).provider_subscription_id
        st, r = post_event("payment.succeeded", {**good, "provider_subscription_id": prov})
        assert r["outcome"] == "REJECTED_UNKNOWN_CHECKOUT", "a checkout can complete only once"
        print("[PASS] A checkout completes once; replaying it with a new event id is rejected.")

        # -------------------------------------------------------------- 7. idempotency + ordering + renewal
        print("\n--- 7. Idempotency, ordering, renewal ---")
        end_before = as_utc(db_sub(sub_id).end_date)
        renew = {"subscription_ref": sub_id, "provider_subscription_id": prov, "amount_minor": price["amount_minor"], "currency": price["currency"]}
        st, r = post_event("payment.succeeded", renew, event_id=f"evt_renew_{stamp}")
        assert r["outcome"] == "PROCESSED", r
        end_after = as_utc(db_sub(sub_id).end_date)
        assert (end_after - end_before).days == settings.SUBSCRIPTION_PERIOD_DAYS, (end_before, end_after)
        st, r = post_event("payment.succeeded", renew, event_id=f"evt_renew_{stamp}")
        assert r["outcome"] == "DUPLICATE" and as_utc(db_sub(sub_id).end_date) == end_after
        print("[PASS] Renewal extends the period by one period; the same event id again changes nothing (DUPLICATE).")
        st, r = post_event("payment.failed", {"subscription_ref": sub_id, "provider_subscription_id": prov},
                           created=int(time.time()) - 86400, event_id=f"evt_old_{stamp}")
        assert r["outcome"] == "IGNORED_STALE" and db_sub(sub_id).status == "ACTIVE", r
        print("[PASS] An older event arriving late is ignored (IGNORED_STALE).")

        # -------------------------------------------------------------- 8. cancel at period end, resume
        print("\n--- 8. Cancellation at period end ---")
        st, res = call("/payments/cancel", "POST", token=fam1)
        sub = res["subscription"]
        assert st == 200 and sub["status"] == "ACTIVE" and sub["cancel_at_period_end"] and sub["entitled"], res
        assert sub["actions"]["can_resume"] and not sub["actions"]["can_cancel"] and sub["renewal_date"] is None
        st, rs = call("/family/resident-status", token=fam1)
        assert rs["has_active_subscription"], "cancelled-at-period-end keeps features until the paid period ends"
        st, res2 = call("/payments/cancel", "POST", token=fam1)
        assert st == 200 and res2["subscription"]["cancelled_at"] == sub["cancelled_at"], "cancel is idempotent"
        print("[PASS] Cancel: stays ACTIVE and entitled until the period end; no renewal date; repeat is a no-op.")
        st, res = call("/payments/resume", "POST", token=fam1)
        assert st == 200 and not res["subscription"]["cancel_at_period_end"] and res["subscription"]["renewal_date"], res
        st, res = call("/payments/resume", "POST", token=fam1)
        assert st == 409
        call("/payments/cancel", "POST", token=fam1)
        print("[PASS] Resume undoes it (and only when there is something to resume).")

        set_sub(sub_id, end_date=utcnow() - timedelta(hours=1))        # the paid period has now ended
        st, res = call("/payments/subscription", token=fam1)
        assert res["subscription"]["status"] == "CANCELLED" and not res["subscription"]["entitled"], res
        st, rs = call("/family/resident-status", token=fam1)
        assert rs["has_active_subscription"] is False and rs["subscription_status"] == "CANCELLED" and "emergency" in rs, rs
        print("[PASS] After the period end: CANCELLED, optional features off, emergency block still present.")

        # -------------------------------------------------------------- 9. subscribe again, past due, grace, expiry
        print("\n--- 9. Past due, grace, expiry ---")
        st, res = call("/payments/checkout", "POST", token=fam1)
        assert st == 201, res
        checkout2 = res["checkout"]["id"]
        st, res = call(f"/payments/sandbox/checkout/{checkout2}/complete", "POST", {"outcome": "success"}, token=fam1)
        assert res["subscription"]["status"] == "ACTIVE" and not res["subscription"]["cancel_at_period_end"], res
        st, res = call("/payments/sandbox/simulate", "POST", {"event": "renewal_failed"}, token=fam1)
        sub = res["subscription"]
        assert sub["status"] == "PAST_DUE" and sub["entitled"] and sub["grace_until"], res
        print("[PASS] Resubscribe works; a failed renewal gives PAST_DUE with a visible grace period (still entitled).")
        set_sub(sub_id, past_due_since=utcnow() - timedelta(days=settings.SUBSCRIPTION_GRACE_DAYS + 2),
                end_date=utcnow() - timedelta(days=settings.SUBSCRIPTION_GRACE_DAYS + 2))
        st, res = call("/payments/subscription", token=fam1)
        assert res["subscription"]["status"] == "EXPIRED" and not res["subscription"]["entitled"], res
        print("[PASS] Grace ended without payment: EXPIRED, not entitled.")

        # -------------------------------------------------------------- 10. emergency access independent of subscription
        print("\n--- 10. Emergency visibility ---")
        with Session(engine) as s:
            a = Alert(room_id=mary_room, event_type="POSSIBLE_FALL", severity="CRITICAL", status="new", source="simulated",
                      message=f"Possible fall - verification required (test {stamp})")
            low = Alert(room_id=mary_room, event_type="NOTE", severity="LOW", status="new", source="simulated", message=f"low {stamp}")
            s.add(a)
            s.add(low)
            s.commit()
            alerts += [a.id, low.id]
            crit_id = a.id
        st, em = call("/family/emergency-status", token=fam1)
        ids = [x["id"] for x in em["emergency"]["open_alerts"]]
        assert st == 200 and crit_id in ids and low.id not in ids, em
        st, rs = call("/family/resident-status", token=fam1)
        assert rs["has_active_subscription"] is False and crit_id in [x["id"] for x in rs["emergency"]["open_alerts"]], rs
        print("[PASS] EXPIRED subscription: the open CRITICAL alert is still visible (only HIGH/CRITICAL are shown).")
        st, _ = call("/family/emergency-status", token=fam2)
        assert st == 403, "no approved connection: no emergency information"
        print("[PASS] Emergency view needs an approved connection: the unconnected family user is refused (403). A subscription never grants it.")

        # -------------------------------------------------------------- 11. administrator hold
        print("\n--- 11. Administrator hold ---")
        st, res = call("/payments/checkout", "POST", token=fam1)
        checkout3 = res["checkout"]["id"]
        call(f"/payments/sandbox/checkout/{checkout3}/complete", "POST", {"outcome": "success"}, token=fam1)
        assert db_sub(sub_id).status == "ACTIVE"
        st, _ = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "SUSPENDED"}, token=fam1)
        assert st == 403, "family cannot change subscription status"
        st, _ = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "SUSPENDED"}, token=corp_fm)
        assert st == 403, "corporate staff cannot"
        for bad in ("PAID", "CANCELLED", "EXPIRED"):
            st, _ = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": bad}, token=staff)
            assert st == 422, (bad, st)
        st, _ = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "ACTIVE"}, token=staff)
        assert st == 409, "staff cannot mark a subscription active without a hold to lift"
        st, res = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "SUSPENDED"}, token=staff)
        assert st == 200 and res["status"] == "SUSPENDED", res
        print("[PASS] Staff can suspend; family / corporate staff cannot; staff cannot mark anything paid or active directly.")

        st, res = call("/payments/checkout", "POST", token=fam1)
        assert st == 409, "no checkout while on hold"
        st, res = call("/payments/sandbox/simulate", "POST", {"event": "renewal_succeeded"}, token=fam1)
        assert res["webhook_outcome"] == "HELD_BY_ADMIN" and res["subscription"]["status"] == "SUSPENDED", res
        st, rs = call("/family/resident-status", token=fam1)
        assert rs["has_active_subscription"] is False and rs["subscription_status"] == "SUSPENDED" and "emergency" in rs
        print("[PASS] A payment while suspended is recorded but does NOT lift the hold; emergency block still present.")
        st, res = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "ACTIVE"}, token=staff)
        assert st == 200 and res["status"] == "ACTIVE", res
        set_sub(sub_id, status="SUSPENDED", end_date=utcnow() - timedelta(days=1))
        st, res = call(f"/family/subscriptions/{sub_id}", "PATCH", {"status": "ACTIVE"}, token=staff)
        assert res["status"] == "EXPIRED", "lifting a hold must not grant unpaid time"
        print("[PASS] Lifting a hold restores only what was paid for.")

        # -------------------------------------------------------------- 12. visibility and RBAC of the payment APIs
        print("\n--- 12. Access control of payment APIs ---")
        st, evs = call("/payments/events", token=staff)
        assert st == 200 and any(e["subscription_id"] == sub_id for e in evs), "facility staff see their own organization's events"
        assert call("/payments/events", token=fam1)[0] == 403
        st, evs_c = call("/payments/events", token=corp_fm)
        assert st == 403 or all(e["subscription_id"] != sub_id for e in evs_c), "other organizations must not see these events"
        assert call("/payments/maintenance/reconcile", "POST", token=staff)[0] == 403
        assert call("/payments/maintenance/reconcile", "POST", token=sysadmin)[0] == 200
        assert call("/payments/subscription", token=staff)[0] == 403
        st, subs = call("/family/subscriptions", token=corp_fm)
        assert st == 403
        st, subs = call("/family/subscriptions", token=fam2)
        assert st == 200 and subs == [], "a family user sees only their own subscriptions"
        print("[PASS] Family cannot read events or reconcile; staff are scoped; corporate staff refused; users see only their own subscription.")

        # -------------------------------------------------------------- 13. nothing resembling payment details stored
        print("\n--- 13. No payment details stored ---")
        st, r = post_event("payment.succeeded", {**renew, "card_number": "4242424242424242", "cvv": "123"}, event_id=f"evt_card_{stamp}")
        with Session(engine) as s:
            ev = s.exec(select(PaymentEvent).where(PaymentEvent.event_id == f"evt_card_{stamp}")).first()
            stored = json.dumps(ev.summary)
        assert "4242" not in stored and "cvv" not in stored and set(ev.summary) <= {"type", "subscription_ref", "amount_minor", "currency", "created"}, stored
        cols = {c.name for t in (FamilySubscription.__table__, PaymentEvent.__table__) for c in t.columns}
        assert not {c for c in cols if any(w in c for w in ("card", "cvv", "pan", "iban", "account_number"))}, cols
        print("[PASS] Stored event summary is whitelisted; no card-like columns exist in the subscription tables.")

        # -------------------------------------------------------------- 14. audit attribution
        print("\n--- 14. Audit trail ---")
        with Session(engine) as s:
            rows = s.exec(select(AuditLog).where(AuditLog.resource_id == sub_id)).all()
            actions = {r.what_action for r in rows}
            assert {"SUBSCRIPTION_CHECKOUT_STARTED", "PAYMENT_SUCCEEDED", "SUBSCRIPTION_CANCEL_REQUESTED"} <= actions, actions
            assert all(r.organization_id for r in rows), "every subscription audit row must belong to an organization"
            rej = s.exec(select(AuditLog).where(AuditLog.what_action == "PAYMENT_WEBHOOK_REJECTED").order_by(AuditLog.created_at.desc())).first()
            assert rej and rej.result == "DENIED"
        print("[PASS] Audit rows exist, are organization-attributed, and rejected webhooks are logged as DENIED.")

        # -------------------------------------------------------------- 15. Production gating of sandbox simulation
        print("\n--- 15. Production gating of sandbox simulation ---")
        from fastapi import HTTPException
        from app.core.config import Settings
        from app.routers import payments as pay
        from app.services.payments.signing import WebhookError
        from app.services.payments.webhooks import handle_webhook

        # (a) Settings environment configuration resolution
        saved_env = os.environ.copy()
        try:
            # 1. Default in non-production: True
            os.environ["ENVIRONMENT"] = "development"
            os.environ.pop("PAYMENTS_SANDBOX_SIMULATOR_ENABLED", None)
            s_dev = Settings()
            assert s_dev.PAYMENTS_SANDBOX_SIMULATOR_ENABLED is True, "Must default to True outside production"

            # 2. Default in production: False
            os.environ["ENVIRONMENT"] = "production"
            os.environ["SECRET_KEY"] = "prod-test-secret-at-least-32-chars-long-123456"
            os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
            os.environ.pop("PAYMENTS_SANDBOX_SIMULATOR_ENABLED", None)
            s_prod = Settings()
            assert s_prod.PAYMENTS_SANDBOX_SIMULATOR_ENABLED is False, "Must default to False when ENVIRONMENT=production"

            # 3. Explicit opt-in in production: True
            os.environ["PAYMENTS_SANDBOX_SIMULATOR_ENABLED"] = "true"
            s_prod_opt = Settings()
            assert s_prod_opt.PAYMENTS_SANDBOX_SIMULATOR_ENABLED is True, "Explicit opt-in must enable simulator in production"
        finally:
            os.environ.clear()
            os.environ.update(saved_env)

        # (b) Endpoint gating when PAYMENTS_SANDBOX_SIMULATOR_ENABLED is False
        orig_sim_enabled = settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED
        orig_mode = settings.PAYMENTS_MODE
        try:
            settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED = False
            # 1. _sandbox_only() raises 404
            try:
                pay._sandbox_only()
                raise AssertionError("_sandbox_only must raise 404 when simulator is disabled")
            except HTTPException as exc:
                assert exc.status_code == 404

            # 2. POST /payments/checkout handler returns 404
            with Session(engine) as s:
                fam_u = s.get(User, uid1)
                try:
                    pay.start_checkout(session=s, current_user=fam_u)
                    raise AssertionError("start_checkout must return 404 when simulator is disabled")
                except HTTPException as exc:
                    assert exc.status_code == 404

            # 3. POST /payments/sandbox/checkout/{id}/complete handler returns 404
            with Session(engine) as s:
                fam_u = s.get(User, uid1)
                try:
                    pay.sandbox_complete_checkout("sbx_cs_test", pay.SandboxComplete(outcome="success"), session=s, current_user=fam_u)
                    raise AssertionError("sandbox_complete_checkout must return 404 when simulator is disabled")
                except HTTPException as exc:
                    assert exc.status_code == 404

            # 4. POST /payments/sandbox/simulate handler returns 404
            with Session(engine) as s:
                fam_u = s.get(User, uid1)
                try:
                    pay.sandbox_simulate(pay.SandboxSimulate(event="renewal_succeeded"), session=s, current_user=fam_u)
                    raise AssertionError("sandbox_simulate must return 404 when simulator is disabled")
                except HTTPException as exc:
                    assert exc.status_code == 404

            # (c) Signed webhook verification is unchanged when simulator is disabled
            # Webhook signature rejection with current timestamp: must fail specifically for signature mismatch
            test_body, _ = sandbox.build_signed_event("payment.succeeded", {"test": 1})
            curr_ts = int(time.time())
            with Session(engine) as s:
                try:
                    handle_webhook(s, test_body, f"t={curr_ts},v1=invalidsig")
                    raise AssertionError("Webhook with forged signature must be rejected")
                except WebhookError as exc:
                    assert exc.reason == "signature mismatch", f"Expected 'signature mismatch', got {exc.reason}"

                # Stale timestamp: must fail specifically for tolerance window
                stale_ts = curr_ts - 3600
                stale_header = signing.sign(settings.PAYMENT_WEBHOOK_SECRET, test_body, stale_ts)
                try:
                    handle_webhook(s, test_body, stale_header)
                    raise AssertionError("Webhook with stale timestamp must be rejected")
                except WebhookError as exc:
                    assert exc.reason == "timestamp outside the tolerance window", f"Expected 'timestamp outside the tolerance window', got {exc.reason}"

            # Webhook endpoints via HTTP over the server process
            st_rej, _ = post_event("payment.succeeded", {}, header=f"t={int(time.time())},v1=invalidsig")
            assert st_rej == 400, "POST /payments/webhooks/sandbox must reject invalid signatures even when simulator is disabled"

            # Valid webhook delivery still works
            with Session(engine) as s:
                sub_row = s.get(FamilySubscription, sub_id)
                prov_id = sub_row.provider_subscription_id
            st_ok, r_ok = post_event("payment.succeeded", {
                "subscription_ref": sub_id,
                "provider_subscription_id": prov_id,
                "amount_minor": 49900,
                "currency": "INR"
            })
            assert st_ok == 200 and r_ok.get("received") is True, "Valid signed webhook must be accepted"

            # (d) Explicit opt-in enables the simulation endpoints
            settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED = True
            # Now _sandbox_only does not raise
            pay._sandbox_only()

            # When PAYMENTS_MODE is not sandbox, _sandbox_only raises 404
            settings.PAYMENTS_MODE = "disabled"
            try:
                pay._sandbox_only()
                raise AssertionError("_sandbox_only must raise 404 when PAYMENTS_MODE != sandbox")
            except HTTPException as exc:
                assert exc.status_code == 404
        finally:
            settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED = orig_sim_enabled
            settings.PAYMENTS_MODE = orig_mode

        print("[PASS] Production gating: 404 when disabled, explicit opt-in enables, webhook verification unchanged.")

        print("\n=== ALL FAMILY SUBSCRIPTION TESTS PASSED ===")
    finally:
        print("\n--- Cleanup ---")
        with Session(engine) as s:
            for aid in alerts:
                row = s.get(Alert, aid)
                if row:
                    s.delete(row)
            for uid in users:
                sub = s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == uid)).first()
                if sub:
                    for ev in s.exec(select(PaymentEvent).where(PaymentEvent.subscription_id == sub.id)).all():
                        s.delete(ev)
                    s.delete(sub)
                for c in s.exec(select(FamilyConnection).where(FamilyConnection.family_user_id == uid)).all():
                    s.delete(c)
                for t in s.exec(select(RefreshToken).where(RefreshToken.user_id == uid)).all():
                    s.delete(t)
                for ur in s.exec(select(UserRole).where(UserRole.user_id == uid)).all():
                    s.delete(ur)
                u = s.get(User, uid)
                if u:
                    s.delete(u)
            s.commit()
        print("Cleaned up test users, subscriptions, connections and alerts.")


if __name__ == "__main__":
    run_tests()
