from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.models.entities import ActivityType, Building, Floor, Organization, Room, RoomBooking, SensingEvent, User
from app.routers.auth import get_current_user, get_user_role_and_context, get_user_scopes, require_roles

router = APIRouter(prefix="/bookings", tags=["Room Bookings"])

MANAGER_ROLES = ["system_admin", "facility_manager"]
VIEW_ROLES = ["system_admin", "facility_manager", "corporate_staff"]
MAX_DURATION = timedelta(hours=12)
DEFAULT_LEAD_MINUTES = 5


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    room_id: str
    purpose: str = Field(min_length=3, max_length=200)
    start_at: datetime
    end_at: datetime


class BookingCancel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Optional[str] = Field(default=None, max_length=200)


class BookingOut(BaseModel):
    id: str
    room_id: str
    room_name: Optional[str] = None
    organization_id: Optional[str] = None
    organizer_name: str
    purpose: str
    start_at: datetime
    end_at: datetime
    status: str
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None


class ReminderOut(BaseModel):
    booking_id: str
    room_id: str
    room_name: Optional[str] = None
    purpose: str
    organizer_name: str
    start_at: datetime
    end_at: datetime
    minutes_until_start: int
    occupied_now: Optional[bool] = None
    occupancy_source: Optional[str] = None
    message: str


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _room_context(session: Session, room_id: str):
    room = session.get(Room, room_id)
    flr = session.get(Floor, room.floor_id) if room else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None
    return room, bld, org


def _in_scope(scopes, bld, room) -> bool:
    if scopes["is_system_admin"]:
        return True
    return bool(bld and (bld.organization_id in scopes["organization_ids"] or bld.id in scopes["building_ids"]
                         or room.id in scopes["room_ids"]))


def _out(b: RoomBooking, room_name: Optional[str]) -> BookingOut:
    return BookingOut(
        id=b.id, room_id=b.room_id, room_name=room_name, organization_id=b.organization_id,
        organizer_name=b.organizer_name, purpose=b.purpose, start_at=_utc(b.start_at), end_at=_utc(b.end_at),
        status=b.status, cancelled_at=_utc(b.cancelled_at) if b.cancelled_at else None, cancel_reason=b.cancel_reason,
    )


def _visible_bookings(session: Session, user: User, since: datetime) -> List[RoomBooking]:
    """Bookings of the corporate organizations the caller belongs to (everything for a system admin)."""
    scopes = get_user_scopes(user)
    stmt = select(RoomBooking).where(RoomBooking.end_at >= since)
    if not scopes["is_system_admin"]:
        org_ids = set(scopes["organization_ids"])
        for bid in scopes["building_ids"]:
            bld = session.get(Building, bid)
            if bld:
                org_ids.add(bld.organization_id)
        if not org_ids:
            return []
        stmt = stmt.where(RoomBooking.organization_id.in_(list(org_ids)))
    return session.exec(stmt.order_by(RoomBooking.start_at)).all()


