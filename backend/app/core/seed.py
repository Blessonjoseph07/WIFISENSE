from sqlmodel import Session, select, text
from datetime import datetime, timedelta
from app.models.entities import (
    Role, User, UserRole, Organization, Building, Floor, Room, 
    SensingDevice, Resident, ActivityType, SensingEvent, Alert, AlertAcknowledgement, AccessRequest
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
    # 1. Clear existing database contents
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
    
    org_lab = Organization(name="WiFi Sense Research Lab", type="ELDER_CARE")
    session.add(org_lab)
    session.commit()
    session.refresh(org_ajce)
    session.refresh(org_lab)

    # 5. Seed Buildings
    bld_mca = Building(organization_id=org_ajce.id, name="Department of Computer Applications (MCA Block)", address="Amal Jyothi College of Engineering Campus, Kanjirappally, Kerala, India")
    session.add(bld_mca)
    
    bld_rd = Building(organization_id=org_ajce.id, name="R&D Central Annex", address="Main Campus Block C")
    session.add(bld_rd)

    bld_wing_a = Building(organization_id=org_lab.id, name="Care Wing Alpha (North Sector)", address="Research Lab Assisted Living Facility, Ward 1")
    session.add(bld_wing_a)
    
    bld_wing_b = Building(organization_id=org_lab.id, name="Care Wing Beta (South Sector)", address="Research Lab Assisted Living Facility, Ward 2")
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
    flr_wing_b_1 = Floor(building_id=bld_wing_b.id, floor_number=1)
    session.add(flr_wing_b_1)

    session.commit()
    session.refresh(flr_mca_1)
    session.refresh(flr_mca_2)
    session.refresh(flr_rd_1)
    session.refresh(flr_wing_a_1)
    session.refresh(flr_wing_b_1)

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

    # Elder Care rooms (WiFi Sense Research Lab)
    rm_room_101 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 101", room_type="Resident Bedroom", capacity=2)
    session.add(rm_room_101)
    rm_room_102 = Room(floor_id=flr_wing_a_1.id, name="Resident Room 102", room_type="Resident Bedroom", capacity=2)
    session.add(rm_room_102)
    rm_recreation = Room(floor_id=flr_wing_b_1.id, name="Recreation Center", room_type="Resident Bedroom", capacity=15)
    session.add(rm_recreation)
    rm_ward_1 = Room(floor_id=flr_wing_b_1.id, name="Common Area Ward 1", room_type="Resident Bedroom", capacity=10)
    session.add(rm_ward_1)

    session.commit()
    session.refresh(rm_mca_lab)
    session.refresh(rm_seminar_hall)
    session.refresh(rm_staff_room)
    session.refresh(rm_iot_lab)
    session.refresh(rm_room_101)
    session.refresh(rm_room_102)
    session.refresh(rm_recreation)
    session.refresh(rm_ward_1)

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

    # Caregivers for WiFi Sense Lab
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

    # 9. Seed Residents (Monitored Persons)
    # Corporate block monitored users
    res_abhinand = Resident(room_id=rm_mca_lab.id, first_name="Abhinand", last_name="M A")
    session.add(res_abhinand)
    res_tomy = Resident(room_id=rm_staff_room.id, first_name="Prof. Tomy", last_name="Joseph")
    session.add(res_tomy)
    res_anandhu = Resident(room_id=rm_iot_lab.id, first_name="Anandhu", last_name="K S")
    session.add(res_anandhu)
    res_jerin = Resident(room_id=rm_mca_lab.id, first_name="Jerin", last_name="Sebastian")
    session.add(res_jerin)

    # Elder Care monitored residents
    res_devassy = Resident(room_id=rm_room_101.id, first_name="Devassy", last_name="Varghese")
    session.add(res_devassy)
    res_annamma = Resident(room_id=rm_room_102.id, first_name="Annamma", last_name="Joseph")
    session.add(res_annamma)
    res_mathew = Resident(room_id=rm_recreation.id, first_name="K. C.", last_name="Mathew")
    session.add(res_mathew)
    res_rosamma = Resident(room_id=rm_ward_1.id, first_name="Rosamma", last_name="Thomas")
    session.add(res_rosamma)
    session.commit()
    session.refresh(res_devassy)
    session.refresh(res_annamma)
    session.refresh(res_mathew)
    session.refresh(res_rosamma)

    # 10. Seed Devices
    # Corporate device nodes
    dev_c1 = SensingDevice(
        mac_address="4C:75:25:AA:BB:CC",
        room_id=rm_mca_lab.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node 101",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_c1)
    
    dev_c2 = SensingDevice(
        mac_address="4C:75:25:11:22:33",
        room_id=rm_staff_room.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node 102",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_c2)

    dev_c3 = SensingDevice(
        mac_address="4C:75:25:99:88:77",
        room_id=rm_iot_lab.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node 103",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_c3)

    # Elder Care device nodes
    dev_ec1 = SensingDevice(
        mac_address="24:0A:C4:00:11:22",
        room_id=rm_room_101.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node EC1",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_ec1)

    dev_ec2 = SensingDevice(
        mac_address="24:0A:C4:33:44:55",
        room_id=rm_room_102.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node EC2",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_ec2)

    dev_ec3 = SensingDevice(
        mac_address="24:0A:C4:66:77:88",
        room_id=rm_recreation.id,
        device_status="ONLINE",
        firmware_version="ESP32-CSI Node EC3",
        last_seen_at=datetime.utcnow()
    )
    session.add(dev_ec3)
    
    session.commit()
    session.refresh(dev_c1)
    session.refresh(dev_c2)
    session.refresh(dev_c3)
    session.refresh(dev_ec1)
    session.refresh(dev_ec2)
    session.refresh(dev_ec3)

    # 11. Seed Sensing Events
    now = datetime.utcnow()
    # Seed walking event in MCA Lab
    session.add(SensingEvent(
        device_id=dev_c1.id,
        room_id=rm_mca_lab.id,
        timestamp=now - timedelta(minutes=5),
        rssi=-55,
        subcarrier_count=64,
        extracted_features={
            "amplitude_variance": 12.45,
            "phase_variance": 1.89,
            "presence_detected": True
        },
        inferred_activity_id=3,  # Walking
        model_confidence=0.92
    ))
    # Seed sitting event in Staff Room
    session.add(SensingEvent(
        device_id=dev_c2.id,
        room_id=rm_staff_room.id,
        timestamp=now - timedelta(minutes=12),
        rssi=-62,
        subcarrier_count=64,
        extracted_features={
            "amplitude_variance": 1.12,
            "phase_variance": 0.23,
            "presence_detected": True
        },
        inferred_activity_id=4,  # Sitting
        model_confidence=0.88
    ))
    # Seed walking event in Room 101
    session.add(SensingEvent(
        device_id=dev_ec1.id,
        room_id=rm_room_101.id,
        timestamp=now - timedelta(minutes=2),
        rssi=-50,
        subcarrier_count=64,
        extracted_features={
            "amplitude_variance": 8.95,
            "phase_variance": 1.34,
            "presence_detected": True
        },
        inferred_activity_id=3,  # Walking
        model_confidence=0.95
    ))
    # Seed fall warning event in Recreation Room
    session.add(SensingEvent(
        device_id=dev_ec3.id,
        room_id=rm_recreation.id,
        timestamp=now - timedelta(minutes=1),
        rssi=-48,
        subcarrier_count=64,
        extracted_features={
            "amplitude_variance": 89.45,
            "phase_variance": 14.89,
            "presence_detected": True
        },
        inferred_activity_id=5,  # Fall_Detected
        model_confidence=0.99
    ))
    session.commit()

    # 12. Seed Alerts (Historical Audit Trails)
    # Incident 1: Devassy Varghese (Resolved)
    alert_1 = Alert(
        room_id=rm_room_101.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="resolved",
        message="Critical Fall Warning: Devassy Varghese detected horizontal fall stance in Resident Room 101",
        created_at=now - timedelta(hours=3),
        resolved_at=now - timedelta(hours=2, minutes=45)
    )
    session.add(alert_1)
    session.commit()
    session.refresh(alert_1)

    resolve_1 = AlertAcknowledgement(
        alert_id=alert_1.id,
        user_id=abhinanth_user.id,
        acknowledged_at=now - timedelta(hours=2, minutes=58),
        resolved_at=now - timedelta(hours=2, minutes=45),
        resolution_notes="Resident assisted. Devassy Varghese was sitting on the floor but unhurt. Safely helped back to armchair."
    )
    session.add(resolve_1)

    # Incident 2: Annamma Joseph (Resolved)
    alert_2 = Alert(
        room_id=rm_room_102.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="resolved",
        message="Fall Stance Detected: Annamma Joseph in Resident Room 102",
        created_at=now - timedelta(hours=1),
        resolved_at=now - timedelta(minutes=45)
    )
    session.add(alert_2)
    session.commit()
    session.refresh(alert_2)

    resolve_2 = AlertAcknowledgement(
        alert_id=alert_2.id,
        user_id=mary_user.id,
        acknowledged_at=now - timedelta(minutes=45),
        resolved_at=now - timedelta(minutes=45),
        resolution_notes="Checked Resident Room 102. Resident was picking up a fallen book. False alarm resolved safely."
    )
    session.add(resolve_2)

    # Incident 3: K. C. Mathew (New Alert currently warning in header!)
    alert_3 = Alert(
        room_id=rm_recreation.id,
        event_type="Fall_Detected",
        severity="CRITICAL",
        status="new",
        message="Emergency Fall Event: K. C. Mathew in Recreation Center",
        created_at=now - timedelta(minutes=1)
    )
    session.add(alert_3)
    session.commit()

    # 12. Seed Family Members (emergency_contact) and AccessRequests
    # John Smith - Linked to Annamma Joseph (Approved)
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

    # Susan Varghese - Linked to Devassy Varghese (Pending)
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

