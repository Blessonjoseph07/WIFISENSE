"""
Delivery metrics for /sensing/ingest: how long the server took, how old the packets were when they arrived, and what
the device-side bridge itself measured for its previous request.

Kept in memory per device (the last MAX_BATCHES requests), so it costs nothing in the database and resets when the
process restarts. With several server instances each reports its own traffic. These are operational numbers for
people watching a deployment, not part of any clinical record.

ingest_delay_ms is (server clock at arrival) - (packet timestamp set by the bridge when it read the packet). It
therefore includes the bridge's batching wait, queueing and network time, and it is only as accurate as the two
clocks agree. It is reported as measured, never adjusted.
"""
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

MAX_BATCHES = 200

_lock = threading.Lock()
_batches: Dict[str, Deque[Dict[str, Any]]] = defaultdict(lambda: deque(maxlen=MAX_BATCHES))


def record(device_id: str, packets: int, server_ms: float, delay_oldest_ms: Optional[float],
           delay_newest_ms: Optional[float], client_rtt_ms: Optional[float], client_queue: Optional[int],
           client_dropped: Optional[int] = None) -> None:
    with _lock:
        _batches[device_id].append({
            "t": datetime.now(timezone.utc).timestamp(), "packets": packets, "server_ms": server_ms,
            "delay_oldest_ms": delay_oldest_ms, "delay_newest_ms": delay_newest_ms,
            "client_rtt_ms": client_rtt_ms, "client_queue": client_queue, "client_dropped": client_dropped,
        })


def _pct(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    v = sorted(values)
    return round(v[min(len(v) - 1, int(round(q * (len(v) - 1))))], 1)


def summary(device_id: str) -> Dict[str, Any]:
    with _lock:
        rows = list(_batches.get(device_id, ()))
    if not rows:
        return {"batches": 0, "note": "No delivery measurements yet (this server process has received nothing from this device)."}
    server = [r["server_ms"] for r in rows]
    delay = [r["delay_oldest_ms"] for r in rows if r["delay_oldest_ms"] is not None]
    rtt = [r["client_rtt_ms"] for r in rows if r["client_rtt_ms"] is not None]
    span = max(rows[-1]["t"] - rows[0]["t"], 1e-6)
    total = sum(r["packets"] for r in rows)
    last = rows[-1]
    return {
        "batches": len(rows),
        "packets": total,
        "avg_batch_size": round(total / len(rows), 1),
        "packets_per_second": round(total / span, 1) if len(rows) > 1 else None,
        "server_ms": {"p50": _pct(server, 0.5), "p95": _pct(server, 0.95), "max": round(max(server), 1)},
        "ingest_delay_ms": {"p50": _pct(delay, 0.5), "p95": _pct(delay, 0.95)} if delay else None,
        "client_rtt_ms": {"p50": _pct(rtt, 0.5), "p95": _pct(rtt, 0.95)} if rtt else None,
        "bridge_queue_depth": last["client_queue"],
        "bridge_packets_dropped": last["client_dropped"],
        "last_batch_at": datetime.fromtimestamp(last["t"], timezone.utc).isoformat(),
        "scope": "this server process, last %d requests" % MAX_BATCHES,
    }
