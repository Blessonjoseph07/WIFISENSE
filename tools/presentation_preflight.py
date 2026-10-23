#!/usr/bin/env python3
"""
Run this 10-15 minutes before presenting the hosted demo. It wakes the free API, checks it answers fast and
repeatedly, and checks the frontend and CORS, so a cold start never happens in front of the audience.

  python tools/presentation_preflight.py --api https://wifisense-api.onrender.com --web https://wifisense-ecru.vercel.app

It sends no credentials and writes nothing. Exit code 0 = ready, 1 = not ready (the reason is printed).
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def get(url, headers=None, timeout=90, method="GET"):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace"), dict(r.headers), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), dict(e.headers), time.time() - t0
    except Exception as e:  # noqa: BLE001
        return 0, str(e), {}, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", required=True)
    ap.add_argument("--web", required=True)
    a = ap.parse_args()
    api, web = a.api.rstrip("/"), a.web.rstrip("/")
    problems = []

    print("1. Waking the API (a sleeping free instance can take up to a minute) ...")
    for i in range(1, 9):
        st, body, _, secs = get(api + "/health")
        print(f"   try {i}: HTTP {st} in {secs:.1f}s")
        if st == 200:
            break
        time.sleep(8)
    else:
        problems.append("the API never answered /health with 200")
    try:
        h = json.loads(body)
        print(f"   status={h.get('status')} database={h.get('database')} model={h.get('detection_model')} env={h.get('environment')}")
        if h.get("status") != "ok" or h.get("database") != "ok":
            problems.append(f"health is not ok: {h}")
    except ValueError:
        problems.append("/health did not return JSON")

    print("2. Ten quick requests in a row (all must be fast and succeed) ...")
    times = []
    for _ in range(10):
        st, _, _, secs = get(api + "/health", timeout=30)
        times.append(secs)
        if st != 200:
            problems.append(f"a /health request returned {st}")
        time.sleep(0.5)
    print(f"   median {sorted(times)[5]:.2f}s, slowest {max(times):.2f}s")
    if max(times) > 5:
        problems.append(f"one request took {max(times):.1f}s (over 5s)")

    print("3. The website ...")
    st, body, _, secs = get(web)
    print(f"   HTTP {st} in {secs:.1f}s")
    if st != 200 or "Wi-Fi Sense" not in body:
        problems.append("the website did not return the Wi-Fi Sense page")

    print("4. Browser access (CORS) from the website to the API ...")
    st, _, hdr, _ = get(api + "/auth/login", {"Origin": web, "Access-Control-Request-Method": "POST",
                                              "Access-Control-Request-Headers": "content-type"}, method="OPTIONS")
    allowed = {k.lower(): v for k, v in hdr.items()}.get("access-control-allow-origin")
    print(f"   HTTP {st}, allowed origin: {allowed}")
    if allowed != web:
        problems.append(f"the API does not allow {web} (ALLOWED_ORIGINS in Render must be exactly that address)")

    print()
    if problems:
        print("NOT READY:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("READY. Keep the browser tab open and log in once before the audience arrives.")


if __name__ == "__main__":
    main()
