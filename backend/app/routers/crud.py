from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.routers.auth import get_current_user
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

# ============================================================================
# 1. ORGANIZATIONS
# ============================================================================

@router.post("/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
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
    
    # Check duplicate
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

@router.get("/organizations", response_model=List[OrganizationOut])
def list_organizations(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(Organization)).all()

# ============================================================================
# 2. BUILDINGS
# ============================================================================

@router.post("/buildings", response_model=BuildingOut, status_code=status.HTTP_201_CREATED)
def create_building(
    bld: BuildingCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Validate parent Org
    org = session.get(Organization, bld.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent Organization not found."
        )

    db_bld = Building(organization_id=bld.organization_id, name=bld.name, address=bld.address)
    session.add(db_bld)
    session.commit()
    session.refresh(db_bld)
    return db_bld

@router.get("/buildings", response_model=List[BuildingOut])
def list_buildings(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(Building)).all()

# ============================================================================
# 3. FLOORS
# ============================================================================

@router.post("/floors", response_model=FloorOut, status_code=status.HTTP_201_CREATED)
def create_floor(
    flr: FloorCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Validate parent Building
    bld = session.get(Building, flr.building_id)
    if not bld:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent Building not found."
        )

    db_flr = Floor(building_id=flr.building_id, floor_number=flr.floor_number, floor_plan_url=flr.floor_plan_url)
    session.add(db_flr)
    session.commit()
    session.refresh(db_flr)
    return db_flr

@router.get("/floors", response_model=List[FloorOut])
def list_floors(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(Floor)).all()

# ============================================================================
# 4. ROOMS
# ============================================================================

@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    rm: RoomCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Validate parent Floor
    flr = session.get(Floor, rm.floor_id)
    if not flr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent Floor not found."
        )

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

@router.get("/rooms", response_model=List[RoomOut])
def list_rooms(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(Room)).all()

# ============================================================================
# 5. SENSING DEVICES
# ============================================================================

@router.post("/devices", response_model=SensingDeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    dev: SensingDeviceCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Validate parent Room if provided
    if dev.room_id:
        rm = session.get(Room, dev.room_id)
        if not rm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned Room not found."
            )

    # Check MAC address duplicates
    existing = session.exec(select(SensingDevice).where(SensingDevice.mac_address == dev.mac_address)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A device with this MAC address is already registered."
        )

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

@router.get("/devices", response_model=List[SensingDeviceOut])
def list_devices(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(SensingDevice)).all()

# ============================================================================
# 6. RESIDENTS
# ============================================================================

@router.post("/residents", response_model=ResidentOut, status_code=status.HTTP_201_CREATED)
def create_resident(
    res: ResidentCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Validate parent Room
    rm = session.get(Room, res.room_id)
    if not rm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target Room not found."
        )

    db_res = Resident(room_id=res.room_id, first_name=res.first_name, last_name=res.last_name)
    session.add(db_res)
    session.commit()
    session.refresh(db_res)
    return db_res

@router.get("/residents", response_model=List[ResidentOut])
def list_residents(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    return session.exec(select(Resident)).all()
