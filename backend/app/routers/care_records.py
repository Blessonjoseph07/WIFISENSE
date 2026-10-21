"""
Elder-care records: doctor edits, appointments and the medication administration log.

These are real, stored records entered by staff. Nothing here is sensed or simulated.
Access follows the existing elder-care rules (verify_elder_care_access): corporate users
are rejected and everyone else is limited to residents inside their organization/building scope.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, or_

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.models.entities import (
    Appointment, Building, Doctor, Floor, MedicationLog, Organization,
    Prescription, Resident, Room, User,
)
from app.routers.auth import get_current_user, get_user_scopes, require_roles
from app.routers.crud import verify_elder_care_access
from app.schemas.schemas import (
    AppointmentCreate, AppointmentOut, AppointmentUpdate, DoctorOut, DoctorUpdate,
    MedicationLogCreate, MedicationLogOut,
)

router = APIRouter(tags=["Care Records"])

READ_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver"]
WRITE_ROLES = ["system_admin", "organization_admin", "facility_manager"]  # doctors, prescriptions
SCHEDULE_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver"]  # appointments, med log


def _to_utc_naive(dt: datetime) -> datetime:
    """SQLite keeps naive datetimes; store everything as UTC wall-clock."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _appointment_out(appt: Appointment, session: Session) -> AppointmentOut:
    resident = session.get(Resident, appt.resident_id)
    doctor = session.get(Doctor, appt.doctor_id) if appt.doctor_id else None
    return AppointmentOut(
        id=appt.id,
        resident_id=appt.resident_id,
        resident_name=f"{resident.first_name} {resident.last_name}" if resident else None,
        doctor_id=appt.doctor_id,
        doctor_name=doctor.name if doctor else None,
        scheduled_at=_as_utc(appt.scheduled_at),
        purpose=appt.purpose,
        status=appt.status,
        notes=appt.notes,
        created_at=_as_utc(appt.created_at),
        updated_at=_as_utc(appt.updated_at),
    )


def _log_out(log: MedicationLog, session: Session) -> MedicationLogOut:
    rx = session.get(Prescription, log.prescription_id)
    user = session.get(User, log.administered_by) if log.administered_by else None
    return MedicationLogOut(
        id=log.id,
        resident_id=log.resident_id,
        prescription_id=log.prescription_id,
        medication_name=rx.medication_name if rx else None,
        status=log.status,
        administered_at=_as_utc(log.administered_at),
        administered_by=log.administered_by,
        administered_by_name=f"{user.first_name} {user.last_name}" if user else None,
        notes=log.notes,
    )


# ----------------------------------------------------------------------------
# Doctors: edit / remove (create + list already exist in crud.py)
# ----------------------------------------------------------------------------

