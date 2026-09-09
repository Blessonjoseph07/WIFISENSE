import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

# ============================================================================
# 1. CORE GEOGRAPHY & TENANT MODULE
# ============================================================================

class Organization(SQLModel, table=True):
    __tablename__ = "organizations"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    type: str = Field(nullable=False) # 'ELDER_CARE' or 'CORPORATE'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    buildings: List["Building"] = Relationship(back_populates="organization", cascade_delete=True)
    users: List["UserRole"] = Relationship(back_populates="organization", cascade_delete=True)

class Building(SQLModel, table=True):
    __tablename__ = "buildings"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    organization_id: str = Field(foreign_key="organizations.id", nullable=False)
    name: str = Field(nullable=False)
    address: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(back_populates="buildings")
    floors: List["Floor"] = Relationship(back_populates="building", cascade_delete=True)

class Floor(SQLModel, table=True):
    __tablename__ = "floors"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    building_id: str = Field(foreign_key="buildings.id", nullable=False)
    floor_number: int = Field(nullable=False)
    floor_plan_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    building: Building = Relationship(back_populates="floors")
    rooms: List["Room"] = Relationship(back_populates="floor", cascade_delete=True)

class Room(SQLModel, table=True):
    __tablename__ = "rooms"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    floor_id: str = Field(foreign_key="floors.id", nullable=False)
    name: str = Field(nullable=False)
    room_type: str = Field(nullable=False)
    capacity: int = Field(default=1)
    dimensions_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    floor: Floor = Relationship(back_populates="rooms")
    devices: List["SensingDevice"] = Relationship(back_populates="room")
    residents: List["Resident"] = Relationship(back_populates="room", cascade_delete=True)
    alerts: List["Alert"] = Relationship(back_populates="room", cascade_delete=True)

# ============================================================================
# 2. IDENTITY & ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================================

class Role(SQLModel, table=True):
    __tablename__ = "roles"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    photo_url: Optional[str] = Field(default=None)
    resident_id: Optional[str] = Field(default=None, foreign_key="residents.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    roles: List["UserRole"] = Relationship(back_populates="user", cascade_delete=True)
    caregiver_profile: Optional["CaregiverProfile"] = Relationship(back_populates="user", cascade_delete=True)

class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    role_id: int = Field(foreign_key="roles.id", nullable=False)
    organization_id: Optional[str] = Field(default=None, foreign_key="organizations.id")
    building_id: Optional[str] = Field(default=None, foreign_key="buildings.id")
    room_id: Optional[str] = Field(default=None, foreign_key="rooms.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="roles")
    role: Role = Relationship()
    organization: Optional[Organization] = Relationship(back_populates="users")

class AccessRequest(SQLModel, table=True):
    __tablename__ = "access_requests"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    requesting_user_id: str = Field(foreign_key="users.id", nullable=False)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    status: str = Field(default="pending")
    reviewed_by: Optional[str] = Field(default=None, foreign_key="users.id")
    reviewed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CaregiverProfile(SQLModel, table=True):
    __tablename__ = "caregiver_profiles"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, nullable=False)
    photo_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    work_history: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="caregiver_profile")

class SharingPolicy(SQLModel, table=True):
    __tablename__ = "sharing_policies"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    organization_id: Optional[str] = Field(default=None, foreign_key="organizations.id")
    resident_id: Optional[str] = Field(default=None, foreign_key="residents.id")
    share_presence: bool = Field(default=True)
    share_activity_detail: bool = Field(default=True)
    share_room_name: bool = Field(default=True)
    share_alert_history: bool = Field(default=True)
    share_alert_severity_threshold: str = Field(default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# 3. DEVICE & SENSING ENGINE
# ============================================================================

class SensingDevice(SQLModel, table=True):
    __tablename__ = "devices"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: Optional[str] = Field(default=None, foreign_key="rooms.id")
    mac_address: str = Field(unique=True, index=True, nullable=False)
    device_status: str = Field(default="OFFLINE")
    firmware_version: Optional[str] = Field(default=None)
    last_seen_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    room: Optional[Room] = Relationship(back_populates="devices")

class Resident(SQLModel, table=True):
    __tablename__ = "residents"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    date_of_birth: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    room: Room = Relationship(back_populates="residents")
    health_conditions: List["HealthCondition"] = Relationship(back_populates="resident", cascade_delete=True)

class HealthCondition(SQLModel, table=True):
    __tablename__ = "health_conditions"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    condition_name: str = Field(nullable=False)
    notes: Optional[str] = Field(default=None)
    diagnosed_date: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    resident: Resident = Relationship(back_populates="health_conditions")

class ActivityType(SQLModel, table=True):
    __tablename__ = "activity_types"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)
    category: str = Field(nullable=False)

class SensingEvent(SQLModel, table=True):
    __tablename__ = "sensing_events"
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="devices.id", nullable=False)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    rssi: int = Field(nullable=False)
    subcarrier_count: int = Field(nullable=False)
    raw_csi_payload_path: Optional[str] = Field(default=None)
    extracted_features: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    inferred_activity_id: int = Field(foreign_key="activity_types.id", nullable=False)
    model_confidence: float = Field(nullable=False)

# ============================================================================
# 4. ALERTS & NOTIFICATION ENGINE
# ============================================================================

class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    event_type: str = Field(nullable=False)
    severity: str = Field(nullable=False)
    message: str = Field(nullable=False)
    status: str = Field(default="new")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    room: Room = Relationship(back_populates="alerts")
    acknowledgement: Optional["AlertAcknowledgement"] = Relationship(back_populates="alert", cascade_delete=True)

class AlertAcknowledgement(SQLModel, table=True):
    __tablename__ = "alert_acknowledgements"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    alert_id: str = Field(foreign_key="alerts.id", unique=True, nullable=False)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)

    alert: Alert = Relationship(back_populates="acknowledgement")
