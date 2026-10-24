"""
Razorpay provider (Orders + Checkout).

Flow
  1. The server creates an ORDER for the plan price (POST /orders) and gives the browser the order id and the PUBLIC key id.
  2. The browser opens Razorpay's own Checkout. Card/UPI/netbanking details are entered there; they never reach this server.
  3. Razorpay returns order_id, payment_id and a signature to the browser, which sends them to POST /payments/razorpay/verify.
  4. The server checks the signature (HMAC-SHA256 with the key secret over "order_id|payment_id"), then ASKS Razorpay for the payment
     (GET /payments/{id}) and only accepts it when the order, amount, currency and status match. Only then is the subscription activated,
     through the same idempotent event processor the sandbox uses (amount check, admin hold, replay protection).
  5. A signed Razorpay webhook (payment.captured / payment.failed) is accepted as a backup and lands in the same processor.

Secrets: the key secret and webhook secret are read from the environment, are never logged, never returned, and never put in an error.
"""
import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from app.core.config import settings

PROVIDER = "razorpay"


class RazorpayError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def is_test_mode() -> bool:
    return settings.RAZORPAY_KEY_ID.startswith("rzp_test_")


def mode_label() -> str:
    return "RAZORPAY_TEST" if is_test_mode() else "RAZORPAY_LIVE"


def _request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    token = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
    req = urllib.request.Request(
        settings.RAZORPAY_API_BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = "Razorpay rejected the request."
        try:
            detail = json.loads(exc.read()).get("error", {}).get("description") or detail
        except (ValueError, AttributeError):
            pass
        raise RazorpayError(502 if exc.code >= 500 else 400 if exc.code != 401 else 502,
                            "Razorpay did not accept the credentials." if exc.code == 401 else detail)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RazorpayError(502, "Could not reach Razorpay. Try again in a moment.")


def create_order(amount_minor: int, currency: str, receipt: str, notes: Dict[str, str]) -> Dict[str, Any]:
    return _request("POST", "/orders", {"amount": int(amount_minor), "currency": currency, "receipt": receipt[:40], "notes": notes})


def fetch_payment(payment_id: str) -> Dict[str, Any]:
    return _request("GET", f"/payments/{payment_id}")


def capture_payment(payment_id: str, amount_minor: int, currency: str) -> Dict[str, Any]:
    return _request("POST", f"/payments/{payment_id}/capture", {"amount": int(amount_minor), "currency": currency})


def verify_checkout_signature(order_id: str, payment_id: str, signature: str) -> bool:
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (signature or "").strip().lower())


def verify_webhook_signature(raw_body: bytes, signature: Optional[str]) -> bool:
    if not settings.RAZORPAY_WEBHOOK_SECRET or not signature:
        return False
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())
