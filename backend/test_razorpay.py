"""
RAZORPAY PAYMENTS TEST SUITE (against a FAKE Razorpay)
======================================================
Starts a second copy of the API in PAYMENTS_MODE=razorpay, pointed at a fake Razorpay server run by this test (no internet, no real keys),
sharing the same database as the main test server. Checks the parts that matter for money:

  * the order is created server-side for the plan price, the browser gets only the PUBLIC key id, the secret never appears
  * a wrong signature, an unpaid payment, a payment for another order and a wrong amount never activate anything
  * a correct payment activates the Care Plan once; confirming it again changes nothing
  * an authorized (not yet captured) payment is captured by the server before it is accepted
  * another user cannot confirm someone else's order
  * Razorpay webhooks need a valid signature, activate exactly once and are idempotent
  * live keys are refused unless RAZORPAY_ALLOW_LIVE=1, and the sandbox simulator is off in this mode
"""
import base64
import hashlib
import hmac
import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
import urllib.error
import urllib.request
from datetime import timedelta

from sqlmodel import Session, select

from app.core.database import engine
from app.core.timeutil import utcnow
from app.models.entities import FamilyConnection, FamilySubscription, Resident

KEY_ID, KEY_SECRET, WH_SECRET = "rzp_test_FAKEKEYID01", "fake-key-secret-never-real", "fake-webhook-secret"
PLAN_AMOUNT = int(os.getenv("CARE_MONTHLY_PRICE_MINOR", "49900"))
ORDERS, PAYMENTS, SEEN_AUTH = {}, {}, []
RUN = uuid.uuid4().hex[:8]        # payment ids must be unique per run: the event table remembers every id it has seen


