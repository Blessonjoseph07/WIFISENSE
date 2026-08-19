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

    # 3. Seed Primary User (Blesson Joseph Byju)
    admin_email = "blesson@wifisense.com"
    statement = select(User).where(User.email == admin_email)
    admin_user = session.exec(statement).first()
    
    if not admin_user:
        hashed_pwd = hash_password("blessonpassword")
        admin_user = User(
            email=admin_email,
            password_hash=hashed_pwd,
            first_name="Blesson",
            last_name="Joseph Byju",
            is_active=True
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        # Mapped to system_admin role
        admin_role_map = UserRole(
            user_id=admin_user.id,
            role_id=ROLE_MAPPING["system_admin"]
        )
        session.add(admin_role_map)
        session.commit()

    # 4. Seed Organizations
    org_ajce = session.exec(select(Organization).where(Organization.name == "Amal Jyothi College of Engineering")).first()
    if not org_ajce:
        org_ajce = Organization(name="Amal Jyothi College of Engineering", type="CORPORATE")
        session.add(org_ajce)
        session.commit()
        session.refresh(org_ajce)

    org_lab = session.exec(select(Organization).where(Organization.name == "WiFi Sense Research Lab")).first()
    if not org_lab:
        org_lab = Organization(name="WiFi Sense Research Lab", type="ELDER_CARE")
        session.add(org_lab)
        session.commit()
        session.refresh(org_lab)

    # 5. Seed Buildings
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

    # 6. Seed Floors
    flr_1 = session.exec(select(Floor).where(Floor.building_id == bld_mca.id).where(Floor.floor_number == 1)).first()
    if not flr_1:
        flr_1 = Floor(building_id=bld_mca.id, floor_number=1)
        session.add(flr_1)
        session.commit()
        session.refresh(flr_1)

    flr_2 = session.exec(select(Floor).where(Floor.building_id == bld_mca.id).where(Floor.floor_number == 2)).first()
    if not flr_2:
        flr_2 = Floor(building_id=bld_mca.id, floor_number=2)
        session.add(flr_2)
        session.commit()
        session.refresh(flr_2)

    # 7. Seed Rooms
    rm_mca_lab = session.exec(select(Room).where(Room.name == "MCA Lab")).first()
    if not rm_mca_lab:
        rm_mca_lab = Room(floor_id=flr_1.id, name="MCA Lab", room_type="Conference Room", capacity=30)
        session.add(rm_mca_lab)
        session.commit()
        session.refresh(rm_mca_lab)

    rm_res_lab = session.exec(select(Room).where(Room.name == "Research Lab")).first()
    if not rm_res_lab:
        rm_res_lab = Room(floor_id=flr_1.id, name="Research Lab", room_type="Resident Bedroom", capacity=10)
        session.add(rm_res_lab)
        session.commit()
        session.refresh(rm_res_lab)

    rm_project_room = session.exec(select(Room).where(Room.name == "Project Room")).first()
    if not rm_project_room:
        rm_project_room = Room(floor_id=flr_1.id, name="Project Room", room_type="Resident Bedroom", capacity=6)
        session.add(rm_project_room)
        session.commit()
        session.refresh(rm_project_room)

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

    dev_3 = session.exec(select(SensingDevice).where(SensingDevice.mac_address == "4C:75:25:11:22:33")).first()
    if not dev_3:
        dev_3 = SensingDevice(
            mac_address="4C:75:25:11:22:33",
            room_id=rm_project_room.id,
            device_status="OFFLINE",
            firmware_version="WiFiSense-Node-01",
            last_seen_at=datetime.utcnow() - timedelta(days=2)
        )
        session.add(dev_3)
    session.commit()

    # 10. Seed Sensing Events
    # Ensure there are recent events so dashboard renders realistically
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

    event_2 = session.exec(select(SensingEvent).where(SensingEvent.device_id == dev_2.id)).first()
    if not event_2:
        event_2 = SensingEvent(
            device_id=dev_2.id,
            room_id=rm_res_lab.id,
            timestamp=datetime.utcnow() - timedelta(minutes=10),
            rssi=-48,
            subcarrier_count=64,
            extracted_features={"variance_amplitude": 0.125, "entropy_phase": 0.118},
            inferred_activity_id=ACTIVITY_MAPPING["Sitting"][0],
            model_confidence=0.941
        )
        session.add(event_2)
    session.commit()

    # 11. Seed Alerts (Handful of alerts with different statuses)
    alert_1 = session.exec(select(Alert).where(Alert.room_id == rm_mca_lab.id)).first()
    if not alert_1:
        alert_1 = Alert(
            room_id=rm_mca_lab.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room MCA Lab!",
            status="resolved",
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=1, minutes=45)
        )
        session.add(alert_1)
        session.commit()

        ack_1 = AlertAcknowledgement(
            alert_id=alert_1.id,
            user_id=admin_user.id,
            acknowledged_at=datetime.utcnow() - timedelta(hours=1, minutes=58),
            resolved_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            resolution_notes="Dispatched first aid. Blesson Joseph Byju assisted the resident, verified it was a simulated test, and cleared the room."
        )
        session.add(ack_1)

    alert_2 = session.exec(select(Alert).where(Alert.room_id == rm_res_lab.id)).first()
    if not alert_2:
        alert_2 = Alert(
            room_id=rm_res_lab.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room Research Lab!",
            status="acknowledged",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            updated_at=datetime.utcnow() - timedelta(minutes=25)
        )
        session.add(alert_2)
        session.commit()

        ack_2 = AlertAcknowledgement(
            alert_id=alert_2.id,
            user_id=admin_user.id,
            acknowledged_at=datetime.utcnow() - timedelta(minutes=25)
        )
        session.add(ack_2)

    alert_3 = session.exec(select(Alert).where(Alert.room_id == rm_project_room.id)).first()
    if not alert_3:
        alert_3 = Alert(
            room_id=rm_project_room.id,
            event_type="Fall_Detected",
            severity="CRITICAL",
            message="Critical Fall Detected in Room Project Room!",
            status="new",
            created_at=datetime.utcnow() - timedelta(minutes=2)
        )
        session.add(alert_3)

    session.commit()
