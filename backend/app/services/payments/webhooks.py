"""
Webhook handling: signature check, idempotency, ordering, validation and the subscription state changes.

What a webhook can and cannot do
  * It can only act on a subscription it names, and only with a checkout id or provider subscription id that the
    subscription already holds. A genuine but unrelated event cannot activate someone else's subscription.
  * A payment is only accepted if its amount and currency equal the plan price. A mismatch is recorded and rejected.
  * An administrator's SUSPENDED hold is never lifted by a payment.
  * Repeats (same event id) change nothing. Older events than one already applied are ignored.
  * It never touches the family connection, the resident, roles or any other access control.
  * Only whitelisted fields are stored (see PaymentEvent): never anything resembling payment details.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.config import settings
from app.core.timeutil import as_utc, utcnow
from app.models.entities import (
    Building, FamilyConnection, FamilySubscription, Floor, PaymentEvent, Resident, Room,
)
from app.services.payments import lifecycle, signing
from app.services.payments.signing import WebhookError

PROVIDER = "sandbox"
HANDLED = ("payment.succeeded", "payment.failed", "subscription.cancelled")


def subscription_org_id(session: Session, sub: FamilySubscription) -> Optional[str]:
    """Organization of the resident this subscription is attached to (used to attribute audit events)."""
    conn = session.get(FamilyConnection, sub.family_connection_id) if sub.family_connection_id else None
    resident = session.get(Resident, conn.resident_id) if conn else None
    room = session.get(Room, resident.room_id) if resident else None
    floor = session.get(Floor, room.floor_id) if room else None
    building = session.get(Building, floor.building_id) if floor else None
    return building.organization_id if building else None


def handle_webhook(session: Session, raw_body: bytes, signature: Optional[str], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Entry point for EVERY webhook (external HTTP request or sandbox delivery). Raises WebhookError if not authentic."""
    signing.verify(settings.PAYMENT_WEBHOOK_SECRET, raw_body, signature, settings.WEBHOOK_TOLERANCE_SECONDS)
    try:
        event = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError):
        raise WebhookError("body is not valid JSON")
    return process_event(session, event, now)


def _summary(event: Dict[str, Any]) -> Dict[str, Any]:
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    return {"type": event.get("type"), "subscription_ref": data.get("subscription_ref"),
            "amount_minor": data.get("amount_minor"), "currency": data.get("currency"), "created": event.get("created")}


def _record(session: Session, event: Dict[str, Any], sub: Optional[FamilySubscription], outcome: str) -> None:
    session.add(PaymentEvent(provider=str(event.get("provider") or PROVIDER)[:30], event_id=str(event["id"])[:100], event_type=str(event["type"])[:60],
                             subscription_id=sub.id if sub else None, outcome=outcome, summary=_summary(event)))