def _occupied_now(session: Session, room_id: str):
    """Best effort from the latest sensing event of the room in the last 15 minutes: (occupied, source) or (None, None)."""
    ev = session.exec(
        select(SensingEvent).where(SensingEvent.room_id == room_id).order_by(SensingEvent.id.desc())
    ).first()
    if not ev or not ev.timestamp or _utc(ev.timestamp) < datetime.now(timezone.utc) - timedelta(minutes=15):
        return None, None
    act = session.get(ActivityType, ev.inferred_activity_id)
    return (act.name not in ("Empty",) if act else None), ev.source


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles(MANAGER_ROLES))])
def create_booking(
    payload: BookingCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    room, bld, org = _room_context(session, payload.room_id)
    if not room or not _in_scope(get_user_scopes(current_user), bld, room):
        raise HTTPException(status_code=404, detail="Room not found.")  # same answer for missing and for not yours
    if not org or org.type != "CORPORATE":
        raise HTTPException(status_code=400, detail="Only corporate rooms can be booked.")

    start, end = _utc(payload.start_at), _utc(payload.end_at)
    now = datetime.now(timezone.utc)
    if end <= start:
        raise HTTPException(status_code=400, detail="The end time must be after the start time.")
    if end - start > MAX_DURATION:
        raise HTTPException(status_code=400, detail="A booking cannot be longer than 12 hours.")
    if start < now - timedelta(minutes=2):
        raise HTTPException(status_code=400, detail="The start time is in the past.")

    clash = session.exec(
        select(RoomBooking).where(RoomBooking.room_id == room.id, RoomBooking.status == "BOOKED",
                                  RoomBooking.start_at < end, RoomBooking.end_at > start)
    ).first()
    if clash:
        raise HTTPException(
            status_code=409,
            detail=f"{room.name} is already booked {_utc(clash.start_at).strftime('%H:%M')}-{_utc(clash.end_at).strftime('%H:%M')} UTC for '{clash.purpose}'.",
        )

    booking = RoomBooking(
        room_id=room.id, organization_id=org.id, organizer_user_id=current_user.id,
        organizer_name=f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email,
        purpose=payload.purpose.strip(), start_at=start, end_at=end,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    record_audit_event(session=session, what_action="ROOM_BOOKING_CREATED", resource_type="ROOM_BOOKING", resource_id=booking.id,
                       who_user_id=current_user.id, who_email=current_user.email, organization_id=org.id,
                       details={"room": room.name, "start_at": start.isoformat(), "end_at": end.isoformat()}, request=request)
    return _out(booking, room.name)


@router.get("", response_model=List[BookingOut], dependencies=[Depends(require_roles(VIEW_ROLES))])
def list_bookings(
    room_id: Optional[str] = None,
    include_cancelled: bool = Query(True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=1)
    rows = _visible_bookings(session, current_user, since)
    names = {r.id: r.name for r in session.exec(select(Room)).all()}
    out = []
    for b in rows:
        if room_id and b.room_id != room_id:
            continue
        if not include_cancelled and b.status != "BOOKED":
            continue
        out.append(_out(b, names.get(b.room_id)))
    return out


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: str,
    payload: BookingCancel,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    role, _ctx, is_sys = get_user_role_and_context(current_user, session)
    booking = session.get(RoomBooking, booking_id)
    room, bld, _org = _room_context(session, booking.room_id) if booking else (None, None, None)
    if not booking or not room or not _in_scope(get_user_scopes(current_user), bld, room):
        raise HTTPException(status_code=404, detail="Booking not found.")
    if not (is_sys or role == "facility_manager" or booking.organizer_user_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only a facility manager or the organizer can cancel a booking.")
    if booking.status != "BOOKED":
        raise HTTPException(status_code=409, detail="This booking is already cancelled.")
    if _utc(booking.end_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="This booking has already ended.")

    booking.status = "CANCELLED"
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancelled_by = current_user.id
    booking.cancel_reason = (payload.reason or "").strip() or None
    session.add(booking)
    session.commit()
    session.refresh(booking)
    record_audit_event(session=session, what_action="ROOM_BOOKING_CANCELLED", resource_type="ROOM_BOOKING", resource_id=booking.id,
                       who_user_id=current_user.id, who_email=current_user.email, organization_id=booking.organization_id,
                       details={"room": room.name, "reason": booking.cancel_reason}, request=request)
    return _out(booking, room.name)


@router.get("/reminders", response_model=List[ReminderOut], dependencies=[Depends(require_roles(VIEW_ROLES))])
def due_reminders(
    lead_minutes: int = Query(DEFAULT_LEAD_MINUTES, ge=1, le=60),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Bookings in the caller's organization that start within `lead_minutes`. Corporate users are told to leave the room."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=lead_minutes)
    names = {r.id: r.name for r in session.exec(select(Room)).all()}
    out: List[ReminderOut] = []
    for b in _visible_bookings(session, current_user, now):
        start = _utc(b.start_at)
        if b.status != "BOOKED" or start > horizon or start < now - timedelta(minutes=2):
            continue
        mins = max(0, int((start - now).total_seconds() // 60) + (1 if (start - now).total_seconds() % 60 else 0))
        occupied, source = _occupied_now(session, b.room_id)
        room_name = names.get(b.room_id, "The room")
        when = "now" if mins == 0 else f"in {mins} minute{'s' if mins != 1 else ''}"
        out.append(ReminderOut(
            booking_id=b.id, room_id=b.room_id, room_name=room_name, purpose=b.purpose, organizer_name=b.organizer_name,
            start_at=start, end_at=_utc(b.end_at), minutes_until_start=mins, occupied_now=occupied, occupancy_source=source,
            message=f"{room_name} is booked {when} for '{b.purpose}' ({b.organizer_name}). Please vacate the room.",
        ))
        if b.reminder_issued_at is None:
            b.reminder_issued_at = now
            session.add(b)
            session.commit()
            record_audit_event(session=session, what_action="ROOM_BOOKING_REMINDER_ISSUED", resource_type="ROOM_BOOKING",
                               resource_id=b.id, who_user_id="system", organization_id=b.organization_id,
                               details={"room": room_name, "minutes_until_start": mins})
    return out
