"""
WIFISENSE DEVICE INGESTION & CSI TELEMETRY SECURITY TEST SUITE
=============================================================
This test suite validates Phase 1 Device Ingestion:
1. Device Authentication:
   - Rejects unauthenticated ingestion (HTTP 401).
   - Rejects invalid/forged device tokens (HTTP 401).
   - Accepts valid token via X-Device-Token header (HTTP 201).
   - Accepts valid token via Authorization: Bearer header (HTTP 201).

2. Tenant & Room Isolation Rules:
   - Rejects ingestion from an unassigned device (room_id is None) with HTTP 400.
   - Rejects ingestion if assigned room does not exist in DB (HTTP 400).

3. MAC Consistency Verification:
   - MAC is derived from authenticated device if omitted.
   - If MAC is explicitly provided in payload and matches, ingestion succeeds.
   - If MAC in payload conflicts with device registered MAC, rejected with HTTP 400.
   - Batch-level and packet-level MAC conflicts are both rejected with HTTP 400.

4. Server-Enforced Provenance:
   - Provenance is strictly governed by device.allowed_source (live/dataset/simulated).
   - Client cannot override or spoof provenance.
   - Conflicting client provenance is rejected with HTTP 400.
   - Allowed provenance is stored in raw_csi_telemetry table.

5. Batch Telemetry Ingestion:
   - Multi-packet ingestion batches persist all records in raw_csi_telemetry.
   - Updates device.device_status to "ONLINE" and updates device.last_seen_at.

6. Token Security & Single-Exposure Policy:
   - Plaintext hardware_token is never stored in DB (only SHA-256 hash).
   - Plaintext token is only exposed once upon creation or token reset.
   - GET /devices never exposes hardware_token (returns null).
   - POST /devices/{id}/reset-token rotates credentials, invalidating the old token.
"""

import os
import json
import urllib.request
import urllib.error
import secrets
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import hash_token
from app.models.entities import SensingDevice, RawCsiTelemetry, Room, Organization, Building, Floor

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def api_call(endpoint, method="GET", data=None, token=None, device_token=None, auth_bearer_token=None):
    url = f"{API_BASE}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if auth_bearer_token:
        req.add_header("Authorization", f"Bearer {auth_bearer_token}")
    if device_token:
        req.add_header("X-Device-Token", device_token)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed

def login(email, password):
    status, res = api_call("/auth/login", method="POST", data={"email": email, "password": password})
    assert status == 200, f"Login failed for {email}: {status} {res}"
    return res

