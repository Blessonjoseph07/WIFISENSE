# Implementation Plan: WIFISENSE Master Hardening & Engineering Evolution

WIFISENSE is a privacy-preserving WiFi/CSI sensing platform supporting two dual-context domains:
- **CARE**: Elder-care, fall detection, resident safety monitoring, family portal, clinical profiles, emergency escalation.
- **SPACE**: Corporate/facility occupancy, meeting room utilization, HVAC/lighting energy optimization, unexpected occupancy detection.

This plan executes the Master Implementation & Product Hardening roadmap, referencing RuView for sensing gateway, ESP32 CSI ingestion, real/simulated separation, calibration, and observability, while strictly preserving WIFISENSE's product identity, RBAC, and data contracts.

## Mandatory Human Checkpoints Summary
- **Checkpoint 1 (After Phase 1)**: Security & Production Foundation (JWT lifecycle, refresh tokens, revocation list, rate limiting, audit logging, migrations). STOP and await approval.
- **Checkpoint 2 (After Phase 2)**: Real Device Foundation (Hardware ingestion, device authentication, credentials, heartbeat, lifecycle). STOP and await approval.
- **Checkpoint 3 (After Phase 4)**: Real-Time System (WebSocket streaming, scoped pub/sub, auth, event routing). STOP and await approval.
- **Checkpoint 4 (After Phase 5)**: CARE Safety System (Fall alert lifecycle, confidence handling, multi-resident family access, notifications). STOP and await approval.

---

## Phase 0: Complete Repository Audit

### 1. Current Architecture
- **Backend**: FastAPI with SQLModel/SQLAlchemy ORM (`backend/app`).
  - `app/core`: Configuration (`config.py`), Security (`security.py`), Database (`database.py`), Bootstrap (`bootstrap.py`), Seed (`seed.py`, `seed_extensions.py`).
  - `app/models/entities.py`: Multi-tenant hierarchy (`Organization`, `Building`, `Floor`, `Room`), RBAC (`Role`, `User`, `UserRole`, `AccessRequest`, `FamilyConnection`, `FamilySubscription`), Care records (`Resident`, `HealthCondition`, `EmergencyContact`, `Doctor`, `HospitalVisit`, `LabReport`, `Prescription`), Hardware & Sensing (`SensingDevice`, `SensingEvent`, `ActivityType`, `RoomCalibration`, `RoomSchedule`, `Alert`, `AlertAcknowledgement`, `NodeFaultReport`).
  - `app/routers`: `auth.py`, `crud.py`, `sensing.py`, `alerts.py`, `analytics.py`, `family_portal.py`, `users.py`.
- **Frontend**: React + Vite + TailwindCSS + Vanilla CSS (`frontend/src`).
  - Multi-context shells: `CareAppShell`, `SpaceAppShell`, `SystemAdminShell`, `FamilyPortalShell`, and Splashes (`LandingSplash`, `ElderCareSplash`, `CorporateSplash`).
  - 13 Modular Views (`AlertsView`, `AnalyticsView`, `CaregiverView`, `CorporateView`, `DevicesView`, `FacilityAssetsView`, `FamilyPortalView`, `OccupancyView`, `OrgAdminView`, `ResidentsView`, `SysAdminView`, `UserProfileView`, `CentralMonitoringView`).
  - Components: `EmergencyFallModal`, `ResidentProfileModal`, `LoadingScreen`, `SubcarrierWaveformStream`.
- **Test Baseline**:
  - `test_boundaries.py` (12 boundary tests covering role context pinning, tenant isolation, sharing policy scopes, family status).
  - `test_master_phases.py` (8 requirement validation tests covering emergency contacts, doctor/lab records, room calibrations, corporate energy recommendations).
  - Pre-phase CI: `.github/workflows/ci.yml` running both test suites on GitHub push/PR.

### 2. Current Functionality
- Deterministic RBAC with 7 canonical roles: `system_admin (1)`, `organization_admin (2)`, `facility_manager (3)`, `caregiver (4)`, `corporate_staff (5)`, `emergency_contact (6)`, `family_member (7)`.
- Context isolation (`ELDER_CARE`, `CORPORATE`, `SYSTEM`) with strict 403 / empty-list multi-tenant filtering.
- Resident health profile management (emergency contacts, doctors, hospital visits, lab reports, prescriptions).
- Room baseline RF calibration recording (`RoomCalibration`).
- Corporate schedule anomaly detection and HVAC/lighting energy mitigation actions.
- Simulated CSI sensing events (`/sensing/simulate-event`) with deterministic OFDM subcarrier waveforms.
- Node fault reporting and technician tracer tokens (`NodeFaultReport`).

