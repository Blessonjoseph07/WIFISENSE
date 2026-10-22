"""
Family subscription payments (CARE_MONTHLY) with a SANDBOX provider.

Nothing here moves real money or touches payment details, and the API says so in every response (`mode: SANDBOX`).
The pieces that would be identical with a real provider are real: signed webhooks, idempotency, amount checks,
cancellation at period end, renewal, past-due and expiry handling.

A subscription never grants access. Checkout requires an approved connection to a resident (the facility's decision),
and paying never creates, approves or widens a connection, a role or a sharing policy.

Simulation gating:
Endpoints for simulated checkout and lifecycle events (POST /payments/checkout, POST /payments/sandbox/checkout/{id}/complete,
and POST /payments/sandbox/simulate) are controlled by PAYMENTS_SANDBOX_SIMULATOR_ENABLED. Outside production, this defaults
to true. Under production (ENVIRONMENT=production), it defaults to false, causing these endpoints to return 404 unless
explicitly enabled. Signed webhook verification on POST /payments/webhooks/sandbox is independent and never disabled.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.config import settings
from app.core.database import get_session
from app.core.limiter import rate_limit
from app.core.timeutil import utcnow
from app.models.entities import FamilyConnection, FamilySubscription, PaymentEvent, User
from app.routers.auth import get_current_user, get_user_scopes, require_roles
from app.services.payments import lifecycle, sandbox
from app.services.payments.signing import WebhookError
from app.services.payments.webhooks import handle_webhook, subscription_org_id

router = APIRouter(prefix="/payments", tags=["Family Subscription (SANDBOX payments)"])

FAMILY = ["family_member"]
ADMINS = ["system_admin", "facility_manager"]
SANDBOX_NOTICE = ("SANDBOX: payments are simulated. No real money moves and no card or payment details are collected "
                  "or stored.")


class SandboxComplete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    outcome: Literal["success", "failure"]


class SandboxSimulate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: Literal["renewal_succeeded", "renewal_failed", "provider_cancelled"]


def _sandbox_only() -> None:
    if settings.PAYMENTS_MODE != "sandbox" or not settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED:
        raise HTTPException(status_code=404, detail="Sandbox simulator endpoints are disabled in this environment.")


def _own_subscription(session: Session, user: User) -> Optional[FamilySubscription]:
    sub = session.exec(select(FamilySubscription).where(FamilySubscription.family_user_id == user.id)).first()
    if sub:
        lifecycle.reconcile(session, sub)
    return sub


def _approved_connection(session: Session, user: User) -> Optional[FamilyConnection]:
    return session.exec(
        select(FamilyConnection).where(FamilyConnection.family_user_id == user.id, FamilyConnection.status == "approved")
        .order_by(FamilyConnection.created_at.desc())
    ).first()


def _response(sub: Optional[FamilySubscription], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "mode": sandbox.MODE_LABEL,
        "sandbox_notice": SANDBOX_NOTICE,
        "simulator_enabled": settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED,
        "plan": lifecycle.plan_price(),
        "subscription": lifecycle.view(sub) if sub else None,
    }
    out.update(extra or {})
    return out


def _audit(session: Session, user: User, sub: Optional[FamilySubscription], action: str, details: Optional[dict] = None) -> None:
    record_audit_event(session, what_action=action, resource_type="SUBSCRIPTION", resource_id=sub.id if sub else None,
                       who_user_id=user.id, who_email=user.email,
                       organization_id=subscription_org_id(session, sub) if sub else None, details=details)


# ----------------------------------------------------------------------------- family member
@router.get("/subscription", dependencies=[Depends(require_roles(FAMILY))])
def my_subscription(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    sub = _own_subscription(session, current_user)
    conn = _approved_connection(session, current_user)
    return _response(sub, {
        "connection_approved": conn is not None,
        "emergency_access": "Emergency alerts for your resident never depend on a subscription, only on an approved connection.",
    })


@router.post("/checkout", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(FAMILY))])
def start_checkout(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _sandbox_only()
    conn = _approved_connection(session, current_user)
    if not conn:
        raise HTTPException(status_code=403, detail="A subscription needs an approved connection to a resident. The facility approves connections.")
    sub = _own_subscription(session, current_user)
    if not sub:
        sub = FamilySubscription(family_user_id=current_user.id, family_connection_id=conn.id, plan="CARE_MONTHLY", status="PENDING")
        session.add(sub)
        session.commit()
        session.refresh(sub)
    if sub.status == "SUSPENDED":
        raise HTTPException(status_code=409, detail="This subscription is on hold by the care facility. Please contact the facility.")
    if sub.status == "ACTIVE":
        raise HTTPException(status_code=409, detail="The subscription is already active." + (
            " It is set to end at the period end: use Resume instead." if sub.cancel_at_period_end else ""))

    price = lifecycle.plan_price()
    sub.provider = sandbox.PROVIDER
    sub.provider_checkout_id = sandbox.new_checkout_id()
    sub.price_minor, sub.currency = price["amount_minor"], price["currency"]
    sub.updated_at = utcnow()
    session.add(sub)
    session.commit()
    session.refresh(sub)
    _audit(session, current_user, sub, "SUBSCRIPTION_CHECKOUT_STARTED", {"provider": sandbox.PROVIDER})
    return _response(sub, {
        "checkout": {"id": sub.provider_checkout_id, "provider": sandbox.PROVIDER, "amount_minor": sub.price_minor,
                     "currency": sub.currency, "mode": sandbox.MODE_LABEL},
    })


@router.post("/cancel", dependencies=[Depends(require_roles(FAMILY))])
def cancel_subscription(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Cancel at the END of the paid period: access continues until then. A never-paid subscription is cancelled at once."""
    sub = _own_subscription(session, current_user)
    if not sub or sub.status not in ("ACTIVE", "PAST_DUE", "PENDING"):
        raise HTTPException(status_code=409, detail="There is no active subscription to cancel.")
    if sub.cancel_at_period_end or sub.status == "CANCELLED":
        return _response(sub)                       # idempotent
    now = utcnow()
    sub.cancelled_at = now
    sub.renewal_date = None
    sub.updated_at = now
    if sub.status == "PENDING":
        sub.status = "CANCELLED"
        sub.provider_checkout_id = None
    else:
        sub.cancel_at_period_end = True
    session.add(sub)
    session.commit()
    session.refresh(sub)
    _audit(session, current_user, sub, "SUBSCRIPTION_CANCEL_REQUESTED", {"effective": "period_end" if sub.cancel_at_period_end else "immediate"})
    return _response(sub)


