"""
Master Report Builder — Chapters 5 to 7 (Wi-Fi Sense Architecture)
MCA Academic Report Toolkit — Amal Jyothi College of Engineering Autonomous
Department of Computer Applications | Course: 24MCAR295
"""

import os
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

try:
    from .styles import (
        add_chapter_heading, add_heading_1, add_heading_2, add_heading_3,
        add_body_p, add_bullet_p, add_styled_table, add_figure_image, add_code_block
    )
except ImportError:
    from styles import (
        add_chapter_heading, add_heading_1, add_heading_2, add_heading_3,
        add_body_p, add_bullet_p, add_styled_table, add_figure_image, add_code_block
    )

def add_chapters_5_to_7(doc, cfg=None):
    """Builds Chapter 5, Chapter 6, and Chapter 7 for Wi-Fi Sense."""
    if cfg is None:
        cfg = {}

    pj = cfg.get("project", {})
    st = cfg.get("student", {})
    project_title = pj.get("title", "Wi-Fi Sense: AI-Powered Indoor Monitoring and Facility Intelligence Platform Using Wi-Fi CSI")
    project_short = pj.get("short_name", "Wi-Fi Sense")
    student_name = st.get("full_name", "BLESSON JOSEPH BYJU")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    diagrams_dir = os.path.join(base_dir, "01_Inputs", "diagrams")
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")

    # =========================================================================
    # CHAPTER 5: SYSTEM TESTING
    # =========================================================================
    add_chapter_heading(doc, 5, "System Testing")

    add_heading_1(doc, "5.1 INTRODUCTION")
    add_body_p(
        doc,
        f"System testing is an essential phase in the software development lifecycle of {project_short}, verifying that the "
        "integrated platform functions in strict compliance with its functional, clinical, and security requirements. "
        "The testing process evaluates end-to-end operational behavior, mathematical subcarrier feature extraction, "
        "instantaneous emergency fall alerting, multi-tenant Role-Based Access Control (RBAC), and hardware diagnostic stability."
    )
    add_body_p(
        doc,
        "The testing strategy follows a structured, layered methodology. Unit testing verifies isolated functions and algorithms, "
        "integration testing validates communication between the serial bridge, FastAPI backend, PostgreSQL database, and WebSocket channels, "
        "validation testing confirms functional business rules and boundaries, and automated browser-driven Selenium testing validates "
        "complete user journeys through real desktop and mobile viewports."
    )

    add_heading_2(doc, "Guiding Principles of the Testing Process")
    add_bullet_p(doc, "Deterministic Testing: Tests must produce consistent, reproducible outcomes using controlled synthetic CSI vectors and simulated serial packets.", "Deterministic Testing")
    add_bullet_p(doc, "Integration Testing: Verifies end-to-end message flow across the PySerial gateway, ASGI endpoints, PostgreSQL database, and WebSocket broadcasts.", "Integration Testing")
    add_bullet_p(doc, "Code Coverage: Rigorous coverage measurement across backend routers, entities, and signal processing routines with a minimum target of 90%.", "Code Coverage")
    add_bullet_p(doc, "Continuous Integration: Automated test suites execute upon every Git push to prevent regression anomalies from reaching production.", "Continuous Integration")
    add_bullet_p(doc, "Functional Testing: Validates that presence detection, walking, sitting, and catastrophic fall states are correctly inferred and surfaced.", "Functional Testing")
    add_bullet_p(doc, "Security Testing: Verifies JWT token verification, password hashing, RBAC route gating, and zero-leak sharing policy boundaries.", "Security Testing")
    add_bullet_p(doc, "Error Handling: Asserts that invalid sensor tokens, malformed packets, and dropped network connections fail safely without crashing the platform.", "Error Handling")

    add_heading_1(doc, "5.2 TEST PLAN")
    add_body_p(
        doc,
        f"The test plan defines the testing activities, environments, tools, and acceptance criteria for {project_short}. "
        "Testing progresses systematically from isolated units to the fully assembled production system."
    )

    add_heading_2(doc, "1. Unit Testing")
    add_bullet_p(doc, "Scope: Individual classes, mathematical preprocessors, password hashing functions, and JWT validation logic.", "Scope")
    add_bullet_p(doc, "Tools: Pytest 8.1, Python unittest, and Requests.", "Tools")
    add_bullet_p(doc, "Entry Criteria: The relevant module code compiles and loads in the Python virtual environment.", "Entry Criteria")
    add_bullet_p(doc, "Exit Criteria: All unit tests pass with >=90% line coverage of critical business logic.", "Exit Criteria")

    add_heading_3(doc, "Sample Unit Test Cases")
    ut_headers = ["Test ID", "Test Scenario", "Expected Result"]
    ut_rows = [
        ["UT-01", "Validate salted bcrypt password hashing", "Produces valid hash; verify_password returns True for valid password"],
        ["UT-02", "Validate incorrect password verification", "verify_password returns False for invalid credentials"],
        ["UT-03", "Create user entity with valid email and role", "User record initialized with active status and UUID primary key"],
        ["UT-04", "Create user entity with duplicate email", "IntegrityError raised; database prevents duplicate user registration"],
        ["UT-05", "Generate JWT access token with user claims", "Token generated containing user UUID, role, and valid expiry timestamp"],
        ["UT-06", "Verify expired JWT access token", "HTTP 401 Unauthorized returned with signature expired message"],
        ["UT-07", "Validate linear phase unwrapping algorithm", "Eliminates 2π phase jump discontinuities across 56 subcarriers"],
        ["UT-08", "Apply Hampel outlier filter on noisy signal", "Outlier impulse spikes replaced with 7-sample moving median"],
        ["UT-09", "Compute normalized subcarrier amplitude variance", "Variance metric computed strictly within normalized range [0.0, 1.0]"],
        ["UT-10", "Evaluate empty-room dynamic baseline subtraction", "Static wall reflection covariance subtracted, leaving zero mean noise"],
        ["UT-11", "Classify static presence from CSI variance", "Infers 'Presence' activity state with confidence >= 0.85"],
        ["UT-12", "Classify walking motion from Doppler shift", "Infers 'Walking' activity state with high Doppler velocity signature"],
        ["UT-13", "Classify catastrophic fall from sudden drop", "Infers 'Fall_Detected' and flags emergency state machine"],
        ["UT-14", "Evaluate emergency alert cooldown prevention", "Suppresses duplicate alert within 60-second cooldown window"],
        ["UT-15", "Validate node MAC address format", "Accepts standard 17-char colon-separated IEEE 802 MAC string"],
        ["UT-16", "Reject invalid node MAC address", "Pydantic validation error raised for malformed MAC string"],
        ["UT-17", "Validate tenant context switching logic", "ELDER_CARE user routed to CareAppShell; CORPORATE to SpaceAppShell"],
        ["UT-18", "Verify family sharing policy filtering", "Suppresses activity detail when activity_detail toggle is disabled"],
        ["UT-19", "Compute room utilization percentage", "Calculates active hours divided by total operational hours accurately"],
        ["UT-20", "Validate audit log event generation", "Audit record created with timestamp, actor UUID, and action string"]
    ]
    add_styled_table(doc, ut_headers, ut_rows, [0.8, 2.8, 2.8], "Table 5.1: Sample Unit Test Cases (UT-01 to UT-20)")

    add_heading_3(doc, "Coverage Targets")
    cov_headers = ["Component", "Proposed Target", "Measurement Tool"]
    cov_rows = [
        ["Authentication & Security Modules", "95% line coverage", "Coverage.py / Pytest-cov"],
        ["CSI Preprocessing & Inference Logic", "92% line coverage", "Coverage.py / Pytest-cov"],
        ["Database Entity Repositories & Migrations", "90% line coverage", "Coverage.py / Pytest-cov"],
        ["RESTful ASGI Controllers & Gateways", "90% line coverage", "Pytest TestClient"],
        ["Frontend UI Shells & Hooks", "85% component coverage", "Jest / React Testing Library"]
    ]
    add_styled_table(doc, cov_headers, cov_rows, [2.4, 2.0, 2.0], "Table 5.2: Code Coverage Targets by Component")

    add_heading_2(doc, "2. Integration Testing")
    add_bullet_p(doc, "Scope: Communication between the serial bridge, FastAPI backend, PostgreSQL database, and WebSocket alert streams.", "Scope")
    add_bullet_p(doc, "Tools: Pytest, Testcontainers, PostgreSQL sandbox, and WebSocket test clients.", "Tools")
    add_bullet_p(doc, "Entry Criteria: All unit tests pass cleanly.", "Entry Criteria")
    add_bullet_p(doc, "Exit Criteria: End-to-end integration flows execute without unhandled exceptions or data loss.", "Exit Criteria")

    add_heading_3(doc, "Sample Integration Test Cases")
    it_headers = ["Test ID", "Test Scenario", "Expected Result"]
    it_rows = [
        ["IT-01", "Create and retrieve tenant organization", "Organization persisted in PostgreSQL and retrievable via GET /organizations"],
        ["IT-02", "Register ESP32-S3 device to room", "Device mapped to room_id; hardware token generated and verified"],
        ["IT-03", "Ingest raw CSI packet stream from node", "POST /sensing/ingest accepts payload, parses subcarriers, commits to database"],
        ["IT-04", "Trigger fall event to alert dispatch", "Fall event triggers atomic alert creation and WebSocket broadcast to clients"],
        ["IT-05", "Caregiver acknowledges emergency alert", "Alert status transitions from DETECTION to ACKNOWLEDGED with user attribution"],
        ["IT-06", "Caregiver resolves emergency incident", "Status transitions to RESOLVED; resolution notes committed to database"],
        ["IT-07", "Enforce tenant boundary between care and corporate", "Corporate user querying /residents endpoint receives HTTP 403 Forbidden"],
        ["IT-08", "Handle database connection pool exhaustion", "FastAPI connection pool queues requests and recovers gracefully without 500 errors"],
        ["IT-09", "Verify WebSocket client reconnection on network drop", "Client automatically reconnects with exponential backoff and resynchronizes state"],
        ["IT-10", "Simulate high-frequency packet flood (100 pkts/sec)", "Ingestion queue buffers packets cleanly without memory leak or dropped frames"],
        ["IT-11", "Verify sharing policy toggle update", "Mutation to SharingPolicy immediately filters data returned by /family endpoints"],
        ["IT-12", "Process simulated Razorpay subscription webhook", "Payment webhook validates signature and activates Family Care Plan subscription"],
        ["IT-13", "Audit log persistence on administrative mutation", "Administrative role modification generates immutable record in audit_logs"],
        ["IT-14", "Verify node heartbeat and fault detection", "Node offline for >5 minutes flagged as OFFLINE with service desk ticket"],
        ["IT-15", "Validate empty-room baseline recalibration API", "POST /sensing/calibrate computes and stores new amplitude baseline in DB"],
        ["IT-16", "Verify database rollback on transactional failure", "Failed multi-table write rolls back cleanly, preserving data consistency"]
    ]
    add_styled_table(doc, it_headers, it_rows, [0.8, 2.8, 2.8], "Table 5.3: Sample Integration Test Cases (IT-01 to IT-16)")

    add_heading_2(doc, "3. Validation Testing (System Testing)")
    add_body_p(
        doc,
        "Validation testing confirms that the fully assembled software satisfies all functional business rules, "
        "security policies, and input boundary constraints specified in the requirements document."
    )
    vt_headers = ["Test ID", "Field / Boundary Condition", "Expected Result"]
    vt_rows = [
        ["VT-01", "Empty email or password during login", "Validation error returned; form submission rejected with HTTP 422"],
        ["VT-02", "Malformed email address format", "Rejected with descriptive 'Invalid email format' message"],
        ["VT-03", "Missing mandatory room name during creation", "Request rejected before database insert occurs"],
        ["VT-04", "Duplicate room name within same floor", "Rejected due to unique composite room constraint"],
        ["VT-05", "Invalid JWT authorization header format", "Rejected with HTTP 401 Unauthorized; missing Bearer prefix"],
        ["VT-06", "Tampered JWT cryptographic signature", "Signature verification fails; access immediately denied"],
        ["VT-07", "CSI payload with missing subcarrier array", "Payload rejected with HTTP 400 Bad Request"],
        ["VT-08", "Out-of-range model confidence (>1.0)", "Check constraint rejects record; value must be within [0.0, 1.0]"],
        ["VT-09", "Caregiver resolving alert without notes", "Accepted or warned depending on facility mandatory notes policy"],
        ["VT-10", "Unauthorized user calling admin endpoints", "HTTP 403 Forbidden returned; privilege escalation blocked"]
    ]
    add_styled_table(doc, vt_headers, vt_rows, [0.8, 2.8, 2.8], "Table 5.4: Sample Validation Test Cases (VT-01 to VT-10)")

    add_heading_2(doc, "4. User Acceptance Testing (UAT)")
    add_body_p(
        doc,
        "User Acceptance Testing evaluates the system from the operational perspective of clinical caregivers, "
        "facility directors, and corporate administrators. Testing sessions were conducted using realistic duty scenarios:"
    )
    uat_headers = ["Scenario ID", "User Task / Operational Scenario", "Evaluation Criteria"]
    uat_rows = [
        ["UAT-01", "Caregiver logs in and monitors room feed", "Room status cards render cleanly; color coding is immediately clear"],
        ["UAT-02", "Accidental fall occurs in resident bedroom", "High-contrast emergency banner and audio siren alert caregiver in <1s"],
        ["UAT-03", "Caregiver acknowledges emergency and triages", "One-tap button silences siren; status updates to 'Acknowledged'"],
        ["UAT-04", "Caregiver resolves incident with notes", "Resolution saved cleanly; incident archived in historical log"],
        ["UAT-05", "Facility manager inspects sensor health fleet", "Online/offline counters accurately reflect physical node states"],
        ["UAT-06", "Facility manager updates privacy sharing rules", "Toggles for presence and activity detail update instantly"],
        ["UAT-07", "Family member views parent status in portal", "Dignified presence status displayed without camera images"],
        ["UAT-08", "Corporate staff audits vacant meeting rooms", "Accurately identifies unoccupied rooms running air conditioning"]
    ]
    add_styled_table(doc, uat_headers, uat_rows, [0.8, 2.8, 2.8], "Table 5.5: User Acceptance Testing Scenarios (UAT-01 to UAT-08)")

    add_heading_2(doc, "5. Automation Testing")
    add_body_p(
        doc,
        "Automation testing replaces manual verification with deterministic, repeatable scripts executed via command-line "
        "runners and continuous integration pipelines. In Wi-Fi Sense, browser-level user workflows are automated using "
        "Selenium WebDriver with Python and Pytest (Section 5.2.6). Five comprehensive test suites were executed against the "
        "running application."
    )

    # 5.2.6 SELENIUM TESTING
    doc.add_page_break()
    add_heading_2(doc, "5.2.6 Selenium Testing")
    add_body_p(
        doc,
        "Selenium WebDriver automates real browser sessions the way an authentic user would: opening pages, locating DOM elements, "
        "entering credentials, clicking controls, asserting visual state, and capturing high-resolution evidence screenshots. "
        "The Wi-Fi Sense test suites are written in Python and executed using Pytest in headless Google Chrome at 1920x1080 resolution."
    )

    # -------------------------------------------------------------------------
    # TEST CASE 1: USER AUTHENTICATION & ROLE-BASED ROUTING
    # -------------------------------------------------------------------------
    add_heading_3(doc, "Test Case 1: User Login & Role-Based Dashboard Routing")
    add_body_p(doc, "Code:")
    tc1_code = (
        "import os\n"
        "import pytest\n"
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "from selenium.webdriver.support.ui import WebDriverWait\n"
        "from selenium.webdriver.support import expected_conditions as EC\n\n"
        "BASE_URL = os.getenv('WIFISENSE_BASE_URL', 'http://localhost:5173')\n"
        "TEST_EMAIL = 'mary@wifisense.com'\n"
        "TEST_PASSWORD = 'marypassword'\n\n"
        "def test_caregiver_authentication(driver):\n"
        "    driver.get(f'{BASE_URL}/login')\n"
        "    wait = WebDriverWait(driver, 10)\n"
        "    email_in = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type=\"email\"]')))\n"
        "    pass_in = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[type=\"password\"]')))\n"
        "    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type=\"submit\"]')))\n"
        "    email_in.send_keys(TEST_EMAIL)\n"
        "    pass_in.send_keys(TEST_PASSWORD)\n"
        "    submit_btn.click()\n"
        "    # Verify routing to CareAppShell\n"
        "    heading = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Central Monitoring')]\")))\n"
        "    assert heading.is_displayed(), 'Failed to mount Caregiver Monitoring Console.'"
    )
    add_code_block(doc, tc1_code)

    add_body_p(doc, "Screenshot:")
    t1_term = os.path.join(diagrams_dir, "terminal_test_1.png")
    if os.path.exists(t1_term):
        add_figure_image(doc, t1_term, "Figure 5.1: Login test run (pytest output)", width_inches=5.8)

    add_body_p(
        doc,
        "Figure 5.1 shows four authentication tests collected from tests/test_01_authentication.py, all passed, in 11.65 seconds."
    )

    add_body_p(doc, "Test Report:")
    tc1_rep_headers = ["Field", "Detail", "Field", "Detail"]
    tc1_rep_rows = [
        ["Project Name", "Wi-Fi Sense", "Module Name", "Authentication & RBAC"],
        ["Test Case ID", "Test_1", "Test Priority", "High"],
        ["Test Title", "Verify user login and role-based shell routing", "Test Designed Date", "30/09/2026"],
        ["Test Designed By", student_name, "Test Execution Date", "22/10/2026"],
        ["Test Executed By", student_name, "Execution Status", "Passed"]
    ]
    add_styled_table(doc, tc1_rep_headers, tc1_rep_rows, [1.4, 1.8, 1.4, 1.8], "Test Case 1 Summary: User Authentication")

    tc1_steps_headers = ["Step", "Test Step", "Test Data", "Expected Result", "Actual Result", "Status"]
    tc1_steps_rows = [
        ["1", "Open login page", "URL: <base_url>/login", "Landing page and login form mount cleanly", "Passed (test_open_landing_page)", "Pass"],
        ["2", "Submit valid caregiver credentials", "mary@wifisense.com / marypassword", "JWT token issued; user redirected to CareAppShell", "Passed (test_valid_caregiver_login)", "Pass"],
        ["3", "Submit invalid credentials", "invalid@wifisense.com / badpass", "Error banner rendered; user remains on login page", "Passed (test_invalid_credentials_rejected)", "Pass"],
        ["4", "Verify CareAppShell console elements", "Role: caregiver", "Central Monitoring heading and room feed displayed", "Passed (test_careapp_shell_routing)", "Pass"]
    ]
    add_styled_table(doc, tc1_steps_headers, tc1_steps_rows, [0.5, 1.5, 1.4, 1.5, 1.0, 0.5], "Test Case 1 Steps: Verification Breakdown")

    # -------------------------------------------------------------------------
    # TEST CASE 2: REAL-TIME FALL DETECTION & EMERGENCY PROTOCOL
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_3(doc, "Test Case 2: Contactless Fall Detection & Emergency Incident Workflow")
    add_body_p(doc, "Code:")
    tc2_code = (
        "import os\n"
        "import pytest\n"
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "from selenium.webdriver.support.ui import WebDriverWait\n"
        "from selenium.webdriver.support import expected_conditions as EC\n\n"
        "def test_fall_detection_and_emergency_protocol(driver):\n"
        "    # Authenticate as caregiver\n"
        "    login_as_caregiver(driver)\n"
        "    wait = WebDriverWait(driver, 15)\n"
        "    # Trigger simulated CSI fall event via test harness\n"
        "    simulate_csi_fall_vector(room_id='room_204')\n"
        "    # Assert high-contrast emergency fall banner appears\n"
        "    alert_banner = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'EMERGENCY FALL DETECTED')]\")))\n"
        "    assert alert_banner.is_displayed(), 'Emergency fall alert banner not displayed.'\n"
        "    # Click Acknowledge button\n"
        "    ack_btn = wait.until(EC.element_to_be_clickable((By.XPATH, \"//button[contains(text(), 'ACKNOWLEDGE')]\")))\n"
        "    ack_btn.click()\n"
        "    # Verify audio siren silences and status updates\n"
        "    wait.until(EC.invisibility_of_element_located((By.XPATH, \"//button[contains(text(), 'ACKNOWLEDGE')]\")))"
    )
    add_code_block(doc, tc2_code)

    add_body_p(doc, "Screenshot:")
    t2_term = os.path.join(diagrams_dir, "terminal_test_2.png")
    if os.path.exists(t2_term):
        add_figure_image(doc, t2_term, "Figure 5.2: Fall incident test run (pytest output)", width_inches=5.8)

    add_body_p(
        doc,
        "Figure 5.2 shows three fall incident tests collected from tests/test_02_fall_incident.py, all passed, in 14.82 seconds."
    )

    add_body_p(doc, "Test Report:")
    tc2_rep_headers = ["Field", "Detail", "Field", "Detail"]
    tc2_rep_rows = [
        ["Project Name", "Wi-Fi Sense", "Module Name", "Incident & Alert Management"],
        ["Test Case ID", "Test_2", "Test Priority", "Critical"],
        ["Test Title", "Verify real-time fall detection, siren alert, and acknowledgment", "Test Designed Date", "30/09/2026"],
        ["Test Designed By", student_name, "Test Execution Date", "22/10/2026"],
        ["Test Executed By", student_name, "Execution Status", "Passed"]
    ]
    add_styled_table(doc, tc2_rep_headers, tc2_rep_rows, [1.4, 1.8, 1.4, 1.8], "Test Case 2 Summary: Fall Incident Management")

    tc2_steps_headers = ["Step", "Test Step", "Test Data", "Expected Result", "Actual Result", "Status"]
    tc2_steps_rows = [
        ["1", "Sign in as caregiver", "mary@wifisense.com", "Landed on Central Monitoring console", "Passed (test_caregiver_login)", "Pass"],
        ["2", "Inject CSI fall perturbation vector", "Room 204: Sudden Drop", "Variance > threshold; Alert created in PostgreSQL", "Passed (test_csi_fall_vector)", "Pass"],
        ["3", "Verify emergency alert banner in DOM", "Room 204: Annamma Joseph", "Red pulsing banner rendered with resident details", "Passed (test_emergency_banner)", "Pass"],
        ["4", "Click 'Acknowledge' button", "Actor: Sr. Mary Sebastian", "Alert status transitions to Acknowledged; siren silences", "Passed (test_caregiver_ack)", "Pass"]
    ]
    add_styled_table(doc, tc2_steps_headers, tc2_steps_rows, [0.5, 1.5, 1.4, 1.5, 1.0, 0.5], "Test Case 2 Steps: Verification Breakdown")

    # -------------------------------------------------------------------------
    # TEST CASE 3: SHARING POLICY CONFIGURATION
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_3(doc, "Test Case 3: Resident Privacy & Telemetry Sharing Policy Configuration")
    add_body_p(doc, "Code:")
    tc3_code = (
        "import os\n"
        "import pytest\n"
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "from selenium.webdriver.support.ui import WebDriverWait\n"
        "from selenium.webdriver.support import expected_conditions as EC\n\n"
        "def test_sharing_policy_configuration(driver):\n"
        "    login_as_facility_manager(driver)\n"
        "    wait = WebDriverWait(driver, 10)\n"
        "    # Navigate to Sharing Policies page\n"
        "    driver.get(f'{BASE_URL}/policies')\n"
        "    heading = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Family Data Sharing Policies')]\")))\n"
        "    assert heading.is_displayed(), 'Sharing policy management page failed to load.'\n"
        "    # Toggle Activity & Posture Detail disclosure off\n"
        "    toggle_btn = wait.until(EC.element_to_be_clickable((By.XPATH, \"//div[contains(., 'Activity & Posture Detail')]//input[@type='checkbox']\")))\n"
        "    toggle_btn.click()\n"
        "    # Save policy changes\n"
        "    save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, \"//button[contains(., 'Save Policy Changes')]\")))\n"
        "    save_btn.click()\n"
        "    # Verify success toast notification\n"
        "    toast = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Policy updated successfully')]\")))\n"
        "    assert toast.is_displayed()"
    )
    add_code_block(doc, tc3_code)

    add_body_p(doc, "Screenshot:")
    t3_term = os.path.join(diagrams_dir, "terminal_test_3.png")
    if os.path.exists(t3_term):
        add_figure_image(doc, t3_term, "Figure 5.3: Sharing policy test run (pytest output)", width_inches=5.8)

    add_body_p(
        doc,
        "Figure 5.3 shows three sharing policy tests collected from tests/test_03_sharing_policy.py, all passed, in 9.40 seconds."
    )

    add_body_p(doc, "Test Report:")
    tc3_rep_headers = ["Field", "Detail", "Field", "Detail"]
    tc3_rep_rows = [
        ["Project Name", "Wi-Fi Sense", "Module Name", "Data Governance & Sharing Policies"],
        ["Test Case ID", "Test_3", "Test Priority", "Medium"],
        ["Test Title", "Verify resident privacy controls and telemetry sharing toggles", "Test Designed Date", "30/09/2026"],
        ["Test Designed By", student_name, "Test Execution Date", "22/10/2026"],
        ["Test Executed By", student_name, "Execution Status", "Passed"]
    ]
    add_styled_table(doc, tc3_rep_headers, tc3_rep_rows, [1.4, 1.8, 1.4, 1.8], "Test Case 3 Summary: Privacy Policies")

    tc3_steps_headers = ["Step", "Test Step", "Test Data", "Expected Result", "Actual Result", "Status"]
    tc3_steps_rows = [
        ["1", "Sign in as Facility Manager", "elizabeth@wifisense.com", "Landed on Facility Management console", "Passed (test_manager_login)", "Pass"],
        ["2", "Navigate to Sharing Policies page", "Route: /policies", "Policy toggles render with current tenant state", "Passed (test_load_policies)", "Pass"],
        ["3", "Toggle 'Activity & Posture Detail' to OFF", "Disclosure: False", "Checkbox state updates to unchecked", "Passed (test_toggle_activity)", "Pass"],
        ["4", "Save policy changes and commit", "Click 'Save Changes'", "HTTP 200 returned; toast notification confirms commit", "Passed (test_save_policy)", "Pass"]
    ]
    add_styled_table(doc, tc3_steps_headers, tc3_steps_rows, [0.5, 1.5, 1.4, 1.5, 1.0, 0.5], "Test Case 3 Steps: Verification Breakdown")

    # -------------------------------------------------------------------------
    # TEST CASE 4: FAMILY GUARDIAN PORTAL
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_3(doc, "Test Case 4: Family Guardian Subscription Portal & Daily Health Check")
    add_body_p(doc, "Code:")
    tc4_code = (
        "import os\n"
        "import pytest\n"
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "from selenium.webdriver.support.ui import WebDriverWait\n"
        "from selenium.webdriver.support import expected_conditions as EC\n\n"
        "def test_family_portal_wellness_check(driver):\n"
        "    login_as_family_member(driver)\n"
        "    wait = WebDriverWait(driver, 10)\n"
        "    # Assert Family Care Portal header\n"
        "    heading = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Family Care Portal')]\")))\n"
        "    assert heading.is_displayed()\n"
        "    # Verify presence indicator for Annamma Joseph\n"
        "    presence_badge = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Presence detected')]\")))\n"
        "    assert presence_badge.is_displayed()\n"
        "    # Verify no cameras badge\n"
        "    no_cam_badge = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'No cameras: Wi-Fi sensing only')]\")))\n"
        "    assert no_cam_badge.is_displayed()\n"
        "    # Verify Care Plan subscription card\n"
        "    plan_card = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Care Plan subscription')]\")))\n"
        "    assert plan_card.is_displayed()"
    )
    add_code_block(doc, tc4_code)

    add_body_p(doc, "Screenshot:")
    t4_term = os.path.join(diagrams_dir, "terminal_test_4.png")
    if os.path.exists(t4_term):
        add_figure_image(doc, t4_term, "Figure 5.4: Family portal test run (pytest output)", width_inches=5.8)

    add_body_p(
        doc,
        "Figure 5.4 shows three family portal tests collected from tests/test_04_family_portal.py, all passed, in 10.15 seconds."
    )

    add_body_p(doc, "Test Report:")
    tc4_rep_headers = ["Field", "Detail", "Field", "Detail"]
    tc4_rep_rows = [
        ["Project Name", "Wi-Fi Sense", "Module Name", "Family Portal & Subscriptions"],
        ["Test Case ID", "Test_4", "Test Priority", "High"],
        ["Test Title", "Verify family member presence check, safety log, and subscription plan", "Test Designed Date", "30/09/2026"],
        ["Test Designed By", student_name, "Test Execution Date", "22/10/2026"],
        ["Test Executed By", student_name, "Execution Status", "Passed"]
    ]
    add_styled_table(doc, tc4_rep_headers, tc4_rep_rows, [1.4, 1.8, 1.4, 1.8], "Test Case 4 Summary: Family Portal")

    tc4_steps_headers = ["Step", "Test Step", "Test Data", "Expected Result", "Actual Result", "Status"]
    tc4_steps_rows = [
        ["1", "Sign in as family member", "john@wifisense.com", "Landed on Family Care Portal shell", "Passed (test_family_login)", "Pass"],
        ["2", "Inspect resident wellness card", "Annamma Joseph", "Presence detected badge and room suite displayed", "Passed (test_presence_badge)", "Pass"],
        ["3", "Verify privacy guarantee badge", "Zero-camera policy", "'No cameras: Wi-Fi sensing only' badge rendered", "Passed (test_privacy_badge)", "Pass"],
        ["4", "Inspect subscription plan status", "Care Plan: Active", "Monthly 499 INR plan status and next renewal date displayed", "Passed (test_plan_card)", "Pass"]
    ]
    add_styled_table(doc, tc4_steps_headers, tc4_steps_rows, [0.5, 1.5, 1.4, 1.5, 1.0, 0.5], "Test Case 4 Steps: Verification Breakdown")

    # -------------------------------------------------------------------------
    # TEST CASE 5: CORPORATE WORKPLACE OCCUPANCY & ENERGY ANALYTICS
    # -------------------------------------------------------------------------
    doc.add_page_break()
    add_heading_3(doc, "Test Case 5: Corporate Workplace Occupancy & Energy Analytics")
    add_body_p(doc, "Code:")
    tc5_code = (
        "import os\n"
        "import pytest\n"
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "from selenium.webdriver.support.ui import WebDriverWait\n"
        "from selenium.webdriver.support import expected_conditions as EC\n\n"
        "def test_corporate_workspace_intelligence(driver):\n"
        "    login_as_corporate_staff(driver)\n"
        "    wait = WebDriverWait(driver, 10)\n"
        "    # Assert Corporate Space & Energy header\n"
        "    heading = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Corporate Space & Energy Intelligence')]\")))\n"
        "    assert heading.is_displayed()\n"
        "    # Verify Peak Utilization metric card\n"
        "    util_card = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'Peak Utilization Rate')]\")))\n"
        "    assert util_card.is_displayed()\n"
        "    # Verify energy action recommendation\n"
        "    action_btn = wait.until(EC.element_to_be_clickable((By.XPATH, \"//button[contains(., 'SHUT OFF ALL VACANT ROOMS')]\")))\n"
        "    assert action_btn.is_displayed()\n"
        "    # Trigger bulk shutdown action\n"
        "    action_btn.click()\n"
        "    # Confirm success message\n"
        "    toast = wait.until(EC.visibility_of_element_located((By.XPATH, \"//*[contains(text(), 'HVAC power mitigations applied')]\")))\n"
        "    assert toast.is_displayed()"
    )
    add_code_block(doc, tc5_code)

    add_body_p(doc, "Screenshot:")
    t5_term = os.path.join(diagrams_dir, "terminal_test_5.png")
    if os.path.exists(t5_term):
        add_figure_image(doc, t5_term, "Figure 5.5: Corporate space test run (pytest output)", width_inches=5.8)

    add_body_p(
        doc,
        "Figure 5.5 shows three corporate space tests collected from tests/test_05_corporate_space.py, all passed, in 12.30 seconds."
    )

    add_body_p(doc, "Test Report:")
    tc5_rep_headers = ["Field", "Detail", "Field", "Detail"]
    tc5_rep_rows = [
        ["Project Name", "Wi-Fi Sense", "Module Name", "Workplace Space & Energy Analytics"],
        ["Test Case ID", "Test_5", "Test Priority", "Medium"],
        ["Test Title", "Verify workplace space utilization, meeting room status, and energy mitigation", "Test Designed Date", "30/09/2026"],
        ["Test Designed By", student_name, "Test Execution Date", "22/10/2026"],
        ["Test Executed By", student_name, "Execution Status", "Passed"]
    ]
    add_styled_table(doc, tc5_rep_headers, tc5_rep_rows, [1.4, 1.8, 1.4, 1.8], "Test Case 5 Summary: Corporate Analytics")

    tc5_steps_headers = ["Step", "Test Step", "Test Data", "Expected Result", "Actual Result", "Status"]
    tc5_steps_rows = [
        ["1", "Sign in as Corporate Staff", "tomy@wifisense.com", "Landed on SpaceAppShell corporate console", "Passed (test_corp_login)", "Pass"],
        ["2", "Inspect workplace KPI metrics", "Context: AJCE Campus", "Peak utilization rate and underutilized spaces rendered", "Passed (test_util_kpis)", "Pass"],
        ["3", "Verify meeting room list", "Conf Room A, Lab 1", "Real-time occupancy badges (Occupied / Vacant) displayed", "Passed (test_room_list)", "Pass"],
        ["4", "Click 'Shut Off All Vacant Rooms'", "Action: Energy desk", "HVAC standby commands dispatched; toast confirmed", "Passed (test_shut_off)", "Pass"]
    ]
    add_styled_table(doc, tc5_steps_headers, tc5_steps_rows, [0.5, 1.5, 1.4, 1.5, 1.0, 0.5], "Test Case 5 Steps: Verification Breakdown")

    # =========================================================================
    # CHAPTER 6: IMPLEMENTATION
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 6, "Implementation")

    add_heading_1(doc, "6.1 INTRODUCTION")
    add_body_p(
        doc,
        f"The implementation phase of {project_short} operationalizes the theoretical algorithms and relational architectures "
        "designed in preceding chapters. The system adopts a modern decoupled cloud-edge topology, separating the IoT edge sensing "
        "transceivers, Python FastAPI ASGI backend, and React 18 single page application. This decoupled architecture allows "
        "individual services to be developed, containerized, and deployed independently without operational downtime."
    )

    add_heading_2(doc, "Deployment Architecture")
    add_body_p(
        doc,
        "Figure 4.8 in Section 4.2.8 illustrates the overall deployment topology. The React frontend is compiled and hosted on "
        "Vercel Global Edge CDN, delivering assets over HTTPS. The Python FastAPI backend runs inside a containerized Linux environment "
        "on Render Cloud, managing business logic, CSI packet parsing, and WebSocket broadcasts. PostgreSQL 17 is hosted on "
        "Supabase Managed Cloud in region ap-south-1 (Mumbai) with connection pooling and automated daily backups."
    )

    add_heading_1(doc, "6.2 IMPLEMENTATION PROCEDURES")
    add_body_p(
        doc,
        "The step-by-step implementation procedure for provisioning and commissioning Wi-Fi Sense comprises the following ten phases:"
    )
    impl_steps = [
        "1. Flashed ESP32-S3 microcontroller nodes with custom C++/ESP-IDF firmware configured for promiscuous 802.11 CSI collection.",
        "2. Deployed the local PySerial gateway ingestion daemon on host hardware to buffer UART frames at 921600 baud.",
        "3. Provisioned the PostgreSQL 17 relational database on Supabase Cloud, creating UUID extensions and 15 normalized tables.",
        "4. Developed the asynchronous Python FastAPI ASGI backend incorporating SQLModel ORM, JWT authentication, and RBAC middleware.",
        "5. Implemented the signal preprocessing pipeline in NumPy, including linear phase unwrapping and Hampel outlier filtering.",
        "6. Engineered the WiFall activity classification heuristic and emergency fall state machine with atomic database transactions.",
        "7. Built the reactive frontend SPA in React 18 using Vite, Tailwind CSS, and HTML5 Canvas spectrogram renderers.",
        "8. Configured bidirectional WebSocket channels between FastAPI and React clients for sub-second emergency siren alerting.",
        "9. Deployed the backend container to Render Cloud with health check probes and hosted the frontend SPA on Vercel Global Edge.",
        "10. Conducted end-to-end smoke testing, automated Pytest regression suites, and browser-driven Selenium verification."
    ]
    for s in impl_steps:
        add_body_p(doc, s)

    add_heading_2(doc, "Pre-Deployment Checklist")
    add_bullet_p(doc, "Firmware Verification: Confirm ESP32-S3 nodes stream valid 64-subcarrier CSI frames over UART without buffer overflows.", "Firmware Check")
    add_bullet_p(doc, "Database Schema Initialisation: Verify all 15 tables, foreign keys, and indexes are cleanly created on Supabase PostgreSQL.", "Database Check")
    add_bullet_p(doc, "Environment Secrets: Ensure JWT secret keys, database connection strings, and encryption salts are securely set.", "Secrets Check")
    add_bullet_p(doc, "CORS & Domain Security: Restrict allowed CORS origins to the production frontend domain (https://wifisense-ecru.vercel.app).", "CORS Check")
    add_bullet_p(doc, "Audio Siren Verification: Test Web Audio API synthesizer playback across major desktop and mobile browsers.", "Audio Check")

    add_heading_2(doc, "Environment Configuration")
    add_body_p(
        doc,
        "Wi-Fi Sense utilizes environment variables to isolate sensitive credentials across development and cloud production environments:"
    )
    add_bullet_p(doc, "DATABASE_URL: PostgreSQL connection string pointing to Supabase transaction pooler (port 6543) with SSL enabled.", "Database URL")
    add_bullet_p(doc, "SECRET_KEY: 256-bit cryptographic secret for signing stateless JWT bearer tokens.", "Secret Key")
    add_bullet_p(doc, "ALGORITHM: Cryptographic signature algorithm (HS256).", "JWT Algorithm")
    add_bullet_p(doc, "ACCESS_TOKEN_EXPIRE_MINUTES: Access token validity duration (15 minutes).", "Token Expiry")
    add_bullet_p(doc, "VITE_API_BASE: Frontend environment variable pointing to the Render backend API (https://wifisense-api.onrender.com).", "Frontend API Base")

    add_heading_2(doc, "Rolling Deployment and Rollback")
    add_body_p(
        doc,
        "Continuous delivery pipelines on GitHub automatically trigger zero-downtime builds upon merging pull requests to the main branch. "
        "Vercel deploys immutable preview releases before promoting to production. If an unexpected runtime regression occurs, "
        "instant one-click rollback on both Vercel and Render restores the previous stable build in under 60 seconds."
    )

    add_heading_2(doc, "6.2.1 User Training")
    add_body_p(
        doc,
        "User training programs were conducted to familiarize caregivers and facility managers with the platform. "
        "Training emphasized rapid recognition of emergency fall sirens, reading the central room feed, one-tap acknowledgment, "
        "and configuring data sharing policies. Interactive demonstrations and digital user manuals were provided."
    )

    add_heading_2(doc, "6.2.2 Training on the Application Software")
    train_headers = ["User Role", "Core Training Topics", "Methodology", "Duration"]
    train_rows = [
        ["Caregivers / Nurses", "Central monitoring room feed, fall alert acknowledgment, siren muting, resident profile review", "Interactive duty desk simulation", "1 hour"],
        ["Facility Managers", "Staff account provisioning, privacy sharing policy toggles, sensor node health, audit logs", "Guided administrative workshop", "2 hours"],
        ["Corporate Staff", "Meeting room occupancy grids, utilization heatmaps, automated HVAC shutdown controls", "Self-paced video walkthrough", "30 minutes"],
        ["System Maintainers", "ESP32-S3 firmware flashing, PySerial gateway daemon setup, PostgreSQL backups, Render monitoring", "Hands-on technical lab", "Half-day"]
    ]
    add_styled_table(doc, train_headers, train_rows, [1.6, 2.4, 1.6, 0.8], "Table 6.1: Role-Based User Training Curriculum")

    add_heading_2(doc, "6.2.3 System Maintenance")
    add_body_p(
        doc,
        "System maintenance ensures that Wi-Fi Sense remains dependable, secure, and accurate following institutional deployment:"
    )
    add_bullet_p(doc, "Corrective Maintenance: Immediate diagnosis and patching of reported software defects or signal calibration anomalies.", "Corrective")
    add_bullet_p(doc, "Adaptive Maintenance: Updating Python dependencies, React packages, and browser APIs to maintain compatibility.", "Adaptive")
    add_bullet_p(doc, "Perfective Maintenance: Enhancing ML classification accuracy and adding custom alert sounds based on caregiver feedback.", "Perfective")
    add_bullet_p(doc, "Preventive Maintenance: Routine database index re-indexing, vacuuming, and cleaning stale high-frequency telemetry logs.", "Preventive")

    add_heading_3(doc, "Maintenance Schedule")
    maint_headers = ["Maintenance Activity", "Frequency", "Purpose"]
    maint_rows = [
        ["Review emergency alert logs & sirens", "Daily", "Verify all fall alarms were triaged and resolved by staff"],
        ["Check ESP32 sensor node heartbeats", "Daily", "Identify disconnected or degraded transceivers promptly"],
        ["Review Supabase database performance", "Weekly", "Audit query latency, connection pool usage, and disk volume"],
        ["Apply security patches & package updates", "Monthly", "Keep Python virtual environment and npm packages secure"],
        ["Recalibrate empty-room CSI baselines", "Quarterly / On-Demand", "Adjust baseline profiles after room furniture rearrangements"],
        ["Test database backup restoration", "Quarterly", "Verify disaster recovery procedures against standby database"]
    ]
    add_styled_table(doc, maint_headers, maint_rows, [2.2, 1.8, 2.4], "Table 6.2: Scheduled Routine Maintenance Activities")

    add_heading_3(doc, "Backup and Disaster Recovery")
    add_bullet_p(doc, "PostgreSQL Backups: Supabase Cloud executes automated daily database snapshots with Point-in-Time Recovery (PITR) up to 7 days.", "Database Backups")
    add_bullet_p(doc, "Source Code & Configs: Complete codebase, database schemas, and migration scripts are version-controlled in Git and backed up on GitHub.", "Code Backups")
    add_bullet_p(doc, "Edge Failover: If cloud connectivity drops, host gateway PCs continue logging fall incidents locally and sounding hardware buzzer alarms.", "Edge Failover")

    add_heading_2(doc, "6.2.4 Hosting")
    add_body_p(
        doc,
        "Wi-Fi Sense is deployed in a modern, production-grade cloud topology providing high availability and global accessibility. "
        "The web application is accessible via its public production domain:"
    )
    add_bullet_p(doc, "Hosted Web Frontend: https://wifisense-ecru.vercel.app", "Frontend URL")
    add_bullet_p(doc, "Hosted Cloud Backend API: https://wifisense-api.onrender.com", "Backend URL")
    add_bullet_p(doc, "Interactive Swagger Documentation: https://wifisense-api.onrender.com/docs", "API Docs")

    qr_path = os.path.join(diagrams_dir, "qr_hosted_link.png")
    if os.path.exists(qr_path):
        add_figure_image(
            doc,
            qr_path,
            "Figure 6.1: QR code for the hosted production website (https://wifisense-ecru.vercel.app)",
            width_inches=2.2
        )

    # =========================================================================
    # CHAPTER 7: CONCLUSION AND FUTURE SCOPE
    # =========================================================================
    doc.add_page_break()
    add_chapter_heading(doc, 7, "Conclusion and Future Scope")

    add_heading_1(doc, "7.1 CONCLUSION")
    add_body_p(
        doc,
        f"{project_short} successfully demonstrates the feasibility, clinical efficacy, and commercial practicality of "
        "contactless indoor human monitoring and emergency fall detection using commercial Wi-Fi Channel State Information. "
        "By transforming ambient 2.4 GHz radio waves into fine-grained sensory signatures, the platform resolves the critical "
        "privacy and compliance trilemma that has hindered legacy camera and wearable systems for decades."
    )
    add_body_p(
        doc,
        "The project delivers a fully integrated, production-grade software and hardware architecture. Dual-core ESP32-S3 transceivers "
        "capture 64 OFDM subcarrier channel state vectors in promiscuous mode. An asynchronous Python FastAPI backend sanitizes phase noise, "
        "subtracts dynamic empty-room clutter, and classifies human movement in real time. PostgreSQL manages multi-tenant clinical "
        "and corporate data with strict 3NF normalization, while React 18 single page applications provide glanceable room grids, "
        "subcarrier spectrogram heatmaps, and sub-second emergency siren escalation. The platform establishes an unobtrusive, "
        "dignified safety net for vulnerable elderly residents while optimizing facility energy expenditures."
    )

    add_heading_2(doc, "Implementation Status")
    add_body_p(
        doc,
        "The table below separates capabilities supported with verifiable implementation and test evidence from planned extensions:"
    )
    status_headers = ["Capability / Feature", "Status", "Implementation Evidence"]
    status_rows = [
        ["User Authentication & RBAC", "Tested & Verified", "auth.py, UserLogin schema; Pytest & Selenium passed; test_case_1_login.png"],
        ["Dual-Context Routing (Care vs Space)", "Tested & Verified", "App.jsx, navConfig.js; context-pinned dashboard shells"],
        ["ESP32-S3 CSI Packet Sniffer", "Built & Tested", "Firmware in C++/ESP-IDF; 90 pkts/sec promiscuous capture verified"],
        ["PySerial Host Gateway Daemon", "Built & Tested", "csi_serial_bridge.py; UART framing at 921600 baud without buffer drops"],
        ["Linear Phase Unwrapping & Hampel Filter", "Built & Tested", "csi_preprocessor.py; linear regression detrending verified"],
        ["Dynamic Baseline Subtraction", "Built & Tested", "analytics.py; static reflection covariance subtracted cleanly"],
        ["WiFall Activity Classifier", "Tested & Verified", "sensing.py; classifies Empty, Presence, Walking, Sitting, Fall_Detected"],
        ["Emergency Siren & WebSocket Dispatch", "Tested & Verified", "alerts.py, Web Audio API; test_case_2_fall_alert.png passed"],
        ["Central Monitoring Room Feed", "Tested & Verified", "CentralMonitoringView.jsx; glanceable status tiles and active alert banners"],
        ["Real-Time Subcarrier Spectrogram", "Built & Tested", "SubcarrierWaveformStream.jsx; HTML5 Canvas 2D at 90 fps"],
        ["Family Data Sharing Policies", "Tested & Verified", "SharingPolicyManager.jsx, test_case_3_sharing_policy.png passed"],
        ["Family Guardian Portal & Care Plan", "Tested & Verified", "FamilyPortalShell.jsx, test_case_4_family_portal.png passed"],
        ["Corporate Space & Energy Intelligence", "Tested & Verified", "CorporateView.jsx, test_case_5_corporate_space.png passed"],
        ["Hardware Device Service Desk", "Shown in Screenshot", "DevicesView.jsx, test_case_6_device_service_desk.png"],
        ["Resident Accounts Directory", "Shown in Screenshot", "ResidentsView.jsx, test_case_7_residents_directory.png"],
        ["System Administration Console", "Shown in Screenshot", "SystemAdminShell.jsx, test_case_8_system_admin_console.png"],
        ["Multi-Antenna MIMO Localization", "Planned (Part 2)", "Phase Difference of Arrival (PDoA) triangulation deferred to Phase 2"],
        ["Contactless Vital Sign Extraction", "Planned (Part 2)", "Micro-Doppler respiration rate extraction described as future research"]
    ]
    add_styled_table(
        doc,
        status_headers,
        status_rows,
        [2.2, 1.4, 2.8],
        "Table 7.1: Implementation Status and Verification Evidence of Wi-Fi Sense Capabilities"
    )

    add_heading_1(doc, "7.2 FUTURE SCOPE")
    add_body_p(
        doc,
        f"{project_short} has been architected with a modular, extensible foundation that facilitates advanced research "
        "and feature enhancements in subsequent project iterations. Key planned directions include:"
    )
    add_bullet_p(doc, "Multi-Antenna MIMO Beamforming & 2D Spatial Localization: Integrating multi-antenna transceiver arrays to calculate Phase Difference of Arrival (PDoA) and triangulate precise (X, Y) resident room coordinates without tags.", "Spatial Localization")
    add_bullet_p(doc, "Contactless Vital Sign Extraction: Implementing micro-Doppler subcarrier phase filtering to extract breathing rates (0.2–0.5 Hz) and heart rates (1.0–1.8 Hz) during stationary sleep states.", "Vital Signs")
    add_bullet_p(doc, "Federated Machine Learning Across Care Homes: Training neural activity classifiers collaboratively across multiple assisted living centers without transmitting raw RF signatures, preserving cross-facility privacy.", "Federated Learning")
    add_bullet_p(doc, "Wearable-Free Sleep Quality Profiling: Continuous overnight monitoring of bed restless movements, sleep stage transitions, and nighttime wandering detection.", "Sleep Profiling")
    add_bullet_p(doc, "Edge TPU & Microcontroller Neural Acceleration: Deploying quantized TensorFlow Lite models directly onto ESP32-S3 or Edge TPU chips for on-device inference.", "Edge TPU")
    add_bullet_p(doc, "Building Management System (BMS) BACnet Integration: Direct hardware integration with commercial HVAC chillers and lighting controllers via standard BACnet/IP protocols.", "BMS BACnet")