### 3. Current Gaps
- **Security**: No refresh token rotation; tokens are 24-hour static JWTs; no server-side token revocation / logout blacklist; no rate limiting on login/register/ingest; no structured audit trail (`audit_logs`); reliance on `create_all()` with ad-hoc `ALTER TABLE` scripts instead of Alembic migrations.
- **Hardware Ingestion**: No real device ingestion transport (no UDP socket / MQTT bridge / lightweight device ingestion endpoint); devices authenticated solely via human JWTs; no device heartbeat or status lifecycle (`REGISTERED`, `PROVISIONING`, `ONLINE`, `DEGRADED`, `OFFLINE`, `REVOKED`); hardware tokens cannot be securely rotated/revoked.
- **Sensing Engine**: Sensing events lack explicit provenance (`REAL_DEVICE`, `SIMULATION`, `MANUAL_TEST`); raw CSI is not validated; no device-level packet health tracking.
- **Real-Time**: No WebSockets or SSE; frontend relies on polling or manual trigger.
- **CARE Safety**: Alerts lack strict 5-stage lifecycle state machine (`DETECTED` -> `ACTIVE` -> `ACKNOWLEDGED` -> `RESPONDING` -> `RESOLVED`); notifications are mock payloads without web push or email delivery.
- **Family Multi-Resident**: Single-resident access assumption in status endpoints rather than multi-resident selection.
- **Observability**: No System Admin observatory dashboard showing real ingestion rates, active connections, database health, or sensor health scores.

### 4. RuView Features Worth Adopting
- **ESP32 CSI Sensing & Gateway**: Robust ingestion protocol with packet sequence validation, RSSI, noise, and 56-subcarrier phase/amplitude vectors.
- **Device Authentication & Credential Lifecycle**: Dedicated device API tokens / hardware tokens isolated from human user JWTs.
- **Real vs. Simulated Separation**: Strict provenance flags on all telemetry and UI indicators (● LIVE HARDWARE vs ◉ SIMULATION MODE).
- **Calibration Engine**: Room baseline RF profile calculation, similarity scoring, and noise floor monitoring.
- **Device Health & Signal Observability**: Real-time signal quality, noise floor, dropped packets, and latency tracking.

### 5. RuView Features to Reject
- Full Rust rewrite (WIFISENSE is Python/FastAPI backend with React frontend).
- Full DensePose / 17-keypoint humanoid pose reconstruction (unnecessary complexity; high CPU/GPU cost).
- Mesh swarm protocol (unjustified for targeted elder care / corporate room monitoring).
- WASM client-side inference (unnecessary complexity; edge gateway/server classification is more robust).
- Research-grade vital sign medical diagnostics (high liability without certified medical sensors).

### 6. Dependencies & Risks
- **Dependencies**: Python 3.8+ compatibility; packages: `slowapi` (rate limiting), `alembic` (database migrations), `websockets` (real-time streaming).
- **Risks**:
  - Regression of existing RBAC role IDs or context mappings (`test_boundaries.py` must stay 100% green).
  - Database schema migration breaking existing seeded data in `wifisense.db`.
  - Stale WebSocket connections leaking multi-tenant events across tenant boundaries.

---

## Phase-by-Phase Implementation Plan

### Pre-Phase CI: Minimal Regression Safety Net
- **Status**: Completed (`.github/workflows/ci.yml`).

---

### Phase 1: Security & Production Foundation (CURRENT TARGET)
- **Token Lifecycle & Security**:
  - Access token expiration (15 minutes).
  - Refresh tokens (7 days) stored in a `refresh_tokens` database table with device/user binding, family tracking, and single-use rotation.
  - Server-side revocation blacklist (`token_revocations` table) checked in `decode_access_token` and `get_current_user`.
  - POST `/auth/refresh` endpoint to exchange valid refresh token for a new access token and rotated refresh token.
  - POST `/auth/logout` endpoint to revoke access token and refresh token immediately.
  - Revoke all active tokens for a user upon password change or role modification.
- **Rate Limiting**:
  - In-memory rate limiting for `/auth/login`, `/auth/register`, and sensitive endpoints.
- **Audit Logging**:
  - `AuditLog` entity (`who_user_id`, `who_email`, `what_action`, `when_timestamp`, `resource_type`, `resource_id`, `result`, `ip_address`, `details`).
  - Helper functions to log: login, logout, failed login, role change, access approval/rejection, sharing policy update, alert actions, device credential rotation/revocation.
- **Database Migrations**:
  - Initialize Alembic environment in `backend/alembic`.
  - Configure `alembic.ini` and `alembic/env.py` pointing to `SQLModel.metadata`.
  - Create baseline migration capturing the schema.
  - Ensure zero database wipes and graceful execution.
- **Production Safeguards**:
  - Enforce environment variable validation (fail loudly if `SECRET_KEY` is default or empty in non-dev environment).
- **Testing & Verification**:
  - Run `test_boundaries.py`, `test_master_phases.py`, and new security test suite `test_phase1_security.py`.
- **HUMAN CHECKPOINT 1**: STOP and present Phase 1 report.

---

### Phase 2: Real Device Foundation (Upon Checkpoint 1 Approval)
- Real device ingestion transport (lightweight authenticated endpoint `POST /sensing/devices/ingest` with HMAC / token authentication).
- Device model enhancements: `status` (`REGISTERED`, `PROVISIONING`, `ONLINE`, `DEGRADED`, `OFFLINE`, `REVOKED`), `credential_hash`, `firmware_version`, `last_seen`, `packet_count`, `dropped_packet_count`.
- Provisioning, rotation, and revocation endpoints.
- Device heartbeat tracker.
- Dedicated device test suite `test_phase2_devices.py`.
- **HUMAN CHECKPOINT 2**: STOP and present Phase 2 report.

