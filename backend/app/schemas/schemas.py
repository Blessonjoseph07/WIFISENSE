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
    role: str = Field(..., description="Role must be one of: system_admin, organization_admin, facility_manager, caregiver, corporate_staff, family_member")
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
    resident_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: UserOut
    application_context: str
    is_system_admin: bool
    refresh_token: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class AuditLogOut(BaseModel):
    id: str
    who_user_id: Optional[str] = None
    who_email: Optional[str] = None
    what_action: str
    resource_type: str
    resource_id: Optional[str] = None
    result: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
    classification: Optional[str] = None
    capacity: Optional[int] = 1
    dimensions_metadata: Optional[Dict[str, Any]] = None

class RoomOut(BaseModel):
    id: str
    floor_id: str
    name: str
    room_type: str
    classification: Optional[str] = None
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
    last_seen_at: Optional[datetime]
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

class FaultReportCreate(BaseModel):
    issue_type: str = "FAULTY_CSI_VALUES"
    description: str
    severity: str = "HIGH"

class FaultReportServiceUpdate(BaseModel):
    status: str
    service_notes: Optional[str] = None

class FaultReportOut(BaseModel):
    id: str
    device_id: str
    mac_address: Optional[str] = "Unknown MAC"
    room_name: Optional[str] = "Unassigned Room"
    organization_name: Optional[str] = "Global / Unassigned"
    organization_type: Optional[str] = "SYSTEM"
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

class SharingPolicyOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    resident_id: Optional[str] = None
    share_presence: bool
    share_activity_detail: bool
    share_room_name: bool
    share_alert_history: bool
    share_alert_severity_threshold: str = "MEDIUM"
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

class PersonnelOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role_name: str
    scope_description: str
    permissions: List[str]

# ============================================================================
# 6. EMERGENCY CONTACT & MEDICAL SCHEMAS
# ============================================================================

class EmergencyContactCreate(BaseModel):
    resident_id: str
    name: str
    relationship: str
    phone: str
    priority: Optional[int] = 1
    email: Optional[str] = None
    availability: Optional[str] = "24/7 Primary Response"

class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    priority: Optional[int] = None
    email: Optional[str] = None
    availability: Optional[str] = None

class EmergencyContactOut(BaseModel):
    id: str
    resident_id: str
    name: str
    relationship: str
    phone: str
    priority: int
    email: Optional[str] = None
    availability: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DoctorCreate(BaseModel):
    resident_id: str
    name: str
    specialty: str
    hospital: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class DoctorOut(BaseModel):
    id: str
    resident_id: str
    name: str
    specialty: str
    hospital: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HospitalVisitCreate(BaseModel):
    resident_id: str
    hospital_name: str
    reason: str
    visit_date: datetime
    discharge_date: Optional[datetime] = None
    doctor_notes: Optional[str] = None

class HospitalVisitOut(BaseModel):
    id: str
    resident_id: str
    hospital_name: str
    reason: str
    visit_date: datetime
    discharge_date: Optional[datetime] = None
    doctor_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LabReportCreate(BaseModel):
    resident_id: str
    test_name: str
    test_date: datetime
    result_summary: str
    normal_range: Optional[str] = None
    flag: Optional[str] = "NORMAL"

class LabReportOut(BaseModel):
    id: str
    resident_id: str
    test_name: str
    test_date: datetime
    result_summary: str
    normal_range: Optional[str] = None
    flag: Optional[str] = "NORMAL"
    created_at: datetime

    class Config:
        from_attributes = True

class PrescriptionCreate(BaseModel):
    resident_id: str
    medication_name: str
    dosage: str
    frequency: str
    start_date: datetime
    end_date: Optional[datetime] = None
    prescribing_doctor: Optional[str] = None

class PrescriptionOut(BaseModel):
    id: str
    resident_id: str
    medication_name: str
    dosage: str
    frequency: str
    start_date: datetime
    end_date: Optional[datetime] = None
    prescribing_doctor: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ResidentDetailOut(BaseModel):
    id: str
    room_id: str
    room_name: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    resident_status: Optional[str] = "Active"
    emergency_contacts: List[EmergencyContactOut] = []
    health_conditions: List[HealthConditionOut] = []
    doctors: List[DoctorOut] = []
    hospital_visits: List[HospitalVisitOut] = []
    lab_reports: List[LabReportOut] = []
    prescriptions: List[PrescriptionOut] = []
    current_activity: Optional[str] = "Resting"
    latest_sensing_event: Optional[Dict[str, Any]] = None
    safety_status: Optional[str] = "Normal"
    active_alert: Optional[Dict[str, Any]] = None
    recent_activity_history: List[Dict[str, Any]] = []

# ============================================================================
# 7. FAMILY CONNECTION & SUBSCRIPTION SCHEMAS
# ============================================================================

class FamilyConnectionCreate(BaseModel):
    resident_id: str
    relationship: str # Son, Daughter, Son-in-law, Daughter-in-law, Grandson, Granddaughter, Brother, Sister, Other
    notes: Optional[str] = None

class FamilyConnectionReview(BaseModel):
    status: str # approved, rejected, revoked

class FamilyConnectionOut(BaseModel):
    id: str
    resident_id: str
    resident_name: Optional[str] = None
    room_name: Optional[str] = None
    family_user_id: str
    family_user_name: Optional[str] = None
    family_user_email: Optional[str] = None
    relationship: str
    status: str
    requested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    subscription_status: Optional[str] = "PENDING"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FamilySubscriptionUpdate(BaseModel):
    status: str # PENDING, ACTIVE, EXPIRED, SUSPENDED, CANCELLED
    plan: Optional[str] = "CARE_MONTHLY"

class FamilySubscriptionOut(BaseModel):
    id: str
    family_user_id: str
    family_connection_id: Optional[str] = None
    plan: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# 8. ROOM CALIBRATION & SCHEDULE SCHEMAS
# ============================================================================

class RoomCalibrationOut(BaseModel):
    id: str
    room_id: str
    room_name: Optional[str] = None
    device_id: Optional[str] = None
    device_mac: Optional[str] = None
    baseline_status: str
    baseline_captured_at: datetime
    noise_floor_dbm: int
    baseline_rssi: int
    rf_similarity_pct: float
    rf_environment_status: str
    subcarrier_profile: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class RoomScheduleCreate(BaseModel):
    room_id: str
    day_of_week: Optional[str] = "ALL"
    start_time: str
    end_time: str
    expected_status: Optional[str] = "FREE"
    meeting_title: Optional[str] = None
    organizer: Optional[str] = None
    ac_state: Optional[str] = "OFF"

class RoomScheduleOut(BaseModel):
    id: str
    room_id: str
    day_of_week: str
    start_time: str
    end_time: str
    expected_status: str
    meeting_title: Optional[str] = None
    organizer: Optional[str] = None
    ac_state: Optional[str] = "OFF"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EnergyActionIn(BaseModel):
    action: str = "SHUT_OFF_AC" # SHUT_OFF_AC, SHUT_OFF_LIGHTS, ECO_STANDBY, RESTORE_NORMAL

class EnergyActionOut(BaseModel):
    success: bool
    room_id: str
    room_name: str
    action: str
    energy_state: dict
    message: str

