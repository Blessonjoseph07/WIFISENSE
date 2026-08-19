from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.models.entities import (
    Role, User, UserRole, Organization, Building, Floor, Room, 
    SensingDevice, Resident, ActivityType, SensingEvent, Alert, AlertAcknowledgement
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
    # 1. Seed Roles
    for name, role_id in ROLE_MAPPING.items():
        existing = session.get(Role, role_id)
        if not existing:
            new_role = Role(id=role_id, name=name)
            session.add(new_role)
    session.commit()

    # 2. Seed Activity Types
    for name, (act_id, category) in ACTIVITY_MAPPING.items():
        existing = session.get(ActivityType, act_id)
        if not existing:
            new_act = ActivityType(id=act_id, name=name, category=category)
            session.add(new_act)
    session.commit()

    # 3. Seed Organizations
    # Amal Jyothi College of Engineering (Corporate)
    org_ajce = session.exec(select(Organization).where(Organization.name == "Amal Jyothi College of Engineering")).first()
    if not org_ajce:
        org_ajce = Organization(name="Amal Jyothi College of Engineering", type="CORPORATE")
        session.add(org_ajce)
        session.commit()
        session.refresh(org_ajce)

    # WiFi Sense Research Lab (Elder Care)
    org_lab = session.exec(select(Organization).where(Organization.name == "WiFi Sense Research Lab")).first()
    if not org_lab:
        org_lab = Organization(name="WiFi Sense Research Lab", type="ELDER_CARE")
        session.add(org_lab)
        session.commit()
        session.refresh(org_lab)

    # 4. Seed Buildings
    bld_mca = session.exec(select(Building).where(Building.name == "MCA Block")).first()
    if not bld_mca:
        bld_mca = Building(organization_id=org_ajce.id, name="MCA Block", address="Kanjirappally, Kerala, India")
        session.add(bld_mca)
        session.commit()
        session.refresh(bld_mca)

    bld_res = session.exec(select(Building).where(Building.name == "Research Lab Block")).first()
    if not bld_res:
        bld_res = Building(organization_id=org_lab.id, name="Research Lab Block", address="Main Campus Block C")
        session.add(bld_res)
        session.commit()
        session.refresh(bld_res)

    # 5. Seed Floors
    flr_1 = session.exec(select(Floor).where(Floor.building_id == bld_mca.id).where(Floor.floor_number == 1)).first()
    if not flr_1:
        flr_1 = Floor(building_id=bld_mca.id, floor_number=1)
        session.add(flr_1)

    flr_2 = session.exec(select(Floor).where(Floor.building_id == bld_mca.id).where(Floor.floor_number == 2)).first()
    if not flr_2:
        flr_2 = Floor(building_id=bld_mca.id, floor_number=2)
        session.add(flr_2)

    flr_elder_1 = session.exec(select(Floor).where(Floor.building_id == bld_res.id).where(Floor.floor_number == 1)).first()
    if not flr_elder_1:
        flr_elder_1 = Floor(building_id=bld_res.id, floor_number=1)
        session.add(flr_elder_1)

    session.commit()
    session.refresh(flr_1)
    session.refresh(flr_2)
    session.refresh(flr_elder_1)

    # 6. Seed Rooms
    # Corporate rooms (AJCE)
    rm_mca_lab = session.exec(select(Room).where(Room.name == "MCA Lab")).first()
    if not rm_mca_lab:
        rm_mca_lab = Room(floor_id=flr_1.id, name="MCA Lab", room_type="Conference Room", capacity=30)
        session.add(rm_mca_lab)

    rm_seminar_hall = session.exec(select(Room).where(Room.name == "Seminar Hall")).first()
    if not rm_seminar_hall:
        rm_seminar_hall = Room(floor_id=flr_2.id, name="Seminar Hall", room_type="Conference Room", capacity=150)
        session.add(rm_seminar_hall)

    # Elder care rooms (Research Lab Block)
    rm_res_lab = session.exec(select(Room).where(Room.name == "Research Lab")).first()
    if not rm_res_lab:
        rm_res_lab = Room(floor_id=flr_elder_1.id, name="Research Lab", room_type="Resident Bedroom", capacity=10)
        session.add(rm_res_lab)

    rm_project_room = session.exec(select(Room).where(Room.name == "Project Room")).first()
    if not rm_project_room:
        rm_project_room = Room(floor_id=flr_elder_1.id, name="Project Room", room_type="Resident Bedroom", capacity=6)
        session.add(rm_project_room)

    rm_bed_1 = session.exec(select(Room).where(Room.name == "Resident Bedroom 1")).first()
    if not rm_bed_1:
        rm_bed_1 = Room(floor_id=flr_elder_1.id, name="Resident Bedroom 1", room_type="Resident Bedroom", capacity=2)
        session.add(rm_bed_1)

    session.commit()
    session.refresh(rm_mca_lab)
    session.refresh(rm_seminar_hall)
    session.refresh(rm_res_lab)
    session.refresh(rm_project_room)
    session.refresh(rm_bed_1)

    # 7. Seed System Users (Devs and Caregivers)
    admin_email = "blesson@wifisense.com"
    blesson_user = session.exec(select(User).where(User.email == admin_email)).first()
    if not blesson_user:
        blesson_user = User(
            email=admin_email,
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

    manager_email = "abhinand@wifisense.com"
    abhinand_user = session.exec(select(User).where(User.email == manager_email)).first()
    if not abhinand_user:
        abhinand_user = User(
            email=manager_email,
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

    caregiver_email = "abhinanth@wifisense.com"
    abhinanth_user = session.exec(select(User).where(User.email == caregiver_email)).first()
    if not abhinanth_user:
        abhinanth_user = User(
            email=caregiver_email,
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
            building_id=bld_res.id
        ))
        session.commit()

    # 8. Seed Residents
    res_blesson = session.exec(select(Resident).where(Resident.first_name == "Blesson")).first()
    if not res_blesson:
        res_blesson = Resident(room_id=rm_res_lab.id, first_name="Blesson", last_name="Joseph Byju")
        session.add(res_blesson)

    res_abhinand = session.exec(select(Resident).where(Resident.first_name == "Abhinand")).first()
    if not res_abhinand:
        res_abhinand = Resident(room_id=rm_mca_lab.id, first_name="Abhinand", last_name="M A")
        session.add(res_abhinand)

    res_abhinanth = session.exec(select(Resident).where(Resident.first_name == "Abhinanth")).first()
    if not res_abhinanth:
        res_abhinanth = Resident(room_id=rm_project_room.id, first_name="Abhinanth", last_name="S Pillai")
        session.add(res_abhinanth)
    session.commit()

    # 9. Seed Devices
    # Corporate devices (presence tracking)
    dev_1 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:AA:BB:CC")).first()
    if not dev_1:
        dev_1 = SensingDevice(
            mac_address="4C:75:25:AA:BB:CC",
            room_id=rm_mca_lab.id,
            device_status="ONLINE",
            firmware_version="ESP32-CSI-01",
            last_seen_at=datetime.utcnow()
        )
        session.add(dev_1)

    dev_3 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:11:22:33")).first()
    if not dev_3:
        dev_3 = SensingDevice(
            mac_address="4C:75:25:11:22:33",
            room_id=rm_seminar_hall.id,
            device_status="ONLINE",
            firmware_version="WiFiSense-Node-01",
            last_seen_at=datetime.utcnow()
        )
        session.add(dev_3)

    # Elder-care devices (fall detection alerts)
    dev_2 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:DD:EE:FF")).first()
    if not dev_2:
        dev_2 = SensingDevice(
            mac_address="4C:75:25:DD:EE:FF",
            room_id=rm_res_lab.id,
            device_status="ONLINE",
            firmware_version="ESP32-CSI-02",
            last_seen_at=datetime.utcnow()
        )
        session.add(dev_2)

    dev_4 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:55:66:77")).first()
    if not dev_4:
        dev_4 = SensingDevice(
            mac_address="4C:75:25:55:66:77",
            room_id=rm_project_room.id,
            device_status="ONLINE",
            firmware_version="ESP32-CSI-03",
            last_seen_at=datetime.utcnow()
        )
        session.add(dev_4)

    dev_5 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:88:99:00")).first()
    if not dev_5:
        dev_5 = SensingDevice(
            mac_address="4C:75:25:88:99:00",
            room_id=rm_bed_1.id,
            device_status="ONLINE",
            firmware_version="ESP32-CSI-04",
            last_seen_at=datetime.utcnow()
        )
        session.add(dev_5)

    session.commit()
    session.refresh(dev_1)
    session.refresh(dev_2)
    session.refresh(dev_3)
    session.refresh(dev_4)
    session.refresh(dev_5)

    # 10. Seed Sensing Events
    # A. Corporate Events (Strictly presence detection only - no falls)
    event_1 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_1.id)).first()
    if not event_1:
        event_1 = SensingEvent(
            device_id=dev_1.id,
            room_id=rm_mca_lab.id,
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            rssi=-42,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 0.352, "entropy_phase": 0.221},
            inferred_activity_id=ACTIVITY_MAPPING["Walking"][0],
            model_confidence=0.962
        )
        session.add(event_1)

    event_3 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_3.id)).first()
    if not event_3:
        event_3 = SensingEvent(
            device_id=dev_3.id,
            room_id=rm_seminar_hall.id,
            timestamp=datetime.utcnow() - timedelta(minutes=12),
            rssi=-45,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 0.28, "entropy_phase": 0.19},
            inferred_activity_id=ACTIVITY_MAPPING["Sitting"][0],
            model_confidence=0.932
        )
        session.add(event_3)

    # B. Elder-care Events (Fall events)
    event_2 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_2.id)).first()
    if not event_2:
        event_2 = SensingEvent(
            device_id=dev_2.id,
            room_id=rm_res_lab.id,
            timestamp=datetime.utcnow() - timedelta(minutes=30),
            rssi=-48,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 1.45, "entropy_phase": 0.65},
            inferred_activity_id=ACTIVITY_MAPPING["Fall_Detected"][0],
            model_confidence=0.985
        )
        session.add(event_2)

    event_4 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_4.id)).first()
    if not event_4:
        event_4 = SensingEvent(
            device_id=dev_4.id,
            room_id=rm_project_room.id,
            timestamp=datetime.utcnow() - timedelta(minutes=2),
            rssi=-50,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 1.62, "entropy_phase": 0.72},
            inferred_activity_id=ACTIVITY_MAPPING["Fall_Detected"][0],
            model_confidence=0.991
        )
        session.add(event_4)

    event_5 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_5.id)).first()
    if not event_5:
        event_5 = SensingEvent(
            device_id=dev_5.id,
            room_id=rm_bed_1.id,
            timestamp=datetime.utcnow() - timedelta(hours=2),
            rssi=-47,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 1.55, "entropy_phase": 0.68},
            inferred_activity_id=ACTIVITY_MAPPING["Fall_Detected"][0],
            model_confidence=0.978
        )
        session.add(event_5)

    session.commit()

    # 11. Seed Alerts (Elder-Care Only)
    # A. Resolved Fall Alert (Bedroom 1)
    alert_resolved = session.exec(select(Alert).where(Alert.room_id == rm_bed_1.id)).first()
    if not alert_resolved:
        alert_resolved = Alert(
            room_id=rm_bed_1.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room Resident Bedroom 1!",
            status="resolved",
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=1, minutes=45)
        )
        session.add(alert_resolved)
        session.commit()

        ack_1 = AlertAcknowledgement(
            alert_id=alert_resolved.id,
            user_id=blesson_user.id,
            acknowledged_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
            resolved_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            resolution_notes="Dispatched Research Lab block caregivers. Blesson Joseph Byju assisted the resident, verified it was a simulated test, and cleared the room."
        )
        session.add(ack_1)

    # B. Acknowledged Fall Alert (Research Lab)
    alert_ack = session.exec(select(Alert).where(Alert.room_id == rm_res_lab.id)).first()
    if not alert_ack:
        alert_ack = Alert(
            room_id=rm_res_lab.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room Research Lab!",
            status="acknowledged",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            updated_at=datetime.utcnow() - timedelta(minutes=25)
        )
        session.add(alert_ack)
        session.commit()

        ack_2 = AlertAcknowledgement(
            alert_id=alert_ack.id,
            user_id=abhinand_user.id,
            acknowledged_at=datetime.utcnow() - timedelta(minutes=25)
        )
        session.add(ack_2)

    # C. New Fall Alert (Project Room)
    alert_new = session.exec(select(Alert).where(Alert.room_id == rm_project_room.id)).first()
    if not alert_new:
        alert_new = Alert(
            room_id=rm_project_room.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room Project Room!",
            status="new",
            created_at=datetime.utcnow() - timedelta(minutes=2)
        )
        session.add(alert_new)

    session.commit()