@router.patch("/doctors/{doctor_id}", response_model=DoctorOut, dependencies=[Depends(require_roles(WRITE_ROLES))])
def update_doctor(
    doctor_id: str,
    body: DoctorUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    verify_elder_care_access(current_user, doctor.resident_id, session)
    for field, value in body.model_dump(exclude_unset=True).items():
        if field in ("name", "specialty") and not value:
            raise HTTPException(status_code=422, detail=f"{field} cannot be empty.")
        setattr(doctor, field, value)
    doctor.updated_at = datetime.now(timezone.utc)
    session.add(doctor)
    session.commit()
    session.refresh(doctor)
    return doctor


@router.delete("/doctors/{doctor_id}", dependencies=[Depends(require_roles(WRITE_ROLES))])
def delete_doctor(
    doctor_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    verify_elder_care_access(current_user, doctor.resident_id, session)
    # Keep appointment history: detach rather than delete.
    for appt in session.exec(select(Appointment).where(Appointment.doctor_id == doctor_id)).all():
        appt.doctor_id = None
        session.add(appt)
    session.delete(doctor)
    session.commit()
    return {"status": "deleted", "id": doctor_id}


@router.delete("/prescriptions/{prescription_id}", dependencies=[Depends(require_roles(WRITE_ROLES))])
def delete_prescription(
    prescription_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    rx = session.get(Prescription, prescription_id)
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    verify_elder_care_access(current_user, rx.resident_id, session)
    if session.exec(select(MedicationLog).where(MedicationLog.prescription_id == prescription_id)).first():
        raise HTTPException(
            status_code=409,
            detail="Prescription has medication-log entries and cannot be deleted. Set an end date instead.",
        )
    session.delete(rx)
    session.commit()
    return {"status": "deleted", "id": prescription_id}


# ----------------------------------------------------------------------------
# Appointments
# ----------------------------------------------------------------------------

@router.get("/residents/{resident_id}/appointments", response_model=List[AppointmentOut], dependencies=[Depends(require_roles(READ_ROLES))])
def list_resident_appointments(
    resident_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    verify_elder_care_access(current_user, resident_id, session)
    appts = session.exec(
        select(Appointment).where(Appointment.resident_id == resident_id).order_by(Appointment.scheduled_at.desc())
    ).all()
    return [_appointment_out(a, session) for a in appts]


@router.post("/residents/{resident_id}/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(SCHEDULE_ROLES))])
def create_appointment(
    resident_id: str,
    body: AppointmentCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    verify_elder_care_access(current_user, resident_id, session)
    if body.doctor_id:
        doctor = session.get(Doctor, body.doctor_id)
        if not doctor or doctor.resident_id != resident_id:
            raise HTTPException(status_code=400, detail="Doctor does not belong to this resident.")
    appt = Appointment(
        resident_id=resident_id,
        doctor_id=body.doctor_id,
        scheduled_at=_to_utc_naive(body.scheduled_at),
        purpose=body.purpose.strip(),
        notes=body.notes,
        created_by=current_user.id,
    )
    session.add(appt)
    session.commit()
    session.refresh(appt)
    record_audit_event(
        session, what_action="APPOINTMENT_CREATED", resource_type="appointment",
        who_user_id=current_user.id, who_email=current_user.email, resource_id=appt.id,
        details={"resident_id": resident_id},
    )
    return _appointment_out(appt, session)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut, dependencies=[Depends(require_roles(SCHEDULE_ROLES))])
def update_appointment(
    appointment_id: str,
    body: AppointmentUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    appt = session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    verify_elder_care_access(current_user, appt.resident_id, session)
    changes = body.model_dump(exclude_unset=True)
    if "scheduled_at" in changes and changes["scheduled_at"] is not None:
        changes["scheduled_at"] = _to_utc_naive(changes["scheduled_at"])
    for field, value in changes.items():
        if value is None and field in ("scheduled_at", "purpose", "status"):
            continue
        setattr(appt, field, value)
    appt.updated_at = datetime.now(timezone.utc)
    session.add(appt)
    session.commit()
    session.refresh(appt)
    record_audit_event(
        session, what_action="APPOINTMENT_UPDATED", resource_type="appointment",
        who_user_id=current_user.id, who_email=current_user.email, resource_id=appt.id,
        details={"fields": sorted(changes.keys())},
    )
    return _appointment_out(appt, session)


@router.get("/appointments/upcoming", response_model=List[AppointmentOut], dependencies=[Depends(require_roles(READ_ROLES))])
def list_upcoming_appointments(
    days: int = Query(default=7, ge=1, le=90),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """SCHEDULED appointments in the next `days` days, limited to residents the caller may see."""
    scopes = get_user_scopes(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = (
        select(Appointment)
        .join(Resident, Resident.id == Appointment.resident_id)
        .where(
            Appointment.status == "SCHEDULED",
            Appointment.scheduled_at >= now,
            Appointment.scheduled_at <= now + timedelta(days=days),
        )
        .order_by(Appointment.scheduled_at)
    )
    if not scopes["is_system_admin"]:
        stmt = (
            stmt.join(Room, Room.id == Resident.room_id)
            .join(Floor, Floor.id == Room.floor_id)
            .join(Building, Building.id == Floor.building_id)
            .join(Organization, Organization.id == Building.organization_id)
            .where(
                Organization.type == "ELDER_CARE",
                or_(
                    Building.organization_id.in_(list(scopes["organization_ids"])),
                    Building.id.in_(list(scopes["building_ids"])),
                ),
            )
        )
    return [_appointment_out(a, session) for a in session.exec(stmt).all()]


# ----------------------------------------------------------------------------
# Medication administration log
# ----------------------------------------------------------------------------

@router.post("/prescriptions/{prescription_id}/administer", response_model=MedicationLogOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(SCHEDULE_ROLES))])
def log_medication(
    prescription_id: str,
    body: MedicationLogCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    rx = session.get(Prescription, prescription_id)
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    verify_elder_care_access(current_user, rx.resident_id, session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if rx.end_date and _to_utc_naive(rx.end_date) < now:
        raise HTTPException(status_code=400, detail="Prescription has ended; no further doses can be logged.")
    log = MedicationLog(
        resident_id=rx.resident_id,
        prescription_id=rx.id,
        status=body.status,
        administered_at=now,
        administered_by=current_user.id,
        notes=body.notes,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    record_audit_event(
        session, what_action=f"MEDICATION_{body.status}", resource_type="medication_log",
        who_user_id=current_user.id, who_email=current_user.email, resource_id=log.id,
        details={"resident_id": rx.resident_id, "prescription_id": rx.id},
    )
    return _log_out(log, session)


@router.get("/residents/{resident_id}/medication-log", response_model=List[MedicationLogOut], dependencies=[Depends(require_roles(READ_ROLES))])
def list_medication_log(
    resident_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    verify_elder_care_access(current_user, resident_id, session)
    logs = session.exec(
        select(MedicationLog)
        .where(MedicationLog.resident_id == resident_id)
        .order_by(MedicationLog.administered_at.desc())
        .limit(limit)
    ).all()
    return [_log_out(l, session) for l in logs]