@router.post("/resume", dependencies=[Depends(require_roles(FAMILY))])
def resume_subscription(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    sub = _own_subscription(session, current_user)
    if not sub or sub.status != "ACTIVE" or not sub.cancel_at_period_end:
        raise HTTPException(status_code=409, detail="Only a subscription that is set to end at the period end can be resumed. Otherwise start a new checkout.")
    sub.cancel_at_period_end = False
    sub.cancelled_at = None
    sub.renewal_date = sub.end_date
    sub.updated_at = utcnow()
    session.add(sub)
    session.commit()
    session.refresh(sub)
    _audit(session, current_user, sub, "SUBSCRIPTION_RESUMED")
    return _response(sub)


# ----------------------------------------------------------------------------- sandbox controls (the "provider")
@router.post("/sandbox/checkout/{checkout_id}/complete", dependencies=[Depends(require_roles(FAMILY))])
def sandbox_complete_checkout(checkout_id: str, body: SandboxComplete, session: Session = Depends(get_session),
                              current_user: User = Depends(get_current_user)):
    """SANDBOX ONLY: choose the outcome of a simulated payment. The result arrives as a signed webhook, like a real one."""
    _sandbox_only()
    sub = session.exec(select(FamilySubscription).where(
        FamilySubscription.provider_checkout_id == checkout_id, FamilySubscription.family_user_id == current_user.id)).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Checkout not found.")      # same answer for 'missing' and 'not yours'
    base = {"subscription_ref": sub.id, "checkout_id": checkout_id}
    if body.outcome == "success":
        outcome = sandbox.deliver(session, "payment.succeeded", {**base, "provider_subscription_id": sandbox.new_provider_subscription_id(),
                                                                  "amount_minor": sub.price_minor, "currency": sub.currency})
    else:
        outcome = sandbox.deliver(session, "payment.failed", base)
    session.refresh(sub)
    return _response(sub, {"webhook_outcome": outcome["outcome"]})


@router.post("/sandbox/simulate", dependencies=[Depends(require_roles(FAMILY))])
def sandbox_simulate(body: SandboxSimulate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """SANDBOX ONLY: simulate what a provider would send later (renewal paid, renewal failed, cancelled at the provider)."""
    _sandbox_only()
    sub = _own_subscription(session, current_user)
    if not sub or not sub.provider_subscription_id:
        raise HTTPException(status_code=409, detail="Nothing to simulate: this subscription has not been paid yet.")
    base = {"subscription_ref": sub.id, "provider_subscription_id": sub.provider_subscription_id}
    if body.event == "renewal_succeeded":
        outcome = sandbox.deliver(session, "payment.succeeded", {**base, "amount_minor": sub.price_minor or lifecycle.plan_price()["amount_minor"],
                                                                  "currency": sub.currency or lifecycle.plan_price()["currency"]})
    elif body.event == "renewal_failed":
        outcome = sandbox.deliver(session, "payment.failed", base)
    else:
        outcome = sandbox.deliver(session, "subscription.cancelled", base)
    session.refresh(sub)
    lifecycle.reconcile(session, sub)
    return _response(sub, {"webhook_outcome": outcome["outcome"]})


# ----------------------------------------------------------------------------- webhook (unauthenticated: the signature is the proof)
@router.post("/webhooks/sandbox", dependencies=[Depends(rate_limit(max_requests=120, window_seconds=60, bucket="payment_webhook"))])
async def sandbox_webhook(request: Request, session: Session = Depends(get_session)):
    raw = await request.body()
    if len(raw) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Payload too large.")
    try:
        result = handle_webhook(session, raw, request.headers.get("X-Sandbox-Signature"))
    except WebhookError as exc:
        record_audit_event(session, what_action="PAYMENT_WEBHOOK_REJECTED", resource_type="PAYMENT_WEBHOOK", result="DENIED",
                           who_email="payment-provider:sandbox", details={"reason": exc.reason},
                           ip_address=request.client.host if request.client else None)
        raise HTTPException(status_code=400, detail=f"Webhook rejected: {exc.reason}.")
    return {"received": True, "outcome": result["outcome"]}


# ----------------------------------------------------------------------------- staff
@router.get("/events", dependencies=[Depends(require_roles(ADMINS))])
def list_payment_events(limit: int = 50, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Recent payment events for the staff member's organizations (system admin: all). No payment details exist to show."""
    scopes = get_user_scopes(current_user)
    out: List[Dict[str, Any]] = []
    for ev in session.exec(select(PaymentEvent).order_by(PaymentEvent.received_at.desc()).limit(500)).all():
        sub = session.get(FamilySubscription, ev.subscription_id) if ev.subscription_id else None
        org = subscription_org_id(session, sub) if sub else None
        if not scopes["is_system_admin"] and org not in scopes["organization_ids"]:
            continue
        out.append({"event_id": ev.event_id, "type": ev.event_type, "outcome": ev.outcome, "subscription_id": ev.subscription_id,
                    "received_at": ev.received_at.isoformat(), "summary": ev.summary})
        if len(out) >= max(1, min(limit, 200)):
            break
    return out


@router.post("/maintenance/reconcile", dependencies=[Depends(require_roles(["system_admin"]))])
def reconcile_all(session: Session = Depends(get_session)):
    """Apply time-based transitions (period end, past due, expiry) to every subscription. Normally done lazily on read."""
    changed = sum(1 for s in session.exec(select(FamilySubscription)).all() if lifecycle.reconcile(session, s))
    return {"subscriptions_changed": changed}
