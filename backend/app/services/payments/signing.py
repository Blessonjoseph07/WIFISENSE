"""
Webhook signatures (Stripe-style): header `t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>." + raw body>`.

A webhook is an unauthenticated request from outside, so its signature is the only proof of origin. It is therefore:
  * computed over the exact raw bytes received (never over re-serialised JSON),
  * compared in constant time,
  * rejected when the timestamp is outside a tolerance window (stops replay of an old, genuine request).
Several `v1=` values are accepted so a secret can be rotated without downtime.
"""
import hashlib
import hmac
import time
from typing import Optional


class WebhookError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def sign(secret: str, payload: bytes, timestamp: Optional[int] = None) -> str:
    ts = int(time.time()) if timestamp is None else int(timestamp)
    mac = hmac.new(secret.encode("utf-8"), f"{ts}.".encode("utf-8") + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def verify(secret: str, payload: bytes, header: Optional[str], tolerance_seconds: int, now: Optional[float] = None) -> int:
    """Returns the signed timestamp, or raises WebhookError(reason)."""
    if not header:
        raise WebhookError("missing signature header")
    timestamp = None
    candidates = []
    for part in header.split(","):
        key, _, value = part.strip().partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                raise WebhookError("malformed timestamp")
        elif key == "v1" and value:
            candidates.append(value)
    if timestamp is None or not candidates:
        raise WebhookError("malformed signature header")
    current = time.time() if now is None else now
    if abs(current - timestamp) > tolerance_seconds:
        raise WebhookError("timestamp outside the tolerance window")
    expected = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, c) for c in candidates):
        raise WebhookError("signature mismatch")
    return timestamp
