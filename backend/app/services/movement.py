"""
Movement on the Wi-Fi link between the two ESP32 boards, from real CSI packets.

What it measures: how much the signal's amplitude fluctuates over a short block of packets (the same "amplitude variation" the
live stream shows). When something moves through the room the multipath changes and that number rises.

What it can NOT do, and the API says so:
  * it does not count people, locate anyone or identify anyone, and one transmitter-receiver pair gives no position;
  * a person standing or lying completely still barely changes the signal, so "quiet" does not mean "empty";
  * a fan, a door, a pet or a person in the next room can also raise it.

It is only meaningful against a reference: an operator records a baseline while the room is empty and still, and a block counts
as movement only when it is clearly above that baseline. Without a baseline the state is NO_BASELINE and no judgement is made.
"""
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from app.services import csi_physics

BLOCK = 50                 # packets per measurement block (about one second at the radio's rate)
MIN_BASELINE_BLOCKS = 6    # a baseline needs at least this many blocks (about 6 seconds)
SIGMA = 4.0                # blocks above baseline mean + SIGMA * std ...
MIN_RATIO = 1.5            # ... and above baseline mean * MIN_RATIO count as movement
RECENT_BLOCKS = 3          # the state follows the latest blocks, so one noisy block does not flip it
# How long a computed reading is reused. The free hosted instance has a tenth of a CPU, and several panels plus the board
# poll every 1-2.5 s, so production reuses each result longer; set SENSING_CACHE_SECONDS to override.
CACHE_SECONDS = float(os.getenv("SENSING_CACHE_SECONDS") or ("3.0" if os.getenv("ENVIRONMENT", "").lower() == "production" else "1.5"))

_cache_lock = threading.Lock()
_cache: Dict[str, Any] = {}


def block_variations(records) -> List[float]:
    """Amplitude variation per block of BLOCK consecutive packets (oldest first). Packets without a usable I/Q are skipped."""
    amps = []
    for r in records:
        data = r.csi_data if isinstance(r.csi_data, dict) else {}
        ap = csi_physics.iq_to_amp_phase(data.get("iq"))
        if ap and ap.get("amplitude"):
            amps.append(ap["amplitude"])
    out = []
    for i in range(0, len(amps) - BLOCK + 1, BLOCK):
        a = np.asarray(amps[i:i + BLOCK], dtype=float)
        out.append(float((a.std(axis=0) / (a.mean(axis=0) + 1e-9)).mean()))
    return out


def baseline_from(blocks: List[float]) -> Optional[Dict[str, Any]]:
    if len(blocks) < MIN_BASELINE_BLOCKS:
        return None
    b = np.asarray(blocks, dtype=float)
    mean, std = float(b.mean()), float(b.std())
    return {
        "mean": round(mean, 5), "std": round(std, 5), "blocks": len(blocks), "max": round(float(b.max()), 5),
        "threshold": round(max(mean + SIGMA * std, mean * MIN_RATIO), 5),
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


# Reference used when nobody has recorded an empty-room baseline yet. It is the signal of this ESP32-S3 pair measured in a quiet room
# (hardware_test.db recording: 30 consecutive blocks, median 0.048, 90th percentile 0.053, maximum 0.067). A different room or placement
# can sit higher or lower, so it is labelled "default" everywhere and an operator baseline replaces it.
DEFAULT_REFERENCE = {"mean": 0.048, "std": 0.004, "threshold": 0.072, "blocks": None, "captured_at": None, "default": True}

PRESENCE_BLOCKS = 12        # about 12 seconds: presence is a sustained level, not a single spike
PRESENCE_SIGMA = 2.0
PRESENCE_RATIO = 1.15


def classify(blocks: List[float], baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """State from the latest blocks against the reference: MOVEMENT (clearly above: presence, moving), PRESENT (held above the empty level
    for several seconds: presence), QUIET (close to the empty level). With no operator baseline the DEFAULT_REFERENCE is used."""
    if not blocks:
        return {"state": "NO_DATA", "headline": "No readings yet", "detail": "The board has not sent enough readings.",
                "activity_ratio": None, "reference": None}
    using_default = not baseline
    ref = baseline or DEFAULT_REFERENCE
    mean, std, thr = ref["mean"], ref["std"], ref["threshold"]
    latest = blocks[-RECENT_BLOCKS:]
    over = sum(1 for v in latest if v > thr)
    moving = over >= max(1, (len(latest) + 1) // 2) and latest[-1] > thr * 0.9
    recent = blocks[-PRESENCE_BLOCKS:]
    level = float(np.median(recent))
    ratio = round(level / mean, 2) if mean > 0 else None
    present = len(recent) >= 6 and level > max(mean + PRESENCE_SIGMA * std, mean * PRESENCE_RATIO)
    out = {"activity_ratio": ratio, "reference": "default" if using_default else "room"}
    if moving:
        out.update(state="MOVEMENT", headline="Presence detected",
                   detail="The signal is fluctuating well above the empty-room level, so someone is in the room and moving.")
    elif present:
        out.update(state="PRESENT", headline="Presence detected",
                   detail="The signal has stayed above the empty-room level for the last several seconds, so the room is occupied.")
    else:
        out.update(state="QUIET", headline="No presence detected",
                   detail="The signal is close to the empty-room level. A person standing completely still could look like this too.")
    return out


def cached(key: str, builder):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    value = builder()
    with _cache_lock:
        _cache[key] = (now, value)
    return value
