"""
Hardware link helper for the ESP32-S3 receiver (no packets are ever invented here).

  register   Create a LIVE device for your receiver's MAC and print its token ONCE (put it in the firmware).
  auth       Check the token is accepted WITHOUT sending any CSI: posts an intentionally empty batch, so
             HTTP 422 means "token ok, body rejected" and 401/403 means "token wrong".
  watch      Show what the server has really received from the device: packet rate, RSSI, loss, last packet age.

Examples
  python tools/hardware_link_check.py register --mac 24:0A:C4:12:34:56 --room "Research Lab 2 - Embedded CSI"
  python tools/hardware_link_check.py auth  --token TK-ESP32-...
  python tools/hardware_link_check.py watch --mac 24:0A:C4:12:34:56

Defaults use the seeded development accounts, so use it only against a local development API.
"""
import argparse
import functools
import json
import sys
import time
import urllib.error
import urllib.request


print = functools.partial(print, flush=True)  # noqa: A001  show progress immediately, also when piped


def call(api, path, method="GET", data=None, token=None, headers=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    h.update(headers or {})
    req = urllib.request.Request(api + path, data=json.dumps(data).encode() if data is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, None
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach {api}: {e.reason}")


def login(api, email, password):
    st, body = call(api, "/auth/login", "POST", {"email": email, "password": password})
    if st != 200:
        sys.exit(f"Login failed ({st}): {body}")
    return body["access_token"]


def find_device(api, token, mac):
    st, devs = call(api, "/devices", token=token)
    return next((d for d in devs or [] if d["mac_address"].lower() == mac.lower()), None)


def cmd_register(a):
    token = login(a.api, a.email, a.password)
    if find_device(a.api, token, a.mac):
        sys.exit(f"{a.mac} is already registered. Its token was shown once at registration; delete the device or use the "
                 f"token-regeneration action in the app's Devices page to get a new one.")
    st, rooms = call(a.api, "/rooms", token=token)
    room = next((r for r in rooms if a.room.lower() in r["name"].lower()), None)
    if not room:
        sys.exit("Room not found. Available: " + ", ".join(r["name"] for r in rooms))
    st, dev = call(a.api, "/devices", "POST", {"room_id": room["id"], "mac_address": a.mac, "device_status": "ONLINE",
                                               "firmware_version": a.firmware, "allowed_source": "live"}, token)
    if st != 201:
        sys.exit(f"Could not register ({st}): {dev}")
    print(f"Registered LIVE receiver {dev['mac_address']} in '{room['name']}'")
    print(f"device id : {dev['id']}")
    print(f"token     : {dev['hardware_token']}")
    print("Copy the token into the firmware now. It is not shown again.")


def cmd_auth(a):
    st, body = call(a.api, "/sensing/ingest", "POST", {"packets": []}, headers={"X-Device-Token": a.token})
    if st in (401, 403):
        print(f"REJECTED ({st}): the token is wrong, or the device is not in service.  {body}")
        sys.exit(1)
    if st == 422:
        print("OK: the server accepted the token (it only rejected the deliberately empty body). No data was stored.")
        return
    print(f"Unexpected answer {st}: {body}")
    sys.exit(1)


def cmd_watch(a):
    token = login(a.api, a.email, a.password)
    dev = find_device(a.api, token, a.mac)
    if not dev:
        sys.exit(f"No device with MAC {a.mac}. Run 'register' first.")
    print(f"Watching {dev['mac_address']} ({dev['allowed_source']}). Ctrl+C to stop.")
    after = 0
    try:
        while True:
            st, live = call(a.api, f"/sensing/devices/{dev['id']}/live?after_id={after}", token=token)
            if st != 200:
                sys.exit(f"Live endpoint answered {st}: {live}")
            after = live["latest_id"]
            s = live["stats"]
            if not live["has_data"]:
                print("no packets received yet - check Wi-Fi, IP, port, token and the firmware's HTTP status codes")
            else:
                last = live["last_seen_at"]
                print(f"[{live['mode']}] total={live['packets_total']} new={len(live['packets'])} rate={s['arrival_rate_hz']} Hz "
                      f"loss={s['packet_loss_pct']}% rssi={s['rssi_mean_dbm']} dBm snr={s['snr_db']} dB "
                      f"variation={s['amplitude_variation']} ch={live['link']['channel']} last_seen={last}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nstopped")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--email", default="abhinand@wifisense.com")
    ap.add_argument("--password", default="abhinandpassword")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("--mac", required=True)
    r.add_argument("--room", default="Research Lab 2 - Embedded CSI")
    r.add_argument("--firmware", default="esp32-s3 csi rx")
    r.set_defaults(fn=cmd_register)
    au = sub.add_parser("auth")
    au.add_argument("--token", required=True)
    au.set_defaults(fn=cmd_auth)
    w = sub.add_parser("watch")
    w.add_argument("--mac", required=True)
    w.set_defaults(fn=cmd_watch)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
