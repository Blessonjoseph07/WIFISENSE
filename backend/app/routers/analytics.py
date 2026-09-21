from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select, or_
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import Room, Floor, Building, Organization, SensingEvent, ActivityType, Alert
from app.schemas.schemas import OccupancySummaryOut, AlertSummaryOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])
STAFF_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver", "corporate_staff"]

@router.get("/occupancy-summary", response_model=OccupancySummaryOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_occupancy_summary(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Room)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
    
    rooms = session.exec(stmt).all()
    total_rooms = len(rooms)
    occupied_rooms = 0
    vacant_rooms = 0
    occupied_room_details = []

    floors_map = {f.id: f for f in session.exec(select(Floor)).all()}
    blds_map = {b.id: b for b in session.exec(select(Building)).all()}
    orgs_map = {o.id: o for o in session.exec(select(Organization)).all()}

    breakdown = {
        "ELDER_CARE": {
            "total_rooms": 0,
            "occupied_rooms": 0,
            "vacant_rooms": 0,
            "occupancy_rate": 0.0
        },
        "CORPORATE": {
            "total_rooms": 0,
            "occupied_rooms": 0,
            "vacant_rooms": 0,
            "occupancy_rate": 0.0
        }
    }

    for r in rooms:
        flr = floors_map.get(r.floor_id) if r.floor_id else None
        bld = blds_map.get(flr.building_id) if flr and flr.building_id else None
        org = orgs_map.get(bld.organization_id) if bld and bld.organization_id else None
        org_type = org.type if org else None

        stmt_evt = select(SensingEvent).where(SensingEvent.room_id == r.id).order_by(SensingEvent.timestamp.desc())
        latest_event = session.exec(stmt_evt).first()
        
        is_occupied = False
        activity = "Empty"
        confidence = 0.0
        last_update = None

        if latest_event:
            act_type = session.get(ActivityType, latest_event.inferred_activity_id)
            if act_type:
                activity = act_type.name
                if activity != "Empty":
                    is_occupied = True
            confidence = float(latest_event.model_confidence)
            last_update = latest_event.timestamp.isoformat()

        if is_occupied:
            occupied_rooms += 1
        else:
            vacant_rooms += 1

        if org_type in breakdown:
            breakdown[org_type]["total_rooms"] += 1
            if is_occupied:
                breakdown[org_type]["occupied_rooms"] += 1
            else:
                breakdown[org_type]["vacant_rooms"] += 1

        meta = r.dimensions_metadata or {}
        classification = getattr(r, "classification", None) or meta.get("classification") or r.room_type
        expected_state = meta.get("expected_state", "Occupied" if is_occupied else "Vacant")
        schedule = meta.get("schedule", [])
        energy_state = meta.get("energy_state", {})

        discrepancy = "NORMAL"
        if expected_state == "Vacant" and is_occupied:
            discrepancy = "UNEXPECTED_OCCUPANCY"
        elif expected_state == "Occupied" and not is_occupied:
            discrepancy = "UNEXPECTED_VACANCY"

        occupied_room_details.append({
            "room_id": r.id,
            "room_name": r.name,
            "room_type": r.room_type,
            "organization_type": org_type,
            "classification": classification,
            "capacity": r.capacity or 1,
            "is_occupied": is_occupied,
            "current_activity": activity,
            "model_confidence": confidence,
            "last_updated": last_update,
            "expected_state": expected_state,
            "discrepancy": discrepancy,
            "schedule": schedule,
            "energy_state": energy_state
        })

    for b in breakdown.values():
        tot = b["total_rooms"]
        b["occupancy_rate"] = round((b["occupied_rooms"] / tot * 100), 2) if tot > 0 else 0.0

    rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0.0
    return OccupancySummaryOut(
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
        vacant_rooms=vacant_rooms,
        occupancy_rate=round(rate, 2),
        occupied_room_details=occupied_room_details,
        breakdown=breakdown
    )

@router.get("/alert-summary", response_model=AlertSummaryOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_alert_summary(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Alert)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Room).join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))

    alerts = session.exec(stmt).all()
    total_alerts = len(alerts)

    rooms_map = {r.id: r for r in session.exec(select(Room)).all()}
    floors_map = {f.id: f for f in session.exec(select(Floor)).all()}
    blds_map = {b.id: b for b in session.exec(select(Building)).all()}
    orgs_map = {o.id: o for o in session.exec(select(Organization)).all()}

    status_counts = {"new": 0, "acknowledged": 0, "resolved": 0}
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    breakdown = {
        "ELDER_CARE": {
            "total_alerts": 0,
            "status_counts": {"new": 0, "acknowledged": 0, "resolved": 0},
            "severity_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        },
        "CORPORATE": {
            "total_alerts": 0,
            "status_counts": {"new": 0, "acknowledged": 0, "resolved": 0},
            "severity_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        }
    }

    for a in alerts:
        room = rooms_map.get(a.room_id) if a.room_id else None
        flr = floors_map.get(room.floor_id) if room and room.floor_id else None
        bld = blds_map.get(flr.building_id) if flr and flr.building_id else None
        org = orgs_map.get(bld.organization_id) if bld and bld.organization_id else None
        org_type = org.type if org else None

        if a.status in status_counts:
            status_counts[a.status] += 1
        else:
            status_counts[a.status] = 1

        if a.severity in severity_counts:
            severity_counts[a.severity] += 1
        else:
            severity_counts[a.severity] = 1

        if org_type in breakdown:
            breakdown[org_type]["total_alerts"] += 1
            if a.status in breakdown[org_type]["status_counts"]:
                breakdown[org_type]["status_counts"][a.status] += 1
            else:
                breakdown[org_type]["status_counts"][a.status] = 1

            if a.severity in breakdown[org_type]["severity_counts"]:
                breakdown[org_type]["severity_counts"][a.severity] += 1
            else:
                breakdown[org_type]["severity_counts"][a.severity] = 1

    return AlertSummaryOut(
        total_alerts=total_alerts,
        status_counts=status_counts,
        severity_counts=severity_counts,
        breakdown=breakdown
    )
