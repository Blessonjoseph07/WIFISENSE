from sqlmodel import Session, select, text
from datetime import datetime, timedelta
import random
from app.models.entities import (
    Role, User, UserRole, Organization, Building, Floor, Room, 
    SensingDevice, Resident, ActivityType, SensingEvent, Alert, AlertAcknowledgement, AccessRequest,
    SharingPolicy, HealthCondition, CaregiverProfile
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
    "Fall_Detected": (5, "CRITICAL")
}

def seed_database(session: Session):
    # 1. Clean existing tables
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

    # 4. Seed Organizations
    org_ajce = Organization(name="Amal Jyothi College of Engineering", type="CORPORATE")
    session.add(org_ajce)
    
    org_lab = Organization(name="St. Peter's Elder Care Home", type="ELDER_CARE")
    session.add(org_lab)
    session.commit()
    session.refresh(org_ajce)
    session.refresh(org_lab)

    # 5. Seed Buildings
    bld_mca = Building(organization_id=org_ajce.id, name="Department of Computer Applications (MCA Block)", address="Amal Jyothi College of Engineering Campus, Kanjirappally, Kerala, India")
    session.add(bld_mca)
    
    bld_rd = Building(organization_id=org_ajce.id, name="R&D Central Annex", address="Main Campus Block C")
    session.add(bld_rd)

    bld_wing_a = Building(organization_id=org_lab.id, name="Care Wing Alpha (North Sector)", address="St. Peter's Elder Care Campus, North Wing")
    session.add(bld_wing_a)
    
    bld_wing_b = Building(organization_id=org_lab.id, name="Care Wing Beta (South Sector)", address="St. Peter's Elder Care Campus, South Wing")
    session.add(bld_wing_b)
    
    session.commit()
    session.refresh(bld_mca)
    session.refresh(bld_rd)
    session.refresh(bld_wing_a)
    session.refresh(bld_wing_b)

    # 6. Seed Floors
    flr_mca_1 = Floor(building_id=bld_mca.id, floor_number=1)
    session.add(flr_mca_1)
    flr_mca_2 = Floor(building_id=bld_mca.id, floor_number=2)
    session.add(flr_mca_2)
    
    flr_rd_1 = Floor(building_id=bld_rd.id, floor_number=1)
    session.add(flr_rd_1)

    flr_wing_a_1 = Floor(building_id=bld_wing_a.id, floor_number=1)
    session.add(flr_wing_a_1)
    flr_wing_a_2 = Floor(building_id=bld_wing_a.id, floor_number=2)
    session.add(flr_wing_a_2)

    flr_wing_b_1 = Floor(building_id=bld_wing_b.id, floor_number=1)
    session.add(flr_wing_b_1)
    flr_wing_b_2 = Floor(building_id=bld_wing_b.id, floor_number=2)
    session.add(flr_wing_b_2)

    session.commit()
    session.refresh(flr_mca_1)
    session.refresh(flr_mca_2)
    session.refresh(flr_rd_1)
    session.refresh(flr_wing_a_1)
    session.refresh(flr_wing_a_2)
    session.refresh(flr_wing_b_1)
    session.refresh(flr_wing_b_2)

    # 7. Seed Rooms
    # Corporate rooms (AJCE)
    rm_mca_lab = Room(floor_id=flr_mca_1.id, name="MCA Lab 1", room_type="Conference Room", capacity=30)
    session.add(rm_mca_lab)
    rm_seminar_hall = Room(floor_id=flr_mca_2.id, name="MCA Seminar Hall", room_type="Conference Room", capacity=150)
    session.add(rm_seminar_hall)
    rm_staff_room = Room(floor_id=flr_mca_1.id, name="Staff Room A", room_type="Conference Room", capacity=15)
    session.add(rm_staff_room)
    rm_iot_lab = Room(floor_id=flr_rd_1.id, name="Internet IoT Lab", room_type="Conference Room", capacity=25)
    session.add(rm_iot_lab)

    # Elder Care rooms (St. Peter's Elder Care Home)
    # Wing Alpha Floor 1
    rm_101 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 101", room_type="Resident Bedroom", capacity=2)
    rm_102 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 102", room_type="Resident Bedroom", capacity=2)
    rm_103 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 103", room_type="Resident Bedroom", capacity=2)
    rm_104 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 104", room_type="Resident Bedroom", capacity=2)
    session.add_all([rm_101, rm_102, rm_103, rm_104])

    # Wing Alpha Floor 2
    rm_201 = Room(floor_id=flr_wing_a_2.id, name="Resident Room 201", room_type="Resident Bedroom", capacity=2)
    rm_202 = Room(floor_id=flr_wing_a_2.id, name="Resident Room 202", room_type="Resident Bedroom", capacity=2)
    rm_203 = Room(floor_id=flr_wing_a_2.id, name="Resident Room 203", room_type="Resident Bedroom", capacity=2)
    session.add_all([rm_201, rm_202, rm_203])

    # Wing Beta Floor 1 & 2
    rm_recreation = Room(floor_id=flr_wing_b_1.id, name="Recreation Center", room_type="Common Area", capacity=25)
    rm_ward_1 = Room(floor_id=flr_wing_b_1.id, name="Common Area Ward 1", room_type="Observation Ward", capacity=10)
    rm_physio = Room(floor_id=flr_wing_b_1.id, name="Physiotherapy Hall", room_type="Therapy Room", capacity=12)
    rm_dining = Room(floor_id=flr_wing_b_2.id, name="Community Dining Hall", room_type="Dining Facility", capacity=35)
    rm_quiet = Room(floor_id=flr_wing_b_2.id, name="Quiet Reading Lounge", room_type="Lounge", capacity=8)
    session.add_all([rm_recreation, rm_ward_1, rm_physio, rm_dining, rm_quiet])

    session.commit()
    for r in [rm_mca_lab, rm_seminar_hall, rm_staff_room, rm_iot_lab,
              rm_101, rm_102, rm_103, rm_104, rm_201, rm_202, rm_203,
              rm_recreation, rm_ward_1, rm_physio, rm_dining, rm_quiet]:
        session.refresh(r)

    # 8. Seed System Users (Staff / Faculty / Caregivers)
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
    session.commit()

    # AJCE Facility Manager
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
    session.commit()

    # AJCE Faculty / Staff
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
    session.commit()

    # St. Peter's Caregivers and Facility Manager
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
        building_id=bld_wing_a.id,
        room_id=rm_101.id
    ))
    session.add(CaregiverProfile(
        user_id=abhinanth_user.id,
        bio="Senior Caregiver with 8 years of experience in assisted living.",
        work_history=[{"title": "Nurse Assistant", "years": 3}]
    ))
    session.commit()

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
    session.commit()

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
    session.commit()

    # 9. Seed Residents (Monitored Persons) - Elder Care Only

    # Elder Care monitored residents (14 residents across buildings and rooms)
    res_devassy = Resident(room_id=rm_101.id, first_name="Devassy", last_name="Varghese", date_of_birth=datetime(1942, 3, 10))
    res_annamma = Resident(room_id=rm_102.id, first_name="Annamma", last_name="Joseph", date_of_birth=datetime(1938, 7, 22))
    res_mathew = Resident(room_id=rm_recreation.id, first_name="K. C.", last_name="Mathew", date_of_birth=datetime(1945, 12, 5))
    res_rosamma = Resident(room_id=rm_ward_1.id, first_name="Rosamma", last_name="Thomas", date_of_birth=datetime(1940, 9, 18))
    res_george = Resident(room_id=rm_103.id, first_name="George", last_name="Philip", date_of_birth=datetime(1941, 4, 14))
    res_mariamma = Resident(room_id=rm_104.id, first_name="Mariamma", last_name="Kuruvilla", date_of_birth=datetime(1939, 11, 30))
    res_thomas = Resident(room_id=rm_201.id, first_name="Thomas", last_name="Varkey", date_of_birth=datetime(1944, 8, 19))
    res_saramma = Resident(room_id=rm_202.id, first_name="Saramma", last_name="Chacko", date_of_birth=datetime(1937, 2, 8))
    res_abraham = Resident(room_id=rm_203.id, first_name="Abraham", last_name="Joseph", date_of_birth=datetime(1946, 6, 25))
    res_thresia = Resident(room_id=rm_physio.id, first_name="Thresia", last_name="Augustine", date_of_birth=datetime(1943, 10, 11))
    res_joseph = Resident(room_id=rm_dining.id, first_name="Joseph", last_name="Anthony", date_of_birth=datetime(1940, 1, 29))
    res_philomina = Resident(room_id=rm_quiet.id, first_name="Philomina", last_name="Xavier", date_of_birth=datetime(1947, 5, 16))
    res_varghese = Resident(room_id=rm_101.id, first_name="Varghese", last_name="Mathai", date_of_birth=datetime(1945, 9, 3))
    res_aleyamma = Resident(room_id=rm_102.id, first_name="Aleyamma", last_name="Paul", date_of_birth=datetime(1942, 12, 21))

    elder_residents = [
        res_devassy, res_annamma, res_mathew, res_rosamma,
        res_george, res_mariamma, res_thomas, res_saramma,
        res_abraham, res_thresia, res_joseph, res_philomina,
        res_varghese, res_aleyamma
    ]
    session.add_all(elder_residents)
    session.commit()

    for r in elder_residents:
        session.refresh(r)

    # Health conditions for elder care residents
    session.add_all([
        HealthCondition(resident_id=res_devassy.id, condition_name="Hypertension", diagnosed_date=datetime(2015, 6, 1)),
        HealthCondition(resident_id=res_devassy.id, condition_name="Osteoarthritis", diagnosed_date=datetime(2018, 2, 14)),
        HealthCondition(resident_id=res_annamma.id, condition_name="Type 2 Diabetes", notes="Requires daily insulin", diagnosed_date=datetime(2010, 11, 5)),
        HealthCondition(resident_id=res_mathew.id, condition_name="Parkinson's Early Stage", notes="Gait instability warning", diagnosed_date=datetime(2021, 3, 12)),
        HealthCondition(resident_id=res_rosamma.id, condition_name="Cardiac Arrhythmia", notes="Prescribed beta-blockers", diagnosed_date=datetime(2017, 8, 20)),
        HealthCondition(resident_id=res_george.id, condition_name="Chronic Bronchitis", diagnosed_date=datetime(2019, 1, 15)),
        HealthCondition(resident_id=res_mariamma.id, condition_name="Glaucoma", diagnosed_date=datetime(2016, 7, 4)),
        HealthCondition(resident_id=res_thomas.id, condition_name="Knee Joint Arthroplasty", diagnosed_date=datetime(2022, 5, 23))
    ])
    session.commit()

    # Sharing Policies
    session.add(SharingPolicy(organization_id=org_lab.id, share_presence=True, share_activity_detail=True, share_room_name=True, share_alert_history=True))
    session.add(SharingPolicy(organization_id=org_ajce.id, share_presence=False, share_activity_detail=False, share_room_name=False, share_alert_history=False))
    session.add(SharingPolicy(resident_id=res_annamma.id, share_presence=True, share_activity_detail=False, share_room_name=True, share_alert_history=True))
    session.commit()

    # 10. Seed Devices
    dev_c1 = SensingDevice(mac_address="4C:75:25:AA:BB:CC", room_id=rm_mca_lab.id, device_status="ONLINE", firmware_version="ESP32-CSI Node 101", last_seen_at=datetime.utcnow())
    dev_c2 = SensingDevice(mac_address="4C:75:25:11:22:33", room_id=rm_staff_room.id, device_status="ONLINE", firmware_version="ESP32-CSI Node 102", last_seen_at=datetime.utcnow())
    dev_c3 = SensingDevice(mac_address="4C:75:25:99:88:77", room_id=rm_iot_lab.id, device_status="ONLINE", firmware_version="ESP32-CSI Node 103", last_seen_at=datetime.utcnow())

    dev_ec1 = SensingDevice(mac_address="24:0A:C4:00:11:22", room_id=rm_101.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC101", last_seen_at=datetime.utcnow())
    dev_ec2 = SensingDevice(mac_address="24:0A:C4:33:44:55", room_id=rm_102.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC102", last_seen_at=datetime.utcnow())
    dev_ec3 = SensingDevice(mac_address="24:0A:C4:66:77:88", room_id=rm_recreation.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-REC", last_seen_at=datetime.utcnow())
    dev_ec4 = SensingDevice(mac_address="24:0A:C4:99:AA:BB", room_id=rm_103.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC103", last_seen_at=datetime.utcnow())
    dev_ec5 = SensingDevice(mac_address="24:0A:C4:CC:DD:EE", room_id=rm_104.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC104", last_seen_at=datetime.utcnow())
    dev_ec6 = SensingDevice(mac_address="24:0A:C4:12:34:56", room_id=rm_201.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC201", last_seen_at=datetime.utcnow())
    dev_ec7 = SensingDevice(mac_address="24:0A:C4:78:9A:BC", room_id=rm_ward_1.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-WRD", last_seen_at=datetime.utcnow())
    dev_ec8 = SensingDevice(mac_address="24:0A:C4:DE:F0:12", room_id=rm_physio.id, device_status="ONLINE", firmware_version="ESP32-CSI Node EC-PHY", last_seen_at=datetime.utcnow())

    all_devices = [dev_c1, dev_c2, dev_c3, dev_ec1, dev_ec2, dev_ec3, dev_ec4, dev_ec5, dev_ec6, dev_ec7, dev_ec8]
    session.add_all(all_devices)
    session.commit()
    for d in all_devices:
        session.refresh(d)

    # 11. Seed Realistic Historical Sensing Events (spanning past 7 days, ~120 events)
    now = datetime.utcnow()
    events_to_add = []

    # Recent baseline events (now - 5 mins) to power live occupancy
    live_scenarios = [
        (dev_c1, rm_mca_lab, 3, -55, 0.94),      # Walking
        (dev_c2, rm_staff_room, 4, -62, 0.91),   # Sitting
        (dev_c3, rm_iot_lab, 2, -68, 0.87),      # Presence
        (dev_ec1, rm_101, 3, -50, 0.96),         # Walking (Devassy)
        (dev_ec2, rm_102, 4, -58, 0.93),         # Sitting (Annamma)
        (dev_ec3, rm_recreation, 5, -48, 0.99),  # Fall_Detected (Mathew - active incident)
        (dev_ec4, rm_103, 4, -60, 0.89),         # Sitting (George)
        (dev_ec5, rm_104, 3, -54, 0.92),         # Walking (Mariamma)
        (dev_ec6, rm_201, 2, -64, 0.88),         # Presence (Thomas)
        (dev_ec7, rm_ward_1, 3, -52, 0.95),      # Walking (Rosamma)
        (dev_ec8, rm_physio, 4, -57, 0.90)       # Sitting (Thresia)
    ]

    for dev, rm, act_id, rssi, conf in live_scenarios:
        events_to_add.append(SensingEvent(
            device_id=dev.id,
            room_id=rm.id,
            timestamp=now - timedelta(minutes=random.randint(1, 10)),
            rssi=rssi,
            subcarrier_count=64,
            extracted_features={
                "amplitude_variance": round(random.uniform(4.0, 45.0), 2),
                "phase_variance": round(random.uniform(0.5, 8.0), 2),
                "presence_detected": True
            },
            inferred_activity_id=act_id,
            model_confidence=conf
        ))

    # Multi-day history: 1 to 7 days in the past across devices
    activity_pool = [1, 2, 3, 4, 3, 4, 2, 1]  # mostly empty, presence, walking, sitting
    for day in range(1, 8):
        for dev in [dev_ec1, dev_ec2, dev_ec3, dev_ec4, dev_ec5, dev_ec6, dev_ec7, dev_ec8, dev_c1, dev_c2]:
            for hour_offset in [3, 7, 11, 15, 19, 23]:
                evt_time = now - timedelta(days=day, hours=hour_offset, minutes=random.randint(5, 55))
                act_choice = random.choice(activity_pool)
                events_to_add.append(SensingEvent(
                    device_id=dev.id,
                    room_id=dev.room_id,
                    timestamp=evt_time,
                    rssi=random.randint(-72, -45),
                    subcarrier_count=64,
                    extracted_features={
                        "amplitude_variance": round(random.uniform(0.2, 15.0), 2),
                        "phase_variance": round(random.uniform(0.05, 3.5), 2),
                        "presence_detected": act_choice != 1
                    },
                    inferred_activity_id=act_choice,
                    model_confidence=round(random.uniform(0.85, 0.98), 2)
                ))

    session.add_all(events_to_add)
    session.commit()

    # 12. Seed Alerts (Realistic spread of 12 alerts over past 7 days)
    alerts_to_create = [
        # Incident 1: Active Alert (Right now, recreation room)
        Alert(
            room_id=rm_recreation.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="new",
            message="Critical Fall Alert: K. C. Mathew sudden descent stance in Recreation Center",
            created_at=now - timedelta(minutes=2)
        ),
        # Incident 2: Acknowledged Alert (45 min ago, Room 104)
        Alert(
            room_id=rm_104.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="acknowledged",
            message="Fall Signature Warning: Mariamma Kuruvilla detected in Resident Room 104",
            created_at=now - timedelta(minutes=45)
        ),
        # Incident 3: Resolved (3 hours ago, Room 101)
        Alert(
            room_id=rm_101.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="resolved",
            message="Emergency Fall Warning: Devassy Varghese detected horizontal in Resident Room 101",
            created_at=now - timedelta(hours=3),
            resolved_at=now - timedelta(hours=2, minutes=45)
        ),
        # Incident 4: Resolved (Yesterday morning, Room 102)
        Alert(
            room_id=rm_102.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="resolved",
            message="Fall Warning: Annamma Joseph in Resident Room 102",
            created_at=now - timedelta(days=1, hours=2),
            resolved_at=now - timedelta(days=1, hours=1, minutes=40)
        ),
        # Incident 5: Resolved (2 days ago, Ward 1)
        Alert(
            room_id=rm_ward_1.id,
            event_type="Fall_Detected",
            severity="HIGH",
            status="resolved",
            message="Rapid Stance Change: Rosamma Thomas in Common Area Ward 1",
            created_at=now - timedelta(days=2, hours=5),
            resolved_at=now - timedelta(days=2, hours=4, minutes=30)
        ),
        # Incident 6: Resolved (3 days ago, Room 103)
        Alert(
            room_id=rm_103.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="resolved",
            message="Possible Slip Incident: George Philip in Resident Room 103",
            created_at=now - timedelta(days=3, hours=8),
            resolved_at=now - timedelta(days=3, hours=7, minutes=50)
        ),
        # Incident 7: Resolved (4 days ago, Physiotherapy Hall)
        Alert(
            room_id=rm_physio.id,
            event_type="Fall_Detected",
            severity="HIGH",
            status="resolved",
            message="Loss of Balance Detected: Thresia Augustine in Physiotherapy Hall",
            created_at=now - timedelta(days=4, hours=3),
            resolved_at=now - timedelta(days=4, hours=2, minutes=35)
        ),
        # Incident 8: Resolved (5 days ago, Room 201)
        Alert(
            room_id=rm_201.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="resolved",
            message="Impact Event: Thomas Varkey in Resident Room 201",
            created_at=now - timedelta(days=5, hours=6),
            resolved_at=now - timedelta(days=5, hours=5, minutes=40)
        ),
        # Incident 9: Resolved (6 days ago, Room 101)
        Alert(
            room_id=rm_101.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            status="resolved",
            message="Bedside Fall Stance: Varghese Mathai in Resident Room 101",
            created_at=now - timedelta(days=6, hours=10),
            resolved_at=now - timedelta(days=6, hours=9, minutes=50)
        ),
        # Incident 10: Resolved (7 days ago, Recreation Center)
        Alert(
            room_id=rm_recreation.id,
            event_type="Fall_Detected",
            severity="HIGH",
            status="resolved",
            message="Unbalanced Movement Pattern in Recreation Center",
            created_at=now - timedelta(days=7, hours=4),
            resolved_at=now - timedelta(days=7, hours=3, minutes=30)
        ),
        # Incident 11: Corporate False Spike (Resolved, MCA Lab)
        Alert(
            room_id=rm_mca_lab.id,
            event_type="Anomaly_Movement",
            severity="MEDIUM",
            status="resolved",
            message="CSI Doppler Burst during off-hours in MCA Lab 1",
            created_at=now - timedelta(days=2, hours=12),
            resolved_at=now - timedelta(days=2, hours=11, minutes=45)
        ),
        # Incident 12: Corporate Sensor Calibration Warning (Resolved, IoT Lab)
        Alert(
            room_id=rm_iot_lab.id,
            event_type="Anomaly_Movement",
            severity="LOW",
            status="resolved",
            message="Intermittent Carrier Noise detected on Node 103",
            created_at=now - timedelta(days=5, hours=1),
            resolved_at=now - timedelta(days=5, hours=0, minutes=45)
        )
    ]

    session.add_all(alerts_to_create)
    session.commit()
    for a in alerts_to_create:
        session.refresh(a)

    # Acknowledgements and resolution notes for resolved & acknowledged alerts
    session.add_all([
        AlertAcknowledgement(
            alert_id=alerts_to_create[1].id,  # Incident 2 (acknowledged)
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(minutes=40)
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[2].id,  # Incident 3 (resolved)
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(hours=2, minutes=58),
            resolved_at=now - timedelta(hours=2, minutes=45),
            resolution_notes="Resident assisted. Devassy Varghese was sitting on the floor but unhurt. Safely helped back to armchair."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[3].id,  # Incident 4 (resolved)
            user_id=mary_user.id,
            acknowledged_at=now - timedelta(days=1, hours=1, minutes=55),
            resolved_at=now - timedelta(days=1, hours=1, minutes=40),
            resolution_notes="Checked Room 102. Resident was picking up fallen eyeglasses. No injury."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[4].id,  # Incident 5 (resolved)
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(days=2, hours=4, minutes=45),
            resolved_at=now - timedelta(days=2, hours=4, minutes=30),
            resolution_notes="Staff attended Rosamma Thomas in Ward 1. Stabilized with walker."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[5].id,  # Incident 6 (resolved)
            user_id=mary_user.id,
            acknowledged_at=now - timedelta(days=3, hours=7, minutes=55),
            resolved_at=now - timedelta(days=3, hours=7, minutes=50),
            resolution_notes="George Philip reached for water pitcher. Vitals normal."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[6].id,  # Incident 7 (resolved)
            user_id=elizabeth_user.id,
            acknowledged_at=now - timedelta(days=4, hours=2, minutes=40),
            resolved_at=now - timedelta(days=4, hours=2, minutes=35),
            resolution_notes="Physiotherapist caught resident during balance exercises. Resident rested comfortably."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[7].id,  # Incident 8 (resolved)
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(days=5, hours=5, minutes=50),
            resolved_at=now - timedelta(days=5, hours=5, minutes=40),
            resolution_notes="Bed transfer assist performed. Floor mats repositioned."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[8].id,  # Incident 9 (resolved)
            user_id=mary_user.id,
            acknowledged_at=now - timedelta(days=6, hours=9, minutes=55),
            resolved_at=now - timedelta(days=6, hours=9, minutes=50),
            resolution_notes="Varghese assisted back to bed. Blood pressure measured 125/80."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[9].id,  # Incident 10 (resolved)
            user_id=abhinanth_user.id,
            acknowledged_at=now - timedelta(days=7, hours=3, minutes=40),
            resolved_at=now - timedelta(days=7, hours=3, minutes=30),
            resolution_notes="Chair bumped by wheelchair; false positive movement cleared."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[10].id,  # Incident 11 (resolved)
            user_id=abhinand_user.id,
            acknowledged_at=now - timedelta(days=2, hours=11, minutes=50),
            resolved_at=now - timedelta(days=2, hours=11, minutes=45),
            resolution_notes="Janitorial staff entered room for routine scheduled cleanup."
        ),
        AlertAcknowledgement(
            alert_id=alerts_to_create[11].id,  # Incident 12 (resolved)
            user_id=abhinand_user.id,
            acknowledged_at=now - timedelta(days=5, hours=0, minutes=50),
            resolved_at=now - timedelta(days=5, hours=0, minutes=45),
            resolution_notes="Antenna re-oriented; RSSI sensitivity threshold normalized."
        )
    ])
    session.commit()

    # 13. Seed Family Members (emergency_contact) and AccessRequests
    john_user = User(
        email="john@wifisense.com",
        password_hash=hash_password("johnpassword"),
        first_name="John",
        last_name="Smith",
        resident_id=res_annamma.id,
        is_active=True
    )
    session.add(john_user)
    session.commit()
    session.refresh(john_user)
    
    session.add(UserRole(
        user_id=john_user.id,
        role_id=ROLE_MAPPING["emergency_contact"],
        organization_id=org_lab.id
    ))
    
    req_john = AccessRequest(
        requesting_user_id=john_user.id,
        resident_id=res_annamma.id,
        status="approved",
        reviewed_by=blesson_user.id,
        reviewed_at=datetime.utcnow() - timedelta(days=2)
    )
    session.add(req_john)
    session.commit()

    susan_user = User(
        email="susan@wifisense.com",
        password_hash=hash_password("susanpassword"),
        first_name="Susan",
        last_name="Varghese",
        resident_id=None,
        is_active=True
    )
    session.add(susan_user)
    session.commit()
    session.refresh(susan_user)

    session.add(UserRole(
        user_id=susan_user.id,
        role_id=ROLE_MAPPING["emergency_contact"],
        organization_id=org_lab.id
    ))

    req_susan = AccessRequest(
        requesting_user_id=susan_user.id,
        resident_id=res_devassy.id,
        status="pending"
    )
    session.add(req_susan)
    session.commit()
