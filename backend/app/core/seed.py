from sqlmodel import Session, select, text
from datetime import datetime, timedelta
import random
from app.models.entities import (
    Role, User, UserRole, Organization, Building, Floor, Room, 
    SensingDevice, Resident, ActivityType, SensingEvent, Alert, AlertAcknowledgement, AccessRequest,
    SharingPolicy, HealthCondition, CaregiverProfile, NodeFaultReport
)
from app.core.security import hash_password

ROLE_MAPPING = {
    "system_admin": 1,
    "organization_admin": 2,
    "facility_manager": 3,
    "caregiver": 4,
    "corporate_staff": 5,
    "emergency_contact": 6
}

ACTIVITY_MAPPING = {
    "Empty": (1, "STATUS"),
    "Presence": (2, "STATUS"),
    "Walking": (3, "ACTIVITY"),
    "Sitting": (4, "ACTIVITY"),
    "Fall_Detected": (5, "CRITICAL"),
    "Resting": (6, "ACTIVITY")
}

def seed_database(session: Session, force: bool = False):
    # Guard against accidental data wipe on server reload/restart
    if not force:
        existing_org = session.exec(select(Organization)).first()
        if existing_org:
            return

    # 1. Clean existing tables

    try:
        session.execute(text("DELETE FROM node_fault_reports"))
    except Exception:
        pass
    session.execute(text("DELETE FROM health_conditions"))
    session.execute(text("DELETE FROM caregiver_profiles"))
    session.execute(text("DELETE FROM sharing_policies"))
    session.execute(text("DELETE FROM access_requests"))
    session.execute(text("DELETE FROM alert_acknowledgements"))
    session.execute(text("DELETE FROM alerts"))
    session.execute(text("DELETE FROM sensing_events"))
    session.execute(text("DELETE FROM residents"))
    session.execute(text("DELETE FROM devices"))
    session.execute(text("DELETE FROM rooms"))
    session.execute(text("DELETE FROM floors"))
    session.execute(text("DELETE FROM buildings"))
    session.execute(text("DELETE FROM user_roles"))
    session.execute(text("DELETE FROM users"))
    session.execute(text("DELETE FROM organizations"))
    session.execute(text("DELETE FROM roles"))
    session.execute(text("DELETE FROM activity_types"))
    session.commit()

    # 2. Seed Roles
    for name, role_id in ROLE_MAPPING.items():
        new_role = Role(id=role_id, name=name)
        session.add(new_role)
    session.commit()

    # 3. Seed Activity Types
    for name, (act_id, category) in ACTIVITY_MAPPING.items():
        new_act = ActivityType(id=act_id, name=name, category=category)
        session.add(new_act)
    session.commit()

    # 4. Seed Organizations (Strict Separation)
    org_ajce = Organization(
        name="Amal Jyothi College of Engineering", 
        type="CORPORATE"
    )
    org_lab = Organization(
        name="St. Peter's Elder Care Home", 
        type="ELDER_CARE"
    )
    session.add_all([org_ajce, org_lab])
    session.commit()
    session.refresh(org_ajce)
    session.refresh(org_lab)

    # 5. Seed Buildings
    # SPACE Buildings
    bld_mca = Building(
        organization_id=org_ajce.id, 
        name="Department of Computer Applications (MCA Block)", 
        address="Amal Jyothi College of Engineering Campus, Kanjirappally, Kerala, India"
    )
    bld_rd = Building(
        organization_id=org_ajce.id, 
        name="R&D Central Annex", 
        address="Main Campus Block C, Tech Park"
    )
    bld_admin = Building(
        organization_id=org_ajce.id, 
        name="Administrative & Corporate Center", 
        address="Executive Quadrangle, Building 4"
    )

    # CARE Buildings
    bld_wing_a = Building(
        organization_id=org_lab.id, 
        name="Care Wing Alpha (North Sector)", 
        address="St. Peter's Elder Care Campus, North Wing"
    )
    bld_wing_b = Building(
        organization_id=org_lab.id, 
        name="Care Wing Beta (South Sector)", 
        address="St. Peter's Elder Care Campus, South Wing"
    )
    bld_med = Building(
        organization_id=org_lab.id, 
        name="St. Jude Medical & Therapy Pavilion", 
        address="St. Peter's Healthcare Facility, East Sector"
    )

    all_buildings = [bld_mca, bld_rd, bld_admin, bld_wing_a, bld_wing_b, bld_med]
    session.add_all(all_buildings)
    session.commit()
    for b in all_buildings:
        session.refresh(b)

    # 6. Seed Floors
    # SPACE Floors
    flr_mca_1 = Floor(building_id=bld_mca.id, floor_number=1)
    flr_mca_2 = Floor(building_id=bld_mca.id, floor_number=2)
    flr_mca_3 = Floor(building_id=bld_mca.id, floor_number=3)
    flr_rd_1 = Floor(building_id=bld_rd.id, floor_number=1)
    flr_rd_2 = Floor(building_id=bld_rd.id, floor_number=2)
    flr_admin_1 = Floor(building_id=bld_admin.id, floor_number=1)

    # CARE Floors
    flr_wing_a_1 = Floor(building_id=bld_wing_a.id, floor_number=1)
    flr_wing_a_2 = Floor(building_id=bld_wing_a.id, floor_number=2)
    flr_wing_b_1 = Floor(building_id=bld_wing_b.id, floor_number=1)
    flr_wing_b_2 = Floor(building_id=bld_wing_b.id, floor_number=2)
    flr_med_1 = Floor(building_id=bld_med.id, floor_number=1)

    all_floors = [
        flr_mca_1, flr_mca_2, flr_mca_3, flr_rd_1, flr_rd_2, flr_admin_1,
        flr_wing_a_1, flr_wing_a_2, flr_wing_b_1, flr_wing_b_2, flr_med_1
    ]
    session.add_all(all_floors)
    session.commit()
    for f in all_floors:
        session.refresh(f)

    # 7. Seed Rooms (Strict Separation & Meaningful Classifications)
    # -------------------------------------------------------------
    # CORPORATE (SPACE) ROOMS
    rm_conf_a = Room(
        floor_id=flr_mca_1.id,
        name="Executive Conference Room A",
        room_type="Conference Room",
        classification="Conference Room",
        capacity=20,
        dimensions_metadata={
            "classification": "Conference Room",
            "expected_state": "Occupied",
            "schedule": [
                {"time_range": "10:00 - 11:30", "title": "Faculty Board Review", "status": "Occupied"},
                {"time_range": "14:00 - 15:30", "title": "Quarterly Operations Sync", "status": "Occupied"},
                {"time_range": "16:00 - 17:00", "title": "Project Demo", "status": "Vacant"}
            ],
            "energy_state": {"ac_status": "ON", "hvac_setpoint_c": 22.0, "lighting_status": "AUTO"}
        }
    )

    rm_meet_b = Room(
        floor_id=flr_mca_2.id,
        name="Board Meeting Room B",
        room_type="Meeting Room",
        classification="Meeting Room",
        capacity=12,
        dimensions_metadata={
            "classification": "Meeting Room",
            "expected_state": "Vacant",
            "schedule": [
                {"time_range": "09:00 - 10:30", "title": "Department Briefing", "status": "Occupied"},
                {"time_range": "11:00 - 17:00", "title": "Open Booking Window", "status": "Vacant"}
            ],
            "energy_state": {
                "ac_status": "ON",
                "vacant_duration_hours": 2.5,
                "efficiency_recommendation": "Room has remained vacant for 2.5 hours while AC is ON. Consider turning off AC to improve energy efficiency."
            }
        }
    )

    rm_comp_lab1 = Room(
        floor_id=flr_mca_1.id,
        name="Computer Lab 1 - Systems Hub",
        room_type="Computer Lab",
        classification="Computer Lab",
        capacity=45,
        dimensions_metadata={
            "classification": "Computer Lab",
            "expected_state": "Vacant",
            "schedule": [
                {"time_range": "09:00 - 12:00", "title": "MCA601 Distributed Systems Lab", "status": "Class"},
                {"time_range": "12:00 - 14:00", "title": "Scheduled Maintenance & Sanitization", "status": "Vacant"},
                {"time_range": "14:00 - 17:00", "title": "MCA602 Cloud Computing Practical", "status": "Class"}
            ],
            "security_policy": {"restricted_hours": "21:00 - 07:00", "after_hours_monitoring": True}
        }
    )

    rm_comp_lab2 = Room(
        floor_id=flr_mca_2.id,
        name="Computer Lab 2 - AI Research",
        room_type="Computer Lab",
        classification="Computer Lab",
        capacity=35,
        dimensions_metadata={
            "classification": "Computer Lab",
            "expected_state": "Occupied",
            "schedule": [
                {"time_range": "10:00 - 16:00", "title": "Deep Learning Studio Practice", "status": "Class"}
            ]
        }
    )

    rm_res_lab2 = Room(
        floor_id=flr_rd_1.id,
        name="Research Lab 2 - Embedded CSI",
        room_type="Research Lab",
        classification="Research Lab",
        capacity=18,
        dimensions_metadata={
            "classification": "Research Lab",
            "expected_state": "Vacant",
            "schedule": [
                {"time_range": "08:30 - 18:00", "title": "Faculty Research & Experiments", "status": "Occupied"},
                {"time_range": "18:00 - 08:30", "title": "Restricted Access Hours", "status": "Vacant"}
            ],
            "security_policy": {"restricted_hours": "22:00 - 06:00", "after_hours_monitoring": True}
        }
    )

    rm_class_101 = Room(
        floor_id=flr_mca_1.id,
        name="Smart Classroom 101",
        room_type="Classroom",
        classification="Classroom",
        capacity=60,
        dimensions_metadata={
            "classification": "Classroom",
            "expected_state": "Occupied",
            "schedule": [
                {"time_range": "09:30 - 11:00", "title": "Software Engineering Lecture", "status": "Class"},
                {"time_range": "11:15 - 12:45", "title": "Computer Networks Lecture", "status": "Class"}
            ]
        }
    )

    rm_class_102 = Room(
        floor_id=flr_mca_2.id,
        name="Smart Classroom 102",
        room_type="Classroom",
        classification="Classroom",
        capacity=60,
        dimensions_metadata={
            "classification": "Classroom",
            "expected_state": "Vacant",
            "schedule": [
                {"time_range": "13:00 - 15:00", "title": "Database Management Lecture", "status": "Class"}
            ],
            "energy_state": {
                "ac_status": "ON",
                "vacant_duration_hours": 1.8,
                "efficiency_recommendation": "Room vacant for 1.8 hours with HVAC running. Auto-standby recommended."
            }
        }
    )

    rm_staff_a = Room(
        floor_id=flr_mca_1.id,
        name="Faculty Staff Room A",
        room_type="Office",
        classification="Office",
        capacity=15,
        dimensions_metadata={"classification": "Office", "expected_state": "Occupied"}
    )

    rm_server_telecom = Room(
        floor_id=flr_mca_1.id,
        name="Department Server & Telecom Room",
        room_type="Server Room",
        classification="Server Room",
        capacity=4,
        dimensions_metadata={
            "classification": "Server Room",
            "expected_state": "Vacant",
            "security_policy": {"restricted_hours": "00:00 - 23:59", "after_hours_monitoring": True}
        }
    )

    rm_seminar_mca = Room(
        floor_id=flr_mca_3.id,
        name="MCA Seminar Hall",
        room_type="Seminar Hall",
        classification="Seminar Hall",
        capacity=150,
        dimensions_metadata={
            "classification": "Seminar Hall",
            "expected_state": "Vacant",
            "schedule": [
                {"time_range": "15:00 - 17:00", "title": "Guest Lecture: Ambient AI in IoT", "status": "Upcoming"}
            ]
        }
    )

    rm_cafeteria = Room(
        floor_id=flr_admin_1.id,
        name="Campus Corporate Cafeteria Hub",
        room_type="Cafeteria",
        classification="Cafeteria",
        capacity=90,
        dimensions_metadata={"classification": "Cafeteria", "expected_state": "Occupied"}
    )

    rm_lounge_rd = Room(
        floor_id=flr_rd_2.id,
        name="Innovation Center Common Lounge",
        room_type="Common Area",
        classification="Common Area",
        capacity=30,
        dimensions_metadata={"classification": "Common Area", "expected_state": "Occupied"}
    )

    space_rooms = [
        rm_conf_a, rm_meet_b, rm_comp_lab1, rm_comp_lab2, rm_res_lab2,
        rm_class_101, rm_class_102, rm_staff_a, rm_server_telecom,
        rm_seminar_mca, rm_cafeteria, rm_lounge_rd
    ]
    session.add_all(space_rooms)

    # -------------------------------------------------------------
    # ELDER CARE (CARE) ROOMS
    rm_101 = Room(
        floor_id=flr_wing_a_1.id,
        name="Resident Room 101",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_102 = Room(
        floor_id=flr_wing_a_1.id,
        name="Resident Room 102",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_103 = Room(
        floor_id=flr_wing_a_1.id,
        name="Resident Room 103",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_104 = Room(
        floor_id=flr_wing_a_1.id,
        name="Resident Room 104",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_201 = Room(
        floor_id=flr_wing_a_2.id,
        name="Resident Room 201",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_202 = Room(
        floor_id=flr_wing_a_2.id,
        name="Resident Room 202",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_203 = Room(
        floor_id=flr_wing_a_2.id,
        name="Resident Room 203",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )
    rm_204 = Room(
        floor_id=flr_wing_a_2.id,
        name="Resident Room 204",
        room_type="Resident Room",
        classification="Resident Bedroom",
        capacity=2,
        dimensions_metadata={"classification": "Resident Bedroom", "resident_capacity": 2}
    )

    rm_bath_1 = Room(
        floor_id=flr_wing_a_1.id,
        name="Wing A Ensuite Bathroom 1",
        room_type="Bathroom",
        classification="Bathroom",
        capacity=1,
        dimensions_metadata={"classification": "Bathroom", "wet_area": True, "high_risk_fall_zone": True}
    )
    rm_bath_2 = Room(
        floor_id=flr_wing_a_2.id,
        name="Wing A Ensuite Bathroom 2",
        room_type="Bathroom",
        classification="Bathroom",
        capacity=1,
        dimensions_metadata={"classification": "Bathroom", "wet_area": True, "high_risk_fall_zone": True}
    )

    rm_physio = Room(
        floor_id=flr_med_1.id,
        name="Central Physiotherapy Clinic",
        room_type="Physiotherapy",
        classification="Physiotherapy",
        capacity=12,
        dimensions_metadata={"classification": "Physiotherapy", "operating_hours": "08:00 - 17:00"}
    )
    rm_recreation = Room(
        floor_id=flr_wing_b_1.id,
        name="Recreation & Activity Lounge",
        room_type="Recreation",
        classification="Recreation",
        capacity=30,
        dimensions_metadata={"classification": "Recreation"}
    )
    rm_dining = Room(
        floor_id=flr_wing_b_2.id,
        name="Community Dining Hall",
        room_type="Dining Area",
        classification="Dining Area",
        capacity=45,
        dimensions_metadata={"classification": "Dining Area"}
    )
    rm_quiet = Room(
        floor_id=flr_wing_b_2.id,
        name="Quiet Reading Room & Hall",
        room_type="Seminar/Common Hall",
        classification="Seminar/Common Hall",
        capacity=15,
        dimensions_metadata={"classification": "Seminar/Common Hall"}
    )
    rm_nursing = Room(
        floor_id=flr_wing_a_1.id,
        name="Central Nursing Station & Duty Desk",
        room_type="Nursing Area",
        classification="Nursing Area",
        capacity=8,
        dimensions_metadata={"classification": "Nursing Area", "24_7_staffed": True}
    )
    rm_doctor_triage = Room(
        floor_id=flr_med_1.id,
        name="Doctor Consultation & Triage Room",
        room_type="Staff Area",
        classification="Staff Area",
        capacity=5,
        dimensions_metadata={"classification": "Staff Area"}
    )
    rm_ward_1 = Room(
        floor_id=flr_wing_b_1.id,
        name="High-Care Observation Ward 1",
        room_type="Nursing Area",
        classification="Nursing Area",
        capacity=8,
        dimensions_metadata={"classification": "Nursing Area"}
    )

    care_rooms = [
        rm_101, rm_102, rm_103, rm_104, rm_201, rm_202, rm_203, rm_204,
        rm_bath_1, rm_bath_2, rm_physio, rm_recreation, rm_dining,
        rm_quiet, rm_nursing, rm_doctor_triage, rm_ward_1
    ]
    session.add_all(care_rooms)
    session.commit()

    for r in space_rooms + care_rooms:
        session.refresh(r)

    # 8. Seed Residents (Monitored Persons) - Strictly Elder Care
    res_mary = Resident(
        room_id=rm_204.id, 
        first_name="Mary", 
        last_name="Joseph", 
        date_of_birth=datetime(1941, 9, 14)
    )
    res_devassy = Resident(
        room_id=rm_101.id, 
        first_name="Devassy", 
        last_name="Varghese", 
        date_of_birth=datetime(1942, 3, 10)
    )
    res_annamma = Resident(
        room_id=rm_102.id, 
        first_name="Annamma", 
        last_name="Joseph", 
        date_of_birth=datetime(1938, 7, 22)
    )
    res_mathew = Resident(
        room_id=rm_103.id, 
        first_name="K. C.", 
        last_name="Mathew", 
        date_of_birth=datetime(1945, 12, 5)
    )
    res_rosamma = Resident(
        room_id=rm_104.id, 
        first_name="Rosamma", 
        last_name="Thomas", 
        date_of_birth=datetime(1940, 9, 18)
    )
    res_george = Resident(
        room_id=rm_201.id, 
        first_name="George", 
        last_name="Philip", 
        date_of_birth=datetime(1941, 4, 14)
    )
    res_mariamma = Resident(
        room_id=rm_202.id, 
        first_name="Mariamma", 
        last_name="Kuruvilla", 
        date_of_birth=datetime(1939, 11, 30)
    )
    res_thomas = Resident(
        room_id=rm_203.id, 
        first_name="Thomas", 
        last_name="Varkey", 
        date_of_birth=datetime(1944, 8, 19)
    )
    res_saramma = Resident(
        room_id=rm_101.id, 
        first_name="Saramma", 
        last_name="Chacko", 
        date_of_birth=datetime(1937, 2, 8)
    )
    res_abraham = Resident(
        room_id=rm_102.id, 
        first_name="Abraham", 
        last_name="Joseph", 
        date_of_birth=datetime(1946, 6, 25)
    )
    res_thresia = Resident(
        room_id=rm_204.id, 
        first_name="Thresia", 
        last_name="Augustine", 
        date_of_birth=datetime(1943, 10, 11)
    )
    res_joseph = Resident(
        room_id=rm_201.id, 
        first_name="Joseph", 
        last_name="Anthony", 
        date_of_birth=datetime(1940, 1, 29)
    )
    res_varghese = Resident(
        room_id=rm_203.id, 
        first_name="Varghese", 
        last_name="Mathai", 
        date_of_birth=datetime(1945, 9, 3)
    )
    res_aleyamma = Resident(
        room_id=rm_202.id, 
        first_name="Aleyamma", 
        last_name="Paul", 
        date_of_birth=datetime(1942, 12, 21)
    )

    all_residents = [
        res_mary, res_devassy, res_annamma, res_mathew, res_rosamma,
        res_george, res_mariamma, res_thomas, res_saramma, res_abraham,
        res_thresia, res_joseph, res_varghese, res_aleyamma
    ]
    session.add_all(all_residents)
    session.commit()
    for r in all_residents:
        session.refresh(r)

    # 9. Seed Doctors & Health Records
    session.add_all([
        # Mary Joseph
        HealthCondition(
            resident_id=res_mary.id,
            condition_name="Mild Cognitive Impairment & Osteoporosis",
            notes="Doctor: Dr. Anjali Thomas (Geriatric Medicine). Requires morning mobility exercises, prescribed calcium & vitamin D3.",
            diagnosed_date=datetime(2021, 5, 14),
            is_active=True
        ),
        # Devassy Varghese
        HealthCondition(
            resident_id=res_devassy.id,
            condition_name="Hypertension & Osteoarthritis",
            notes="Doctor: Dr. Anjali Thomas (Geriatric Medicine). Monitor prolonged sitting; assist during joint stiffness episodes.",
            diagnosed_date=datetime(2015, 6, 1),
            is_active=True
        ),
        # Annamma Joseph
        HealthCondition(
            resident_id=res_annamma.id,
            condition_name="Type 2 Diabetes & Glaucoma",
            notes="Doctor: Dr. Philip Mathew (Endocrinology). Daily insulin regimen, eye drops administered at 08:00 and 20:00.",
            diagnosed_date=datetime(2010, 11, 5),
            is_active=True
        ),
        # K. C. Mathew
        HealthCondition(
            resident_id=res_mathew.id,
            condition_name="Parkinson's Early Stage",
            notes="Doctor: Dr. George Varghese (Neurology). Gait instability warning; high fall risk in wet areas or unassisted transfers.",
            diagnosed_date=datetime(2021, 3, 12),
            is_active=True
        ),
        # Rosamma Thomas
        HealthCondition(
            resident_id=res_rosamma.id,
            condition_name="Cardiac Arrhythmia",
            notes="Doctor: Dr. Elizabeth Kurian (Cardiology / Facility Manager). Prescribed beta-blockers, monitor for nighttime dizziness.",
            diagnosed_date=datetime(2017, 8, 20),
            is_active=True
        ),
        # Thomas Varkey
        HealthCondition(
            resident_id=res_thomas.id,
            condition_name="Knee Joint Arthroplasty (Post-Op)",
            notes="Doctor: Dr. Joseph Kurian (Orthopedic Surgery). Weekly physiotherapy checkups in Central Rehab clinic.",
            diagnosed_date=datetime(2022, 5, 23),
            is_active=True
        )
    ])
    session.commit()

    # 10. Seed Users & Authorization Profiles
    # System Admin (Root)
    blesson_user = User(
        email="blesson@wifisense.com",
        password_hash=hash_password("blessonpassword"),
        first_name="Blesson",
        last_name="Joseph Byju",
        is_active=True
    )
    session.add(blesson_user)
    session.commit()
    session.refresh(blesson_user)
    session.add(UserRole(user_id=blesson_user.id, role_id=ROLE_MAPPING["system_admin"]))

    # CORPORATE Users (Amal Jyothi College of Engineering)
    abhinand_user = User(
        email="abhinand@wifisense.com",
        password_hash=hash_password("abhinandpassword"),
        first_name="Abhinand",
        last_name="M A",
        is_active=True
    )
    session.add(abhinand_user)
    session.commit()
    session.refresh(abhinand_user)
    session.add(UserRole(
        user_id=abhinand_user.id,
        role_id=ROLE_MAPPING["facility_manager"],
        organization_id=org_ajce.id,
        building_id=bld_mca.id
    ))

    tomy_user = User(
        email="tomy@wifisense.com",
        password_hash=hash_password("tomypassword"),
        first_name="Prof. Tomy",
        last_name="Joseph",
        is_active=True
    )
    session.add(tomy_user)
    session.commit()
    session.refresh(tomy_user)
    session.add(UserRole(
        user_id=tomy_user.id,
        role_id=ROLE_MAPPING["corporate_staff"],
        organization_id=org_ajce.id,
        building_id=bld_mca.id
    ))

    kavitha_user = User(
        email="kavitha@wifisense.com",
        password_hash=hash_password("kavithapassword"),
        first_name="Dr. Kavitha",
        last_name="Nair",
        is_active=True
    )
    session.add(kavitha_user)
    session.commit()
    session.refresh(kavitha_user)
    session.add(UserRole(
        user_id=kavitha_user.id,
        role_id=ROLE_MAPPING["organization_admin"],
        organization_id=org_ajce.id
    ))

    rahul_user = User(
        email="rahul@wifisense.com",
        password_hash=hash_password("rahulpassword"),
        first_name="Rahul",
        last_name="Menon",
        is_active=True
    )
    session.add(rahul_user)
    session.commit()
    session.refresh(rahul_user)
    session.add(UserRole(
        user_id=rahul_user.id,
        role_id=ROLE_MAPPING["corporate_staff"],
        organization_id=org_ajce.id,
        building_id=bld_rd.id
    ))

    # CARE Users (St. Peter's Elder Care Home)
    abhinanth_user = User(
        email="abhinanth@wifisense.com",
        password_hash=hash_password("abhinanthpassword"),
        first_name="Abhinanth",
        last_name="S Pillai",
        is_active=True
    )
    session.add(abhinanth_user)
    session.commit()
    session.refresh(abhinanth_user)
    session.add(UserRole(
        user_id=abhinanth_user.id,
        role_id=ROLE_MAPPING["caregiver"],
        organization_id=org_lab.id,
        building_id=bld_wing_a.id
    ))
    session.add(CaregiverProfile(
        user_id=abhinanth_user.id,
        bio="Lead Care Specialist with 8 years of certified geriatric assisted living experience.",
        work_history=[{"title": "Senior Care Nurse", "facility": "St. Peter's Elder Care", "years": 4}]
    ))

    mary_user = User(
        email="mary@wifisense.com",
        password_hash=hash_password("marypassword"),
        first_name="Sr. Mary",
        last_name="Sebastian",
        is_active=True
    )
    session.add(mary_user)
    session.commit()
    session.refresh(mary_user)
    session.add(UserRole(
        user_id=mary_user.id,
        role_id=ROLE_MAPPING["caregiver"],
        organization_id=org_lab.id,
        building_id=bld_wing_b.id
    ))

    elizabeth_user = User(
        email="elizabeth@wifisense.com",
        password_hash=hash_password("elizabethpassword"),
        first_name="Dr. Elizabeth",
        last_name="Kurian",
        is_active=True
    )
    session.add(elizabeth_user)
    session.commit()
    session.refresh(elizabeth_user)
    session.add(UserRole(
        user_id=elizabeth_user.id,
        role_id=ROLE_MAPPING["facility_manager"],
        organization_id=org_lab.id,
        building_id=bld_wing_a.id
    ))

    priya_user = User(
        email="priya@wifisense.com",
        password_hash=hash_password("priyapassword"),
        first_name="Nurse Priya",
        last_name="Nair",
        is_active=True
    )
    session.add(priya_user)
    session.commit()
    session.refresh(priya_user)
    session.add(UserRole(
        user_id=priya_user.id,
        role_id=ROLE_MAPPING["caregiver"],
        organization_id=org_lab.id,
        building_id=bld_wing_a.id
    ))

    anjali_user = User(
        email="anjali@wifisense.com",
        password_hash=hash_password("anjalipassword"),
        first_name="Dr. Anjali",
        last_name="Thomas",
        is_active=True
    )
    session.add(anjali_user)
    session.commit()
    session.refresh(anjali_user)
    session.add(UserRole(
        user_id=anjali_user.id,
        role_id=ROLE_MAPPING["organization_admin"],
        organization_id=org_lab.id
    ))

    # Family Members (Emergency Contacts)
    john_user = User(
        email="john@wifisense.com",
        password_hash=hash_password("johnpassword"),
        first_name="John",
        last_name="Smith",
        resident_id=res_annamma.id,
        is_active=True
    )
    anna_user = User(
        email="anna@wifisense.com",
        password_hash=hash_password("annapassword"),
        first_name="Anna",
        last_name="Joseph",
        resident_id=res_mary.id,
        is_active=True
    )
    robert_user = User(
        email="robert@wifisense.com",
        password_hash=hash_password("robertpassword"),
        first_name="Robert",
        last_name="Lang",
        resident_id=res_mary.id,
        is_active=True
    )
    susan_user = User(
        email="susan@wifisense.com",
        password_hash=hash_password("susanpassword"),
        first_name="Susan",
        last_name="Varghese",
        resident_id=None,
        is_active=True
    )
    david_user = User(
        email="david@wifisense.com",
        password_hash=hash_password("davidpassword"),
        first_name="David",
        last_name="Mathew",
        resident_id=res_mathew.id,
        is_active=True
    )
    grace_user = User(
        email="grace@wifisense.com",
        password_hash=hash_password("gracepassword"),
        first_name="Grace",
        last_name="Thomas",
        resident_id=None,
        is_active=True
    )

    all_family = [john_user, anna_user, robert_user, susan_user, david_user, grace_user]
    session.add_all(all_family)
    session.commit()
    for u in all_family:
        session.refresh(u)
        session.add(UserRole(
            user_id=u.id,
            role_id=ROLE_MAPPING["emergency_contact"],
            organization_id=org_lab.id
        ))

    # Access Requests (Approved and Pending)
    session.add_all([
        AccessRequest(
            requesting_user_id=john_user.id,
            resident_id=res_annamma.id,
            status="approved",
            reviewed_by=blesson_user.id,
            reviewed_at=datetime.utcnow() - timedelta(days=5)
        ),
        AccessRequest(
            requesting_user_id=anna_user.id,
            resident_id=res_mary.id,
            status="approved",
            reviewed_by=elizabeth_user.id,
            reviewed_at=datetime.utcnow() - timedelta(days=12)
        ),
        AccessRequest(
            requesting_user_id=robert_user.id,
            resident_id=res_mary.id,
            status="approved",
            reviewed_by=elizabeth_user.id,
            reviewed_at=datetime.utcnow() - timedelta(days=10)
        ),
        AccessRequest(
            requesting_user_id=david_user.id,
            resident_id=res_mathew.id,
            status="approved",
            reviewed_by=elizabeth_user.id,
            reviewed_at=datetime.utcnow() - timedelta(days=2)
        ),
        AccessRequest(
            requesting_user_id=susan_user.id,
            resident_id=res_devassy.id,
            status="pending"
        ),
        AccessRequest(
            requesting_user_id=grace_user.id,
            resident_id=res_rosamma.id,
            status="pending"
        )
    ])
    session.commit()

    # 11. Seed Sharing Policies
    session.add_all([
        SharingPolicy(
            organization_id=org_lab.id,
            share_presence=True,
            share_activity_detail=True,
            share_room_name=True,
            share_alert_history=True,
            share_alert_severity_threshold="MEDIUM"
        ),
        SharingPolicy(
            organization_id=org_ajce.id,
            share_presence=False,
            share_activity_detail=False,
            share_room_name=False,
            share_alert_history=False
        ),
        SharingPolicy(
            resident_id=res_annamma.id,
            share_presence=True,
            share_activity_detail=False,
            share_room_name=True,
            share_alert_history=True
        ),
        SharingPolicy(
            resident_id=res_mary.id,
            share_presence=True,
            share_activity_detail=True,
            share_room_name=True,
            share_alert_history=True
        )
    ])
    session.commit()

    # 12. Seed Sensing Devices
    # SPACE Devices
    dev_c_conf_a = SensingDevice(mac_address="4C:75:25:AA:10:01", room_id=rm_conf_a.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP101", hardware_token="TK-ESP32-CONF-A", last_seen_at=datetime.utcnow())
    dev_c_meet_b = SensingDevice(mac_address="4C:75:25:AA:10:02", room_id=rm_meet_b.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP102", hardware_token="TK-ESP32-MEET-B", last_seen_at=datetime.utcnow())
    dev_c_lab1 = SensingDevice(mac_address="4C:75:25:AA:10:03", room_id=rm_comp_lab1.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP103", hardware_token="TK-ESP32-LAB-01", last_seen_at=datetime.utcnow())
    dev_c_lab2 = SensingDevice(mac_address="4C:75:25:AA:10:04", room_id=rm_comp_lab2.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP104", hardware_token="TK-ESP32-LAB-02", last_seen_at=datetime.utcnow())
    dev_c_res2 = SensingDevice(mac_address="4C:75:25:AA:10:05", room_id=rm_res_lab2.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP105", hardware_token="TK-ESP32-RES-02", last_seen_at=datetime.utcnow())
    dev_c_cls101 = SensingDevice(mac_address="4C:75:25:AA:10:06", room_id=rm_class_101.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP106", hardware_token="TK-ESP32-CLS-101", last_seen_at=datetime.utcnow())
    dev_c_cls102 = SensingDevice(mac_address="4C:75:25:AA:10:07", room_id=rm_class_102.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP107", hardware_token="TK-ESP32-CLS-102", last_seen_at=datetime.utcnow())
    dev_c_staff = SensingDevice(mac_address="4C:75:25:AA:10:08", room_id=rm_staff_a.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP108", hardware_token="TK-ESP32-STF-01", last_seen_at=datetime.utcnow())
    dev_c_server = SensingDevice(mac_address="4C:75:25:AA:10:09", room_id=rm_server_telecom.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP109", hardware_token="TK-ESP32-SRV-01", last_seen_at=datetime.utcnow())
    dev_c_sem = SensingDevice(mac_address="4C:75:25:AA:10:10", room_id=rm_seminar_mca.id, device_status="ONLINE", firmware_version="ESP32-CSI Node SP110", hardware_token="TK-ESP32-SEM-01", last_seen_at=datetime.utcnow())

    # CARE Devices
    dev_ec_101 = SensingDevice(mac_address="24:0A:C4:00:20:01", room_id=rm_101.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC101", hardware_token="TK-ESP32-EC-101", last_seen_at=datetime.utcnow())
    dev_ec_102 = SensingDevice(mac_address="24:0A:C4:00:20:02", room_id=rm_102.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC102", hardware_token="TK-ESP32-EC-102", last_seen_at=datetime.utcnow())
    dev_ec_103 = SensingDevice(mac_address="24:0A:C4:00:20:03", room_id=rm_103.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC103", hardware_token="TK-ESP32-EC-103", last_seen_at=datetime.utcnow())
    dev_ec_104 = SensingDevice(mac_address="24:0A:C4:00:20:04", room_id=rm_104.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC104", hardware_token="TK-ESP32-EC-104", last_seen_at=datetime.utcnow())
    dev_ec_201 = SensingDevice(mac_address="24:0A:C4:00:20:05", room_id=rm_201.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC201", hardware_token="TK-ESP32-EC-201", last_seen_at=datetime.utcnow())
    dev_ec_202 = SensingDevice(mac_address="24:0A:C4:00:20:06", room_id=rm_202.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC202", hardware_token="TK-ESP32-EC-202", last_seen_at=datetime.utcnow())
    dev_ec_203 = SensingDevice(mac_address="24:0A:C4:00:20:07", room_id=rm_203.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC203", hardware_token="TK-ESP32-EC-203", last_seen_at=datetime.utcnow())
    dev_ec_204 = SensingDevice(mac_address="24:0A:C4:00:20:08", room_id=rm_204.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC204", hardware_token="TK-ESP32-EC-204", last_seen_at=datetime.utcnow())
    dev_ec_bath1 = SensingDevice(mac_address="24:0A:C4:00:20:09", room_id=rm_bath_1.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-B01", hardware_token="TK-ESP32-EC-B01", last_seen_at=datetime.utcnow())
    dev_ec_physio = SensingDevice(mac_address="24:0A:C4:00:20:10", room_id=rm_physio.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-PHY", hardware_token="TK-ESP32-EC-PHY", last_seen_at=datetime.utcnow())
    dev_ec_rec = SensingDevice(mac_address="24:0A:C4:00:20:11", room_id=rm_recreation.id, device_status="FAULT_REPORTED", firmware_version="ESP32-CSI Node EC-REC", hardware_token="TK-ESP32-EC-REC", last_seen_at=datetime.utcnow())
    dev_ec_dining = SensingDevice(mac_address="24:0A:C4:00:20:12", room_id=rm_dining.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-DIN", hardware_token="TK-ESP32-EC-DIN", last_seen_at=datetime.utcnow())
    dev_ec_nurse = SensingDevice(mac_address="24:0A:C4:00:20:13", room_id=rm_nursing.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-NUR", hardware_token="TK-ESP32-EC-NUR", last_seen_at=datetime.utcnow())

    all_devices = [
        dev_c_conf_a, dev_c_meet_b, dev_c_lab1, dev_c_lab2, dev_c_res2,
        dev_c_cls101, dev_c_cls102, dev_c_staff, dev_c_server, dev_c_sem,
        dev_ec_101, dev_ec_102, dev_ec_103, dev_ec_104, dev_ec_201,
        dev_ec_202, dev_ec_203, dev_ec_204, dev_ec_bath1, dev_ec_physio,
        dev_ec_rec, dev_ec_dining, dev_ec_nurse
    ]
    session.add_all(all_devices)
    session.commit()
    for d in all_devices:
        session.refresh(d)

    # 13. Seed Hardware Maintenance Fault Reports
    session.add_all([
        NodeFaultReport(
            device_id=dev_ec_rec.id,
            reported_by_user_id=mary_user.id,
            issue_type="FAULTY_CSI_VALUES",
            description="Subcarrier amplitude fluctuation with 90% phase variance spikes in Recreation Lounge. Receiver antenna desync suspected.",
            severity="HIGH",
            tracer_token="TRC-94A2F801",
            status="REPORTED",
            service_notes="Pending hardware engineer inspection on next scheduled maintenance sweep."
        ),
        NodeFaultReport(
            device_id=dev_c_server.id,
            reported_by_user_id=abhinand_user.id,
            issue_type="INTERMITTENT_CONNECTIVITY",
            description="High thermal buildup near server rack causing node packet retransmissions.",
            severity="MEDIUM",
            tracer_token="TRC-C83E1094",
            status="UNDER_INSPECTION",
            service_notes="Thermal shield relocated. Monitoring packet drop rates over 48 hours."
        )
    ])
    session.commit()

    # 14. Seed Realistic Sensing Events with Relative Timestamps
    now = datetime.utcnow()
    events = []

    # SCENARIO A: Mary Joseph in Room 204 (Walking -> Sitting -> Resting)
    events.append(SensingEvent(
        device_id=dev_ec_204.id, room_id=rm_204.id,
        timestamp=now - timedelta(minutes=6),
        rssi=-54, subcarrier_count=64,
        extracted_features={"phase_var": 4.2, "doppler_hz": 1.4, "subject": "Mary Joseph"},
        inferred_activity_id=3, model_confidence=0.96 # Walking
    ))
    events.append(SensingEvent(
        device_id=dev_ec_204.id, room_id=rm_204.id,
        timestamp=now - timedelta(minutes=3),
        rssi=-58, subcarrier_count=64,
        extracted_features={"phase_var": 0.8, "doppler_hz": 0.2, "subject": "Mary Joseph"},
        inferred_activity_id=4, model_confidence=0.94 # Sitting
    ))
    events.append(SensingEvent(
        device_id=dev_ec_204.id, room_id=rm_204.id,
        timestamp=now - timedelta(seconds=45),
        rssi=-62, subcarrier_count=64,
        extracted_features={"phase_var": 0.1, "doppler_hz": 0.02, "subject": "Mary Joseph"},
        inferred_activity_id=6, model_confidence=0.98 # Resting
    ))

    # SCENARIO B: Devassy Varghese in Room 101 (Prolonged Inactivity - Sitting > 1 hour)
    events.append(SensingEvent(
        device_id=dev_ec_101.id, room_id=rm_101.id,
        timestamp=now - timedelta(hours=1, minutes=15),
        rssi=-56, subcarrier_count=64,
        extracted_features={"phase_var": 0.9, "subject": "Devassy Varghese"},
        inferred_activity_id=4, model_confidence=0.93 # Sitting
    ))
    events.append(SensingEvent(
        device_id=dev_ec_101.id, room_id=rm_101.id,
        timestamp=now - timedelta(minutes=2),
        rssi=-57, subcarrier_count=64,
        extracted_features={"phase_var": 0.4, "subject": "Devassy Varghese", "inactivity_duration_minutes": 75},
        inferred_activity_id=4, model_confidence=0.95 # Sitting (Unusually long period)
    ))

    # SCENARIO C: K. C. Mathew in Ensuite Bathroom 1 (Fall_Detected, Active Emergency)
    events.append(SensingEvent(
        device_id=dev_ec_bath1.id, room_id=rm_bath_1.id,
        timestamp=now - timedelta(minutes=4),
        rssi=-50, subcarrier_count=64,
        extracted_features={"phase_var": 3.8, "doppler_hz": 1.2, "subject": "K. C. Mathew"},
        inferred_activity_id=3, model_confidence=0.94 # Walking into bathroom
    ))
    events.append(SensingEvent(
        device_id=dev_ec_bath1.id, room_id=rm_bath_1.id,
        timestamp=now - timedelta(minutes=1, seconds=30),
        rssi=-45, subcarrier_count=64,
        extracted_features={"rapid_stance_drop": True, "floor_plane_proximity": 0.98, "subject": "K. C. Mathew"},
        inferred_activity_id=5, model_confidence=0.99 # Fall_Detected
    ))

    # SCENARIO D: Rosamma Thomas in Room 104 (Nighttime movement)
    events.append(SensingEvent(
        device_id=dev_ec_104.id, room_id=rm_104.id,
        timestamp=now - timedelta(minutes=12),
        rssi=-55, subcarrier_count=64,
        extracted_features={"nighttime_motion": True, "subject": "Rosamma Thomas"},
        inferred_activity_id=3, model_confidence=0.91 # Walking
    ))

    # SCENARIO E: Other CARE Rooms live status
    events.append(SensingEvent(
        device_id=dev_ec_102.id, room_id=rm_102.id,
        timestamp=now - timedelta(minutes=5),
        rssi=-61, subcarrier_count=64,
        extracted_features={"subject": "Annamma Joseph"},
        inferred_activity_id=6, model_confidence=0.95 # Resting
    ))
    events.append(SensingEvent(
        device_id=dev_ec_103.id, room_id=rm_103.id,
        timestamp=now - timedelta(minutes=8),
        rssi=-59, subcarrier_count=64,
        extracted_features={"subject": "George Philip"},
        inferred_activity_id=4, model_confidence=0.92 # Sitting
    ))
    events.append(SensingEvent(
        device_id=dev_ec_physio.id, room_id=rm_physio.id,
        timestamp=now - timedelta(minutes=7),
        rssi=-52, subcarrier_count=64,
        extracted_features={"subject": "Thomas Varkey"},
        inferred_activity_id=3, model_confidence=0.93 # Walking / Balance therapy
    ))
    events.append(SensingEvent(
        device_id=dev_ec_dining.id, room_id=rm_dining.id,
        timestamp=now - timedelta(minutes=15),
        rssi=-50, subcarrier_count=64,
        extracted_features={"occupants_count": 8},
        inferred_activity_id=2, model_confidence=0.96 # Presence
    ))
    events.append(SensingEvent(
        device_id=dev_ec_nurse.id, room_id=rm_nursing.id,
        timestamp=now - timedelta(minutes=1),
        rssi=-48, subcarrier_count=64,
        extracted_features={"staff_present": True},
        inferred_activity_id=3, model_confidence=0.97 # Walking
    ))

    # -------------------------------------------------------------
    # CORPORATE (SPACE) SENSING SCENARIOS
    # SCENARIO F: Computer Lab 1 (Unexpected Occupancy during scheduled vacant maintenance)
    events.append(SensingEvent(
        device_id=dev_c_lab1.id, room_id=rm_comp_lab1.id,
        timestamp=now - timedelta(minutes=3),
        rssi=-53, subcarrier_count=64,
        extracted_features={"doppler_hz": 1.6, "unexpected_occupancy": True},
        inferred_activity_id=3, model_confidence=0.94 # Walking
    ))

    # SCENARIO G: Executive Conference Room A (Normal Scheduled Meeting)
    events.append(SensingEvent(
        device_id=dev_c_conf_a.id, room_id=rm_conf_a.id,
        timestamp=now - timedelta(minutes=4),
        rssi=-56, subcarrier_count=64,
        extracted_features={"group_presence": True, "ambient_variance": 3.2},
        inferred_activity_id=4, model_confidence=0.92 # Sitting
    ))

    # SCENARIO H: Board Meeting Room B (Vacant, AC running)
    events.append(SensingEvent(
        device_id=dev_c_meet_b.id, room_id=rm_meet_b.id,
        timestamp=now - timedelta(hours=2, minutes=30),
        rssi=-78, subcarrier_count=64,
        extracted_features={"presence_detected": False, "ac_running_no_occupants": True},
        inferred_activity_id=1, model_confidence=0.99 # Empty
    ))

    # SCENARIO I: Research Lab 2 (After-hours unexpected activity)
    events.append(SensingEvent(
        device_id=dev_c_res2.id, room_id=rm_res_lab2.id,
        timestamp=now - timedelta(minutes=18),
        rssi=-55, subcarrier_count=64,
        extracted_features={"off_hours_burst": True, "doppler_hz": 2.1},
        inferred_activity_id=3, model_confidence=0.91 # Walking
    ))

    # SCENARIO J: Smart Classroom 101 (Class in session)
    events.append(SensingEvent(
        device_id=dev_c_cls101.id, room_id=rm_class_101.id,
        timestamp=now - timedelta(minutes=6),
        rssi=-51, subcarrier_count=64,
        extracted_features={"density_cluster": "HIGH"},
        inferred_activity_id=4, model_confidence=0.95 # Sitting
    ))

    # SCENARIO K: Smart Classroom 102 (Vacant, HVAC running)
    events.append(SensingEvent(
        device_id=dev_c_cls102.id, room_id=rm_class_102.id,
        timestamp=now - timedelta(hours=1, minutes=48),
        rssi=-75, subcarrier_count=64,
        extracted_features={"presence_detected": False},
        inferred_activity_id=1, model_confidence=0.98 # Empty
    ))

    # SCENARIO L: Staff Room A
    events.append(SensingEvent(
        device_id=dev_c_staff.id, room_id=rm_staff_a.id,
        timestamp=now - timedelta(minutes=5),
        rssi=-60, subcarrier_count=64,
        extracted_features={"desk_presence": True},
        inferred_activity_id=4, model_confidence=0.92 # Sitting
    ))

    # SCENARIO M: Server Room (Empty, secure)
    events.append(SensingEvent(
        device_id=dev_c_server.id, room_id=rm_server_telecom.id,
        timestamp=now - timedelta(minutes=30),
        rssi=-80, subcarrier_count=64,
        extracted_features={"secure_baseline": True},
        inferred_activity_id=1, model_confidence=0.99 # Empty
    ))

    # Historical Telemetry spanning 7 days across devices for rich analytics
    for day in range(1, 8):
        for dev in [dev_ec_101, dev_ec_102, dev_ec_204, dev_c_conf_a, dev_c_lab1, dev_c_cls101]:
            for hr in [4, 9, 13, 16, 20]:
                evt_time = now - timedelta(days=day, hours=hr, minutes=random.randint(2, 50))
                act_pick = random.choice([1, 2, 3, 4, 6])
                events.append(SensingEvent(
                    device_id=dev.id,
                    room_id=dev.room_id,
                    timestamp=evt_time,
                    rssi=random.randint(-70, -48),
                    subcarrier_count=64,
                    extracted_features={"historical_log": True},
                    inferred_activity_id=act_pick,
                    model_confidence=round(random.uniform(0.88, 0.98), 2)
                ))

    session.add_all(events)
    session.commit()

    # 15. Seed Alerts (Strict Separation: CARE vs SPACE)
    # -------------------------------------------------
    alerts = []

    # CARE ALERTS
    # 1. Active Critical Fall in Bathroom 1
    alerts.append(Alert(
        room_id=rm_bath_1.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="new",
        message="Critical Fall Alert: K. C. Mathew sudden stance collapse detected in Wing A Ensuite Bathroom 1",
        created_at=now - timedelta(minutes=1, seconds=30)
    ))

    # 2. Acknowledged Fall Alert in Room 202
    alerts.append(Alert(
        room_id=rm_202.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="acknowledged",
        message="Fall Signature Warning: Mariamma Kuruvilla sudden floor descent in Resident Room 202",
        created_at=now - timedelta(minutes=35)
    ))

    # 3. Active Extended Inactivity Alert in Room 101
    alerts.append(Alert(
        room_id=rm_101.id,
        event_type="Prolonged_Inactivity",
        severity="MEDIUM",
        status="new",
        message="Extended Inactivity Detected: Devassy Varghese has remained seated without postural change for over 75 minutes in Resident Room 101",
        created_at=now - timedelta(minutes=2)
    ))

    # 4. Active Nighttime Movement in Room 104
    alerts.append(Alert(
        room_id=rm_104.id,
        event_type="Nighttime_Movement",
        severity="LOW",
        status="new",
        message="Nighttime Activity Notice: Rosamma Thomas unassisted ambulation detected during resting hours in Resident Room 104",
        created_at=now - timedelta(minutes=12)
    ))

    # 5. Resolved Care Alert: Bedside Assist (Room 204)
    alerts.append(Alert(
        room_id=rm_204.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="resolved",
        message="Fall Risk Incident: Mary Joseph slip transfer near bedside in Resident Room 204",
        created_at=now - timedelta(hours=4, minutes=10)
    ))

    # 6. Resolved Care Alert: Loss of balance (Physiotherapy Clinic)
    alerts.append(Alert(
        room_id=rm_physio.id,
        event_type="Rapid_Deceleration",
        severity="HIGH",
        status="resolved",
        message="Postural Instability Warning: Thomas Varkey balance loss during parallel bar walk in Central Physiotherapy Clinic",
        created_at=now - timedelta(days=1, hours=3)
    ))

    # 7. Resolved Care Alert: Slip warning (Room 102)
    alerts.append(Alert(
        room_id=rm_102.id,
        event_type="Fall_Detected",
        severity="HIGH",
        status="resolved",
        message="Sudden Descent: Annamma Joseph dropped glasses in Resident Room 102",
        created_at=now - timedelta(days=2, hours=6)
    ))

    # SPACE ALERTS
    # 8. Active Space Alert: Unexpected Occupancy (Computer Lab 1)
    alerts.append(Alert(
        room_id=rm_comp_lab1.id,
        event_type="Unexpected_Occupancy",
        severity="MEDIUM",
        status="new",
        message="Unexpected Occupancy Alert: Motion detected in Computer Lab 1 during scheduled vacant maintenance window",
        created_at=now - timedelta(minutes=3)
    ))

    # 9. Active Space Alert: After-hours Activity (Research Lab 2)
    alerts.append(Alert(
        room_id=rm_res_lab2.id,
        event_type="Restricted_Hours_Activity",
        severity="HIGH",
        status="new",
        message="Restricted Hours Breach: Unexpected activity detected in Research Lab 2 outside authorized access hours",
        created_at=now - timedelta(minutes=18)
    ))

    # 10. Active Space Alert: Energy Waste Recommendation (Board Meeting Room B)
    alerts.append(Alert(
        room_id=rm_meet_b.id,
        event_type="Energy_Efficiency_Recommendation",
        severity="LOW",
        status="new",
        message="Energy Advisory: Board Meeting Room B has remained vacant for 2.5 hours while AC is ON. Auto-standby recommended.",
        created_at=now - timedelta(minutes=45)
    ))

    # 11. Active Space Alert: Energy Waste Recommendation (Smart Classroom 102)
    alerts.append(Alert(
        room_id=rm_class_102.id,
        event_type="Energy_Efficiency_Recommendation",
        severity="LOW",
        status="new",
        message="HVAC Optimization: Smart Classroom 102 vacant for 1.8 hours with HVAC running. Auto-standby recommended.",
        created_at=now - timedelta(hours=1, minutes=10)
    ))

    # 12. Resolved Space Alert: Janitorial Off-hours sweep (MCA Seminar Hall)
    alerts.append(Alert(
        room_id=rm_seminar_mca.id,
        event_type="Restricted_Hours_Activity",
        severity="LOW",
        status="resolved",
        message="Off-Hours Detection: Routine cleaning personnel sweep in MCA Seminar Hall",
        created_at=now - timedelta(days=2, hours=10)
    ))

    session.add_all(alerts)
    session.commit()
    for a in alerts:
        session.refresh(a)

    # 16. Seed Alert Acknowledgements & Resolution Notes
    session.add_all([
        # Incident 2 (acknowledged by Abhinanth)
        AlertAcknowledgement(
            alert_id=alerts[1].id,
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(minutes=30)
        ),
        # Incident 5 (resolved by Sr. Mary)
        AlertAcknowledgement(
            alert_id=alerts[4].id,
            user_id=mary_user.id,
            acknowledged_at=now - timedelta(hours=4, minutes=5),
            resolved_at=now - timedelta(hours=3, minutes=50),
            resolution_notes="Responded to Room 204 immediately. Mary Joseph was safely seated in armchair; no trauma, vitals stable (BP 120/78). Blanket provided."
        ),
        # Incident 6 (resolved by Dr. Elizabeth)
        AlertAcknowledgement(
            alert_id=alerts[5].id,
            user_id=elizabeth_user.id,
            acknowledged_at=now - timedelta(days=1, hours=2, minutes=55),
            resolved_at=now - timedelta(days=1, hours=2, minutes=45),
            resolution_notes="Physiotherapist caught Thomas Varkey during balance exercise. Assisted to rest couch; gait stability assessment logged."
        ),
        # Incident 7 (resolved by Abhinanth)
        AlertAcknowledgement(
            alert_id=alerts[6].id,
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(days=2, hours=5, minutes=55),
            resolved_at=now - timedelta(days=2, hours=5, minutes=40),
            resolution_notes="Annamma Joseph was retrieving reading glasses from bedside rug. Helped her upright; no injury."
        ),
        # Incident 12 (resolved by Abhinand)
        AlertAcknowledgement(
            alert_id=alerts[11].id,
            user_id=abhinand_user.id,
            acknowledged_at=now - timedelta(days=2, hours=9, minutes=50),
            resolved_at=now - timedelta(days=2, hours=9, minutes=45),
            resolution_notes="Verified authorized night custodial pass. All security locks confirmed intact."
        )
    ])
    session.commit()

    print("[WIFISENSE SEED ENGINE] Database seeded with realistic, strictly separated CARE and SPACE datasets successfully!")
