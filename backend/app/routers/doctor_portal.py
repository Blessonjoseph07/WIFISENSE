"""
Authorized medical provider workflow (Phase 1, deliberately small).

    Organization --approves--> Doctor (DoctorProfile) --is assigned--> Resident (DoctorAssignment)

Rules enforced here, on every request:
  * A doctor has role "doctor" and NO organization scope, so every existing endpoint (which relies on roles
    and organization scopes) denies them by default. They can only use the /medical/* doctor endpoints.
  * A doctor must be APPROVED by the organization they applied to (suspension takes effect immediately).
  * A doctor sees a resident only through an ACTIVE assignment made by that organization's staff.
  * Elder-care organizations are isolated: staff can only review doctors and make assignments inside their own scope,
    and a doctor can only be assigned to residents of the organization that approved them.
  * Every medical-record read, write and denied attempt is written to the audit log.
This module does not diagnose, integrate with hospitals, or handle insurance, pharmacy or telemedicine.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.audit import record_audit_event
from app.core.database import get_session
from app.core.timeutil import as_utc, utcnow
from app.models.entities import (
    Alert, Allergy, Building, Consultation, DoctorAssignment, DoctorProfile, Floor, HealthCondition,
    HospitalVisit, LabReport, Organization, Prescription, Resident, Room, User, UserRole,
)
from app.routers.auth import ROLE_MAPPING, get_current_user, get_user_role_and_context, get_user_scopes, require_roles
from app.routers.crud import verify_elder_care_access
from app.schemas.schemas import (
    AlertOut, AllergyCreate, ConsultationCreate, DoctorApply, DoctorConditionCreate, DoctorPrescriptionCreate,
    DoctorReview, FollowUpUpdate, AssignmentCreate,
)

router = APIRouter(prefix="/medical", tags=["Medical Provider Workflow"])

ORG_REVIEW_ROLES = ["system_admin", "organization_admin", "facility_manager"]
STAFF_READ_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver"]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

_now = utcnow   # timezone-aware UTC (see app/core/timeutil.py)
_naive = as_utc  # historical name: normalises client datetimes to aware UTC


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return as_utc(dt).isoformat().replace("+00:00", "Z")


def _audit(session: Session, user: User, action: str, resource_type: str, resource_id: Optional[str] = None,
           result: str = "SUCCESS", details: Optional[Dict[str, Any]] = None) -> None:
    record_audit_event(
        session=session, what_action=action, resource_type=resource_type, resource_id=resource_id,
        result=result, who_user_id=user.id, who_email=user.email, details=details,
    )


def _resident_org_id(resident: Resident, session: Session) -> Optional[str]:
    room = session.get(Room, resident.room_id)
    floor = session.get(Floor, room.floor_id) if room else None
    building = session.get(Building, floor.building_id) if floor else None
    return building.organization_id if building else None


def _admin_org_ids(user: User, session: Session) -> Optional[set]:
    """Organizations the staff user may manage. None means everything (system admin)."""
    scopes = get_user_scopes(user)
    if scopes["is_system_admin"]:
        return None
    org_ids = set(scopes["organization_ids"])
    for building_id in scopes["building_ids"]:
        building = session.get(Building, building_id)
        if building:
            org_ids.add(building.organization_id)
    return org_ids


def _require_org_access(user: User, org_id: str, session: Session) -> None:
    org_ids = _admin_org_ids(user, session)
    if org_ids is not None and org_id not in org_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found or outside your organization.")


def _profile_out(profile: DoctorProfile, session: Session) -> Dict[str, Any]:
    user = session.get(User, profile.user_id)
    org = session.get(Organization, profile.organization_id)
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "doctor_name": f"{user.first_name} {user.last_name}" if user else None,
        "email": user.email if user else None,
        "organization_id": profile.organization_id,
        "organization_name": org.name if org else None,
        "clinic_name": profile.clinic_name,
        "specialty": profile.specialty,
        "license_number": profile.license_number,
        "status": profile.status,
        "review_note": profile.review_note,
        "reviewed_at": _iso(profile.reviewed_at),
        "created_at": _iso(profile.created_at),
    }


def require_approved_doctor(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DoctorProfile:
    role, _ctx, _sys = get_user_role_and_context(current_user, session)
    profile = session.exec(select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)).first()
    if role != "doctor" or not profile or profile.status != "APPROVED":
        _audit(session, current_user, "MEDICAL_ACCESS_DENIED", "DOCTOR_PORTAL", result="DENIED",
               details={"role": role, "profile_status": profile.status if profile else None})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only approved doctors may use this resource.")
    return profile


def _assigned_resident(profile: DoctorProfile, resident_id: str, user: User, session: Session) -> Resident:
    """Return the resident only if the doctor holds an ACTIVE assignment; otherwise deny and audit."""
    assignment = session.exec(
        select(DoctorAssignment).where(
            DoctorAssignment.doctor_profile_id == profile.id,
            DoctorAssignment.resident_id == resident_id,
            DoctorAssignment.status == "ACTIVE",
        )
    ).first()
    resident = session.get(Resident, resident_id) if assignment else None
    if not assignment or not resident:
        _audit(session, user, "MEDICAL_ACCESS_DENIED", "RESIDENT", resource_id=resident_id, result="DENIED",
               details={"reason": "no active assignment"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not assigned to this resident.")
    return resident


# ----------------------------------------------------------------------------
# Doctor application and organization review
# ----------------------------------------------------------------------------

@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply_as_doctor(
    body: DoctorApply,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """A registered, unprivileged user applies to one elder-care organization. Nothing is granted until it approves."""
    # Self-registered accounts hold a bare family_member role (id 7). Anything else (staff, admin, org-scoped) cannot apply.
    held = session.exec(select(UserRole).where(UserRole.user_id == current_user.id)).all()
    if any(r.role_id != ROLE_MAPPING["family_member"] or r.organization_id or r.building_id or r.room_id for r in held):
        raise HTTPException(status_code=400, detail="Only a plain registered account can apply as a doctor.")
    if session.exec(select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)).first():
        raise HTTPException(status_code=409, detail="You already have a doctor application.")
    org = session.get(Organization, body.organization_id)
    if not org or org.type != "ELDER_CARE":
        raise HTTPException(status_code=400, detail="Choose an elder-care organization.")
    profile = DoctorProfile(
        user_id=current_user.id, organization_id=org.id, clinic_name=body.clinic_name.strip(),
        specialty=body.specialty.strip(), license_number=body.license_number.strip(), created_at=_now(),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    _audit(session, current_user, "DOCTOR_APPLICATION_SUBMITTED", "DOCTOR_PROFILE", profile.id,
           details={"organization_id": org.id})
    return _profile_out(profile, session)


@router.get("/me")
def my_doctor_profile(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    profile = session.exec(select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No doctor application found.")
    return _profile_out(profile, session)


@router.get("/providers", dependencies=[Depends(require_roles(ORG_REVIEW_ROLES))])
def list_providers(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(DoctorProfile).order_by(DoctorProfile.created_at.desc())
    if status_filter:
        stmt = stmt.where(DoctorProfile.status == status_filter.upper())
    org_ids = _admin_org_ids(current_user, session)
    if org_ids is not None:
        stmt = stmt.where(DoctorProfile.organization_id.in_(list(org_ids)))
    return [_profile_out(p, session) for p in session.exec(stmt).all()]


_TRANSITIONS = {
    "APPROVE": ({"PENDING", "SUSPENDED"}, "APPROVED"),
    "REJECT": ({"PENDING"}, "REJECTED"),
    "SUSPEND": ({"APPROVED"}, "SUSPENDED"),
}


@router.patch("/providers/{profile_id}/review", dependencies=[Depends(require_roles(ORG_REVIEW_ROLES))])
def review_provider(
    profile_id: str,
    body: DoctorReview,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    profile = session.get(DoctorProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor application not found.")
    _require_org_access(current_user, profile.organization_id, session)
    allowed_from, new_status = _TRANSITIONS[body.decision]
    if profile.status not in allowed_from:
        raise HTTPException(status_code=409, detail=f"Cannot {body.decision.lower()} a doctor who is {profile.status}.")
    if body.decision in ("REJECT", "SUSPEND") and not (body.note and body.note.strip()):
        raise HTTPException(status_code=422, detail="A note is required to reject or suspend a doctor.")

    profile.status = new_status
    profile.reviewed_by = current_user.id
    profile.reviewed_at = _now()
    profile.review_note = body.note.strip() if body.note else None
    session.add(profile)
    if new_status == "APPROVED":
        # Doctor role carries NO organization/building/room scope on purpose (see module docstring).
        # The bare family_member role is replaced: a doctor account is a dedicated account, not also a family account.
        for held in session.exec(select(UserRole).where(UserRole.user_id == profile.user_id)).all():
            if held.role_id == ROLE_MAPPING["family_member"] and not held.organization_id:
                session.delete(held)
        if not session.exec(select(UserRole).where(UserRole.user_id == profile.user_id, UserRole.role_id == ROLE_MAPPING["doctor"])).first():
            session.add(UserRole(user_id=profile.user_id, role_id=ROLE_MAPPING["doctor"]))
    session.commit()
    session.refresh(profile)
    _audit(session, current_user, f"DOCTOR_{body.decision}", "DOCTOR_PROFILE", profile.id,
           details={"organization_id": profile.organization_id, "new_status": new_status})
    return _profile_out(profile, session)


# ----------------------------------------------------------------------------
# Doctor -> resident assignments (organization staff)
# ----------------------------------------------------------------------------

def _assignment_out(a: DoctorAssignment, session: Session) -> Dict[str, Any]:
    profile = session.get(DoctorProfile, a.doctor_profile_id)
    user = session.get(User, profile.user_id) if profile else None
    resident = session.get(Resident, a.resident_id)
    return {
        "id": a.id,
        "doctor_profile_id": a.doctor_profile_id,
        "doctor_name": f"{user.first_name} {user.last_name}" if user else None,
        "resident_id": a.resident_id,
        "resident_name": f"{resident.first_name} {resident.last_name}" if resident else None,
        "status": a.status,
        "created_at": _iso(a.created_at),
        "revoked_at": _iso(a.revoked_at),
    }


@router.post("/assignments", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(ORG_REVIEW_ROLES))])
def assign_doctor(
    body: AssignmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    profile = session.get(DoctorProfile, body.doctor_profile_id)
    resident = session.get(Resident, body.resident_id)
    if not profile or not resident:
        raise HTTPException(status_code=404, detail="Doctor or resident not found.")
    _require_org_access(current_user, profile.organization_id, session)
    resident_org = _resident_org_id(resident, session)
    if resident_org != profile.organization_id:
        raise HTTPException(status_code=403, detail="Doctor and resident must belong to the same organization.")
    if profile.status != "APPROVED":
        raise HTTPException(status_code=409, detail="Only approved doctors can be assigned to residents.")
    existing = session.exec(
        select(DoctorAssignment).where(
            DoctorAssignment.doctor_profile_id == profile.id,
            DoctorAssignment.resident_id == resident.id,
            DoctorAssignment.status == "ACTIVE",
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Doctor is already assigned to this resident.")
    assignment = DoctorAssignment(
        doctor_profile_id=profile.id, resident_id=resident.id, assigned_by=current_user.id, created_at=_now(),
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    _audit(session, current_user, "DOCTOR_ASSIGNED", "DOCTOR_ASSIGNMENT", assignment.id,
           details={"doctor_profile_id": profile.id, "resident_id": resident.id})
    return _assignment_out(assignment, session)


@router.get("/assignments", dependencies=[Depends(require_roles(ORG_REVIEW_ROLES))])
def list_assignments(
    resident_id: Optional[str] = None,
    doctor_profile_id: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    org_ids = _admin_org_ids(current_user, session)
    out = []
    stmt = select(DoctorAssignment).order_by(DoctorAssignment.created_at.desc())
    if resident_id:
        stmt = stmt.where(DoctorAssignment.resident_id == resident_id)
    if doctor_profile_id:
        stmt = stmt.where(DoctorAssignment.doctor_profile_id == doctor_profile_id)
    for a in session.exec(stmt).all():
        profile = session.get(DoctorProfile, a.doctor_profile_id)
        if org_ids is None or (profile and profile.organization_id in org_ids):
            out.append(_assignment_out(a, session))
    return out


@router.delete("/assignments/{assignment_id}", dependencies=[Depends(require_roles(ORG_REVIEW_ROLES))])
def revoke_assignment(
    assignment_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    a = session.get(DoctorAssignment, assignment_id)
    profile = session.get(DoctorProfile, a.doctor_profile_id) if a else None
    if not a or not profile:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    _require_org_access(current_user, profile.organization_id, session)
    if a.status == "REVOKED":
        raise HTTPException(status_code=409, detail="Assignment is already revoked.")
    a.status = "REVOKED"
    a.revoked_by = current_user.id
    a.revoked_at = _now()
    session.add(a)
    session.commit()
    _audit(session, current_user, "DOCTOR_ASSIGNMENT_REVOKED", "DOCTOR_ASSIGNMENT", a.id,
           details={"doctor_profile_id": a.doctor_profile_id, "resident_id": a.resident_id})
    return _assignment_out(a, session)


# ----------------------------------------------------------------------------
# Doctor portal: only explicitly assigned residents
# ----------------------------------------------------------------------------

def _active_assignments(profile: DoctorProfile, session: Session) -> List[DoctorAssignment]:
    return session.exec(
        select(DoctorAssignment).where(
            DoctorAssignment.doctor_profile_id == profile.id, DoctorAssignment.status == "ACTIVE"
        )
    ).all()


@router.get("/my-residents")
def my_residents(
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
):
    out = []
    for a in _active_assignments(profile, session):
        r = session.get(Resident, a.resident_id)
        room = session.get(Room, r.room_id) if r else None
        if r:
            out.append({
                "id": r.id,
                "name": f"{r.first_name} {r.last_name}",
                "date_of_birth": _iso(r.date_of_birth),
                "room_name": room.name if room else None,
                "status": r.resident_status,
                "assigned_since": _iso(a.created_at),
            })
    return out


@router.get("/my-alerts")
def my_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
):
    """Fall alerts for assigned residents only, with their confidence and verification state."""
    out = []
    for a in _active_assignments(profile, session):
        r = session.get(Resident, a.resident_id)
        if not r:
            continue
        alerts = session.exec(
            select(Alert).where(Alert.room_id == r.room_id, Alert.event_type == "Fall_Detected")
            .order_by(Alert.created_at.desc()).limit(limit)
        ).all()
        for al in alerts:
            data = AlertOut.model_validate(al)
            out.append({
                "alert_id": al.id,
                "resident_id": r.id,
                "resident_name": f"{r.first_name} {r.last_name}",
                "created_at": _iso(al.created_at),
                "status": al.status,
                "source": data.source,
                "confidence": data.confidence,
                "confidence_level": data.confidence_level,
                "signal_level": data.signal_level,
                "verification_status": data.verification_status,
                "requires_verification": data.requires_verification,
            })
    out.sort(key=lambda x: x["created_at"], reverse=True)
    return out[:limit]


@router.get("/residents/{resident_id}/record")
def resident_medical_record(
    resident_id: str,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    resident = _assigned_resident(profile, resident_id, current_user, session)
    room = session.get(Room, resident.room_id)

    def rows(model, order):
        return session.exec(select(model).where(model.resident_id == resident_id).order_by(order)).all()

    fall_alerts = session.exec(
        select(Alert).where(Alert.room_id == resident.room_id, Alert.event_type == "Fall_Detected")
        .order_by(Alert.created_at.desc()).limit(10)
    ).all()

    _audit(session, current_user, "MEDICAL_RECORD_VIEWED", "RESIDENT", resident_id,
           details={"doctor_profile_id": profile.id})
    return {
        "resident": {
            "id": resident.id,
            "name": f"{resident.first_name} {resident.last_name}",
            "date_of_birth": _iso(resident.date_of_birth),
            "room_name": room.name if room else None,
            "status": resident.resident_status,
        },
        "conditions": [
            {"id": c.id, "name": c.condition_name, "notes": c.notes, "active": c.is_active,
             "diagnosed_date": _iso(c.diagnosed_date)}
            for c in rows(HealthCondition, HealthCondition.created_at.desc())
        ],
        "allergies": [
            {"id": a.id, "allergen": a.allergen, "reaction": a.reaction, "severity": a.severity}
            for a in rows(Allergy, Allergy.created_at.desc())
        ],
        "prescriptions": [
            {"id": p.id, "medication": p.medication_name, "dosage": p.dosage, "frequency": p.frequency,
             "start_date": _iso(p.start_date), "end_date": _iso(p.end_date), "prescribed_by": p.prescribing_doctor}
            for p in rows(Prescription, Prescription.start_date.desc())
        ],
        "consultations": [_consultation_out(c, session) for c in rows(Consultation, Consultation.consulted_at.desc())],
        "lab_reports": [
            {"id": l.id, "test": l.test_name, "date": _iso(l.test_date), "result": l.result_summary,
             "normal_range": l.normal_range, "flag": l.flag}
            for l in rows(LabReport, LabReport.test_date.desc())
        ],
        "hospital_visits": [
            {"id": v.id, "hospital": v.hospital_name, "reason": v.reason, "date": _iso(v.visit_date),
             "doctor_notes": v.doctor_notes}
            for v in rows(HospitalVisit, HospitalVisit.visit_date.desc())
        ],
        "recent_fall_alerts": [
            {
                "alert_id": al.id, "created_at": _iso(al.created_at), "status": al.status,
                "source": al.source, "confidence": al.confidence,
                "confidence_level": AlertOut.model_validate(al).confidence_level,
                "verification_status": al.verification_status,
                "requires_verification": AlertOut.model_validate(al).requires_verification,
            }
            for al in fall_alerts
        ],
    }


def _consultation_out(c: Consultation, session: Session) -> Dict[str, Any]:
    profile = session.get(DoctorProfile, c.doctor_profile_id)
    user = session.get(User, profile.user_id) if profile else None
    return {
        "id": c.id,
        "consulted_at": _iso(c.consulted_at),
        "reason": c.reason,
        "notes": c.notes,
        "follow_up_date": _iso(c.follow_up_date),
        "follow_up_done": c.follow_up_done,
        "doctor_name": f"{user.first_name} {user.last_name}" if user else None,
    }


@router.post("/residents/{resident_id}/consultations", status_code=status.HTTP_201_CREATED)
def add_consultation(
    resident_id: str,
    body: ConsultationCreate,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _assigned_resident(profile, resident_id, current_user, session)
    c = Consultation(
        resident_id=resident_id, doctor_profile_id=profile.id, consulted_at=_naive(body.consulted_at) or _now(),
        reason=body.reason.strip(), notes=body.notes, follow_up_date=_naive(body.follow_up_date), created_at=_now(),
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    _audit(session, current_user, "CONSULTATION_RECORDED", "CONSULTATION", c.id, details={"resident_id": resident_id})
    return _consultation_out(c, session)


@router.patch("/consultations/{consultation_id}/follow-up")
def update_follow_up(
    consultation_id: str,
    body: FollowUpUpdate,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    c = session.get(Consultation, consultation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    _assigned_resident(profile, c.resident_id, current_user, session)
    c.follow_up_done = body.done
    session.add(c)
    session.commit()
    _audit(session, current_user, "FOLLOW_UP_UPDATED", "CONSULTATION", c.id, details={"done": body.done})
    return _consultation_out(c, session)


@router.post("/residents/{resident_id}/allergies", status_code=status.HTTP_201_CREATED)
def add_allergy(
    resident_id: str,
    body: AllergyCreate,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _assigned_resident(profile, resident_id, current_user, session)
    a = Allergy(resident_id=resident_id, allergen=body.allergen.strip(), reaction=body.reaction,
                severity=body.severity, recorded_by=current_user.id, created_at=_now())
    session.add(a)
    session.commit()
    session.refresh(a)
    _audit(session, current_user, "ALLERGY_RECORDED", "ALLERGY", a.id, details={"resident_id": resident_id})
    return {"id": a.id, "allergen": a.allergen, "reaction": a.reaction, "severity": a.severity}


@router.post("/residents/{resident_id}/conditions", status_code=status.HTTP_201_CREATED)
def add_condition(
    resident_id: str,
    body: DoctorConditionCreate,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _assigned_resident(profile, resident_id, current_user, session)
    c = HealthCondition(resident_id=resident_id, condition_name=body.condition_name.strip(), notes=body.notes,
                        diagnosed_date=_naive(body.diagnosed_date), is_active=True)
    session.add(c)
    session.commit()
    session.refresh(c)
    _audit(session, current_user, "CONDITION_RECORDED", "HEALTH_CONDITION", c.id, details={"resident_id": resident_id})
    return {"id": c.id, "name": c.condition_name, "notes": c.notes}


@router.post("/residents/{resident_id}/prescriptions", status_code=status.HTTP_201_CREATED)
def add_prescription(
    resident_id: str,
    body: DoctorPrescriptionCreate,
    profile: DoctorProfile = Depends(require_approved_doctor),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _assigned_resident(profile, resident_id, current_user, session)
    rx = Prescription(
        resident_id=resident_id, medication_name=body.medication_name.strip(), dosage=body.dosage.strip(),
        frequency=body.frequency.strip(), start_date=_naive(body.start_date) or _now(),
        end_date=_naive(body.end_date), prescribing_doctor=f"{current_user.first_name} {current_user.last_name}",
    )
    session.add(rx)
    session.commit()
    session.refresh(rx)
    _audit(session, current_user, "PRESCRIPTION_RECORDED", "PRESCRIPTION", rx.id, details={"resident_id": resident_id})
    return {"id": rx.id, "medication": rx.medication_name, "dosage": rx.dosage, "frequency": rx.frequency,
            "prescribed_by": rx.prescribing_doctor}


# ----------------------------------------------------------------------------
# Care staff (read-only view of what doctors recorded)
# ----------------------------------------------------------------------------

@router.get("/residents/{resident_id}/staff-summary", dependencies=[Depends(require_roles(STAFF_READ_ROLES))])
def staff_medical_summary(
    resident_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Allergies, consultations and open follow-ups for care staff of the resident's own organization."""
    verify_elder_care_access(current_user, resident_id, session)
    allergies = session.exec(select(Allergy).where(Allergy.resident_id == resident_id)).all()
    consultations = session.exec(
        select(Consultation).where(Consultation.resident_id == resident_id).order_by(Consultation.consulted_at.desc())
    ).all()
    _audit(session, current_user, "MEDICAL_SUMMARY_VIEWED", "RESIDENT", resident_id)
    return {
        "allergies": [{"id": a.id, "allergen": a.allergen, "reaction": a.reaction, "severity": a.severity} for a in allergies],
        "consultations": [_consultation_out(c, session) for c in consultations],
        "open_follow_ups": [_consultation_out(c, session) for c in consultations if c.follow_up_date and not c.follow_up_done],
    }
