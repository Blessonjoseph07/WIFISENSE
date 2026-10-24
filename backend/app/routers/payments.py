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
import json
import time
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
from app.services.payments import lifecycle, razorpay, sandbox
from app.services.payments.razorpay import RazorpayError
from app.services.payments.signing import WebhookError
from app.services.payments.webhooks import handle_webhook, process_event, subscription_org_id

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


RAZORPAY_TEST_NOTICE = ("TEST MODE: payments go to Razorpay's test environment, so no real money moves. Use Razorpay's test cards or UPI. "
                        "Card details are typed on Razorpay's own page and never reach this server.")
RAZORPAY_LIVE_NOTICE = "Payments are real. Card details are typed on Razorpay's own page and never reach this server."


def _mode_fields() -> Dict[str, Any]:
    if settings.PAYMENTS_MODE == "razorpay":
        return {"mode": razorpay.mode_label(), "sandbox_notice": RAZORPAY_TEST_NOTICE if razorpay.is_test_mode() else RAZORPAY_LIVE_NOTICE,
                "simulator_enabled": False, "provider": razorpay.PROVIDER}
    return {"mode": sandbox.MODE_LABEL, "sandbox_notice": SANDBOX_NOTICE,
            "simulator_enabled": settings.PAYMENTS_SANDBOX_SIMULATOR_ENABLED, "provider": sandbox.PROVIDER}


def _response(sub: Optional[FamilySubscription], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        **_mode_fields(),
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
    if settings.PAYMENTS_MODE != "razorpay":
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
    if settings.PAYMENTS_MODE == "razorpay":
        try:
            order = razorpay.create_order(price["amount_minor"], price["currency"], f"care-{sub.id}", {"subscription_ref": sub.id, "plan": "CARE_MONTHLY"})
        except RazorpayError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.detail)
        sub.provider = razorpay.PROVIDER
        sub.provider_checkout_id = order["id"]
    else:
        sub.provider = sandbox.PROVIDER
        sub.provider_checkout_id = sandbox.new_checkout_id()
    sub.price_minor, sub.currency = price["amount_minor"], price["currency"]
    sub.updated_at = utcnow()
    session.add(sub)
    session.commit()
    session.refresh(sub)
    _audit(session, current_user, sub, "SUBSCRIPTION_CHECKOUT_STARTED", {"provider": sub.provider})
    checkout = {"id": sub.provider_checkout_id, "provider": sub.provider, "amount_minor": sub.price_minor,
                "currency": sub.currency, "mode": _mode_fields()["mode"]}
    if sub.provider == razorpay.PROVIDER:
        name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip()
        checkout.update({"order_id": sub.provider_checkout_id, "key_id": settings.RAZORPAY_KEY_ID,   # the key id is public by design
                         "name": "Wi-Fi Sense Care Plan", "description": f"CARE_MONTHLY, {price['period_days']} days",
                         "prefill": {"name": name, "email": current_user.email}})
    return _response(sub, {"checkout": checkout})


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


# ----------------------------------------------------------------------------- Razorpay
class RazorpayVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def _razorpay_only() -> None:
    if settings.PAYMENTS_MODE != "razorpay":
        raise HTTPException(status_code=404, detail="Razorpay payments are not enabled in this environment.")


def _succeeded_event(sub_id: str, order_id: str, payment_id: str, amount: Any, currency: Any, created: Optional[int] = None) -> Dict[str, Any]:
    return {"id": f"rzp_{payment_id}", "type": "payment.succeeded", "provider": razorpay.PROVIDER,
            "created": int(created if created is not None else time.time()),
            "data": {"subscription_ref": sub_id, "checkout_id": order_id, "provider_subscription_id": payment_id,
                     "amount_minor": amount, "currency": currency}}


