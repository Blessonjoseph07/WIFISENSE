"""
Master Report Builder — Database Schemas & Table Design
MCA Academic Report Toolkit — Amal Jyothi College of Engineering Autonomous
Department of Computer Applications | Course: 24MCAR295
"""

try:
    from .styles import (
        add_heading_1, add_heading_2, add_heading_3, add_body_p, add_bullet_p, add_styled_table
    )
except ImportError:
    from styles import (
        add_heading_1, add_heading_2, add_heading_3, add_body_p, add_bullet_p, add_styled_table
    )

def add_all_database_schemas(doc, cfg=None):
    """
    Renders the complete 15-table relational schema for Wi-Fi Sense strictly matching
    the Table Design specification, followed by Primary Key Summary, Foreign Key Summary,
    Table Relationships, Security, and Module Flow.
    """
    add_heading_1(doc, "4.5 TABLE DESIGN")
    add_body_p(
        doc,
        "The database is PostgreSQL hosted on Supabase Cloud. The tables below are listed as designed "
        "and implemented in the Wi-Fi Sense relational schema, fully normalized to 3NF:"
    )

    tbl_headers = ["No.", "Field name", "Datatype (Size)", "Key Constraints", "Description of the field"]
    widths = [0.4, 1.4, 1.3, 1.3, 2.2]

    # 1. ORGANIZATIONS
    add_heading_2(doc, "1. ORGANIZATIONS")
    add_body_p(doc, "Primary key: organization_id\nForeign key: Nil")
    org_rows = [
        ["1", "organization_id", "UUID", "PK", "Unique organization identifier"],
        ["2", "name", "VARCHAR(150)", "UNIQUE, NOT NULL", "Organization name"],
        ["3", "type", "VARCHAR(20)", "NOT NULL", "Elder Care or Corporate"],
        ["4", "created_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Creation date"],
        ["5", "updated_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Last updated date"]
    ]
    add_styled_table(doc, tbl_headers, org_rows, widths, "Table 4.2: ORGANIZATIONS Schema")

    # 2. BUILDINGS
    add_heading_2(doc, "2. BUILDINGS")
    add_body_p(doc, "Primary key: building_id\nForeign key: organization_id references ORGANIZATIONS")
    bld_rows = [
        ["1", "building_id", "UUID", "PK", "Unique building identifier"],
        ["2", "organization_id", "UUID", "FK", "References ORGANIZATIONS"],
        ["3", "name", "VARCHAR(100)", "NOT NULL", "Building name"],
        ["4", "address", "TEXT", "NULL", "Building address"],
        ["5", "created_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Creation date"]
    ]
    add_styled_table(doc, tbl_headers, bld_rows, widths, "Table 4.3: BUILDINGS Schema")

    # 3. FLOORS
    add_heading_2(doc, "3. FLOORS")
    add_body_p(doc, "Primary key: floor_id\nForeign key: building_id references BUILDINGS")
    flr_rows = [
        ["1", "floor_id", "UUID", "PK", "Unique floor identifier"],
        ["2", "building_id", "UUID", "FK", "References BUILDINGS"],
        ["3", "floor_number", "INTEGER", "NOT NULL", "Floor number"],
        ["4", "floor_plan_url", "VARCHAR(255)", "NULL", "Optional floor plan reference"]
    ]
    add_styled_table(doc, tbl_headers, flr_rows, widths, "Table 4.4: FLOORS Schema")

    # 4. ROOMS
    add_heading_2(doc, "4. ROOMS")
    add_body_p(doc, "Primary key: room_id\nForeign key: floor_id references FLOORS")
    room_rows = [
        ["1", "room_id", "UUID", "PK", "Unique room identifier"],
        ["2", "floor_id", "UUID", "FK", "References FLOORS"],
        ["3", "name", "VARCHAR(50)", "NOT NULL", "Room name"],
        ["4", "room_type", "VARCHAR(50)", "NULL", "Type of room"],
        ["5", "capacity", "INTEGER", "NULL", "Maximum room capacity"],
        ["6", "dimensions_metadata", "JSONB", "NULL", "Room dimension/layout information"]
    ]
    add_styled_table(doc, tbl_headers, room_rows, widths, "Table 4.5: ROOMS Schema")

    # 5. USERS
    add_heading_2(doc, "5. USERS")
    add_body_p(doc, "Primary key: user_id\nForeign key: Nil")
    usr_rows = [
        ["1", "user_id", "UUID", "PK", "Unique user identifier"],
        ["2", "email", "VARCHAR(150)", "UNIQUE, NOT NULL", "User email"],
        ["3", "password_hash", "VARCHAR(255)", "NOT NULL", "Securely hashed password"],
        ["4", "first_name", "VARCHAR(50)", "NOT NULL", "First name"],
        ["5", "last_name", "VARCHAR(50)", "NULL", "Last name"],
        ["6", "is_active", "BOOLEAN", "DEFAULT TRUE", "Account status"],
        ["7", "created_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Registration date"]
    ]
    add_styled_table(doc, tbl_headers, usr_rows, widths, "Table 4.6: USERS Schema")

    # 6. ROLES
    add_heading_2(doc, "6. ROLES")
    add_body_p(doc, "Primary key: role_id\nForeign key: Nil")
    role_rows = [
        ["1", "role_id", "INTEGER", "PK", "Unique role identifier"],
        ["2", "name", "VARCHAR(80)", "UNIQUE, NOT NULL", "System role name"]
    ]
    add_styled_table(doc, tbl_headers, role_rows, widths, "Table 4.7: ROLES Schema")

    # 7. USER_ROLES
    add_heading_2(doc, "7. USER_ROLES")
    add_body_p(doc, "Primary key: user_role_id\nForeign keys: user_id references USERS; role_id references ROLES; organization_id references ORGANIZATIONS; building_id references BUILDINGS; room_id references ROOMS")
    ur_rows = [
        ["1", "user_role_id", "UUID", "PK", "Unique mapping identifier"],
        ["2", "user_id", "UUID", "FK", "References USERS"],
        ["3", "role_id", "INTEGER", "FK", "References ROLES"],
        ["4", "organization_id", "UUID", "FK, NULL", "Organization-level access"],
        ["5", "building_id", "UUID", "FK, NULL", "Building-level access"],
        ["6", "room_id", "UUID", "FK, NULL", "Room-level access"]
    ]
    add_styled_table(doc, tbl_headers, ur_rows, widths, "Table 4.8: USER_ROLES Schema")

    # 8. DEVICES
    add_heading_2(doc, "8. DEVICES")
    add_body_p(doc, "Primary key: device_id\nForeign key: room_id references ROOMS")
    dev_rows = [
        ["1", "device_id", "UUID", "PK", "Unique sensing-device identifier"],
        ["2", "room_id", "UUID", "FK, NULL", "References ROOMS"],
        ["3", "mac_address", "VARCHAR(17)", "UNIQUE, NOT NULL", "ESP32-S3 MAC address"],
        ["4", "device_status", "VARCHAR(20)", "NOT NULL", "Online, Offline or Maintenance"],
        ["5", "firmware_version", "VARCHAR(30)", "NULL", "Firmware version"],
        ["6", "last_seen_at", "TIMESTAMPTZ", "NULL", "Last communication time"]
    ]
    add_styled_table(doc, tbl_headers, dev_rows, widths, "Table 4.9: DEVICES Schema")

    # 9. ACTIVITY_TYPES
    add_heading_2(doc, "9. ACTIVITY_TYPES")
    add_body_p(doc, "Primary key: activity_type_id\nForeign key: Nil")
    act_rows = [
        ["1", "activity_type_id", "INTEGER", "PK", "Unique activity identifier"],
        ["2", "name", "VARCHAR(50)", "UNIQUE, NOT NULL", "Empty, Presence, Walking, Sitting, Fall_Detected"],
        ["3", "category", "VARCHAR(20)", "NOT NULL", "STATUS, ACTIVITY or CRITICAL"]
    ]
    add_styled_table(doc, tbl_headers, act_rows, widths, "Table 4.10: ACTIVITY_TYPES Schema")

    # 10. SENSING_TEMPLATES
    add_heading_2(doc, "10. SENSING_TEMPLATES")
    add_body_p(doc, "Primary key: template_id\nForeign keys: organization_id references ORGANIZATIONS; activity_type_id references ACTIVITY_TYPES")
    st_rows = [
        ["1", "template_id", "UUID", "PK", "Unique template identifier"],
        ["2", "organization_id", "UUID", "FK, NULL", "References ORGANIZATIONS"],
        ["3", "activity_type_id", "INTEGER", "FK", "References ACTIVITY_TYPES"],
        ["4", "template_name", "VARCHAR(100)", "NOT NULL", "CSI template name"],
        ["5", "csi_amplitude_baseline", "DOUBLE PRECISION[]", "NULL", "Reference CSI amplitude profile"],
        ["6", "csi_phase_baseline", "DOUBLE PRECISION[]", "NULL", "Reference CSI phase profile"],
        ["7", "environment_metadata", "JSONB", "NULL", "Room/environment information"],
        ["8", "created_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Creation date"],
        ["9", "updated_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Last updated date"]
    ]
    add_styled_table(doc, tbl_headers, st_rows, widths, "Table 4.11: SENSING_TEMPLATES Schema")

    # 11. SENSING_EVENTS
    add_heading_2(doc, "11. SENSING_EVENTS")
    add_body_p(doc, "Primary key: event_id\nForeign keys: device_id references DEVICES; room_id references ROOMS; inferred_activity_id references ACTIVITY_TYPES")
    se_rows = [
        ["1", "event_id", "BIGSERIAL", "PK", "Unique sensing event"],
        ["2", "device_id", "UUID", "FK", "References DEVICES"],
        ["3", "room_id", "UUID", "FK", "References ROOMS"],
        ["4", "timestamp", "TIMESTAMPTZ", "NOT NULL", "Sensing timestamp"],
        ["5", "rssi", "INTEGER", "NULL", "Received Signal Strength"],
        ["6", "subcarrier_count", "INTEGER", "NULL", "Number of CSI subcarriers"],
        ["7", "raw_csi_payload_path", "VARCHAR(512)", "NULL", "Storage path for raw CSI"],
        ["8", "extracted_features", "JSONB", "NULL", "Preprocessed CSI features"],
        ["9", "inferred_activity_id", "INTEGER", "FK, NULL", "References ACTIVITY_TYPES"],
        ["10", "model_confidence", "NUMERIC(5,4)", "NULL", "ML prediction confidence"]
    ]
    add_styled_table(doc, tbl_headers, se_rows, widths, "Table 4.12: SENSING_EVENTS Schema")

    # 12. ALERT_TEMPLATES
    add_heading_2(doc, "12. ALERT_TEMPLATES")
    add_body_p(doc, "Primary key: alert_template_id\nForeign keys: organization_id references ORGANIZATIONS; event_type_id references ACTIVITY_TYPES")
    at_rows = [
        ["1", "alert_template_id", "UUID", "PK", "Unique alert template"],
        ["2", "organization_id", "UUID", "FK, NULL", "References ORGANIZATIONS"],
        ["3", "event_type_id", "INTEGER", "FK", "References ACTIVITY_TYPES"],
        ["4", "alert_severity", "VARCHAR(20)", "NOT NULL", "LOW, MEDIUM, HIGH or CRITICAL"],
        ["5", "message_template", "TEXT", "NOT NULL", "Alert message format"],
        ["6", "cooldown_period_seconds", "INTEGER", "DEFAULT 0", "Duplicate-alert prevention period"]
    ]
    add_styled_table(doc, tbl_headers, at_rows, widths, "Table 4.13: ALERT_TEMPLATES Schema")

    # 13. ALERT_CONFIGURATIONS
    add_heading_2(doc, "13. ALERT_CONFIGURATIONS")
    add_body_p(doc, "Primary key: alert_configuration_id\nForeign keys: room_id references ROOMS; alert_template_id references ALERT_TEMPLATES")
    ac_rows = [
        ["1", "alert_configuration_id", "UUID", "PK", "Unique configuration"],
        ["2", "room_id", "UUID", "FK", "References ROOMS"],
        ["3", "alert_template_id", "UUID", "FK", "References ALERT_TEMPLATES"],
        ["4", "is_enabled", "BOOLEAN", "DEFAULT TRUE", "Configuration status"]
    ]
    add_styled_table(doc, tbl_headers, ac_rows, widths, "Table 4.14: ALERT_CONFIGURATIONS Schema")

    # 14. ALERTS
    add_heading_2(doc, "14. ALERTS")
    add_body_p(doc, "Primary key: alert_id\nForeign keys: alert_configuration_id references ALERT_CONFIGURATIONS; room_id references ROOMS")
    alt_rows = [
        ["1", "alert_id", "UUID", "PK", "Unique alert identifier"],
        ["2", "alert_configuration_id", "UUID", "FK, NULL", "References ALERT_CONFIGURATIONS"],
        ["3", "room_id", "UUID", "FK", "References ROOMS"],
        ["4", "event_type", "VARCHAR(50)", "NOT NULL", "Event that triggered alert"],
        ["5", "severity", "VARCHAR(20)", "NOT NULL", "Alert severity"],
        ["6", "message", "TEXT", "NOT NULL", "Generated alert message"],
        ["7", "status", "VARCHAR(20)", "NOT NULL", "DETECTION, CREATED, NOTIFIED, ACKNOWLEDGED or RESOLVED"],
        ["8", "created_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Alert creation time"]
    ]
    add_styled_table(doc, tbl_headers, alt_rows, widths, "Table 4.15: ALERTS Schema")

    # 15. ALERT_ACKNOWLEDGEMENTS
    add_heading_2(doc, "15. ALERT_ACKNOWLEDGEMENTS")
    add_body_p(doc, "Primary key: acknowledgement_id\nForeign keys: alert_id references ALERTS; user_id references USERS")
    ack_rows = [
        ["1", "acknowledgement_id", "UUID", "PK", "Unique acknowledgement identifier"],
        ["2", "alert_id", "UUID", "FK", "References ALERTS"],
        ["3", "user_id", "UUID", "FK, NULL", "User who acknowledged/resolved"],
        ["4", "acknowledged_at", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP", "Acknowledgement time"],
        ["5", "resolved_at", "TIMESTAMPTZ", "NULL", "Resolution time"],
        ["6", "resolution_notes", "TEXT", "NULL", "Resolution details"]
    ]
    add_styled_table(doc, tbl_headers, ack_rows, widths, "Table 4.16: ALERT_ACKNOWLEDGEMENTS Schema")

    # PRIMARY KEY SUMMARY
    doc.add_page_break()
    add_heading_2(doc, "PRIMARY KEY SUMMARY")
    pk_headers = ["Table", "Primary Key"]
    pk_rows = [
        ["ORGANIZATIONS", "organization_id"],
        ["BUILDINGS", "building_id"],
        ["FLOORS", "floor_id"],
        ["ROOMS", "room_id"],
        ["USERS", "user_id"],
        ["ROLES", "role_id"],
        ["USER_ROLES", "user_role_id"],
        ["DEVICES", "device_id"],
        ["ACTIVITY_TYPES", "activity_type_id"],
        ["SENSING_TEMPLATES", "template_id"],
        ["SENSING_EVENTS", "event_id"],
        ["ALERT_TEMPLATES", "alert_template_id"],
        ["ALERT_CONFIGURATIONS", "alert_configuration_id"],
        ["ALERTS", "alert_id"],
        ["ALERT_ACKNOWLEDGEMENTS", "acknowledgement_id"]
    ]
    add_styled_table(doc, pk_headers, pk_rows, [3.2, 3.2], "Table 4.17: Primary Key Summary Across All Relational Entities")

    # FOREIGN KEY SUMMARY
    add_heading_2(doc, "FOREIGN KEY SUMMARY")
    fk_headers = ["Table", "Foreign Key", "References"]
    fk_rows = [
        ["BUILDINGS", "organization_id", "ORGANIZATIONS"],
        ["FLOORS", "building_id", "BUILDINGS"],
        ["ROOMS", "floor_id", "FLOORS"],
        ["USER_ROLES", "user_id", "USERS"],
        ["USER_ROLES", "role_id", "ROLES"],
        ["USER_ROLES", "organization_id", "ORGANIZATIONS"],
        ["USER_ROLES", "building_id", "BUILDINGS"],
        ["USER_ROLES", "room_id", "ROOMS"],
        ["DEVICES", "room_id", "ROOMS"],
        ["SENSING_TEMPLATES", "organization_id", "ORGANIZATIONS"],
        ["SENSING_TEMPLATES", "activity_type_id", "ACTIVITY_TYPES"],
        ["SENSING_EVENTS", "device_id", "DEVICES"],
        ["SENSING_EVENTS", "room_id", "ROOMS"],
        ["SENSING_EVENTS", "inferred_activity_id", "ACTIVITY_TYPES"],
        ["ALERT_TEMPLATES", "organization_id", "ORGANIZATIONS"],
        ["ALERT_TEMPLATES", "event_type_id", "ACTIVITY_TYPES"],
        ["ALERT_CONFIGURATIONS", "room_id", "ROOMS"],
        ["ALERT_CONFIGURATIONS", "alert_template_id", "ALERT_TEMPLATES"],
        ["ALERTS", "alert_configuration_id", "ALERT_CONFIGURATIONS"],
        ["ALERTS", "room_id", "ROOMS"],
        ["ALERT_ACKNOWLEDGEMENTS", "alert_id", "ALERTS"],
        ["ALERT_ACKNOWLEDGEMENTS", "user_id", "USERS"]
    ]
    add_styled_table(doc, fk_headers, fk_rows, [2.2, 2.2, 2.2], "Table 4.18: Foreign Key Summary and Referential Target Mappings")

    # TABLE RELATIONSHIPS
    add_heading_2(doc, "TABLE RELATIONSHIPS")
    rel_headers = ["Parent Table", "Child Table", "Relationship"]
    rel_rows = [
        ["ORGANIZATIONS", "BUILDINGS", "One-to-Many"],
        ["BUILDINGS", "FLOORS", "One-to-Many"],
        ["FLOORS", "ROOMS", "One-to-Many"],
        ["ROOMS", "DEVICES", "One-to-Many"],
        ["ROOMS", "SENSING_EVENTS", "One-to-Many"],
        ["DEVICES", "SENSING_EVENTS", "One-to-Many"],
        ["ACTIVITY_TYPES", "SENSING_EVENTS", "One-to-Many"],
        ["ORGANIZATIONS", "SENSING_TEMPLATES", "One-to-Many"],
        ["ACTIVITY_TYPES", "SENSING_TEMPLATES", "One-to-Many"],
        ["USERS", "USER_ROLES", "One-to-Many"],
        ["ROLES", "USER_ROLES", "One-to-Many"],
        ["ROOMS", "ALERT_CONFIGURATIONS", "One-to-Many"],
        ["ALERT_TEMPLATES", "ALERT_CONFIGURATIONS", "One-to-Many"],
        ["ALERT_CONFIGURATIONS", "ALERTS", "One-to-Many"],
        ["ROOMS", "ALERTS", "One-to-Many"],
        ["ALERTS", "ALERT_ACKNOWLEDGEMENTS", "One-to-Many"],
        ["USERS", "ALERT_ACKNOWLEDGEMENTS", "One-to-Many"]
    ]
    add_styled_table(doc, rel_headers, rel_rows, [2.2, 2.2, 2.2], "Table 4.19: Cardinality and Multiplicity Relationships")

    # DATABASE SECURITY
    add_heading_2(doc, "Database Security")
    add_bullet_p(doc, "User passwords are encrypted using secure salted hashing (Argon2 / BCrypt) rather than plain text.", "Password Hashing")
    add_bullet_p(doc, "Role-Based Access Control (RBAC) restricts database read/write queries according to assigned user scopes.", "RBAC Scoping")
    add_bullet_p(doc, "Organization, building, and room-level scopes restrict clinical monitoring and telemetry access.", "Tenant Isolation")
    add_bullet_p(doc, "Foreign-key constraints with ON DELETE CASCADE and RESTRICT maintain absolute referential integrity.", "Referential Integrity")
    add_bullet_p(doc, "Input validation and parameterized ORM queries eliminate SQL injection vulnerabilities.", "SQL Injection Defense")
    add_bullet_p(doc, "Sensitive raw CSI features and health records are restricted to authenticated clinical personnel.", "Data Privacy")
    add_bullet_p(doc, "Alert acknowledgement and resolution audit logs record timestamps and responder user IDs for accountability.", "Auditability")

    # DATABASE MODULE FLOW
    add_heading_2(doc, "Database Module Flow")
    add_body_p(
        doc,
        "The relational data processing pipeline follows a deterministic operational progression:"
    )
    add_body_p(
        doc,
        "ORGANIZATION  -->  BUILDING  -->  FLOOR  -->  ROOM  -->  DEVICE  -->  SENSING EVENT  -->  "
        "ACTIVITY CLASSIFICATION  -->  ALERT CONFIGURATION  -->  ALERT  -->  ACKNOWLEDGEMENT / RESOLUTION"
    )
