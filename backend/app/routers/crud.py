import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List, Optional
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import (
    Organization, Building, Floor, Room, SensingDevice, Resident,
    HealthCondition, SharingPolicy, NodeFaultReport, EmergencyContact,
    Doctor, HospitalVisit, LabReport, Prescription, RoomCalibration,
    RoomSchedule, SensingEvent, ActivityType, Alert
)
from app.schemas.schemas import (
    OrganizationCreate, OrganizationOut,
    BuildingCreate, BuildingOut,
    FloorCreate, FloorOut,
    RoomCreate, RoomOut,
    SensingDeviceCreate, SensingDeviceOut,
    FaultReportCreate, FaultReportServiceUpdate, FaultReportOut,
    ResidentCreate, ResidentOut,
    SharingPolicyOut, SharingPolicyUpdate,
    EmergencyContactCreate, EmergencyContactUpdate, EmergencyContactOut,
    DoctorCreate, DoctorOut,
    HospitalVisitCreate, HospitalVisitOut,
    LabReportCreate, LabReportOut,
    PrescriptionCreate, PrescriptionOut,
    ResidentDetailOut,
    RoomCalibrationOut,
    RoomScheduleCreate, RoomScheduleOut,
    EnergyActionIn, EnergyActionOut
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
        classification=rm.classification or rm.room_type,
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

@router.patch("/devices/fault-tracer/{report_id}/service", response_model=FaultReportOut, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def service_node_fault(
    report_id: str,
    payload: FaultReportServiceUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    from app.routers.auth import get_user_role_and_context
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    report = session.get(NodeFaultReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Fault report not found.")

    # Facility Managers can review and transition to UNDER_INSPECTION or add notes
    if not is_sysadmin and payload.status in ["DISPATCHED_SERVICE", "REPLACED_RESOLVED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only System Administrators at the Platform Service Desk can dispatch service or mark faults REPLACED_RESOLVED."
        )

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

# ============================================================================
# 8. EMERGENCY CONTACTS & STRUCTURED MEDICAL RECORDS (PHASE 2 & 2A)
# ============================================================================

def verify_elder_care_access(current_user, resident_id: str, session: Session):
    from app.routers.auth import get_user_role_and_context
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (app_context == "CORPORATE" or role_name == "corporate_staff"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Corporate users are strictly prohibited from accessing elder-care resident records."
        )
    resident = session.get(Resident, resident_id)
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident record not found.")
    
    scopes = get_user_scopes(current_user)
    if not scopes["is_system_admin"]:
        rm = session.get(Room, resident.room_id)
        if rm:
            flr = session.get(Floor, rm.floor_id)
            bld = session.get(Building, flr.building_id) if flr else None
            if bld and (bld.organization_id not in scopes["organization_ids"] and bld.id not in scopes["building_ids"]):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Resident outside your organization scope.")
    return resident

@router.get("/residents/{resident_id}/profile-details", response_model=ResidentDetailOut, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def get_resident_profile_details(
    resident_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    resident = verify_elder_care_access(current_user, resident_id, session)
    room = session.get(Room, resident.room_id)
    
    # Emergency contacts
    contacts = session.exec(
        select(EmergencyContact).where(EmergencyContact.resident_id == resident_id).order_by(EmergencyContact.priority)
    ).all()

    # Health conditions
    conditions = session.exec(
        select(HealthCondition).where(HealthCondition.resident_id == resident_id).order_by(HealthCondition.created_at.desc())
    ).all()

    # Doctors
    doctors = session.exec(
        select(Doctor).where(Doctor.resident_id == resident_id)
    ).all()

    # Hospital Visits
    visits = session.exec(
        select(HospitalVisit).where(HospitalVisit.resident_id == resident_id).order_by(HospitalVisit.visit_date.desc())
    ).all()

    # Lab reports
    reports = session.exec(
        select(LabReport).where(LabReport.resident_id == resident_id).order_by(LabReport.test_date.desc())
    ).all()

    # Prescriptions
    rx = session.exec(
        select(Prescription).where(Prescription.resident_id == resident_id).order_by(Prescription.start_date.desc())
    ).all()

    # Sensing telemetry
    latest_event = session.exec(
        select(SensingEvent).where(SensingEvent.room_id == resident.room_id).order_by(SensingEvent.timestamp.desc())
    ).first()

    current_activity = "Resting"
    latest_event_dict = None
    if latest_event:
        act = session.get(ActivityType, latest_event.inferred_activity_id)
        if act:
            current_activity = act.name
        latest_event_dict = {
            "timestamp": latest_event.timestamp.isoformat(),
            "activity": current_activity,
            "confidence": latest_event.model_confidence,
            "rssi": latest_event.rssi,
            "subcarriers": latest_event.subcarrier_count,
            "signal_quality": latest_event.signal_quality or 94,
            "event_type": latest_event.event_type or "SensingTelemetry"
        }

    # Recent history
    recent_events = session.exec(
        select(SensingEvent).where(SensingEvent.room_id == resident.room_id).order_by(SensingEvent.timestamp.desc()).limit(6)
    ).all()
    recent_history = []
    for ev in recent_events:
        act = session.get(ActivityType, ev.inferred_activity_id)
        recent_history.append({
            "timestamp": ev.timestamp.strftime("%H:%M:%S"),
            "activity": act.name if act else "Unknown",
            "confidence": round(ev.model_confidence * 100, 1),
            "signal_quality": ev.signal_quality or 94
        })

    # Active alert
    active_alert = session.exec(
        select(Alert).where(Alert.room_id == resident.room_id, Alert.status != "resolved").order_by(Alert.created_at.desc())
    ).first()
    alert_dict = None
    safety_status = "Normal"
    if active_alert:
        alert_dict = {
            "id": active_alert.id,
            "event_type": active_alert.event_type,
            "severity": active_alert.severity,
            "message": active_alert.message,
            "created_at": active_alert.created_at.strftime("%d %b %Y %H:%M:%S")
        }
        safety_status = "EMERGENCY" if active_alert.severity == "CRITICAL" else "Attention"

    return ResidentDetailOut(
        id=resident.id,
        room_id=resident.room_id,
        room_name=room.name if room else "Unknown",
        first_name=resident.first_name,
        last_name=resident.last_name,
        date_of_birth=resident.date_of_birth,
        resident_status=resident.resident_status or "Active",
        emergency_contacts=contacts,
        health_conditions=conditions,
        doctors=doctors,
        hospital_visits=visits,
        lab_reports=reports,
        prescriptions=rx,
        current_activity=current_activity,
        latest_sensing_event=latest_event_dict,
        safety_status=safety_status,
        active_alert=alert_dict,
        recent_activity_history=recent_history
    )

@router.get("/residents/{resident_id}/emergency-contacts", response_model=List[EmergencyContactOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def list_resident_emergency_contacts(
    resident_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    verify_elder_care_access(current_user, resident_id, session)
    return session.exec(
        select(EmergencyContact).where(EmergencyContact.resident_id == resident_id).order_by(EmergencyContact.priority)
    ).all()

@router.post("/residents/{resident_id}/emergency-contacts", response_model=EmergencyContactOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def add_resident_emergency_contact(
    resident_id: str,
    contact_in: EmergencyContactCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    verify_elder_care_access(current_user, resident_id, session)
    new_contact = EmergencyContact(
        resident_id=resident_id,
        name=contact_in.name,
        relationship=contact_in.relationship,
        phone=contact_in.phone,
        priority=contact_in.priority or 1,
        email=contact_in.email,
        availability=contact_in.availability or "24/7 Primary Response"
    )
    session.add(new_contact)
    session.commit()
    session.refresh(new_contact)
    return new_contact

@router.delete("/emergency-contacts/{contact_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def delete_emergency_contact(
    contact_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    contact = session.get(EmergencyContact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Emergency contact not found.")
    verify_elder_care_access(current_user, contact.resident_id, session)
    
    # Check if this is the only emergency contact (Rule: Every resident must have at least one emergency contact)
    remaining_count = session.exec(
        select(EmergencyContact).where(EmergencyContact.resident_id == contact.resident_id, EmergencyContact.id != contact_id)
    ).all()
    if len(remaining_count) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the sole emergency contact. Every resident must have at least one emergency contact."
        )
    session.delete(contact)
    session.commit()
    return {"status": "deleted", "id": contact_id}

@router.get("/emergency-contacts/missing", response_model=List[ResidentOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def list_residents_missing_emergency_contacts(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    from app.routers.auth import get_user_role_and_context
    role_name, app_context, is_sysadmin = get_user_role_and_context(current_user, session)
    if not is_sysadmin and (app_context == "CORPORATE" or role_name == "corporate_staff"):
        raise HTTPException(status_code=403, detail="Corporate users cannot access elder care emergency contacts.")
    
    residents = session.exec(select(Resident)).all()
    missing = []
    for res in residents:
        cnt = session.exec(select(EmergencyContact).where(EmergencyContact.resident_id == res.id)).all()
        if len(cnt) == 0:
            missing.append(res)
    return missing

# Medical sub-entities
@router.get("/residents/{resident_id}/doctors", response_model=List[DoctorOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def list_resident_doctors(resident_id: str, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    return session.exec(select(Doctor).where(Doctor.resident_id == resident_id)).all()

@router.post("/residents/{resident_id}/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def add_resident_doctor(resident_id: str, doc_in: DoctorCreate, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    doc = Doctor(
        resident_id=resident_id,
        name=doc_in.name,
        specialty=doc_in.specialty,
        hospital=doc_in.hospital,
        phone=doc_in.phone,
        email=doc_in.email
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc

@router.get("/residents/{resident_id}/hospital-visits", response_model=List[HospitalVisitOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def list_resident_hospital_visits(resident_id: str, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    return session.exec(select(HospitalVisit).where(HospitalVisit.resident_id == resident_id).order_by(HospitalVisit.visit_date.desc())).all()

@router.post("/residents/{resident_id}/hospital-visits", response_model=HospitalVisitOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def add_resident_hospital_visit(resident_id: str, visit_in: HospitalVisitCreate, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    visit = HospitalVisit(
        resident_id=resident_id,
        hospital_name=visit_in.hospital_name,
        reason=visit_in.reason,
        visit_date=visit_in.visit_date,
        discharge_date=visit_in.discharge_date,
        doctor_notes=visit_in.doctor_notes
    )
    session.add(visit)
    session.commit()
    session.refresh(visit)
    return visit

@router.get("/residents/{resident_id}/lab-reports", response_model=List[LabReportOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def list_resident_lab_reports(resident_id: str, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    return session.exec(select(LabReport).where(LabReport.resident_id == resident_id).order_by(LabReport.test_date.desc())).all()

@router.post("/residents/{resident_id}/lab-reports", response_model=LabReportOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def add_resident_lab_report(resident_id: str, report_in: LabReportCreate, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    rep = LabReport(
        resident_id=resident_id,
        test_name=report_in.test_name,
        test_date=report_in.test_date,
        result_summary=report_in.result_summary,
        normal_range=report_in.normal_range,
        flag=report_in.flag or "NORMAL"
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep

@router.get("/residents/{resident_id}/prescriptions", response_model=List[PrescriptionOut], dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager", "caregiver"]))])
def list_resident_prescriptions(resident_id: str, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    return session.exec(select(Prescription).where(Prescription.resident_id == resident_id).order_by(Prescription.start_date.desc())).all()

@router.post("/residents/{resident_id}/prescriptions", response_model=PrescriptionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def add_resident_prescription(resident_id: str, rx_in: PrescriptionCreate, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    verify_elder_care_access(current_user, resident_id, session)
    rx = Prescription(
        resident_id=resident_id,
        medication_name=rx_in.medication_name,
        dosage=rx_in.dosage,
        frequency=rx_in.frequency,
        start_date=rx_in.start_date,
        end_date=rx_in.end_date,
        prescribing_doctor=rx_in.prescribing_doctor
    )
    session.add(rx)
    session.commit()
    session.refresh(rx)
    return rx

# ============================================================================
# 9. RUVIEW-INSPIRED ROOM CALIBRATION & RF FINGERPRINT (PHASE 7)
# ============================================================================

@router.get("/rooms/{room_id}/calibration", response_model=RoomCalibrationOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_room_calibration(
    room_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    cal = session.exec(select(RoomCalibration).where(RoomCalibration.room_id == room_id)).first()
    if not cal:
        # Create a deterministic baseline calibration if none exists
        cal = RoomCalibration(
            room_id=room_id,
            baseline_status="VALID",
            baseline_captured_at=datetime.utcnow(),
            noise_floor_dbm=-88,
            baseline_rssi=-48,
            rf_similarity_pct=96.5,
            rf_environment_status="NORMAL",
            subcarrier_profile={"subcarriers": 56, "pilot_carriers": [7, 21, 35, 49], "reference_phase_variance": 0.042}
        )
        session.add(cal)
        session.commit()
        session.refresh(cal)
    
    dev = session.exec(select(SensingDevice).where(SensingDevice.room_id == room_id)).first()
    return RoomCalibrationOut(
        id=cal.id,
        room_id=room.id,
        room_name=room.name,
        device_id=dev.id if dev else None,
        device_mac=dev.mac_address if dev else "Unassigned",
        baseline_status=cal.baseline_status,
        baseline_captured_at=cal.baseline_captured_at,
        noise_floor_dbm=cal.noise_floor_dbm,
        baseline_rssi=cal.baseline_rssi,
        rf_similarity_pct=cal.rf_similarity_pct,
        rf_environment_status=cal.rf_environment_status,
        subcarrier_profile=cal.subcarrier_profile
    )

@router.post("/rooms/{room_id}/calibration/recalibrate", response_model=RoomCalibrationOut, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def recalibrate_room_baseline(
    room_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    cal = session.exec(select(RoomCalibration).where(RoomCalibration.room_id == room_id)).first()
    if not cal:
        cal = RoomCalibration(room_id=room_id)
    cal.baseline_status = "VALID"
    cal.baseline_captured_at = datetime.utcnow()
    cal.rf_similarity_pct = 98.8
    cal.rf_environment_status = "NORMAL"
    cal.updated_at = datetime.utcnow()
    session.add(cal)
    session.commit()
    session.refresh(cal)

    dev = session.exec(select(SensingDevice).where(SensingDevice.room_id == room_id)).first()
    return RoomCalibrationOut(
        id=cal.id,
        room_id=room.id,
        room_name=room.name,
        device_id=dev.id if dev else None,
        device_mac=dev.mac_address if dev else "Unassigned",
        baseline_status=cal.baseline_status,
        baseline_captured_at=cal.baseline_captured_at,
        noise_floor_dbm=cal.noise_floor_dbm,
        baseline_rssi=cal.baseline_rssi,
        rf_similarity_pct=cal.rf_similarity_pct,
        rf_environment_status=cal.rf_environment_status,
        subcarrier_profile=cal.subcarrier_profile
    )

# ============================================================================
# 10. CORPORATE SPACE INTELLIGENCE: SCHEDULES & ENERGY (PHASE 8)
# ============================================================================

@router.get("/rooms/{room_id}/schedules", response_model=List[RoomScheduleOut], dependencies=[Depends(require_roles(STAFF_ROLES))])
def list_room_schedules(room_id: str, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    return session.exec(select(RoomSchedule).where(RoomSchedule.room_id == room_id)).all()

@router.post("/rooms/{room_id}/schedules", response_model=RoomScheduleOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["system_admin", "organization_admin", "facility_manager"]))])
def create_room_schedule(room_id: str, sched_in: RoomScheduleCreate, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    sched = RoomSchedule(
        room_id=room_id,
        day_of_week=sched_in.day_of_week or "ALL",
        start_time=sched_in.start_time,
        end_time=sched_in.end_time,
        expected_status=sched_in.expected_status or "FREE",
        meeting_title=sched_in.meeting_title,
        organizer=sched_in.organizer,
        ac_state=sched_in.ac_state or "OFF"
    )
    session.add(sched)
    session.commit()
    session.refresh(sched)
    return sched

@router.get("/schedules/unexpected-occupancy", dependencies=[Depends(require_roles(STAFF_ROLES))])
def detect_unexpected_occupancy(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    # Compares live sensing occupancy against expected availability in CORPORATE rooms
    stmt = select(Room).join(Floor).join(Building).join(Organization).where(Organization.type == "CORPORATE")
    corporate_rooms = session.exec(stmt).all()
    anomalies = []
    
    for rm in corporate_rooms:
        latest_event = session.exec(
            select(SensingEvent).where(SensingEvent.room_id == rm.id).order_by(SensingEvent.timestamp.desc())
        ).first()
        if not latest_event:
            continue
        act = session.get(ActivityType, latest_event.inferred_activity_id)
        is_occupied = act and act.name in ["Presence", "Walking", "Sitting", "Fall_Detected"]
        
        # Check schedule
        schedules = session.exec(select(RoomSchedule).where(RoomSchedule.room_id == rm.id)).all()
        for sched in schedules:
            if sched.expected_status == "FREE" and is_occupied:
                anomalies.append({
                    "room_id": rm.id,
                    "room_name": rm.name,
                    "expected_status": "FREE",
                    "detected_activity": act.name,
                    "detected_at": latest_event.timestamp.strftime("%H:%M:%S"),
                    "schedule_interval": f"{sched.start_time}–{sched.end_time}",
                    "reason": f"Room was scheduled as FREE ({sched.start_time}–{sched.end_time}) but Wi-Fi CSI sensing detected active {act.name}."
                })
            elif sched.expected_status == "AFTER_HOURS_CLOSED" and is_occupied:
                anomalies.append({
                    "room_id": rm.id,
                    "room_name": rm.name,
                    "expected_status": "AFTER_HOURS_CLOSED",
                    "detected_activity": act.name,
                    "detected_at": latest_event.timestamp.strftime("%H:%M:%S"),
                    "schedule_interval": f"{sched.start_time}–{sched.end_time}",
                    "reason": f"Security Notice: After-hours movement detected during non-operational period ({sched.start_time}–{sched.end_time})."
                })
    return anomalies

@router.get("/schedules/energy-recommendations", dependencies=[Depends(require_roles(STAFF_ROLES))])
def get_energy_efficiency_recommendations(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    stmt = select(Room).join(Floor).join(Building).join(Organization).where(Organization.type == "CORPORATE")
    corporate_rooms = session.exec(stmt).all()
    recommendations = []
    seen_room_ids = set()
    
    for rm in corporate_rooms:
        meta = dict(rm.dimensions_metadata or {})
        e_state = meta.get("energy_state", {})
        ac_active = e_state.get("ac_status") == "ON"
        lighting_active = e_state.get("lighting_status") == "ON"
        
        schedules = session.exec(select(RoomSchedule).where(RoomSchedule.room_id == rm.id, RoomSchedule.ac_state == "ON")).all()
        if schedules:
            ac_active = True
            
        if not (ac_active or lighting_active):
            continue
            
        latest_event = session.exec(
            select(SensingEvent).where(SensingEvent.room_id == rm.id).order_by(SensingEvent.timestamp.desc())
        ).first()
        act = session.get(ActivityType, latest_event.inferred_activity_id) if latest_event else None
        is_vacant = (not act) or (act.name in ["Empty", "Unoccupied"])
        
        if is_vacant and rm.id not in seen_room_ids:
            seen_room_ids.add(rm.id)
            vac_hours = e_state.get("vacant_duration_hours", 2.0)
            recommendations.append({
                "room_id": rm.id,
                "room_name": rm.name,
                "ac_status": "ON" if ac_active else "OFF",
                "lighting_status": "ON" if lighting_active else "AUTO",
                "vacant_duration_hours": vac_hours,
                "detected_activity": "Empty (No CSI Movement)",
                "recommendation": f"Room has remained vacant for {vac_hours} hours while {'AC & Lighting are ON' if (ac_active and lighting_active) else 'AC is ON'}. Shut off to prevent energy waste.",
                "recommended_action": "Shut off AC and switch lighting to Eco Standby."
            })
    return recommendations

@router.post("/rooms/{room_id}/energy-action", response_model=EnergyActionOut, dependencies=[Depends(require_roles(STAFF_ROLES))])
def execute_room_energy_action(
    room_id: str,
    action_in: EnergyActionIn,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    meta = dict(room.dimensions_metadata or {})
    energy_state = dict(meta.get("energy_state", {}))
    
    if action_in.action in ["SHUT_OFF_AC", "ECO_STANDBY"]:
        energy_state["ac_status"] = "OFF"
    elif action_in.action == "RESTORE_NORMAL":
        energy_state["ac_status"] = "ON"
        
    if action_in.action in ["SHUT_OFF_LIGHTS", "ECO_STANDBY"]:
        energy_state["lighting_status"] = "OFF"
    elif action_in.action == "RESTORE_NORMAL":
        energy_state["lighting_status"] = "ON"
        
    energy_state["last_action"] = action_in.action
    energy_state["last_action_by"] = current_user.email
    energy_state["last_action_at"] = datetime.utcnow().isoformat()
    energy_state["vacant_duration_hours"] = 0.0
    
    if action_in.action in ["SHUT_OFF_AC", "SHUT_OFF_LIGHTS", "ECO_STANDBY"]:
        energy_state["efficiency_status"] = "SAVING_ACTIVE"
        energy_state["status_message"] = "Eco Standby Active: HVAC & Lighting powered down via IoT relay command."
        energy_state["efficiency_recommendation"] = "Eco Standby Active: Energy waste mitigated."
    else:
        energy_state["efficiency_status"] = "NORMAL"
        energy_state["status_message"] = "Normal power restored."
        energy_state["efficiency_recommendation"] = None
        
    meta["energy_state"] = energy_state
    room.dimensions_metadata = meta
    session.add(room)
    
    # Update schedules ac_state
    schedules = session.exec(select(RoomSchedule).where(RoomSchedule.room_id == room_id)).all()
    for sched in schedules:
        if action_in.action in ["SHUT_OFF_AC", "ECO_STANDBY"]:
            sched.ac_state = "OFF"
        elif action_in.action == "RESTORE_NORMAL":
            sched.ac_state = "ON"
        session.add(sched)
        
    # Resolve any associated energy advisory alerts
    energy_alerts = session.exec(
        select(Alert).where(
            Alert.room_id == room_id,
            Alert.event_type.in_(["Energy_Waste", "HVAC_Advisory", "Energy_Advisory"]),
            Alert.status != "resolved"
        )
    ).all()
    for alert in energy_alerts:
        alert.status = "resolved"
        alert.updated_at = datetime.utcnow()
        session.add(alert)
        
    session.commit()
    session.refresh(room)
    
    return EnergyActionOut(
        success=True,
        room_id=room.id,
        room_name=room.name,
        action=action_in.action,
        energy_state=energy_state,
        message=f"IoT relay action '{action_in.action}' applied successfully for {room.name}."
    )

@router.post("/schedules/energy-actions/bulk", dependencies=[Depends(require_roles(STAFF_ROLES))])
def execute_bulk_energy_actions(
    action_in: EnergyActionIn,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    stmt = select(Room).join(Floor).join(Building).join(Organization).where(Organization.type == "CORPORATE")
    rooms = session.exec(stmt).all()
    affected_rooms = []
    
    for rm in rooms:
        meta = dict(rm.dimensions_metadata or {})
        e_state = meta.get("energy_state", {})
        if e_state.get("ac_status") == "ON" or e_state.get("lighting_status") == "ON":
            # Check if vacant
            latest_event = session.exec(
                select(SensingEvent).where(SensingEvent.room_id == rm.id).order_by(SensingEvent.timestamp.desc())
            ).first()
            act = session.get(ActivityType, latest_event.inferred_activity_id) if latest_event else None
            is_vacant = (not act) or (act.name in ["Empty", "Unoccupied"])
            if is_vacant:
                execute_room_energy_action(rm.id, action_in, session, current_user)
                affected_rooms.append(rm.name)
                
    return {
        "success": True,
        "affected_count": len(affected_rooms),
        "affected_rooms": affected_rooms,
        "action": action_in.action,
        "message": f"Bulk {action_in.action} applied across {len(affected_rooms)} vacant rooms."
    }