@router.post("/razorpay/verify", dependencies=[Depends(require_roles(FAMILY)), Depends(rate_limit(max_requests=20, window_seconds=60, bucket="razorpay_verify"))])
def razorpay_verify(body: RazorpayVerify, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Called by the browser after Razorpay Checkout succeeds. Nothing the browser says is trusted: the signature is checked, and the
    payment is fetched from Razorpay and must match the order, amount and currency before the subscription is activated."""
    _razorpay_only()
    sub = _own_subscription(session, current_user)
    if sub and sub.provider_subscription_id == body.razorpay_payment_id and sub.status == "ACTIVE":
        return _response(sub, {"webhook_outcome": "DUPLICATE"})           # the same payment confirmed twice: nothing changes
    if not sub or sub.provider != razorpay.PROVIDER or sub.provider_checkout_id != body.razorpay_order_id:
        raise HTTPException(status_code=404, detail="Checkout not found.")   # same answer for 'missing' and 'not yours'
    if not razorpay.verify_checkout_signature(body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature):
        _audit(session, current_user, sub, "PAYMENT_SIGNATURE_REJECTED", {"order_id": body.razorpay_order_id})
        raise HTTPException(status_code=400, detail="The payment signature did not match, so it was not accepted.")
    try:
        pay = razorpay.fetch_payment(body.razorpay_payment_id)
        if pay.get("status") == "authorized":
            pay = razorpay.capture_payment(body.razorpay_payment_id, sub.price_minor, sub.currency)
    except RazorpayError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail)
    if pay.get("order_id") != body.razorpay_order_id:
        raise HTTPException(status_code=400, detail="That payment belongs to a different order.")
    if pay.get("status") != "captured":
        raise HTTPException(status_code=402, detail=f"The payment is not completed (status: {pay.get('status')}). Nothing was activated.")
    outcome = process_event(session, _succeeded_event(sub.id, body.razorpay_order_id, body.razorpay_payment_id, pay.get("amount"), pay.get("currency")))
    session.refresh(sub)
    return _response(sub, {"webhook_outcome": outcome["outcome"]})


@router.post("/webhooks/razorpay", dependencies=[Depends(rate_limit(max_requests=120, window_seconds=60, bucket="payment_webhook"))])
async def razorpay_webhook(request: Request, session: Session = Depends(get_session)):
    """Razorpay's own signed events (payment.captured / payment.failed): a backup for the browser confirmation. The signature is the proof."""
    _razorpay_only()
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="The Razorpay webhook secret is not configured.")
    raw = await request.body()
    if len(raw) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Payload too large.")
    if not razorpay.verify_webhook_signature(raw, request.headers.get("X-Razorpay-Signature")):
        record_audit_event(session, what_action="PAYMENT_WEBHOOK_REJECTED", resource_type="PAYMENT_WEBHOOK", result="DENIED",
                           who_email="payment-provider:razorpay", details={"reason": "signature mismatch"},
                           ip_address=request.client.host if request.client else None)
        raise HTTPException(status_code=400, detail="Webhook rejected: signature mismatch.")
    try:
        payload = json.loads(raw)
        entity = payload["payload"]["payment"]["entity"]
        name, payment_id, order_id = payload["event"], entity["id"], entity.get("order_id")
        sub_ref = (entity.get("notes") or {}).get("subscription_ref")
        created = int(payload.get("created_at") or time.time())
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Webhook rejected: malformed event.")
    if name == "payment.captured":
        event = _succeeded_event(sub_ref or "", order_id or "", payment_id, entity.get("amount"), entity.get("currency"), created)
    elif name == "payment.failed":
        event = {"id": f"rzp_fail_{payment_id}", "type": "payment.failed", "provider": razorpay.PROVIDER, "created": created,
                 "data": {"subscription_ref": sub_ref or "", "checkout_id": order_id}}
    else:
        return {"received": True, "outcome": "IGNORED_UNKNOWN_TYPE"}
    return {"received": True, "outcome": process_event(session, event)["outcome"]}


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