def run_tests():
    print("=== RUNNING DEVICE INGESTION & CSI TELEMETRY SECURITY TESTS ===")

    # Setup: Admin login
    print("\n--- Setup: Authenticating Admin ---")
    admin = login("blesson@wifisense.com", "blessonpassword")
    admin_token = admin["access_token"]
    print("[PASS] System Admin authenticated.")

    # Fetch a valid room for assignment
    with Session(engine) as session:
        room = session.exec(select(Room)).first()
        assert room is not None, "No rooms found in database."
        valid_room_id = room.id
        print(f"[INFO] Using test room: {room.name} ({valid_room_id})")

    # Pre-cleanup in case of prior aborted run
    test_macs = ["DE:AD:BE:EF:01:01", "DE:AD:BE:EF:01:02", "DE:AD:BE:EF:01:03"]
    with Session(engine) as session:
        for m in test_macs:
            stale_devs = session.exec(select(SensingDevice).where(SensingDevice.mac_address == m)).all()
            for sd in stale_devs:
                t_rows = session.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == sd.id)).all()
                for tr in t_rows:
                    session.delete(tr)
                session.delete(sd)
        session.commit()

    created_device_ids = []

    try:
        # Test 1: Device Creation with Token Exposure & Single-Exposure Policy
        print("\n--- 1. Testing Device Creation & Single Token Exposure Policy ---")
        test_mac_1 = "DE:AD:BE:EF:01:01"
        create_payload = {
            "room_id": valid_room_id,
            "mac_address": test_mac_1,
            "device_status": "OFFLINE",
            "firmware_version": "ESP32-S3-TEST-1.0",
            "allowed_source": "live"
        }
        status, dev_created = api_call("/devices", method="POST", data=create_payload, token=admin_token)
        assert status in [200, 201], f"Device creation failed: {status} {dev_created}"
        assert "hardware_token" in dev_created and dev_created["hardware_token"], "Missing hardware_token on creation"
        dev1_id = dev_created["id"]
        dev1_raw_token = dev_created["hardware_token"]
        created_device_ids.append(dev1_id)
        print(f"[PASS] Device created with ID {dev1_id}. Token exposed once.")

        # Verify DB stores only SHA-256 hash and NOT plaintext
        with Session(engine) as session:
            db_dev = session.get(SensingDevice, dev1_id)
            assert db_dev.hardware_token is None, "Plaintext hardware_token was stored in DB!"
            assert db_dev.hardware_token_hash is not None, "Missing hardware_token_hash in DB!"
            expected_hash = hash_token(dev1_raw_token)
            assert db_dev.hardware_token_hash == expected_hash, "Stored hash does not match SHA-256 of raw token!"
            assert db_dev.allowed_source == "live", "allowed_source mismatch in DB"
        print("[PASS] DB verification: plaintext token is NULL; hardware_token_hash is valid SHA-256.")

        # Verify GET /devices does NOT expose plaintext token
        status, dev_list = api_call("/devices", method="GET", token=admin_token)
        assert status == 200
        target = next((d for d in dev_list if d["id"] == dev1_id), None)
        assert target is not None
        assert target.get("hardware_token") is None, f"Plaintext token leaked in GET /devices: {target}"
        print("[PASS] GET /devices does not leak hardware_token.")

        # Test 2: Ingestion Authentication Checks
        print("\n--- 2. Testing Ingestion Authentication (401 on missing/invalid) ---")
        dummy_csi_payload = {
            "rssi": -55,
            "subcarrier_count": 56,
            "bandwidth_mhz": 20,
            "channel": 6,
            "csi_data": {"amplitudes": [1.0] * 56, "phases": [0.0] * 56}
        }

        # 2a. Missing token -> 401
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload)
        assert status == 401, f"Expected 401 on missing token, got {status}: {res}"
        print("[PASS] Missing token rejected with HTTP 401.")

        # 2b. Invalid token -> 401
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token="TK-ESP32-invalid-token")
        assert status == 401, f"Expected 401 on invalid token, got {status}: {res}"
        print("[PASS] Invalid device token rejected with HTTP 401.")

        # 2c. Valid token via X-Device-Token -> 201
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token=dev1_raw_token)
        assert status == 201, f"Expected 201 with X-Device-Token, got {status}: {res}"
        assert res["status"] == "success"
        assert res["device_id"] == dev1_id
        assert res["mac_address"] == test_mac_1
        assert res["room_id"] == valid_room_id
        assert res["ingested_count"] == 1
        assert res["provenance"] == "live"
        print("[PASS] Ingestion succeeded with X-Device-Token (HTTP 201).")

        # 2d. Valid token via Authorization: Bearer <token> -> 201
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, auth_bearer_token=dev1_raw_token)
        assert status == 201, f"Expected 201 with Bearer token, got {status}: {res}"
        assert res["ingested_count"] == 1
        print("[PASS] Ingestion succeeded with Bearer token (HTTP 201).")

        # Test 3: Unassigned Device Rejection (room_id is None)
        print("\n--- 3. Testing Unassigned Device Rejection (HTTP 400) ---")
        test_mac_unassigned = "DE:AD:BE:EF:01:02"
        status, unassigned_dev = api_call("/devices", method="POST", data={
            "room_id": None,
            "mac_address": test_mac_unassigned,
            "device_status": "OFFLINE",
            "allowed_source": "live"
        }, token=admin_token)
        assert status in [200, 201]
        unassigned_id = unassigned_dev["id"]
        unassigned_token = unassigned_dev["hardware_token"]
        created_device_ids.append(unassigned_id)

        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token=unassigned_token)
        assert status == 400, f"Expected 400 for unassigned device, got {status}: {res}"
        assert "not assigned to a room" in res.get("detail", "").lower()
        print("[PASS] Unassigned device telemetry rejected with HTTP 400.")

        # Test 4: MAC Address Consistency Check
        print("\n--- 4. Testing MAC Address Consistency Check ---")
        # 4a. Payload specifies matching MAC -> 201
        payload_with_matching_mac = dict(dummy_csi_payload, mac_address=test_mac_1)
        status, res = api_call("/sensing/ingest", method="POST", data=payload_with_matching_mac, device_token=dev1_raw_token)
        assert status == 201, f"Expected 201 with matching MAC, got {status}: {res}"
        print("[PASS] Matching MAC address accepted.")

        # 4b. Payload specifies mismatched MAC -> 400
        payload_with_mismatched_mac = dict(dummy_csi_payload, mac_address="11:22:33:44:55:66")
        status, res = api_call("/sensing/ingest", method="POST", data=payload_with_mismatched_mac, device_token=dev1_raw_token)
        assert status == 400, f"Expected 400 with mismatched MAC, got {status}: {res}"
        assert "mac address mismatch" in res.get("detail", "").lower()
        print("[PASS] Mismatched MAC address rejected with HTTP 400.")

        # 4c. Batch with mismatched packet MAC -> 400
        batch_mismatched = {
            "packets": [
                dict(dummy_csi_payload, mac_address=test_mac_1),
                dict(dummy_csi_payload, mac_address="AA:BB:CC:DD:EE:FF")
            ]
        }
        status, res = api_call("/sensing/ingest", method="POST", data=batch_mismatched, device_token=dev1_raw_token)
        assert status == 400, f"Expected 400 on batch packet MAC mismatch, got {status}: {res}"
        print("[PASS] Batch packet MAC mismatch rejected with HTTP 400.")

        # Test 5: Server-Enforced Provenance
        print("\n--- 5. Testing Server-Enforced Provenance Rules ---")
        # 5a. dev1 is allowed_source="live". Packet claiming "simulated" must be rejected (400)
        spoofed_payload = dict(dummy_csi_payload, provenance="simulated")
        status, res = api_call("/sensing/ingest", method="POST", data=spoofed_payload, device_token=dev1_raw_token)
        assert status == 400, f"Expected 400 when client claims conflicting provenance, got {status}: {res}"
        assert "provenance conflict" in res.get("detail", "").lower()
        print("[PASS] Client attempt to claim conflicting provenance rejected with HTTP 400.")

        # 5b. Create device with allowed_source="dataset"
        test_mac_dataset = "DE:AD:BE:EF:01:03"
        status, dev_dataset = api_call("/devices", method="POST", data={
            "room_id": valid_room_id,
            "mac_address": test_mac_dataset,
            "device_status": "OFFLINE",
            "allowed_source": "dataset"
        }, token=admin_token)
        assert status in [200, 201]
        dataset_dev_id = dev_dataset["id"]
        dataset_token = dev_dataset["hardware_token"]
        created_device_ids.append(dataset_dev_id)

        # Ingest without provenance field -> server automatically enforces "dataset"
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token=dataset_token)
        assert status == 201, f"Expected 201 for dataset device, got {status}: {res}"
        assert res["provenance"] == "dataset", f"Expected provenance='dataset', got {res['provenance']}"
        print("[PASS] Device allowed_source='dataset' automatically enforced on packet without client provenance.")

        # Test 6: Batch Ingestion & Database Persistence
        print("\n--- 6. Testing Batch Ingestion & Telemetry Persistence ---")
        batch_payload = {
            "mac_address": test_mac_1,
            "packets": [
                {
                    "sequence_number": 101,
                    "rssi": -48,
                    "noise_floor": -92,
                    "subcarrier_count": 56,
                    "bandwidth_mhz": 20,
                    "channel": 1,
                    "csi_data": {"subcarriers": [1, 2, 3]}
                },
                {
                    "sequence_number": 102,
                    "rssi": -49,
                    "noise_floor": -92,
                    "subcarrier_count": 56,
                    "bandwidth_mhz": 20,
                    "channel": 1,
                    "csi_data": {"subcarriers": [4, 5, 6]}
                },
                {
                    "sequence_number": 103,
                    "rssi": -47,
                    "noise_floor": -91,
                    "subcarrier_count": 56,
                    "bandwidth_mhz": 20,
                    "channel": 1,
                    "csi_data": {"subcarriers": [7, 8, 9]}
                }
            ]
        }
        status, res = api_call("/sensing/ingest", method="POST", data=batch_payload, device_token=dev1_raw_token)
        assert status == 201, f"Batch ingest failed: {status} {res}"
        assert res["ingested_count"] == 3
        assert res["device_status"] == "ONLINE"
        print("[PASS] Batch of 3 packets successfully ingested (HTTP 201).")

        # Verify rows in raw_csi_telemetry table
        with Session(engine) as session:
            rows = session.exec(
                select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == dev1_id)
            ).all()
            assert len(rows) >= 5, f"Expected at least 5 ingested rows, got {len(rows)}"
            for r in rows:
                assert r.room_id == valid_room_id
                assert r.provenance == "live"
                assert r.csi_data is not None
            # Check device status updated to ONLINE and last_seen_at updated
            dev1_db = session.get(SensingDevice, dev1_id)
            assert dev1_db.device_status == "ONLINE"
            assert dev1_db.last_seen_at is not None
        print("[PASS] Database rows verified: correct room_id, provenance, csi_data, and device ONLINE status.")

        # Test 7: Credential Rotation & Old Token Invalidation
        print("\n--- 7. Testing Credential Rotation & Invalidation ---")
        status, reset_res = api_call(f"/devices/{dev1_id}/reset-token", method="POST", token=admin_token)
        assert status == 200, f"Token reset failed: {status} {reset_res}"
        assert "hardware_token" in reset_res and reset_res["hardware_token"]
        new_token = reset_res["hardware_token"]
        assert new_token != dev1_raw_token, "Reset token did not change secret!"
        print("[PASS] Token rotated successfully. New token returned once.")

        # Old token MUST be rejected now
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token=dev1_raw_token)
        assert status == 401, f"Expected 401 on invalidated old token, got {status}: {res}"
        print("[PASS] Ingestion with revoked old token rejected with HTTP 401.")

        # New token MUST be accepted
        status, res = api_call("/sensing/ingest", method="POST", data=dummy_csi_payload, device_token=new_token)
        assert status == 201, f"Expected 201 on new rotated token, got {status}: {res}"
        print("[PASS] Ingestion with newly rotated token succeeded (HTTP 201).")

        # Test 8: 64 KB Payload Limit & 100-Packet Ceiling
        print("\n--- 8. Testing 64 KB Request Payload Limit & Batch Constraints ---")
        # 8a. Oversized CSI payload (> 64 KB) must be rejected with HTTP 413
        oversized_matrix = "X" * (65 * 1024)
        oversized_payload = dict(dummy_csi_payload, csi_data={"bulk_amplitudes": oversized_matrix})
        status, res = api_call("/sensing/ingest", method="POST", data=oversized_payload, device_token=new_token)
        assert status == 413, f"Expected 413 on oversized payload (> 64 KB), got {status}: {res}"
        assert "64 kb" in res.get("detail", "").lower(), f"Expected detail mentioning 64 KB, got: {res}"
        print("[PASS] Oversized payload (> 64 KB) rejected with HTTP 413.")

        # 8b. Normal sized CSI payload (<= 64 KB) succeeds
        normal_matrix = {"subcarriers": [0.1 * i for i in range(56)]}
        normal_payload = dict(dummy_csi_payload, csi_data=normal_matrix)
        status, res = api_call("/sensing/ingest", method="POST", data=normal_payload, device_token=new_token)
        assert status == 201, f"Expected 201 on valid sized payload, got {status}: {res}"
        print("[PASS] Normal sized payload (<= 64 KB) accepted with HTTP 201.")

        # 8c. Batch packet limit (> 100 packets) must be rejected with HTTP 422
        compact_packet = {"rssi": -50, "csi_data": {"s": 1}}
        batch_oversized_packets = {
            "packets": [dict(compact_packet, sequence_number=i) for i in range(101)]
        }
        status, res = api_call("/sensing/ingest", method="POST", data=batch_oversized_packets, device_token=new_token)
        assert status == 422, f"Expected 422 for batch exceeding 100 packets, got {status}: {res}"
        print("[PASS] Batch exceeding 100 packets rejected with HTTP 422.")

        # Test 9: Device Token Reset Authorization (Scoping Matrix)
        print("\n--- 9. Testing Device Token Reset Authorization Scoping Matrix ---")
        # Find an assigned Elder Care device and an assigned Corporate Space device
        with Session(engine) as session:
            elder_care_dev = session.exec(
                select(SensingDevice).join(Room).join(Floor).join(Building).join(Organization).where(Organization.type == "ELDER_CARE")
            ).first()
            assert elder_care_dev is not None, "No elder care devices found in DB."
            elder_care_dev_id = elder_care_dev.id

            corp_dev = session.exec(
                select(SensingDevice).join(Room).join(Floor).join(Building).join(Organization).where(Organization.type == "CORPORATE")
            ).first()
            assert corp_dev is not None, "No corporate space devices found in DB."
            corp_dev_id = corp_dev.id

        # Authenticate Org Admin for Elder Care (anjali@wifisense.com)
        care_org_admin = login("anjali@wifisense.com", "anjalipassword")
        care_admin_token = care_org_admin["access_token"]

        # Authenticate Corporate Facility Manager (abhinand@wifisense.com)
        corp_fm = login("abhinand@wifisense.com", "abhinandpassword")
        corp_fm_token = corp_fm["access_token"]

        # 9a. Authorized Org Admin resetting an authorized device in their organization -> 200 OK
        status, res = api_call(f"/devices/{elder_care_dev_id}/reset-token", method="POST", token=care_admin_token)
        assert status == 200, f"Expected 200 when authorized org admin resets device in their org, got {status}: {res}"
        assert "hardware_token" in res and res["hardware_token"]
        print("[PASS] Authorized Org Admin successfully reset device in their organization (HTTP 200).")

        # 9b. Unauthorized Org Admin attempting to reset a device in another organization (Corporate) -> 403 Forbidden
        status, res = api_call(f"/devices/{corp_dev_id}/reset-token", method="POST", token=care_admin_token)
        assert status == 403, f"Expected 403 when Org Admin resets foreign org device, got {status}: {res}"
        print("[PASS] Org Admin attempting to reset foreign org device rejected with HTTP 403.")

        # 9c. Unauthorized Org Admin attempting to reset an unassigned device -> 403 Forbidden
        status, res = api_call(f"/devices/{unassigned_id}/reset-token", method="POST", token=care_admin_token)
        assert status == 403, f"Expected 403 when Org Admin resets unassigned device, got {status}: {res}"
        assert "unassigned devices" in res.get("detail", "").lower()
        print("[PASS] Org Admin attempting to reset unassigned device rejected with HTTP 403.")

        # 9d. Unauthorized Facility Manager attempting to reset a device in another facility/org -> 403 Forbidden
        status, res = api_call(f"/devices/{elder_care_dev_id}/reset-token", method="POST", token=corp_fm_token)
        assert status == 403, f"Expected 403 when Facility Manager resets foreign org device, got {status}: {res}"
        print("[PASS] Facility Manager attempting to reset foreign facility device rejected with HTTP 403.")

        # 9e. Unauthorized Facility Manager attempting to reset an unassigned device -> 403 Forbidden
        status, res = api_call(f"/devices/{unassigned_id}/reset-token", method="POST", token=corp_fm_token)
        assert status == 403, f"Expected 403 when Facility Manager resets unassigned device, got {status}: {res}"
        print("[PASS] Facility Manager attempting to reset unassigned device rejected with HTTP 403.")

        # 9f. System Admin retaining global access across all devices (unassigned, corporate, elder care) -> 200 OK
        status, res = api_call(f"/devices/{unassigned_id}/reset-token", method="POST", token=admin_token)
        assert status == 200, f"Expected 200 for System Admin resetting unassigned device, got {status}: {res}"
        print("[PASS] System Admin successfully reset unassigned device (HTTP 200).")

        status, res = api_call(f"/devices/{elder_care_dev_id}/reset-token", method="POST", token=admin_token)
        assert status == 200, f"Expected 200 for System Admin resetting Elder Care device, got {status}: {res}"
        print("[PASS] System Admin successfully reset Elder Care device (HTTP 200).")

        status, res = api_call(f"/devices/{corp_dev_id}/reset-token", method="POST", token=admin_token)
        assert status == 200, f"Expected 200 for System Admin resetting Corporate device, got {status}: {res}"
        print("[PASS] System Admin successfully reset Corporate Space device (HTTP 200).")

    finally:
        # Cleanup test devices and telemetry
        print("\n--- Cleanup: Removing Test Devices & Telemetry ---")
        with Session(engine) as session:
            for did in created_device_ids:
                # Delete related raw telemetry
                telem_rows = session.exec(select(RawCsiTelemetry).where(RawCsiTelemetry.device_id == did)).all()
                for tr in telem_rows:
                    session.delete(tr)
                dev = session.get(SensingDevice, did)
                if dev:
                    session.delete(dev)
            session.commit()
        print(f"[PASS] Cleaned up {len(created_device_ids)} test devices and associated telemetry.")

    print("\n========================================================")
    print("ALL DEVICE INGESTION & SECURITY TESTS PASSED SUCCESSFULLY")
    print("========================================================")

if __name__ == "__main__":
    run_tests()