def process_event(session: Session, event: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = as_utc(now) if now else utcnow()
    if not isinstance(event, dict) or not isinstance(event.get("id"), str) or not isinstance(event.get("type"), str) \
            or not isinstance(event.get("created"), int) or not isinstance(event.get("data"), dict) or not event["id"]:
        raise WebhookError("malformed event")

    if session.exec(select(PaymentEvent).where(PaymentEvent.event_id == event["id"])).first():
        return {"outcome": "DUPLICATE", "event_id": event["id"]}

    data = event["data"]
    sub = session.get(FamilySubscription, data.get("subscription_ref")) if isinstance(data.get("subscription_ref"), str) else None
    org_id = subscription_org_id(session, sub) if sub else None

    def finish(outcome: str, audit_action: Optional[str] = None) -> Dict[str, Any]:
        try:
            _record(session, event, sub, outcome)
            if sub:
                session.add(sub)
            session.commit()
        except IntegrityError:               # a concurrent delivery of the same event id won the race
            session.rollback()
            return {"outcome": "DUPLICATE", "event_id": event["id"]}
        if audit_action:
            record_audit_event(session, what_action=audit_action, resource_type="SUBSCRIPTION",
                               resource_id=sub.id if sub else None, who_email=f"payment-provider:{event.get('provider') or PROVIDER}",
                               organization_id=org_id, details={"event_id": event["id"], "type": event["type"], "outcome": outcome})
        return {"outcome": outcome, "event_id": event["id"], "subscription_id": sub.id if sub else None,
                "status": sub.status if sub else None}

    if not sub:
        return finish("REJECTED_UNKNOWN_SUBSCRIPTION", "PAYMENT_EVENT_REJECTED")
    if event["type"] not in HANDLED:
        return finish("IGNORED_UNKNOWN_TYPE")

    created = datetime.fromtimestamp(event["created"], tz=timezone.utc)
    if sub.last_event_at and created < as_utc(sub.last_event_at):
        return finish("IGNORED_STALE")

    held = sub.status == "SUSPENDED"          # an administrator's hold is never lifted by a payment

    if event["type"] == "payment.succeeded":
        price_minor = sub.price_minor or settings.CARE_MONTHLY_PRICE_MINOR
        currency = sub.currency or settings.CARE_MONTHLY_CURRENCY
        if data.get("amount_minor") != price_minor or data.get("currency") != currency:
            return finish("REJECTED_AMOUNT_MISMATCH", "PAYMENT_EVENT_REJECTED")
        checkout_id, provider_sub = data.get("checkout_id"), data.get("provider_subscription_id")
        first_payment = bool(checkout_id) and checkout_id == sub.provider_checkout_id
        renewal = (not checkout_id) and bool(provider_sub) and provider_sub == sub.provider_subscription_id
        if not (first_payment or renewal):
            return finish("REJECTED_UNKNOWN_CHECKOUT", "PAYMENT_EVENT_REJECTED")
        if first_payment and not provider_sub:
            return finish("REJECTED_UNKNOWN_CHECKOUT", "PAYMENT_EVENT_REJECTED")

        if first_payment:
            period_start, period_end = now, now + lifecycle.period_delta()
            sub.provider_subscription_id = provider_sub
            sub.provider_checkout_id = None                      # a checkout can complete only once
            sub.cancel_at_period_end = False
            sub.cancelled_at = None
        else:
            base = as_utc(sub.end_date) if sub.end_date and as_utc(sub.end_date) > now else now
            period_start, period_end = (as_utc(sub.end_date) if sub.end_date else now), base + lifecycle.period_delta()
        sub.start_date, sub.end_date = period_start, period_end
        sub.renewal_date = None if sub.cancel_at_period_end else period_end
        sub.price_minor, sub.currency = price_minor, currency
        sub.last_payment_status = "SUCCEEDED"
        sub.past_due_since = None
        sub.last_event_at = created
        sub.updated_at = now
        if held:
            return finish("HELD_BY_ADMIN", "PAYMENT_RECEIVED_WHILE_SUSPENDED")
        sub.status = "ACTIVE"
        return finish("PROCESSED", "PAYMENT_SUCCEEDED")

    if event["type"] == "payment.failed":
        sub.last_payment_status = "FAILED"
        sub.last_event_at = created
        sub.updated_at = now
        if sub.status == "ACTIVE":
            sub.status = "PAST_DUE"
            sub.past_due_since = now
        return finish("HELD_BY_ADMIN" if held else "PROCESSED", "PAYMENT_FAILED")

    # subscription.cancelled: the provider says no further renewals will be charged. Access continues to the period end.
    if data.get("provider_subscription_id") != sub.provider_subscription_id or not sub.provider_subscription_id:
        return finish("REJECTED_UNKNOWN_CHECKOUT", "PAYMENT_EVENT_REJECTED")
    sub.cancel_at_period_end = True
    sub.renewal_date = None
    sub.cancelled_at = sub.cancelled_at or now
    sub.last_event_at = created
    sub.updated_at = now
    return finish("PROCESSED", "SUBSCRIPTION_CANCELLED_BY_PROVIDER")