---

### Phase 3: Sensing Engine
- CSI processing pipeline: Validation -> Feature Extraction -> Classification -> Confidence -> Activity Event.
- Provenance tracking: `REAL_DEVICE`, `SIMULATION`, `MANUAL_TEST`.
- Room calibration workflows with RF similarity scoring.

---

### Phase 4: Real-Time System (Upon Phase 3 Completion)
- WebSocket server endpoint `/ws/stream` with JWT authentication and tenant/role channel subscription.
- Scoped event routing: CARE alerts only to authorized caregiver/family; SPACE occupancy only to facility manager / corporate staff.
- Connection management: reconnection, heartbeat/ping-pong, stale connection eviction.
- Dedicated WebSocket tests.
- **HUMAN CHECKPOINT 3**: STOP and present Phase 4 report.

---

### Phase 5: CARE Safety System (Upon Checkpoint 3 Approval)
- 5-stage Alert Lifecycle: `DETECTED` -> `ACTIVE` -> `ACKNOWLEDGED` -> `RESPONDING` -> `RESOLVED`.
- Confidence thresholds and alert escalation timers.
- Multi-resident family membership model and portal selection.
- Multi-channel notification service (Web Push, Email, SMS fallback).
- Family PWA manifest and service worker.
- **HUMAN CHECKPOINT 4**: STOP and present Phase 5 report.

---

### Phases 6 through 15
- Phase 6: Space Intelligence & Honest Heatmaps (LIVE vs SIMULATION vs STALE).
- Phase 7: Device Observability & System Admin Observatory.
- Phase 8: Maintenance Lifecycle & Work Orders.
- Phase 9: Sharing Policy UI Integration.
- Phase 10: CARE & SPACE Analytics Engine.
- Phase 11: Comprehensive Test Expansion.
- Phase 12: Pagination & Query Performance.
- Phase 13: Frontend Modular Architecture & Serious UX.
- Phase 14: Structured Logging, Health Checks & Observability.
- Phase 15: Full CI/CD & Documentation.

---

## User Review Required
> [!IMPORTANT]
> **Human Checkpoints are mandatory**. After Phase 1 execution, we will halt and present the full security & migration report, and wait for your explicit approval before initiating Phase 2.

## Proposed Changes for Phase 1

### Backend Core & Security
#### [MODIFY] [config.py](file:///d:/Wifisense/backend/app/core/config.py)
- Add refresh token settings (`REFRESH_TOKEN_EXPIRE_DAYS = 7`, `ACCESS_TOKEN_EXPIRE_MINUTES = 15`).
- Add production safeguard check on startup (fail loudly if `ENVIRONMENT=production` and default secret key is used).

#### [MODIFY] [security.py](file:///d:/Wifisense/backend/app/core/security.py)
- Implement `create_refresh_token()`, `verify_refresh_token()`, `revoke_token()`, `is_token_revoked()`.

#### [MODIFY] [entities.py](file:///d:/Wifisense/backend/app/models/entities.py)
- Add `RefreshToken` entity (id, user_id, token_hash, expires_at, revoked, replaced_by, created_at).
- Add `TokenRevocation` entity (jti/token_hash, revoked_at, expires_at, reason).
- Add `AuditLog` entity (id, who_user_id, who_email, what_action, resource_type, resource_id, result, details, ip_address, created_at).

#### [MODIFY] [auth.py](file:///d:/Wifisense/backend/app/routers/auth.py)
- Update login response to issue both `access_token` and `refresh_token`.
- Add `POST /auth/refresh` for rotating refresh tokens.
- Add `POST /auth/logout` to revoke access and refresh tokens.
- Add in-memory rate limiting for `/auth/login` and `/auth/register`.
- Add audit logging on login, logout, failed login, and role assignment.

#### [NEW] [audit.py](file:///d:/Wifisense/backend/app/core/audit.py)
- Audit log helper function `record_audit_event(session, who_user, action, resource_type, resource_id, result, details, request)`.

#### [NEW] [limiter.py](file:///d:/Wifisense/backend/app/core/limiter.py)
- Lightweight in-memory rate limiter middleware / dependency protecting auth and sensitive endpoints without requiring external Redis.

#### [NEW] [alembic setup](file:///d:/Wifisense/backend/alembic)
- Alembic migration environment with initial migration script representing current schema + Phase 1 additions.

### Verification Plan
- Run `test_boundaries.py` (Must stay 12/12 PASSED).
- Run `test_master_phases.py` (Must stay 8/8 PASSED).
- Run new `test_phase1_security.py` verifying:
  - Short-lived access token + refresh token generation.
  - Refresh token rotation (old refresh token is revoked when exchanged).
  - Reusing an old refresh token fails.
  - Server-side logout invalidates the access token (subsequent `/auth/me` returns 401).
  - Rate limiting triggers 429 after rapid repeated failed logins.
  - Audit log entries are written on login, logout, and role assignment.
