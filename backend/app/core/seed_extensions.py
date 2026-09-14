from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid

from app.models.entities import (
    EmergencyContact, Doctor, HospitalVisit, LabReport, Prescription,
    FamilyConnection, FamilySubscription, RoomCalibration, RoomSchedule,
    Resident, Room, User, SensingEvent, Alert
)

def populate_master_extensions(session: Session, now: datetime):
    # Retrieve existing entities
    all_residents = session.exec(select(Resident)).all()
    res_map = {f"{r.first_name} {r.last_name}": r for r in all_residents}
    
    all_rooms = session.exec(select(Room)).all()
    room_map = {r.name: r for r in all_rooms}

    all_users = session.exec(select(User)).all()
    user_map = {u.email: u for u in all_users}

    # =========================================================================
    # 1. EMERGENCY CONTACTS (EVERY RESIDENT MUST HAVE >= 1 EMERGENCY CONTACT)
    # =========================================================================
    emergency_contacts_data = [
        # Annamma Joseph
        ("Annamma Joseph", "John Joseph", "Son", "+91 94471 28934", 1, "john.joseph@gmail.com", "24/7 Primary Response"),
        ("Annamma Joseph", "Sarah Kurian", "Daughter", "+91 98462 11090", 2, "sarah.k@gmail.com", "On-Call Evenings & Weekends"),
        
        # Mary Joseph
        ("Mary Joseph", "Anna Joseph", "Daughter", "+91 98470 12345", 1, "anna.j@gmail.com", "24/7 Primary Care"),
        ("Mary Joseph", "Robert Lang", "Son-in-law", "+91 98470 99881", 2, "robert.lang@gmail.com", "Secondary Contact"),
        
        # Devassy Varghese
        ("Devassy Varghese", "Susan Varghese", "Daughter", "+91 94460 78901", 1, "susan.v@gmail.com", "24/7 Primary Response"),
        
        # K. C. Mathew
        ("K. C. Mathew", "David Mathew", "Son", "+91 98950 23456", 1, "david.m@gmail.com", "24/7 Primary Response"),
        
        # Rosamma Thomas
        ("Rosamma Thomas", "Grace Thomas", "Daughter", "+91 97440 34567", 1, "grace.t@gmail.com", "24/7 Primary Response"),
        
        # George Philip
        ("George Philip", "Philip George", "Son", "+91 94472 45678", 1, "philip.g@gmail.com", "24/7 Primary Response"),
        
        # Mariamma Kuruvilla
        ("Mariamma Kuruvilla", "Jacob Kuruvilla", "Son", "+91 98463 56789", 1, "jacob.k@gmail.com", "24/7 Primary Response"),
        
        # Thomas Varkey
        ("Thomas Varkey", "Reji Varkey", "Son", "+91 94473 67890", 1, "reji.v@gmail.com", "24/7 Primary Response"),
        
        # Saramma Chacko
        ("Saramma Chacko", "Chacko Paul", "Son", "+91 98951 78901", 1, "chacko.p@gmail.com", "24/7 Primary Response"),
        
        # Abraham Joseph
        ("Abraham Joseph", "Joseph Abraham", "Son", "+91 97441 89012", 1, "joseph.a@gmail.com", "24/7 Primary Response"),
        
        # Thresia Augustine
        ("Thresia Augustine", "Augustine George", "Son", "+91 94474 90123", 1, "augustine.g@gmail.com", "24/7 Primary Response"),
        
        # Joseph Anthony
        ("Joseph Anthony", "Anthony Joseph", "Son", "+91 98464 01234", 1, "anthony.j@gmail.com", "24/7 Primary Response"),
        
        # Varghese Mathai
        ("Varghese Mathai", "Mathai Varghese", "Son", "+91 94475 12345", 1, "mathai.v@gmail.com", "24/7 Primary Response"),
        
        # Aleyamma Paul
        ("Aleyamma Paul", "Paul Varghese", "Son", "+91 98952 23456", 1, "paul.v@gmail.com", "24/7 Primary Response"),
    ]

    for res_name, c_name, rel, phone, prio, email, avail in emergency_contacts_data:
        res = res_map.get(res_name)
        if res:
            contact = EmergencyContact(
                resident_id=res.id,
                name=c_name,
                relationship=rel,
                phone=phone,
                priority=prio,
                email=email,
                availability=avail,
                created_at=now - timedelta(days=100)
            )
            session.add(contact)
    session.commit()

    # =========================================================================
    # 2. STRUCTURED MEDICAL RECORDS (PHASE 2)
    # =========================================================================
    # Doctors
    doctors_data = [
        ("Annamma Joseph", "Dr. K. M. Mathew", "Geriatric Cardiology", "St. Thomas Hospital", "+91 4828 251999", "km.mathew@stthomashospital.org"),
        ("Annamma Joseph", "Dr. Philip Mathew", "Endocrinology", "Pushpagiri Medical Centre", "+91 469 2700755", "p.mathew@pushpagiri.org"),
        ("K. C. Mathew", "Dr. George Varghese", "Neurology", "Caritas Hospital", "+91 481 2790025", "george.v@caritas.org"),
        ("Devassy Varghese", "Dr. Anjali Thomas", "Geriatric Medicine", "Mary Queens Hospital", "+91 4828 252000", "anjali.t@maryqueens.org"),
        ("Thomas Varkey", "Dr. Joseph Kurian", "Orthopedic Surgery", "Pushpagiri Medical College", "+91 469 2700760", "j.kurian@pushpagiri.org"),
        ("Rosamma Thomas", "Dr. Elizabeth Kurian", "Cardiology", "St. Peter's Health Centre", "+91 4828 251122", "elizabeth@wifisense.com")
    ]
    for res_name, doc_name, spec, hosp, phone, email in doctors_data:
        res = res_map.get(res_name)
        if res:
            doc = Doctor(resident_id=res.id, name=doc_name, specialty=spec, hospital=hosp, phone=phone, email=email)
            session.add(doc)

    # Hospital Visits
    visits_data = [
        ("Annamma Joseph", "St. Thomas Hospital", "Geriatric Cardiology Routine Review & 12-lead ECG", now - timedelta(days=22), now - timedelta(days=22), "Sinus rhythm intact. BP 128/82 mmHg. Vitals stable. Continue Amlodipine 5mg."),
        ("Annamma Joseph", "Pushpagiri Medical Centre", "Endocrine Diabetic Retinopathy follow-up", now - timedelta(days=65), now - timedelta(days=65), "No macular edema observed. Glycemic target maintained."),
        ("K. C. Mathew", "Caritas Hospital", "Parkinson's Motor Assessment & Tremor Evaluation", now - timedelta(days=35), now - timedelta(days=35), "Tremor controlled under current Levodopa regimen. Prescribed assistive walker for wet bathroom transfers."),
        ("Thomas Varkey", "Pushpagiri Medical College", "Total Knee Arthroplasty 6-month postoperative review", now - timedelta(days=50), now - timedelta(days=50), "Implant stable. Knee flexion reached 115 degrees. Active physiotherapy prescribed.")
    ]
    for res_name, hosp, reason, v_date, d_date, notes in visits_data:
        res = res_map.get(res_name)
        if res:
            visit = HospitalVisit(resident_id=res.id, hospital_name=hosp, reason=reason, visit_date=v_date, discharge_date=d_date, doctor_notes=notes)
            session.add(visit)

    # Lab Reports
    labs_data = [
        ("Annamma Joseph", "Glycated Hemoglobin (HbA1c)", now - timedelta(days=18), "6.4%", "4.0 - 5.6%", "ELEVATED"),
        ("Annamma Joseph", "Complete Blood Count (CBC)", now - timedelta(days=18), "Hb: 12.8 g/dL, WBC: 6,200/uL, Platelets: 235k/uL", "Normal adult geriatric range", "NORMAL"),
        ("Annamma Joseph", "Serum Electrolytes", now - timedelta(days=18), "Na+: 138 mEq/L, K+: 4.3 mEq/L, Cl-: 102 mEq/L", "135 - 145 mEq/L", "NORMAL"),
        ("K. C. Mathew", "Serum Creatinine & Blood Urea", now - timedelta(days=30), "Creatinine: 1.05 mg/dL, BUN: 18 mg/dL", "0.7 - 1.3 mg/dL", "NORMAL"),
        ("Devassy Varghese", "Uric Acid & ESR", now - timedelta(days=24), "Uric Acid: 5.8 mg/dL, ESR: 14 mm/hr", "3.5 - 7.2 mg/dL", "NORMAL"),
        ("Rosamma Thomas", "Lipid Profile Screen", now - timedelta(days=40), "Total Cholesterol: 182 mg/dL, HDL: 52 mg/dL, LDL: 104 mg/dL", "< 200 mg/dL", "NORMAL")
    ]
    for res_name, test, t_date, summary, n_range, flag in labs_data:
        res = res_map.get(res_name)
        if res:
            lab = LabReport(resident_id=res.id, test_name=test, test_date=t_date, result_summary=summary, normal_range=n_range, flag=flag)
            session.add(lab)

    # Prescriptions
    rx_data = [
        ("Annamma Joseph", "Amlodipine Besylate", "5 mg", "Once daily in the morning", now - timedelta(days=180), None, "Dr. K. M. Mathew"),
        ("Annamma Joseph", "Metformin Hydrochloride", "500 mg", "Twice daily after meals", now - timedelta(days=365), None, "Dr. Philip Mathew"),
        ("Annamma Joseph", "Latanoprost Ophthalmic Solution", "0.005%", "1 drop in each eye at bedtime", now - timedelta(days=90), None, "Dr. Philip Mathew"),
        ("K. C. Mathew", "Levodopa / Carbidopa", "100 mg / 25 mg", "One tablet thrice daily before meals", now - timedelta(days=120), None, "Dr. George Varghese"),
        ("Devassy Varghese", "Glucosamine Sulphate", "750 mg", "Twice daily with meals for joint support", now - timedelta(days=60), None, "Dr. Anjali Thomas"),
        ("Rosamma Thomas", "Metoprolol Succinate", "25 mg", "Once daily in the morning", now - timedelta(days=90), None, "Dr. Elizabeth Kurian")
    ]
    for res_name, med, dose, freq, s_date, e_date, doc_n in rx_data:
        res = res_map.get(res_name)
        if res:
            rx = Prescription(resident_id=res.id, medication_name=med, dosage=dose, frequency=freq, start_date=s_date, end_date=e_date, prescribing_doctor=doc_n)
            session.add(rx)

    session.commit()

    # =========================================================================
    # 3. FAMILY CONNECTIONS & SUBSCRIPTIONS (PHASE 3, 3A, 3B)
    # =========================================================================
    blesson_user = user_map.get("blesson@wifisense.com")
    admin_id = blesson_user.id if blesson_user else None

    family_links = [
        ("john@wifisense.com", "Annamma Joseph", "Son", "approved", now - timedelta(days=30), now - timedelta(days=29), "ACTIVE"),
        ("anna@wifisense.com", "Mary Joseph", "Daughter", "approved", now - timedelta(days=45), now - timedelta(days=44), "ACTIVE"),
        ("robert@wifisense.com", "Mary Joseph", "Son-in-law", "approved", now - timedelta(days=25), now - timedelta(days=24), "ACTIVE"),
        ("david@wifisense.com", "K. C. Mathew", "Son", "approved", now - timedelta(days=20), now - timedelta(days=19), "ACTIVE"),
        ("susan@wifisense.com", "Devassy Varghese", "Daughter", "pending", now - timedelta(days=2), None, "PENDING"),
        ("grace@wifisense.com", "Rosamma Thomas", "Daughter", "pending", now - timedelta(days=1), None, "PENDING")
    ]

    for user_email, res_name, rel, c_status, req_at, app_at, sub_status in family_links:
        u = user_map.get(user_email)
        res = res_map.get(res_name)
        if u and res:
            conn = FamilyConnection(
                id=str(uuid.uuid4()),
                resident_id=res.id,
                family_user_id=u.id,
                relationship=rel,
                status=c_status,
                requested_at=req_at,
                approved_at=app_at,
                approved_by=admin_id if app_at else None,
                notes=f"Family access verification completed by Care Facility Manager." if app_at else "Verification pending document review."
            )
            session.add(conn)
            session.commit()
            session.refresh(conn)

            sub = FamilySubscription(
                id=str(uuid.uuid4()),
                family_user_id=u.id,
                family_connection_id=conn.id,
                plan="CARE_MONTHLY",
                status=sub_status,
                start_date=req_at if sub_status == "ACTIVE" else None,
                renewal_date=now + timedelta(days=15) if sub_status == "ACTIVE" else None
            )
            session.add(sub)
    session.commit()

    # =========================================================================
    # 4. ROOM CALIBRATIONS (PHASE 7.2 & 7.5 - RUVIEW REFERENCE)
    # =========================================================================
    for r in all_rooms:
        cal = RoomCalibration(
            id=str(uuid.uuid4()),
            room_id=r.id,
            baseline_status="VALID",
            baseline_captured_at=now - timedelta(hours=6),
            noise_floor_dbm=-88,
            baseline_rssi=-48,
            rf_similarity_pct=96.8,
            rf_environment_status="NORMAL",
            subcarrier_profile={"subcarriers": 56, "pilot_indices": [7, 21, 35, 49], "baseline_variance": 0.038}
        )
        session.add(cal)
    session.commit()

    # =========================================================================
    # 5. CORPORATE ROOM SCHEDULES & ENERGY EFFICIENCY (PHASE 8.1 & 8.2)
    # =========================================================================
    # rm_conf_a = Board Meeting Room A: Expected FREE between 14:00-15:00 while AC is ON
    rm_conf_a = room_map.get("Board Meeting Room A")
    if rm_conf_a:
        session.add(RoomSchedule(
            room_id=rm_conf_a.id,
            day_of_week="ALL",
            start_time="14:00",
            end_time="15:00",
            expected_status="FREE",
            meeting_title="Reserved Maintenance & Open Buffer",
            organizer="Central Facility Desk",
            ac_state="ON"
        ))

    # Computer Lab 1: After-hours lockdown
    rm_lab1 = room_map.get("Advanced Computing Lab 1")
    if rm_lab1:
        session.add(RoomSchedule(
            room_id=rm_lab1.id,
            day_of_week="ALL",
            start_time="00:00",
            end_time="06:00",
            expected_status="AFTER_HOURS_CLOSED",
            meeting_title="Overnight Lab Lockdown",
            organizer="Campus Security",
            ac_state="OFF"
        ))

    # MCA Seminar Hall: After-hours lockdown
    rm_sem = room_map.get("Department Seminar & Presentation Hall")
    if rm_sem:
        session.add(RoomSchedule(
            room_id=rm_sem.id,
            day_of_week="ALL",
            start_time="00:00",
            end_time="06:00",
            expected_status="AFTER_HOURS_CLOSED",
            meeting_title="Overnight Security Lockdown",
            organizer="Campus Security",
            ac_state="OFF"
        ))
    session.commit()

    # =========================================================================
    # 6. VERIFY RESIDENT ROOM 204 FALL EMERGENCY (PHASE 5)
    # =========================================================================
    rm_204 = room_map.get("Resident Room 204")
    res_annamma = res_map.get("Annamma Joseph")
    if rm_204 and res_annamma:
        res_annamma.room_id = rm_204.id
        session.add(res_annamma)
        session.commit()

        # Add immediate active fall alert
        fall_alert = session.exec(
            select(Alert).where(Alert.room_id == rm_204.id, Alert.event_type == "Fall_Detected", Alert.status == "new")
        ).first()
        if not fall_alert:
            fall_alert = Alert(
                room_id=rm_204.id,
                event_type="Fall_Detected",
                severity="CRITICAL",
                status="new",
                message="EMERGENCY FALL DETECTED: Annamma Joseph sudden stance collapse in Resident Room 204",
                created_at=now - timedelta(seconds=42)
            )
            session.add(fall_alert)
            session.commit()

        # Add latest fall sensing event
        session.add(SensingEvent(
            device_id="24:0A:C4:00:20:08", # dev_ec_204 mac or device id
            room_id=rm_204.id,
            timestamp=now - timedelta(seconds=42),
            rssi=-42,
            subcarrier_count=56,
            signal_quality=94,
            event_type="FallDetected",
            extracted_features={"rapid_stance_drop": True, "floor_plane_proximity": 0.97, "subject": "Annamma Joseph", "doppler_shift_hz": 4.8},
            inferred_activity_id=5, # Fall_Detected
            model_confidence=0.975
        ))
        session.commit()

    print("[WIFISENSE MASTER EXTENSIONS] Seeded emergency contacts, structured medical, family connections, subscriptions, calibrations, and schedules.")
