# Wi-Fi Sense Focus: Software Testing & Automation Report
**Automated Verification, Regression Testing, and Quality Assurance for Scrum Review 3**

* **Institution**: Amal Jyothi College of Engineering (Autonomous), Department of Computer Applications
* **Course**: Master of Computer Applications (MCA) Mini Project — Phase 1
* **Date**: September 21, 2026 (Target Milestone: Scrum Review 3 — September 22, 2026)
* **Guide / Scrum Master**: Binumon Joseph
* **Repository**: `Blessonjoseph07/WIFISENSE`
* **Target Branch**: `master` (Post-merge of PR #4 and PR #5 — Commit `76db278`)
* **Test Execution Environment**: Windows, Python 3.8.10 Virtual Environment, SQLite 3, Node.js v20, Vite 8.2

---

## 1. Executive Summary

This report documents the automated software testing execution and quality assurance results for the **Wi-Fi Sense Focus** platform leading into **Scrum Review 3** (representing ~75% project milestone completion).

Following the strict Git Merge Protocol, two major feature pull requests were formally reviewed and merged into `master`:
1. **Pull Request #4 (`feature/sharing-policy-ui`)**: Commit `d576148` — Added end-to-end SharingPolicy management UI in `OrgAdminView` and `CareAppShell` with comprehensive RBAC integration tests (`test_ui_flow_sharing_policy.py`).
2. **Pull Request #5 (`feature/test-coverage-expansion`)**: Commit `76db278` — Added unified business logic, sensing pipeline, alert lifecycle, and upload magic-byte verification suite (`test_business_logic.py`).

All automated test suites were executed sequentially against the updated `master` branch. Across 6 backend test modules and the frontend build pipeline:
- **Total Automated Test Suites Executed**: 48 test assertions across 6 test files
- **Total Passed**: 48 / 48 (100% Pass Rate)
- **Total Failed**: 0
- **Frontend Build Status**: Clean (0 errors, 48 modules bundled, 142 KB CSS, 1.17 MB JS)
- **Frontend Linter Status**: 0 errors (oxlint across 34 source files)

---

## 2. Test Suites Summary Table

| Test Suite File | Domain / Scope | Test Cases | Passed | Failed | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [`backend/test_business_logic.py`](file:///d:/Wifisense/backend/test_business_logic.py) | Sensing pipeline, alert lifecycle, non-blocking notification, sharing policy, analytics zero-state, upload magic-bytes | 7 | 7 | 0 | **PASS (100%)** |
| [`backend/test_ui_flow_sharing_policy.py`](file:///d:/Wifisense/backend/test_ui_flow_sharing_policy.py) | Sharing policy navigation gating, Org Admin mutation, Facility Manager read-only, unauthorized 403 enforcement | 4 | 4 | 0 | **PASS (100%)** |
| [`backend/test_boundaries.py`](file:///d:/Wifisense/backend/test_boundaries.py) | Deterministic context pinning, multi-tenant scoped reads, organization constraints, family portal boundaries, subscription gating | 16 | 16 | 0 | **PASS (100%)** |
| [`backend/test_phase1_security.py`](file:///d:/Wifisense/backend/test_phase1_security.py) | JWT refresh token rotation, compromised token reuse detection, server-side logout blacklist, audit logging, prod safeguards | 6 | 6 | 0 | **PASS (100%)** |
| [`backend/test_global_admin_alert_access.py`](file:///d:/Wifisense/backend/test_global_admin_alert_access.py) | Global Admin oversight vs operational separation, Caregiver/Facility Manager incident response, family member alert isolation | 7 | 7 | 0 | **PASS (100%)** |
| [`backend/test_master_phases.py`](file:///d:/Wifisense/backend/test_master_phases.py) | Emergency contact rules, medical records isolation, family portal gating, fall protocol escalation, RF calibration, energy recommendations | 8 | 8 | 0 | **PASS (100%)** |
| **Frontend Production Build** (`npm run build`) | Vite JSX compilation, CSS bundling, dynamic asset generation | 1 | 1 | 0 | **PASS (100%)** |
| **Frontend Linting** (`npm run lint`) | Static code analysis via Oxlint across React components | 34 files | 34 files | 0 errors | **PASS (100%)** |
| **TOTAL** | | **48 API Tests + 2 Frontend Suites** | **50** | **0** | **100% GREEN** |

---

## 3. Test Execution Logs & Evidence

### Suite 1: Comprehensive Business Logic & Sensing Telemetry
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_business_logic.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~8.2s
* **Actual Output**:
```text
==========================================================================
      WIFISENSE COMPREHENSIVE BUSINESS LOGIC & TELEMETRY SUITE            
==========================================================================

--- 1. Testing Sensing Event Pipeline & Classification ---
[PASS] SensingEvent #236 verified in DB (Activity: Walking, Confidence: 0.91).
[PASS] Cleaned up test SensingEvent.

--- 2. Testing Alert Lifecycle & AlertAcknowledgement Attribution ---
[PASS] Fall alert created: 7c7eed35-2bf7-4d80-907d-3534de97a60c (Status: new)
[PASS] Caregiver acknowledged alert 7c7eed35-2bf7-4d80-907d-3534de97a60c.
[PASS] AlertAcknowledgement recorded: acting user f1791ff4-bc2f-41c6-a240-af632edeb5c5 at 2026-09-21 14:35:43.788885.
[PASS] Audit log verified: ALERT_ACKNOWLEDGED by abhinanth@wifisense.com.
[PASS] Caregiver resolved alert 7c7eed35-2bf7-4d80-907d-3534de97a60c.
[PASS] AlertAcknowledgement resolved_at (2026-09-21 14:35:43.811603) and notes verified.
[PASS] Re-acknowledging already resolved alert correctly rejected with HTTP 400.
[PASS] Cleaned up lifecycle test alert and acknowledgements.

--- 3. Testing E2E Fall Alert Creation & Non-Blocking Notification Delivery ---
Simulating Fall_Detected event for device 752f278e-0b21-4ddf-8970-6c48169dbfca...
[PASS] Alert f51413ce-cadd-4b97-ae3a-d66188214e1b created successfully without blocking (HTTP 201).
Waiting for async background notification task...
[PASS] Notification delivery failed gracefully as expected (No SMTP server).
       Resolved recipients (6): ['abhinanth@wifisense.com', 'mary@wifisense.com', 'priya@wifisense.com', 'caregiver1@stmarys.com', 'anna@wifisense.com', 'robert@wifisense.com']
[PASS] Both assigned caregivers and authorized family members resolved.

--- 4. Testing Sharing Policy Gating & Authorization ---
[PASS] Family members successfully excluded when share_alert_history is False.

--- 5. Testing Unit send_alert_email Graceful Error Handling ---
[PASS] send_alert_email handled exception cleanly and created audit log.

--- 6. Testing Analytics 'Not Enough Data' for Empty Organization ---
[PASS] /analytics/occupancy-summary returned honest zero state (0 rooms, 0.0% rate).
[PASS] /analytics/alert-summary returned honest zero state (0 alerts).
[PASS] Cleaned up temporary empty organization and test user.

--- 7. Testing Photo Upload Anti-Disguise & Magic-Byte Verification ---
[PASS] Disguised non-image payload rejected by magic-byte sniffer (HTTP 400).
[PASS] Corrupt payload rejected by Pillow image verifier (HTTP 400).
[PASS] Genuine PNG accepted and processed successfully (DB photo_url: /uploads/user_f1791ff4-bc2f-41c6-a240-af632edeb5c5_1790001352_8b6135dc.png).
[PASS] Restored user photo_url state.

==========================================================================
           ALL BUSINESS LOGIC & TELEMETRY TESTS PASSED 100%!              
==========================================================================
```

---

### Suite 2: Sharing Policy Frontend Config & API Integration
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_ui_flow_sharing_policy.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~2.1s
* **Actual Output**:
```text
==========================================================================
  WIFISENSE SHARING POLICY FRONTEND CONFIG & API INTEGRATION TEST SUITE   
==========================================================================

--- 1. Testing Frontend Nav Configuration & Gating Matrix ---
[PASS] Navigation matrix verified: Org Admin & FM have view access; Caregiver is strictly blocked.

--- 2. Testing Org Admin View & Update UI Flow ---
[PASS] Org Admin successfully viewed 1 policy(ies). Target policy ID: 6cc65dd9-45e9-4dc8-9be7-bf7af262dd4e
Updating policy: share_presence -> False, severity_threshold -> CRITICAL...
[PASS] Org Admin successfully updated policy via UI payload.
[PASS] Policy changes persisted and verified on reload.
[PASS] Audit log verified: SHARING_POLICY_UPDATED by anjali@wifisense.com.
[PASS] Restored original policy values.

--- 3. Testing Facility Manager Read-Only UI Flow ---
[PASS] Facility Manager successfully viewed 1 policy(ies).
[PASS] Facility Manager edit attempt correctly rejected with HTTP 403 Forbidden.

--- 4. Testing Unauthorized Roles Blocked Flow ---
[PASS] Caregiver blocked from both GET (403) and PUT (403).
[PASS] Corporate Staff blocked from both GET (403) and PUT (403).

==========================================================================
           ALL SHARING POLICY INTEGRATION TESTS PASSED!                   
==========================================================================
```

---

### Suite 3: Direct API Boundary & Subscription Isolation
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_boundaries.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~4.1s
* **Actual Output**:
```text
=== RUNNING BACKEND BOUNDARY TESTS ===

--- 1. Testing Deterministic Context Pinning (Fix 1) ---
[PASS] System Admin login context verified (SYSTEM, is_system_admin=True)
[PASS] Corporate Facility Manager login context verified (CORPORATE)
[PASS] Corporate Staff login context verified (CORPORATE)
[PASS] Caregiver login context verified (ELDER_CARE)
[PASS] Elder-care Facility Manager login context verified (ELDER_CARE)
[PASS] Family Member login context verified (ELDER_CARE, role=family_member)

--- 2. Testing Scoped Reads (Fix 3 - Option A) ---
[PASS] Corporate user GET /residents returns empty list [] via scope isolation
[PASS] Caregiver GET /residents returns 14 residents

--- 3. Testing POST /residents Org Type Check (Fix 4) ---
[PASS] Corporate facility manager attempting POST /residents correctly received 403 Forbidden

--- 4. Testing SharingPolicy Endpoints (Fix 5) ---
[PASS] Corporate user calling GET /sharing-policies received 403 Forbidden
[PASS] Caregiver calling GET /sharing-policies received 403 Forbidden
[PASS] Caregiver calling PUT /sharing-policies/{id} received 403 Forbidden
[PASS] Elder-care FM calling GET /sharing-policies received 200 OK (1 policies)
[PASS] System Admin PUT /sharing-policies/{id} succeeded with 200 OK

--- 5. Testing Family Portal Boundaries ---
[PASS] Corporate user calling GET /family/resident-status received 403 Forbidden
[PASS] Corporate user calling POST /family/requests received 403 Forbidden
[PASS] Caregiver calling PATCH /family/requests/{id} received 403 Forbidden
[PASS] Family member GET /family/resident-status returned linked resident: Annamma

--- 6. Testing Legacy emergency_contact Role Access Rejection (B4) ---
[PASS] Legacy emergency_contact role blocked from GET /family/resident-status (HTTP 403)
[PASS] Legacy emergency_contact role blocked from POST /family/connections (HTTP 403)
[PASS] Legacy emergency_contact role blocked from GET /family/subscriptions (HTTP 403)

--- 7. Testing Explicit Subscription Gating Scenarios (B5) ---
[PASS] ACTIVE subscription: Full real-time resident telemetry accessible.
[PASS] PENDING subscription: Real-time telemetry withheld; subscription status communicated.
[PASS] EXPIRED subscription: Real-time telemetry withheld; subscription status communicated.
[PASS] SUSPENDED subscription: Real-time telemetry withheld; subscription status communicated.
[PASS] Restored ACTIVE subscription: Real-time telemetry restored successfully.

>>> ALL 16 DIRECT API BOUNDARY & SUBSCRIPTION TESTS PASSED SUCCESSFULLY! <<<
```

---

### Suite 4: Phase 1 Security & Production Foundation
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_phase1_security.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~1.5s
* **Actual Output**:
```text
=== RUNNING PHASE 1 SECURITY & PRODUCTION FOUNDATION TESTS ===

--- 1. Testing Login & Refresh Token Issuance ---
[PASS] Login successfully issued access_token and rotating refresh_token.

--- 2. Testing Refresh Token Rotation ---
[PASS] Token refresh rotated to new refresh_token successfully.

--- 3. Testing Refresh Token Reuse Detection ---
[PASS] Reusing old refresh token was blocked with HTTP 401 (compromised token reuse detection active).

--- 4. Testing Server-side Logout & Revocation List ---
[PASS] POST /auth/logout completed successfully.
[PASS] Revoked access token was blocked with HTTP 401 Unauthorized.

--- 5. Testing Structured Audit Logging (WHO, WHAT, WHEN, RESOURCE, RESULT) ---
[PASS] Audit logs verified (100 entries recorded with full WHO, WHAT, WHEN, RESOURCE, RESULT schema).

--- 6. Testing Production Safeguards ---
[PASS] Production safeguard successfully blocked default credentials in production mode.

>>> ALL PHASE 1 SECURITY & PRODUCTION FOUNDATION TESTS PASSED 100%! <<<
```

---

### Suite 5: Refined RBAC & Alert Oversight Verification
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_global_admin_alert_access.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~3.8s
* **Actual Output**:
```text
==========================================================================
   WIFISENSE REFINED RBAC & ALERT OVERSIGHT VERIFICATION SUITE           
==========================================================================

--- Test A: Global Admin Can View CARE Alerts (Global Oversight) ---
[PASS] Global Admin retrieved alert e070a00e-c087-4f44-bb67-4b18f5c25ba2 from GET /alerts.
[PASS] Global Admin retrieved alert e070a00e-c087-4f44-bb67-4b18f5c25ba2 from GET /alerts/active.
[PASS] Global Admin retrieved enriched alert details: Room Resident Room 101, Resident Devassy Varghese, Org St. Peter's Elder Care Home.

--- Test B: Global Admin Cannot Acknowledge CARE Alert ---
[PASS] Global Admin cannot acknowledge CARE alert (HTTP 403: You do not have permission to access this resource.).

--- Test C: Global Admin Cannot Mark CARE Alert As Responding ---
[PASS] Global Admin cannot mark CARE alert as responding (HTTP 403: You do not have permission to access this resource.).

--- Test D: Global Admin Cannot Resolve CARE Alert ---
[PASS] Global Admin cannot resolve CARE alert (HTTP 403: You do not have permission to access this resource.).

--- Test E: Facility Manager Can Operate Alerts (Ack -> Responding -> Resolve) ---
[PASS] Facility Manager acknowledged alert 594aa436-879e-44fd-b4e1-42bcf270d77e (HTTP 200).
[PASS] Facility Manager marked alert as responding (HTTP 200).
[PASS] Facility Manager resolved alert (HTTP 200).
[PASS] AlertAcknowledgement attributed to Facility Manager d324b29f-cc7e-458a-8c9c-3473dfdb7efa.
[PASS] AuditLog recorded for ALERT_RESOLVED by Facility Manager elizabeth@wifisense.com.

--- Test F: Caregiver Can Operate Alerts (Ack -> Responding -> Resolve) ---
[PASS] Caregiver acknowledged alert 7018808b-1c22-41a9-9d90-2884c6be1a78 (HTTP 200).
[PASS] Caregiver marked alert as responding (HTTP 200).
[PASS] Caregiver resolved alert (HTTP 200).
[PASS] AlertAcknowledgement attributed to Caregiver f1791ff4-bc2f-41c6-a240-af632edeb5c5.
[PASS] AuditLog recorded for ALERT_RESOLVED by Caregiver abhinanth@wifisense.com.

--- Test G: Family Member Cannot Operate Alerts ---
[PASS] Family Member blocked from GET /alerts (HTTP 403).
[PASS] Family Member blocked from PATCH /acknowledge (HTTP 403).
[PASS] Family Member blocked from PATCH /responding (HTTP 403).
[PASS] Family Member blocked from PATCH /resolve (HTTP 403).

==========================================================================
      ALL REFINED RBAC & ALERT OVERSIGHT TESTS PASSED 100%!               
==========================================================================
```

---

### Suite 6: Master Phases Requirements Verification
* **Command**: `d:\Wifisense\backend\venv\Scripts\python.exe test_master_phases.py`
* **Working Directory**: `d:\Wifisense\backend`
* **Execution Time**: ~2.2s
* **Actual Output**:
```text
=== TESTING MASTER PHASES REQUIREMENTS ===
[PASS] Phase 2: All 14 residents have at least 1 Emergency Contact.
[PASS] Phase 2: Corporate user strictly blocked from Elder Care medical records (HTTP 403).
[PASS] Phase 2 & 2A: Caregiver retrieved full resident profile with 2 emergency contacts, 2 doctors, 3 lab reports.
[PASS] Phase 2: Deleting sole emergency contact blocked by rule enforcement.
[PASS] Phase 3 & 4: Family Portal gated access active for Annamma Joseph.
[PASS] Phase 5 & 5A: Emergency Fall Protocol successfully refreshed active fall with Contact John Joseph (+91 94471 28934).
[PASS] Phase 7: Room Calibration verified (VALID, RF similarity: 96.8%).
[PASS] Phase 8: Corporate Space Intelligence schedules & energy recommendations accessible.

>>> ALL MASTER PHASES BACKEND TESTS PASSED 100%! <<<
```

---

### Suite 7: Frontend Production Bundle Compilation
* **Command**: `npm.cmd run build`
* **Working Directory**: `d:\Wifisense\frontend`
* **Execution Time**: 6.06s
* **Actual Output**:
```text
> frontend@0.0.0 build
> vite build

vite v8.2.1 building client environment for production...
transforming...✓ 48 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                            0.79 kB │ gzip:   0.45 kB
dist/assets/elderly-care-X7NZ7hsN.png     17.83 kB
dist/assets/index-CjB0CBFu.css           142.14 kB │ gzip:  20.34 kB
dist/assets/index-C6_uPOTA.js          1,175.90 kB │ gzip: 272.47 kB

✓ built in 6.06s
```

---

## 4. Quality Analysis & Conformance with Scrum Review 3

1. **Security & Identity**: JWT refresh token rotation with single-use enforcement, compromised refresh token reuse detection, server-side blacklisting (`TokenRevocation`), and complete audit trail logging with actor attribution (`who`, `what`, `when`, `resource`, `result`).
2. **Deterministic RBAC**: Robust separation of duties across 7 system roles. System Admin oversight is strictly decoupled from on-the-ground clinical intervention, ensuring clinical and corporate data privacy is rigorously maintained.
3. **Data Integrity & Boundaries**: Multi-tenant boundaries prevent cross-organization data leakage. Corporate operators cannot read clinical or resident records; family members can only read data for linked residents under an active subscription tier.
4. **Resilience**: Non-blocking asynchronous notifications ensure fall alert creation always completes immediately with HTTP 201 regardless of external mail server latency or failure. Photo uploads are shielded against malicious polyglot file disguise via both magic-byte sniffing and Pillow buffer decoding.
