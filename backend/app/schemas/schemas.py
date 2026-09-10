from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============================================================================
# 1. AUTHENTICATION & USER SCHEMAS
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

class RoleAssignment(BaseModel):
    user_id: str
    role: str = Field(..., description="Role must be one of: system_admin, organization_admin, facility_manager, caregiver, corporate_staff, emergency_contact")
    organization_id: Optional[str] = None
    building_id: Optional[str] = None
    room_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    photo_url: Optional[str] = None
    resident_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    application_context: str
    is_system_admin: bool = False
    user: UserOut

class SharingPolicyOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    resident_id: Optional[str] = None
    share_presence: bool
    share_activity_detail: bool
    share_room_name: bool
    share_alert_history: bool
    share_alert_severity_threshold: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SharingPolicyUpdate(BaseModel):
    share_presence: Optional[bool] = None
    share_activity_detail: Optional[bool] = None
    share_room_name: Optional[bool] = None
    share_alert_history: Optional[bool] = None
    share_alert_severity_threshold: Optional[str] = None

class AccessRequestCreate(BaseModel):
    resident_id: str

class AccessRequestOut(BaseModel):
    id: str
    requesting_user_id: str
    resident_id: str
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AccessRequestReview(BaseModel):
    status: str # 'approved' or 'declined'


# ============================================================================
# 2. CRUD SCHEMAS
# ============================================================================

class OrganizationCreate(BaseModel):
    name: str
    type: str = Field(..., description="Must be either ELDER_CARE or CORPORATE")

class OrganizationOut(BaseModel):
    id: str
    name: str
    type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BuildingCreate(BaseModel):
    organization_id: str
    name: str
    address: Optional[str] = None

class BuildingOut(BaseModel):
    id: str
    organization_id: str
    name: str
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FloorCreate(BaseModel):
    building_id: str
    floor_number: int
    floor_plan_url: Optional[str] = None

class FloorOut(BaseModel):
    id: str
    building_id: str
    floor_number: int
    floor_plan_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RoomCreate(BaseModel):
    floor_id: str
    name: str
    room_type: str
    capacity: Optional[int] = 1
    dimensions_metadata: Optional[Dict[str, Any]] = None

class RoomOut(BaseModel):
    id: str
    floor_id: str
    name: str
    room_type: str
    capacity: int
    dimensions_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SensingDeviceCreate(BaseModel):
    room_id: Optional[str] = None
    mac_address: str = Field(..., description="17-character MAC address, e.g. 4C:75:25:AA:BB:CC")
    device_status: Optional[str] = "OFFLINE"
    firmware_version: Optional[str] = None

class SensingDeviceOut(BaseModel):
    id: str
    room_id: Optional[str]
    mac_address: str
    device_status: str
    firmware_version: Optional[str]
    hardware_token: Optional[str] = None
    last_seen_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    building_name: Optional[str] = None
    room_name: Optional[str] = None

    class Config:
        from_attributes = True

class FaultReportCreate(BaseModel):
    issue_type: str = "FAULTY_CSI_VALUES"
    description: str
    severity: str = "HIGH"

class FaultReportServiceUpdate(BaseModel):
    status: str # UNDER_INSPECTION, DISPATCHED_SERVICE, REPLACED_RESOLVED
    service_notes: Optional[str] = None

class FaultReportOut(BaseModel):
    id: str
    device_id: str
    mac_address: Optional[str] = None
    room_name: Optional[str] = None
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    issue_type: str
    description: str
    severity: str
    tracer_token: str
    status: str
    service_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResidentCreate(BaseModel):
    room_id: str
    first_name: str
    last_name: str

class ResidentOut(BaseModel):
    id: str
    room_id: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HealthConditionOut(BaseModel):
    id: str
    resident_id: str
    condition_name: str
    notes: Optional[str]
    diagnosed_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# 3. SENSING PIPELINE SCHEMAS
# ============================================================================

class SensingEventSimulate(BaseModel):
    device_id: str
    simulated_activity: str = Field(..., description="Activity name, e.g. Empty, Presence, Walking, Sitting, Fall_Detected")

class SensingEventOut(BaseModel):
    id: int
    device_id: str
    room_id: str
    timestamp: datetime
    rssi: int
    subcarrier_count: int
    extracted_features: Dict[str, Any]
    inferred_activity_id: int
    model_confidence: float

    class Config:
        from_attributes = True

# ============================================================================
# 4. ALERTS SCHEMAS
# ============================================================================

class AlertOut(BaseModel):
    id: str
    alert_configuration_id: Optional[str] = None
    room_id: str
    event_type: str
    severity: str
    message: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlertResolve(BaseModel):
    resolution_notes: str

# ============================================================================
# 5. ANALYTICS SCHEMAS
# ============================================================================

class OccupancySummaryOut(BaseModel):
    total_rooms: int
    occupied_rooms: int
    vacant_rooms: int
    occupancy_rate: float
    occupied_room_details: List[Dict[str, Any]]

class AlertSummaryOut(BaseModel):
    total_alerts: int
    status_counts: Dict[str, int]
    severity_counts: Dict[str, int]
