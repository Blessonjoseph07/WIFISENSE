import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List, Optional
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import Organization, Building, Floor, Room, SensingDevice, Resident, HealthCondition, SharingPolicy, NodeFaultReport
from app.schemas.schemas import (
    OrganizationCreate, OrganizationOut,
    BuildingCreate, BuildingOut,
    FloorCreate, FloorOut,
    RoomCreate, RoomOut,
    SensingDeviceCreate, SensingDeviceOut,
    FaultReportCreate, FaultReportServiceUpdate, FaultReportOut,
    ResidentCreate, ResidentOut,
    SharingPolicyOut, SharingPolicyUpdate
)

router = APIRouter(tags=["Hierarchical Asset Management"])
STAFF_ROLES = ["system_admin", "organization_admin", "facility_manager", "caregiver", "corporate_staff"]

# ============================================================================
# 1. ORGANIZATIONS
# ============================================================================

@router.post("/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin"]))])
def create_organization(
    org: OrganizationCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if org.type not in ["ELDER_CARE", "CORPORATE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization type must be either ELDER_CARE or CORPORATE"
        )
    existing = session.exec(select(Organization).where(Organization.name == org.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization with this name already exists."
        )

    db_org = Organization(name=org.name, type=org.type)
    session.add(db_org)
    session.commit()
    session.refresh(db_org)
    return db_org

@router.get("/organizations", response_model=List[OrganizationOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_organizations(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Organization)
    if not scopes["is_system_admin"]:
        stmt = stmt.where(Organization.id.in_(list(scopes["organization_ids"])))
    return session.exec(stmt).all()

# ============================================================================
# 2. BUILDINGS
# ============================================================================

@router.post("/buildings", response_model=BuildingOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin"]))])
def create_building(
    bld: BuildingCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    org = session.get(Organization, bld.organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent Organization not found.")
    
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and org.id not in scopes["organization_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to add building to this organization.")

    db_bld = Building(organization_id=bld.organization_id, name=bld.name, address=bld.address)
    session.add(db_bld)
    session.commit()
    session.refresh(db_bld)
    return db_bld

@router.get("/buildings", response_model=List[BuildingOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_buildings(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Building)
    if not scopes["is_system_admin"]:
        stmt = stmt.where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"]))
        ))
    return session.exec(stmt).all()

# ============================================================================
# 3. FLOORS
# ============================================================================

@router.post("/floors", response_model=FloorOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def create_floor(
    flr: FloorCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    bld = session.get(Building, flr.building_id)
    if not bld:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent Building not found.")
    
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to add floor to this building.")

    db_flr = Floor(building_id=flr.building_id, floor_number=flr.floor_number, floor_plan_url=flr.floor_plan_url)
    session.add(db_flr)
    session.commit()
    session.refresh(db_flr)
    return db_flr

@router.get("/floors", response_model=List[FloorOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_floors(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Floor)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"]))
        ))
    return session.exec(stmt).all()

# ============================================================================
# 4. ROOMS
# ============================================================================

@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def create_room(
    rm: RoomCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    flr = session.get(Floor, rm.floor_id)
    if not flr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent Floor not found.")
    bld = session.get(Building, flr.building_id)
    
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to add room to this floor.")

    db_rm = Room(
        floor_id=rm.floor_id,
        name=rm.name,
        room_type=rm.room_type,
        capacity=rm.capacity or 1,
        dimensions_metadata=rm.dimensions_metadata
    )
    session.add(db_rm)
    session.commit()
    session.refresh(db_rm)
    return db_rm

@router.get("/rooms", response_model=List[RoomOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_rooms(
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
    return session.exec(stmt).all()

# ============================================================================
# 5. SENSING DEVICES
# ============================================================================

@router.post("/devices", response_model=SensingDeviceOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def create_device(
    dev: SensingDeviceCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if dev.room_id:
        rm = session.get(Room, dev.room_id)
        if not rm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned Room not found.")
        flr = session.get(Floor, rm.floor_id)
        bld = session.get(Building, flr.building_id)
        scopes = get_user_scopes(current_user)
        if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized to add device to this room.")

    existing = session.exec(select(SensingDevice).where(SensingDevice.mac_address == dev.mac_address)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A device with this MAC address is already registered.")

    db_dev = SensingDevice(
        room_id=dev.room_id,
        mac_address=dev.mac_address,
        device_status=dev.device_status or "OFFLINE",
        firmware_version=dev.firmware_version,
        hardware_token=f"TK-ESP32-{uuid.uuid4().hex[:6].upper()}"
    )
    session.add(db_dev)
    session.commit()
    session.refresh(db_dev)

    rm = session.get(Room, db_dev.room_id) if db_dev.room_id else None
    flr = session.get(Floor, rm.floor_id) if rm else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None

    return SensingDeviceOut(
        id=db_dev.id,
        room_id=db_dev.room_id,
        mac_address=db_dev.mac_address,
        device_status=db_dev.device_status,
        firmware_version=db_dev.firmware_version,
        hardware_token=db_dev.hardware_token,
        last_seen_at=db_dev.last_seen_at,
        created_at=db_dev.created_at,
        updated_at=db_dev.updated_at,
        organization_id=org.id if org else None,
        organization_name=org.name if org else "Unassigned",
        organization_type=org.type if org else "SYSTEM",
        building_name=bld.name if bld else None,
        room_name=rm.name if rm else None
    )

@router.get("/devices", response_model=List[SensingDeviceOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_devices(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(SensingDevice)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Room).join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
    raw_devices = session.exec(stmt).all()

    rooms = {r.id: r for r in session.exec(select(Room)).all()}
    floors = {f.id: f for f in session.exec(select(Floor)).all()}
    buildings = {b.id: b for b in session.exec(select(Building)).all()}
    orgs = {o.id: o for o in session.exec(select(Organization)).all()}

    output = []
    has_updates = False
    for dev in raw_devices:
        if not dev.hardware_token:
            dev.hardware_token = f"TK-ESP32-{uuid.uuid4().hex[:6].upper()}"
            session.add(dev)
            has_updates = True

        rm = rooms.get(dev.room_id) if dev.room_id else None
        flr = floors.get(rm.floor_id) if rm else None
        bld = buildings.get(flr.building_id) if flr else None
        org = orgs.get(bld.organization_id) if bld else None

        output.append(SensingDeviceOut(
            id=dev.id,
            room_id=dev.room_id,
            mac_address=dev.mac_address,
            device_status=dev.device_status,
            firmware_version=dev.firmware_version,
            hardware_token=dev.hardware_token,
            last_seen_at=dev.last_seen_at,
            created_at=dev.created_at,
            updated_at=dev.updated_at,
            organization_id=org.id if org else None,
            organization_name=org.name if org else "Unassigned / Hub",
            organization_type=org.type if org else "SYSTEM",
            building_name=bld.name if bld else "Main Facility",
            room_name=rm.name if rm else "Unassigned Room"
        ))

    if has_updates:
        session.commit()

    return output

# ============================================================================
# 6. RESIDENTS
# ============================================================================

@router.post("/residents", response_model=ResidentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def create_resident(
    res: ResidentCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    rm = session.get(Room, res.room_id)
    if not rm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target Room not found.")
    flr = session.get(Floor, rm.floor_id)
    bld = session.get(Building, flr.building_id)
    org = session.get(Organization, bld.organization_id)
    if not org or org.type != "ELDER_CARE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Residents can only be registered in ELDER_CARE organizations."
        )

    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to add resident to this room.")

    db_res = Resident(room_id=res.room_id, first_name=res.first_name, last_name=res.last_name)
    session.add(db_res)
    session.commit()
    session.refresh(db_res)
    return db_res

@router.get("/residents", response_model=List[ResidentOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_residents(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    stmt = select(Resident)
    if not scopes["is_system_admin"]:
        stmt = stmt.join(Room).join(Floor).join(Building).join(Organization).where(
            Organization.type == "ELDER_CARE",
            or_(
                Building.organization_id.in_(list(scopes["organization_ids"])),
                Building.id.in_(list(scopes["building_ids"])),
                Room.id.in_(list(scopes["room_ids"]))
            )
        )
    return session.exec(stmt).all()

@router.patch("/devices/{device_id}/toggle", response_model=SensingDeviceOut, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "corporate_staff"]))])
def toggle_device_status(
    device_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_dev = session.get(SensingDevice, device_id)
    if not db_dev:
        raise HTTPException(status_code=404, detail="Device not found.")
    
    if db_dev.room_id:
        rm = session.get(Room, db_dev.room_id)
        flr = session.get(Floor, rm.floor_id)
        bld = session.get(Building, flr.building_id)
        scopes = get_user_scopes(current_user)
        if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
            raise HTTPException(status_code=403, detail="Not authorized.")
            
    db_dev.device_status = "OFFLINE" if db_dev.device_status == "ONLINE" else "ONLINE"
    session.add(db_dev)
    session.commit()
    session.refresh(db_dev)

    rm = session.get(Room, db_dev.room_id) if db_dev.room_id else None
    flr = session.get(Floor, rm.floor_id) if rm else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None

    return SensingDeviceOut(
        id=db_dev.id,
        room_id=db_dev.room_id,
        mac_address=db_dev.mac_address,
        device_status=db_dev.device_status,
        firmware_version=db_dev.firmware_version,
        hardware_token=db_dev.hardware_token,
        last_seen_at=db_dev.last_seen_at,
        created_at=db_dev.created_at,
        updated_at=db_dev.updated_at,
        organization_id=org.id if org else None,
        organization_name=org.name if org else "Unassigned / Hub",
        organization_type=org.type if org else "SYSTEM",
        building_name=bld.name if bld else "Main Facility",
        room_name=rm.name if rm else "Unassigned Room"
    )

@router.post("/devices/{device_id}/reset-token", dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def reset_device_token(
    device_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_dev = session.get(SensingDevice, device_id)
    if not db_dev:
        raise HTTPException(status_code=404, detail="Device not found.")
    
    if db_dev.room_id:
        rm = session.get(Room, db_dev.room_id)
        if rm:
            flr = session.get(Floor, rm.floor_id)
            bld = session.get(Building, flr.building_id) if flr else None
            scopes = get_user_scopes(current_user)
            if not scopes["is_system_admin"] and bld and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
                raise HTTPException(status_code=403, detail="Not authorized to reset token for this device.")

    new_token = f"TK-ESP32-{uuid.uuid4().hex[:6].upper()}"
    db_dev.hardware_token = new_token
    session.add(db_dev)
    session.commit()
    session.refresh(db_dev)
    return {
        "status": "success",
        "device_id": db_dev.id,
        "mac_address": db_dev.mac_address,
        "hardware_token": new_token,
        "message": f"Hardware token successfully reset to {new_token}"
    }

@router.post("/devices/{device_id}/report-fault", response_model=FaultReportOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "corporate_staff", "caregiver"]))])
def report_node_fault(
    device_id: str,
    payload: FaultReportCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_dev = session.get(SensingDevice, device_id)
    if not db_dev:
        raise HTTPException(status_code=404, detail="Device not found.")

    rm = session.get(Room, db_dev.room_id) if db_dev.room_id else None
    flr = session.get(Floor, rm.floor_id) if rm else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None

    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and bld and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to report fault on this device.")

    tracer_code = f"TRC-{uuid.uuid4().hex[:8].upper()}"
    report = NodeFaultReport(
        device_id=device_id,
        reported_by_user_id=current_user.id,
        issue_type=payload.issue_type,
        description=payload.description,
        severity=payload.severity,
        tracer_token=tracer_code,
        status="REPORTED",
        service_notes=None
    )
    session.add(report)
    db_dev.device_status = "FAULT_REPORTED"
    session.add(db_dev)
    session.commit()
    session.refresh(report)

    return FaultReportOut(
        id=report.id,
        device_id=report.device_id,
        mac_address=db_dev.mac_address,
        room_name=rm.name if rm else "Unassigned Room",
        organization_name=org.name if org else "Global / Unassigned",
        organization_type=org.type if org else "SYSTEM",
        issue_type=report.issue_type,
        description=report.description,
        severity=report.severity,
        tracer_token=report.tracer_token,
        status=report.status,
        service_notes=report.service_notes,
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@router.get("/devices/fault-tracer", response_model=List[FaultReportOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "corporate_staff", "caregiver"]))])
def list_fault_reports(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    reports = session.exec(select(NodeFaultReport).order_by(NodeFaultReport.created_at.desc())).all()
    
    devs = {d.id: d for d in session.exec(select(SensingDevice)).all()}
    rooms = {r.id: r for r in session.exec(select(Room)).all()}
    floors = {f.id: f for f in session.exec(select(Floor)).all()}
    buildings = {b.id: b for b in session.exec(select(Building)).all()}
    orgs = {o.id: o for o in session.exec(select(Organization)).all()}

    results = []
    for rep in reports:
        dev = devs.get(rep.device_id)
        rm = rooms.get(dev.room_id) if dev and dev.room_id else None
        flr = floors.get(rm.floor_id) if rm else None
        bld = buildings.get(flr.building_id) if flr else None
        org = orgs.get(bld.organization_id) if bld else None

        if not scopes["is_system_admin"]:
            if bld and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]:
                continue

        results.append(FaultReportOut(
            id=rep.id,
            device_id=rep.device_id,
            mac_address=dev.mac_address if dev else "Unknown MAC",
            room_name=rm.name if rm else "Unassigned Room",
            organization_name=org.name if org else "Global / Unassigned",
            organization_type=org.type if org else "SYSTEM",
            issue_type=rep.issue_type,
            description=rep.description,
            severity=rep.severity,
            tracer_token=rep.tracer_token,
            status=rep.status,
            service_notes=rep.service_notes,
            created_at=rep.created_at,
            updated_at=rep.updated_at
        ))
    return results

@router.patch("/devices/fault-tracer/{report_id}/service", response_model=FaultReportOut, dependencies=[Depends(require_roles(["system_admin"]))])
def service_node_fault(
    report_id: str,
    payload: FaultReportServiceUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    report = session.get(NodeFaultReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Fault report not found.")

    report.status = payload.status
    if payload.service_notes:
        report.service_notes = payload.service_notes
    report.updated_at = datetime.utcnow()

    db_dev = session.get(SensingDevice, report.device_id)
    if db_dev:
        if payload.status == "REPLACED_RESOLVED":
            db_dev.device_status = "ONLINE"
            db_dev.hardware_token = f"TK-ESP32-{uuid.uuid4().hex[:6].upper()}"
            session.add(db_dev)
        elif payload.status == "UNDER_INSPECTION":
            db_dev.device_status = "INSPECTING"
            session.add(db_dev)
        elif payload.status == "DISPATCHED_SERVICE":
            db_dev.device_status = "SERVICING"
            session.add(db_dev)

    session.add(report)
    session.commit()
    session.refresh(report)

    rm = session.get(Room, db_dev.room_id) if db_dev and db_dev.room_id else None
    flr = session.get(Floor, rm.floor_id) if rm else None
    bld = session.get(Building, flr.building_id) if flr else None
    org = session.get(Organization, bld.organization_id) if bld else None

    return FaultReportOut(
        id=report.id,
        device_id=report.device_id,
        mac_address=db_dev.mac_address if db_dev else "Unknown MAC",
        room_name=rm.name if rm else "Unassigned Room",
        organization_name=org.name if org else "Global / Unassigned",
        organization_type=org.type if org else "SYSTEM",
        issue_type=report.issue_type,
        description=report.description,
        severity=report.severity,
        tracer_token=report.tracer_token,
        status=report.status,
        service_notes=report.service_notes,
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@router.get("/residents/{resident_id}/health", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_resident_health(
    resident_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    res = session.get(Resident, resident_id)
    if not res:
        raise HTTPException(status_code=404, detail="Resident not found.")
    
    rm = session.get(Room, res.room_id)
    flr = session.get(Floor, rm.floor_id)
    bld = session.get(Building, flr.building_id)
    org = session.get(Organization, bld.organization_id)
    if not org or org.type != "ELDER_CARE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Health records are only available for ELDER_CARE organizations."
        )

    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"] and bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"] and rm.id not in scopes["room_ids"]:
        raise HTTPException(status_code=403, detail="Not authorized to view health record.")

    conditions = session.exec(select(HealthCondition).where(HealthCondition.resident_id == resident_id)).all()
    
    age = None
    if res.date_of_birth:
        from datetime import date
        today = date.today()
        dob = res.date_of_birth.date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    return {
        "resident_id": res.id,
        "first_name": res.first_name,
        "last_name": res.last_name,
        "date_of_birth": res.date_of_birth.isoformat() if res.date_of_birth else None,
        "computed_age": age,
        "conditions": [
            {
                "condition_name": c.condition_name,
                "notes": c.notes,
                "diagnosed_date": c.diagnosed_date.isoformat() if c.diagnosed_date else None,
                "is_active": c.is_active
            }
            for c in conditions
        ]
    }

# ============================================================================
# 7. SHARING POLICIES (ELDER_CARE ONLY)
# ============================================================================

@router.get("/sharing-policies", response_model=List[SharingPolicyOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def list_sharing_policies(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"]:
        elder_orgs = session.exec(
            select(Organization).where(
                Organization.id.in_(list(scopes["organization_ids"])),
                Organization.type == "ELDER_CARE"
            )
        ).all()
        if not elder_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sharing policies are only accessible for ELDER_CARE organizations."
            )
        elder_org_ids = [o.id for o in elder_orgs]
        stmt = select(SharingPolicy).where(SharingPolicy.organization_id.in_(elder_org_ids))
    else:
        stmt = select(SharingPolicy)
    return session.exec(stmt).all()

@router.put("/sharing-policies/{policy_id}", response_model=SharingPolicyOut, dependencies=[Depends(require_roles(["system_admin", "organization_admin"]))])
def update_sharing_policy(
    policy_id: str,
    update_data: SharingPolicyUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    policy = session.get(SharingPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sharing policy not found.")
    
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"]:
        if policy.organization_id not in scopes["organization_ids"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify sharing policy for this organization."
            )
        org = session.get(Organization, policy.organization_id)
        if not org or org.type != "ELDER_CARE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sharing policies can only be updated for ELDER_CARE organizations."
            )

    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(policy, key, value)
    
    from datetime import datetime
    policy.updated_at = datetime.utcnow()
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy
