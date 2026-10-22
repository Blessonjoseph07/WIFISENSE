import uuid
from datetime import datetime, timezone
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    buildings: List["Building"] = Relationship(back_populates="organization", cascade_delete=True)
    users: List["UserRole"] = Relationship(back_populates="organization", cascade_delete=True)

class Building(SQLModel, table=True):
    __tablename__ = "buildings"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    organization_id: str = Field(foreign_key="organizations.id", nullable=False)
    name: str = Field(nullable=False)
    address: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    organization: Organization = Relationship(back_populates="buildings")
    floors: List["Floor"] = Relationship(back_populates="building", cascade_delete=True)

class Floor(SQLModel, table=True):
    __tablename__ = "floors"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    building_id: str = Field(foreign_key="buildings.id", nullable=False)
    floor_number: int = Field(nullable=False)
    floor_plan_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    building: Building = Relationship(back_populates="floors")
    rooms: List["Room"] = Relationship(back_populates="floor", cascade_delete=True)

class Room(SQLModel, table=True):
    __tablename__ = "rooms"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    floor_id: str = Field(foreign_key="floors.id", nullable=False)
    name: str = Field(nullable=False)
    room_type: str = Field(nullable=False)
    classification: Optional[str] = Field(default=None)
    capacity: int = Field(default=1)
    dimensions_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyConnection(SQLModel, table=True):
    __tablename__ = "family_connections"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    family_user_id: str = Field(foreign_key="users.id", nullable=False)
    relationship: str = Field(nullable=False) # Son, Daughter, Son-in-law, Daughter-in-law, Grandson, Granddaughter, Brother, Sister, Other
    status: str = Field(default="pending") # pending, approved, rejected, revoked
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = Field(default=None)
    approved_by: Optional[str] = Field(default=None, foreign_key="users.id")
    revoked_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="family_connections")

class FamilySubscription(SQLModel, table=True):
    __tablename__ = "family_subscriptions"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    family_user_id: str = Field(foreign_key="users.id", nullable=False)
    family_connection_id: Optional[str] = Field(default=None, foreign_key="family_connections.id")
    plan: str = Field(default="CARE_MONTHLY")
    # PENDING (never paid), ACTIVE, PAST_DUE (renewal failed or missed: grace period), EXPIRED, CANCELLED, SUSPENDED
    # (SUSPENDED is an administrator's hold: payments never lift it)
    status: str = Field(default="PENDING")
    start_date: Optional[datetime] = Field(default=None)      # start of the current paid period
    end_date: Optional[datetime] = Field(default=None)        # end of the current paid period (None = admin-managed, no period)
    renewal_date: Optional[datetime] = Field(default=None)    # next automatic renewal; None when cancelling or unpaid
    cancel_at_period_end: bool = Field(default=False, nullable=False)
    cancelled_at: Optional[datetime] = Field(default=None)
    past_due_since: Optional[datetime] = Field(default=None)
    # Payment provider references only. No card or payment details are ever stored.
    provider: Optional[str] = Field(default=None)
    provider_checkout_id: Optional[str] = Field(default=None, index=True)
    provider_subscription_id: Optional[str] = Field(default=None, index=True)
    last_payment_status: Optional[str] = Field(default=None)  # SUCCEEDED / FAILED
    last_event_at: Optional[datetime] = Field(default=None)   # created-time of the newest provider event applied
    price_minor: Optional[int] = Field(default=None)         # price snapshot of the current period
    currency: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentEvent(SQLModel, table=True):
    """Every provider webhook that passed signature verification, for idempotency and audit. Whitelisted fields only."""
    __tablename__ = "payment_events"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    provider: str = Field(nullable=False)
    event_id: str = Field(nullable=False, unique=True, index=True)
    event_type: str = Field(nullable=False)
    subscription_id: Optional[str] = Field(default=None, index=True)
    outcome: str = Field(nullable=False)   # PROCESSED, HELD_BY_ADMIN, IGNORED_STALE, IGNORED_UNKNOWN_TYPE, REJECTED_*
    summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

class CaregiverProfile(SQLModel, table=True):
    __tablename__ = "caregiver_profiles"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, nullable=False)
    photo_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    work_history: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    hardware_token: Optional[str] = Field(default=None)
    hardware_token_hash: Optional[str] = Field(default=None, index=True)
    allowed_source: str = Field(default="live", nullable=False)
    last_seen_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    room: Optional[Room] = Relationship(back_populates="devices")

class NodeFaultReport(SQLModel, table=True):
    __tablename__ = "node_fault_reports"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    device_id: str = Field(foreign_key="devices.id", nullable=False)
    reported_by_user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    issue_type: str = Field(default="FAULTY_CSI_VALUES")
    description: str = Field(nullable=False)
    severity: str = Field(default="HIGH")
    tracer_token: str = Field(default_factory=lambda: f"TRC-{uuid.uuid4().hex[:8].upper()}")
    status: str = Field(default="REPORTED") # REPORTED, UNDER_INSPECTION, DISPATCHED_SERVICE, REPLACED_RESOLVED
    service_notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmergencyContact(SQLModel, table=True):
    __tablename__ = "emergency_contacts"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    name: str = Field(nullable=False)
    relationship: str = Field(nullable=False)
    phone: str = Field(nullable=False)
    priority: int = Field(default=1) # 1 = primary, 2 = secondary
    email: Optional[str] = Field(default=None)
    availability: Optional[str] = Field(default="24/7 Primary Response")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="emergency_contacts")

class Doctor(SQLModel, table=True):
    __tablename__ = "doctors"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    name: str = Field(nullable=False)
    specialty: str = Field(nullable=False)
    hospital: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="doctors")

class HospitalVisit(SQLModel, table=True):
    __tablename__ = "hospital_visits"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    hospital_name: str = Field(nullable=False)
    reason: str = Field(nullable=False)
    visit_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    discharge_date: Optional[datetime] = Field(default=None)
    doctor_notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="hospital_visits")

class LabReport(SQLModel, table=True):
    __tablename__ = "lab_reports"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    test_name: str = Field(nullable=False)
    test_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_summary: str = Field(nullable=False)
    normal_range: Optional[str] = Field(default=None)
    flag: Optional[str] = Field(default="NORMAL") # NORMAL, ELEVATED, HIGH, CRITICAL
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="lab_reports")

class Prescription(SQLModel, table=True):
    __tablename__ = "prescriptions"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    medication_name: str = Field(nullable=False)
    dosage: str = Field(nullable=False)
    frequency: str = Field(nullable=False)
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = Field(default=None)
    prescribing_doctor: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    resident: "Resident" = Relationship(back_populates="prescriptions")

class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False, index=True)
    doctor_id: Optional[str] = Field(default=None, foreign_key="doctors.id")
    scheduled_at: datetime = Field(nullable=False, index=True)
    purpose: str = Field(nullable=False)
    status: str = Field(default="SCHEDULED", nullable=False)  # SCHEDULED, COMPLETED, CANCELLED
    notes: Optional[str] = Field(default=None)
    created_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MedicationLog(SQLModel, table=True):
    __tablename__ = "medication_logs"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False, index=True)
    prescription_id: str = Field(foreign_key="prescriptions.id", nullable=False, index=True)
    status: str = Field(nullable=False)  # GIVEN, MISSED, REFUSED
    administered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    administered_by: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoctorProfile(SQLModel, table=True):
    """A doctor's application to one elder-care organization. Only APPROVED profiles may use the doctor portal."""
    __tablename__ = "doctor_profiles"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, nullable=False)
    organization_id: str = Field(foreign_key="organizations.id", nullable=False, index=True)
    clinic_name: str = Field(nullable=False)
    specialty: str = Field(nullable=False)
    license_number: str = Field(nullable=False)
    status: str = Field(default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, SUSPENDED
    reviewed_by: Optional[str] = Field(default=None)
    reviewed_at: Optional[datetime] = Field(default=None)
    review_note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoctorAssignment(SQLModel, table=True):
    """Explicit doctor -> resident grant. A doctor can only see residents with an ACTIVE assignment."""
    __tablename__ = "doctor_assignments"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    doctor_profile_id: str = Field(foreign_key="doctor_profiles.id", nullable=False, index=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False, index=True)
    status: str = Field(default="ACTIVE", nullable=False)  # ACTIVE, REVOKED
    assigned_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_by: Optional[str] = Field(default=None)
    revoked_at: Optional[datetime] = Field(default=None)

class Consultation(SQLModel, table=True):
    __tablename__ = "consultations"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False, index=True)
    doctor_profile_id: str = Field(foreign_key="doctor_profiles.id", nullable=False, index=True)
    consulted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = Field(nullable=False)
    notes: Optional[str] = Field(default=None)  # doctor notes
    follow_up_date: Optional[datetime] = Field(default=None)
    follow_up_done: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Allergy(SQLModel, table=True):
    __tablename__ = "allergies"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False, index=True)
    allergen: str = Field(nullable=False)
    reaction: Optional[str] = Field(default=None)
    severity: str = Field(default="MODERATE", nullable=False)  # MILD, MODERATE, SEVERE
    recorded_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Resident(SQLModel, table=True):
    __tablename__ = "residents"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    date_of_birth: Optional[datetime] = Field(default=None)
    resident_status: Optional[str] = Field(default="Active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    room: Room = Relationship(back_populates="residents")
    health_conditions: List["HealthCondition"] = Relationship(back_populates="resident", cascade_delete=True)
    emergency_contacts: List[EmergencyContact] = Relationship(back_populates="resident", cascade_delete=True)
    doctors: List[Doctor] = Relationship(back_populates="resident", cascade_delete=True)
    hospital_visits: List[HospitalVisit] = Relationship(back_populates="resident", cascade_delete=True)
    lab_reports: List[LabReport] = Relationship(back_populates="resident", cascade_delete=True)
    prescriptions: List[Prescription] = Relationship(back_populates="resident", cascade_delete=True)
    family_connections: List[FamilyConnection] = Relationship(back_populates="resident", cascade_delete=True)

class HealthCondition(SQLModel, table=True):
    __tablename__ = "health_conditions"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    resident_id: str = Field(foreign_key="residents.id", nullable=False)
    condition_name: str = Field(nullable=False)
    notes: Optional[str] = Field(default=None)
    diagnosed_date: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    rssi: int = Field(nullable=False)
    subcarrier_count: int = Field(default=56)
    signal_quality: Optional[int] = Field(default=94)
    event_type: Optional[str] = Field(default="SensingTelemetry")
    raw_csi_payload_path: Optional[str] = Field(default=None)
    extracted_features: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    inferred_activity_id: int = Field(foreign_key="activity_types.id", nullable=False)
    model_confidence: float = Field(nullable=False)
    # live | dataset | simulated. Phase 1 events come from the simulator; real classification will set "live"/"dataset".
    source: str = Field(default="simulated", nullable=False)

class RawCsiTelemetry(SQLModel, table=True):
    __tablename__ = "raw_csi_telemetry"
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="devices.id", nullable=False, index=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False, index=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    sequence_number: Optional[int] = Field(default=None)
    rssi: int = Field(nullable=False)
    noise_floor: Optional[int] = Field(default=None)
    subcarrier_count: int = Field(default=56)
    bandwidth_mhz: Optional[int] = Field(default=20)
    channel: Optional[int] = Field(default=None)
    csi_data: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    provenance: str = Field(default="live", nullable=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # NULL = not yet processed by the detector; a SensingEvent id = part of that detection window; -1 = skipped
    # (unsupported CSI format, or too few packets to form a window).
    event_id: Optional[int] = Field(default=None, index=True)

    device: Optional[SensingDevice] = Relationship()
    room: Optional[Room] = Relationship()

class ReplayEvaluation(SQLModel, table=True):
    """Ground truth for a DATASET REPLAY detection window, entered by an administrator.

    It is kept apart from the packets on purpose: a device can never supply labels, so the detector's output and the
    recorded label can be compared honestly afterwards."""
    __tablename__ = "replay_evaluations"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_id: int = Field(foreign_key="sensing_events.id", unique=True, index=True, nullable=False)
    device_id: str = Field(foreign_key="devices.id", nullable=False, index=True)
    dataset_name: str = Field(nullable=False)
    recorded_label: str = Field(nullable=False)
    created_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoomCalibration(SQLModel, table=True):
    __tablename__ = "room_calibrations"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    device_id: Optional[str] = Field(default=None, foreign_key="devices.id")
    baseline_status: str = Field(default="VALID") # VALID, CALIBRATION_REQUIRED, CAPTURING
    baseline_captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    noise_floor_dbm: int = Field(default=-88)
    baseline_rssi: int = Field(default=-48)
    rf_similarity_pct: float = Field(default=96.0) # 0 - 100%
    rf_environment_status: str = Field(default="NORMAL") # NORMAL, ENVIRONMENT_CHANGED
    subcarrier_profile: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoomSchedule(SQLModel, table=True):
    __tablename__ = "room_schedules"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False)
    day_of_week: str = Field(default="ALL")
    start_time: str = Field(default="09:00")
    end_time: str = Field(default="17:00")
    expected_status: str = Field(default="FREE") # FREE, BOOKED, AFTER_HOURS_CLOSED
    meeting_title: Optional[str] = Field(default=None)
    organizer: Optional[str] = Field(default=None)
    ac_state: Optional[str] = Field(default="OFF") # ON, OFF
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RoomBooking(SQLModel, table=True):
    """A dated reservation of a corporate room. RoomSchedule above is the recurring *expected* schedule; this is a booking."""
    __tablename__ = "room_bookings"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", nullable=False, index=True)
    organization_id: Optional[str] = Field(default=None, index=True)
    organizer_user_id: Optional[str] = Field(default=None)
    organizer_name: str = Field(nullable=False)
    purpose: str = Field(nullable=False)
    start_at: datetime = Field(nullable=False, index=True)  # UTC
    end_at: datetime = Field(nullable=False)  # UTC
    status: str = Field(default="BOOKED", index=True)  # BOOKED, CANCELLED
    cancelled_at: Optional[datetime] = Field(default=None)
    cancelled_by: Optional[str] = Field(default=None)
    cancel_reason: Optional[str] = Field(default=None)
    reminder_issued_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Detection evidence copied from the sensing event that raised the alert (all optional: seeded/manual alerts have none).
    source: str = Field(default="simulated", nullable=False)  # live | dataset | simulated
    device_id: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None)
    signal_quality: Optional[int] = Field(default=None)
    # Human verification of an uncertain detection (kept for future analytics).
    verification_status: str = Field(default="UNVERIFIED", nullable=False)  # UNVERIFIED, CONFIRMED, DISMISSED
    verified_by: Optional[str] = Field(default=None)
    verified_at: Optional[datetime] = Field(default=None)
    verification_note: Optional[str] = Field(default=None)

    room: Room = Relationship(back_populates="alerts")
    acknowledgement: Optional["AlertAcknowledgement"] = Relationship(back_populates="alert", cascade_delete=True)

class AlertAcknowledgement(SQLModel, table=True):
    __tablename__ = "alert_acknowledgements"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    alert_id: str = Field(foreign_key="alerts.id", unique=True, nullable=False)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    acknowledged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)

    alert: Alert = Relationship(back_populates="acknowledgement")

    @property
    def who_user_id(self) -> Optional[str]:
        return self.user_id

# ============================================================================
# 5. SECURITY, TOKENS & AUDIT LOGGING (PHASE 1 FOUNDATION)
# ============================================================================

class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, nullable=False)
    token_hash: str = Field(unique=True, index=True, nullable=False)
    expires_at: datetime = Field(index=True, nullable=False)
    revoked_at: Optional[datetime] = Field(default=None)
    replaced_by_token_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenRevocation(SQLModel, table=True):
    __tablename__ = "token_revocations"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    token_identifier: str = Field(unique=True, index=True, nullable=False)
    user_id: Optional[str] = Field(default=None, index=True)
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(index=True, nullable=False)
    reason: Optional[str] = Field(default=None)

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    who_user_id: Optional[str] = Field(default=None, index=True)
    who_email: Optional[str] = Field(default=None, index=True)
    what_action: str = Field(index=True, nullable=False)
    resource_type: str = Field(index=True, nullable=False)
    resource_id: Optional[str] = Field(default=None, index=True)
    result: str = Field(default="SUCCESS") # SUCCESS, FAILURE, DENIED
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    ip_address: Optional[str] = Field(default=None)
    # Organization the event belongs to, so an organization admin only ever reads their own organization's trail.
    # NULL means "not attributable to one organization" (for example a login attempt with an unknown e-mail) and is
    # visible to the system administrator only.
    organization_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