class FakeRazorpay(http.server.BaseHTTPRequestHandler):
    def _json(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        SEEN_AUTH.append(self.headers.get("Authorization"))
        if self.path == "/orders":
            oid = f"order_FAKE{len(ORDERS) + 1:04d}"
            ORDERS[oid] = {"id": oid, "amount": data["amount"], "currency": data["currency"], "status": "created", "notes": data.get("notes", {})}
            return self._json(200, ORDERS[oid])
        if self.path.endswith("/capture") and self.path.startswith("/payments/"):
            pid = self.path.split("/")[2]
            PAYMENTS[pid]["status"] = "captured"
            return self._json(200, PAYMENTS[pid])
        self._json(404, {"error": {"description": "not found"}})

    def do_GET(self):
        SEEN_AUTH.append(self.headers.get("Authorization"))
        if self.path.startswith("/payments/") and self.path.split("/")[2] in PAYMENTS:
            return self._json(200, PAYMENTS[self.path.split("/")[2]])
        self._json(404, {"error": {"description": "payment not found"}})

    def log_message(self, *a):
        pass


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(base, path, method="GET", data=None, token=None, raw=None, headers=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    req = urllib.request.Request(base + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        txt = e.read()
        try:
            return e.code, json.loads(txt or b"null")
        except ValueError:
            return e.code, txt.decode()


def sign_checkout(order_id, payment_id):
    return hmac.new(KEY_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


def pay(order_id, payment_id, status="captured", amount=None, currency="INR", order_ref=None, notes=None):
    PAYMENTS[payment_id] = {"id": payment_id, "order_id": order_ref or order_id, "amount": PLAN_AMOUNT if amount is None else amount,
                            "currency": currency, "status": status, "notes": notes or {}}


def run():
    fake = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeRazorpay)
    threading.Thread(target=fake.serve_forever, daemon=True).start()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, PAYMENTS_MODE="razorpay", RAZORPAY_KEY_ID=KEY_ID, RAZORPAY_KEY_SECRET=KEY_SECRET, RAZORPAY_WEBHOOK_SECRET=WH_SECRET,
               RAZORPAY_API_BASE=f"http://127.0.0.1:{fake.server_address[1]}", PAYMENT_WEBHOOK_SECRET=os.getenv("PAYMENT_WEBHOOK_SECRET", "x" * 24))
    backend = os.path.dirname(os.path.abspath(__file__))
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)], cwd=backend, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    users = []
    try:
        for _ in range(90):
            try:
                if urllib.request.urlopen(base + "/health", timeout=3).status == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            raise AssertionError("the Razorpay-mode server did not start")

        stamp = str(int(time.time()))
        pw = "FamilyTestPass#1"
        with Session(engine) as s:
            mary_id = next(r for r in s.exec(select(Resident)).all() if r.first_name == "Mary").id

        def new_family(tag):
            email = f"rzp_{tag}_{stamp}@example.com"
            st, res = call(base, "/auth/register", "POST", {"email": email, "password": pw, "first_name": "Rzp", "last_name": tag})
            assert st == 201, (st, res)
            users.append(res["id"])
            with Session(engine) as s:
                s.add(FamilyConnection(resident_id=mary_id, family_user_id=res["id"], relationship="Son", status="approved", approved_at=utcnow()))
                s.commit()
            st, tok = call(base, "/auth/login", "POST", {"email": email, "password": pw})
            assert st == 200, tok
            return res["id"], tok["access_token"]

        def sub_of(uid):
            with Session(engine) as s:
                row = s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == uid)).first()
                if row:
                    s.expunge(row)
                return row

        uid_a, fam_a = new_family("a")
        uid_b, fam_b = new_family("b")

        print("--- mode and the sandbox simulator")
        st, info = call(base, "/payments/subscription", token=fam_a)
        assert st == 200 and info["mode"] == "RAZORPAY_TEST" and info["provider"] == "razorpay" and info["simulator_enabled"] is False, info
        assert "TEST MODE" in info["sandbox_notice"] and "never reach this server" in info["sandbox_notice"]
        assert call(base, "/payments/sandbox/simulate", "POST", {"event": "renewal_succeeded"}, fam_a)[0] == 404
        print("[PASS] mode is RAZORPAY_TEST, the notice says so, the sandbox simulator is off")

        print("--- checkout creates a real-shaped order and exposes only the public key")
        st, co = call(base, "/payments/checkout", "POST", token=fam_a)
        c = co["checkout"]
        assert st == 201 and c["provider"] == "razorpay" and c["order_id"].startswith("order_FAKE") and c["key_id"] == KEY_ID, co
        assert c["amount_minor"] == PLAN_AMOUNT and c["currency"] == "INR", c
        assert KEY_SECRET not in json.dumps(co) and WH_SECRET not in json.dumps(co), "a secret leaked into the checkout response"
        assert ORDERS[c["order_id"]]["amount"] == PLAN_AMOUNT and ORDERS[c["order_id"]]["notes"]["subscription_ref"] == sub_of(uid_a).id
        basic = base64.b64decode([a for a in SEEN_AUTH if a][0].split(" ")[1]).decode()
        assert basic == f"{KEY_ID}:{KEY_SECRET}", "the order request must use HTTP basic auth with the key pair"
        order_a = c["order_id"]
        print(f"[PASS] order {order_a} for {PLAN_AMOUNT} paise created server-side; the response holds the public key id and no secret")

        print("--- nothing activates on bad confirmations")
        pay(order_a, "pay_BADSIG_" + RUN)
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_BADSIG_" + RUN, "razorpay_signature": "0" * 64}, fam_a)
        assert st == 400 and "signature" in r["detail"], (st, r)
        pay(order_a, "pay_FAILED_" + RUN, status="failed")
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_FAILED_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_FAILED_" + RUN)}, fam_a)
        assert st == 402 and "not completed" in r["detail"], (st, r)
        pay(order_a, "pay_OTHERORDER_" + RUN, order_ref="order_SOMEONEELSE")
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_OTHERORDER_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_OTHERORDER_" + RUN)}, fam_a)
        assert st == 400 and "different order" in r["detail"], (st, r)
        pay(order_a, "pay_SHORT_" + RUN, amount=100)                                    # signed and captured, but for 1 rupee
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_SHORT_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_SHORT_" + RUN)}, fam_a)
        assert st == 200 and r["webhook_outcome"] == "REJECTED_AMOUNT_MISMATCH" and r["subscription"]["status"] == "PENDING", r
        print("[PASS] wrong signature (400), unpaid payment (402), another order's payment (400) and a wrong amount (rejected): still PENDING")

        print("--- another user cannot confirm this order")
        pay(order_a, "pay_GOOD_" + RUN)
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_GOOD_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_GOOD_" + RUN)}, fam_b)
        assert st == 404, (st, r)
        assert sub_of(uid_a).status == "PENDING"
        print("[PASS] user B gets 404 for user A's order")

        print("--- a correct payment activates once")
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_GOOD_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_GOOD_" + RUN)}, fam_a)
        s_ = r["subscription"]
        assert st == 200 and r["webhook_outcome"] == "PROCESSED" and s_["status"] == "ACTIVE" and s_["entitled"], r
        end1 = sub_of(uid_a).end_date
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order_a, "razorpay_payment_id": "pay_GOOD_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order_a, "pay_GOOD_" + RUN)}, fam_a)
        assert st == 200 and r["webhook_outcome"] == "DUPLICATE" and sub_of(uid_a).end_date == end1, r
        assert call(base, "/payments/checkout", "POST", token=fam_a)[0] == 409, "an active subscription must not start another checkout"
        print("[PASS] ACTIVE after one verified payment; confirming it again is a DUPLICATE and changes nothing")

        print("--- an authorized payment is captured by the server")
        with Session(engine) as s:
            row = s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == uid_a)).first()
            row.status, row.end_date, row.provider_subscription_id = "EXPIRED", utcnow() - timedelta(days=40), None
            s.add(row)
            s.commit()
        st, co = call(base, "/payments/checkout", "POST", token=fam_a)
        order2 = co["checkout"]["order_id"]
        pay(order2, "pay_AUTH_" + RUN, status="authorized")
        st, r = call(base, "/payments/razorpay/verify", "POST", {"razorpay_order_id": order2, "razorpay_payment_id": "pay_AUTH_" + RUN,
                                                                 "razorpay_signature": sign_checkout(order2, "pay_AUTH_" + RUN)}, fam_a)
        assert st == 200 and r["subscription"]["status"] == "ACTIVE" and PAYMENTS["pay_AUTH_" + RUN]["status"] == "captured", (st, r)
        print("[PASS] authorized -> captured by the server -> ACTIVE (a renewal after expiry)")

        print("--- webhooks")
        st, co = call(base, "/payments/checkout", "POST", token=fam_b)
        order_b = co["checkout"]["order_id"]
        sub_b = sub_of(uid_b)
        event = {"event": "payment.captured", "created_at": int(time.time()), "payload": {"payment": {"entity": {
            "id": "pay_WEBHOOK1_" + RUN, "order_id": order_b, "amount": PLAN_AMOUNT, "currency": "INR", "status": "captured",
            "notes": {"subscription_ref": sub_b.id}}}}}
        raw = json.dumps(event).encode()
        good = hmac.new(WH_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        st, r = call(base, "/payments/webhooks/razorpay", "POST", raw=raw, headers={"X-Razorpay-Signature": "f" * 64})
        assert st == 400 and sub_of(uid_b).status == "PENDING", (st, r)
        st, r = call(base, "/payments/webhooks/razorpay", "POST", raw=raw + b" ", headers={"X-Razorpay-Signature": good})
        assert st == 400, "a body that differs from what was signed must be rejected"
        st, r = call(base, "/payments/webhooks/razorpay", "POST", raw=raw, headers={"X-Razorpay-Signature": good})
        assert st == 200 and r["outcome"] == "PROCESSED" and sub_of(uid_b).status == "ACTIVE", (st, r)
        st, r = call(base, "/payments/webhooks/razorpay", "POST", raw=raw, headers={"X-Razorpay-Signature": good})
        assert st == 200 and r["outcome"] == "DUPLICATE", (st, r)
        print("[PASS] bad or altered webhook rejected (400); a signed one activates once; the repeat is a DUPLICATE")
        other = json.dumps({"event": "order.paid", "payload": {"payment": {"entity": {"id": "pay_X_" + RUN}}}}).encode()
        st, r = call(base, "/payments/webhooks/razorpay", "POST", raw=other,
                     headers={"X-Razorpay-Signature": hmac.new(WH_SECRET.encode(), other, hashlib.sha256).hexdigest()})
        assert st == 200 and r["outcome"] == "IGNORED_UNKNOWN_TYPE", (st, r)
        print("[PASS] unknown event types are acknowledged and ignored")
    finally:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(srv.pid), "/T", "/F"], capture_output=True)
        else:
            srv.terminate()
        fake.shutdown()
        with Session(engine) as s:
            for uid in users:
                for row in s.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == uid)).all():
                    s.delete(row)
                for row in s.exec(select(FamilyConnection).where(FamilyConnection.family_user_id == uid)).all():
                    s.delete(row)
            s.commit()

    print("--- configuration guards")
    from app.core.config import Settings
    saved = dict(os.environ)
    try:
        os.environ.update(PAYMENTS_MODE="razorpay", RAZORPAY_KEY_ID="rzp_live_ABCDEF123456", RAZORPAY_KEY_SECRET="x", ENVIRONMENT="development")
        os.environ.pop("RAZORPAY_ALLOW_LIVE", None)
        try:
            Settings()
            raise AssertionError("a live key must be refused by default")
        except RuntimeError as e:
            assert "Live payments are off" in str(e)
        os.environ["RAZORPAY_ALLOW_LIVE"] = "1"
        assert Settings().PAYMENTS_MODE == "razorpay"
        os.environ.pop("RAZORPAY_ALLOW_LIVE")
        os.environ["RAZORPAY_KEY_ID"] = "rzp_test_ABCDEF123456"
        os.environ.pop("RAZORPAY_KEY_SECRET")
        try:
            Settings()
            raise AssertionError("razorpay mode without a secret must not start")
        except RuntimeError as e:
            assert "RAZORPAY_KEY_SECRET" in str(e)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    print("[PASS] live keys are refused unless RAZORPAY_ALLOW_LIVE=1; razorpay mode without keys refuses to start")
    print("\nALL RAZORPAY TESTS PASSED")


if __name__ == "__main__":
    run()
