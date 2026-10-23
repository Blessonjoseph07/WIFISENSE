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
CACHE_SECONDS = 1.5

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


PRESENCE_BLOCKS = 12        # about 12 seconds: presence is a sustained level, not a single spike
PRESENCE_SIGMA = 2.0
PRESENCE_RATIO = 1.15


def classify(blocks: List[float], baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """State from the latest blocks against the empty-room baseline: MOVEMENT (clearly above), PRESENT (held above the empty level
    for several seconds), QUIET (close to the empty-room level)."""
    if not blocks:
        return {"state": "NO_DATA", "headline": "No readings yet", "detail": "The board has not sent enough readings.",
                "activity_ratio": None}
    if not baseline:
        return {"state": "NO_BASELINE", "headline": "Not calibrated", "activity_ratio": None,
                "detail": "Record a baseline while the room is empty and still, then presence and movement can be told apart from quiet."}
    mean, std, thr = baseline["mean"], baseline["std"], baseline["threshold"]
    latest = blocks[-RECENT_BLOCKS:]
    over = sum(1 for v in latest if v > thr)
    moving = over >= max(1, (len(latest) + 1) // 2) and latest[-1] > thr * 0.9
    recent = blocks[-PRESENCE_BLOCKS:]
    level = float(np.median(recent))
    ratio = round(level / mean, 2) if mean > 0 else None
    present = len(recent) >= 6 and level > max(mean + PRESENCE_SIGMA * std, mean * PRESENCE_RATIO)
    if moving:
        return {"state": "MOVEMENT", "headline": "Movement on the link", "activity_ratio": ratio,
                "detail": "The signal is fluctuating well above the empty-room baseline, so something is moving in the room."}
    if present:
        return {"state": "PRESENT", "headline": "Presence likely", "activity_ratio": ratio,
                "detail": "The signal has stayed above the empty-room level for the last several seconds, so the room is probably "
                          "occupied even though little is moving."}
    return {"state": "QUIET", "headline": "Quiet", "activity_ratio": ratio,
            "detail": "The signal is close to the empty-room level. A person standing completely still could look like this too."}


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
