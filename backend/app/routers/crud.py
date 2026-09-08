from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, or_
from typing import List
from app.core.database import get_session
from app.routers.auth import get_current_user, require_roles, get_user_scopes
from app.models.entities import Organization, Building, Floor, Room, SensingDevice, Resident
from app.schemas.schemas import (
    OrganizationCreate, OrganizationOut,
    BuildingCreate, BuildingOut,
    FloorCreate, FloorOut,
    RoomCreate, RoomOut,
    SensingDeviceCreate, SensingDeviceOut,
    ResidentCreate, ResidentOut
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
        firmware_version=dev.firmware_version
    )
    session.add(db_dev)
    session.commit()
    session.refresh(db_dev)
    return db_dev

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
    return session.exec(stmt).all()

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
        stmt = stmt.join(Room).join(Floor).join(Building).where(or_(
            Building.organization_id.in_(list(scopes["organization_ids"])),
            Building.id.in_(list(scopes["building_ids"])),
            Room.id.in_(list(scopes["room_ids"]))
        ))
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
    return db_dev
