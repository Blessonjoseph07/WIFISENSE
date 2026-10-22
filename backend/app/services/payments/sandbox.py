"""
SANDBOX payment provider.

This simulates a payment provider so the whole subscription lifecycle can be built and tested without one. It is clearly
NOT a real provider: no money moves, no card or payment details exist anywhere in this code, and its "checkout" is a
pair of buttons that pick an outcome. A real provider (for example Stripe) would host the checkout page itself, so card
data would never reach this server; it would then only have to implement the same two things as below:
  1. create a checkout and return its id,
  2. send signed webhook events.
Everything else (signature check, idempotency, amount check, lifecycle) is shared and provider-independent.

The sandbox also delivers its events THROUGH the normal webhook code path, signed with the webhook secret, so the sandbox
exercises exactly the code a real provider's webhooks would.

Production gating:
The simulator endpoints (checkout, complete checkout, simulate renewal/cancellation) are gated by
the PAYMENTS_SANDBOX_SIMULATOR_ENABLED configuration flag. By default, this flag is true outside production
(development, staging, test) and defaults to false when ENVIRONMENT=production. In production, simulation
endpoints return 404 unless PAYMENTS_SANDBOX_SIMULATOR_ENABLED is explicitly set to true. Webhook signature
verification remains fully active and unaffected by this simulator gate.
"""
import json
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.services.payments import signing
from app.services.payments.webhooks import handle_webhook

PROVIDER = "sandbox"
MODE_LABEL = "SANDBOX"


def new_checkout_id() -> str:
    return "sbx_cs_" + secrets.token_urlsafe(18)


def new_provider_subscription_id() -> str:
    return "sbx_sub_" + secrets.token_urlsafe(18)


def build_signed_event(event_type: str, data: Dict[str, Any], created: Optional[int] = None,
                       event_id: Optional[str] = None) -> Tuple[bytes, str]:
    event = {"id": event_id or "sbx_evt_" + secrets.token_urlsafe(18), "type": event_type,
             "created": int(created if created is not None else time.time()), "data": data}
    body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return body, signing.sign(settings.PAYMENT_WEBHOOK_SECRET, body)


def deliver(session, event_type: str, data: Dict[str, Any], created: Optional[int] = None,
            event_id: Optional[str] = None) -> Dict[str, Any]:
    """Send a signed event through the same entry point as an external webhook."""
    body, header = build_signed_event(event_type, data, created=created, event_id=event_id)
    return handle_webhook(session, body, header)
