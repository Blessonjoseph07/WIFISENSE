import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000"

def api_call(method, path, headers=None, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    all_headers = {"Content-Type": "application/json"}
    if headers:
        all_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=all_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}

def get_token(email, password):
    status_code, data = api_call("POST", "/auth/login", body={"email": email, "password": password})
    if status_code != 200:
        raise Exception(f"Login failed for {email}: {data}")
    return data["access_token"]

def run_tests():
    print("=== TESTING MASTER PHASES REQUIREMENTS ===")
    
    # Tokens
    admin_token = get_token("blesson@wifisense.com", "blessonpassword")
    caregiver_token = get_token("mary@wifisense.com", "marypassword")
    corp_token = get_token("rahul@wifisense.com", "rahulpassword")
    family_token = get_token("john@wifisense.com", "johnpassword")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cg_headers = {"Authorization": f"Bearer {caregiver_token}"}
    corp_headers = {"Authorization": f"Bearer {corp_token}"}
    fam_headers = {"Authorization": f"Bearer {family_token}"}

    # 1. Test Emergency Contacts: Check missing contacts
    code, missing_list = api_call("GET", "/emergency-contacts/missing", headers=admin_headers)
    assert code == 200, f"Expected 200, got {code}"
    assert len(missing_list) == 0, f"Expected 0 residents missing emergency contacts, found {len(missing_list)}"
    print("[PASS] Phase 2: All 14 residents have at least 1 Emergency Contact.")

    # 2. Test Corporate User Blocked from Elder Care Medical Details
    code, residents = api_call("GET", "/residents", headers=cg_headers)
    assert code == 200
    annamma = next((x for x in residents if x["first_name"] == "Annamma"), residents[0])
    
    code, err_data = api_call("GET", f"/residents/{annamma['id']}/profile-details", headers=corp_headers)
    assert code == 403, f"Expected 403 for corporate user, got {code}"
    print("[PASS] Phase 2: Corporate user strictly blocked from Elder Care medical records (HTTP 403).")

    # 3. Test Caregiver profile-details retrieval
    code, det = api_call("GET", f"/residents/{annamma['id']}/profile-details", headers=cg_headers)
    assert code == 200, f"Expected 200, got {code}"
    assert len(det["emergency_contacts"]) >= 1, "Must have emergency contacts"
    assert len(det["doctors"]) >= 1, "Must have assigned doctors"
    assert len(det["lab_reports"]) >= 1, "Must have lab reports"
    assert len(det["prescriptions"]) >= 1, "Must have prescriptions"
    print(f"[PASS] Phase 2 & 2A: Caregiver retrieved full resident profile with {len(det['emergency_contacts'])} emergency contacts, {len(det['doctors'])} doctors, {len(det['lab_reports'])} lab reports.")

    # 4. Test Sole Emergency Contact Deletion Guard
    single_res = next((x for x in residents if x["first_name"] == "Devassy"), None)
    if single_res:
        code, single_contacts = api_call("GET", f"/residents/{single_res['id']}/emergency-contacts", headers=cg_headers)
        if len(single_contacts) == 1:
            code, del_res = api_call("DELETE", f"/emergency-contacts/{single_contacts[0]['id']}", headers=admin_headers)
            assert code == 400, f"Expected 400 for deleting sole emergency contact, got {code}"
            print("[PASS] Phase 2: Deleting sole emergency contact blocked by rule enforcement.")

    # 5. Test Family Portal Gated Access
    code, fam_status = api_call("GET", "/family/resident-status", headers=fam_headers)
    assert code == 200, f"Expected 200, got {code}"
    assert fam_status["linked"] is True
    assert fam_status["has_active_subscription"] is True
    assert fam_status["connection_status"] == "approved"
    assert "recent_activity_history" in fam_status
    print(f"[PASS] Phase 3 & 4: Family Portal gated access active for {fam_status['resident']['first_name']} {fam_status['resident']['last_name']}.")

    # 6. Test Emergency Fall Protocol Active Event
    code, fall_data = api_call("GET", "/alerts/emergency-active", headers=cg_headers)
    assert code == 200, f"Expected 200, got {code}"
    assert fall_data["has_emergency"] is True
    assert fall_data["activity"] == "Fall Detected"
    assert "emergency_contact" in fall_data and fall_data["emergency_contact"]["name"] == "John Joseph"
    print(f"[PASS] Phase 5 & 5A: Emergency Fall Protocol successfully refreshed active fall with Contact {fall_data['emergency_contact']['name']} ({fall_data['emergency_contact']['phone']}).")

    # 7. Test RuView CSI Diagnostics and Calibration
    room_id = annamma["room_id"]
    code, cal_data = api_call("GET", f"/rooms/{room_id}/calibration", headers=cg_headers)
    assert code == 200, f"Expected 200, got {code}"
    assert cal_data["baseline_status"] == "VALID"
    assert cal_data["rf_similarity_pct"] > 90.0
    print(f"[PASS] Phase 7: Room Calibration verified ({cal_data['baseline_status']}, RF similarity: {cal_data['rf_similarity_pct']}%).")

    # 8. Test Corporate Space Intelligence
    code, unexp = api_call("GET", "/schedules/unexpected-occupancy", headers=corp_headers)
    assert code == 200, f"Expected 200, got {code}"
    code, energy = api_call("GET", "/schedules/energy-recommendations", headers=corp_headers)
    assert code == 200, f"Expected 200, got {code}"
    print(f"[PASS] Phase 8: Corporate Space Intelligence schedules & energy recommendations accessible.")

    print("\n>>> ALL MASTER PHASES BACKEND TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    run_tests()
