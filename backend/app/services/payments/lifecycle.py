"""
Subscription lifecycle rules (CARE_MONTHLY).

States
  PENDING    never paid
  ACTIVE     paid; a period end date means "paid until then"; no end date = managed by an administrator (legacy rows)
  PAST_DUE   the renewal failed or was missed: optional features continue during a short grace period
  EXPIRED    grace ended without payment
  CANCELLED  the user cancelled and the paid period has ended (or it was never paid)
  SUSPENDED  an administrator's hold: payments never lift it

Cancellation is at the END of the paid period: ACTIVE with cancel_at_period_end keeps working until the period ends.

Entitlement only decides OPTIONAL family-portal features. It never grants access to anything: the family member still needs
an approved connection to the resident and the resident's sharing policy still applies. Emergency visibility does not depend
on a subscription at all (see family_portal.emergency_block).
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.timeutil import as_utc, utcnow

ENTITLED_STATUSES = ("ACTIVE", "PAST_DUE")


def plan_price() -> Dict[str, Any]:
    return {"plan": "CARE_MONTHLY", "amount_minor": settings.CARE_MONTHLY_PRICE_MINOR, "currency": settings.CARE_MONTHLY_CURRENCY,
            "period_days": settings.SUBSCRIPTION_PERIOD_DAYS}


def period_delta() -> timedelta:
    return timedelta(days=settings.SUBSCRIPTION_PERIOD_DAYS)


def grace_until(sub) -> Optional[datetime]:
    """Optional features continue until this moment while PAST_DUE. Never earlier than the end of what was already paid."""
    if sub.status != "PAST_DUE" or not sub.past_due_since:
        return None
    base = as_utc(sub.past_due_since)
    if sub.end_date and as_utc(sub.end_date) > base:
        base = as_utc(sub.end_date)
    return base + timedelta(days=settings.SUBSCRIPTION_GRACE_DAYS)


def reconcile(session, sub, now: Optional[datetime] = None) -> bool:
    """Apply time-based transitions and persist them. Cheap, idempotent, called wherever a status is read."""
    now = as_utc(now) if now else utcnow()
    changed = False
    if sub.status == "ACTIVE" and sub.end_date and now >= as_utc(sub.end_date):
        if sub.cancel_at_period_end:
            sub.status = "CANCELLED"
            sub.renewal_date = None
        else:
            sub.status = "PAST_DUE"                       # the renewal did not arrive
            sub.past_due_since = as_utc(sub.end_date)
        changed = True
    if sub.status == "PAST_DUE":
        limit = grace_until(sub)
        if limit is None:                                   # defensive: a PAST_DUE row without a start
            sub.past_due_since = now
            changed = True
        elif now >= limit:
            sub.status = "EXPIRED"
            sub.renewal_date = None
            changed = True
    if changed:
        sub.updated_at = now
        session.add(sub)
        session.commit()
        session.refresh(sub)
    return changed


def is_entitled(sub) -> bool:
    """Call reconcile() first."""
    return bool(sub) and sub.status in ENTITLED_STATUSES


def view(sub, now: Optional[datetime] = None) -> Dict[str, Any]:
    now = as_utc(now) if now else utcnow()
    price = {"amount_minor": sub.price_minor, "currency": sub.currency} if sub.price_minor else \
        {k: v for k, v in plan_price().items() if k in ("amount_minor", "currency")}
    iso = lambda d: as_utc(d).isoformat().replace("+00:00", "Z") if d else None  # noqa: E731
    entitled = is_entitled(sub)
    return {
        "id": sub.id,
        "plan": sub.plan,
        "status": sub.status,
        "entitled": entitled,
        "cancel_at_period_end": bool(sub.cancel_at_period_end),
        "current_period_start": iso(sub.start_date),
        "current_period_end": iso(sub.end_date),
        "renewal_date": iso(sub.renewal_date),
        "cancelled_at": iso(sub.cancelled_at),
        "past_due_since": iso(sub.past_due_since),
        "grace_until": iso(grace_until(sub)),
        "last_payment_status": sub.last_payment_status,
        "price": price,
        "provider": sub.provider,
        "actions": {
            "can_subscribe": sub.status in ("PENDING", "EXPIRED", "CANCELLED", "PAST_DUE"),
            "can_cancel": sub.status in ("ACTIVE", "PAST_DUE", "PENDING") and not sub.cancel_at_period_end,
            "can_resume": sub.status == "ACTIVE" and bool(sub.cancel_at_period_end),
        },
        "access_note": (
            "Optional portal features are on hold. Emergency alerts for your resident are unaffected." if sub.status == "SUSPENDED"
            else "Optional features end when the paid period ends. Emergency alerts are never tied to a subscription."
            if sub.cancel_at_period_end else None
        ),
    }
