import React, { useCallback, useEffect, useRef, useState } from "react";

const sub = "bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl";

const STATES = {
  QUIET: { label: "No presence", tone: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300", icon: "sensors_off" },
  PRESENT: { label: "Presence detected", tone: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200", icon: "groups" },
  MOVEMENT: { label: "Presence detected, moving", tone: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200", icon: "directions_walk" },
  NO_BASELINE: { label: "Not calibrated", tone: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200", icon: "tune" },
  STALE: { label: "Board not sending", tone: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200", icon: "signal_disconnected" },
  NO_DATA: { label: "No readings yet", tone: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200", icon: "hourglass_empty" },
};

/**
 * Movement on the Wi-Fi link between the two boards, from the device's own packets (GET /sensing/devices/{id}/movement).
 * It never says "person detected": it says the signal is fluctuating more or less than in an empty, still room, and states the limits.
 */
export default function MovementIndicator({ deviceId, authToken, API_BASE }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  // One dropped request must not turn the box red: keep the last good reading, never stack requests, give each one a time limit,
  // and only report a problem after several failures in a row.
  const inFlight = useRef(false);
  const failures = useRef(0);
  const [lastOk, setLastOk] = useState(null);

  const load = useCallback(async () => {
    if (!deviceId || inFlight.current) return;
    inFlight.current = true;
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 8000);
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/movement`, {
        headers: { Authorization: `Bearer ${authToken}` }, signal: ctl.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      failures.current = 0;
      setLastOk(Date.now());
      setError(null);
    } catch (e) {
      failures.current += 1;
      if (failures.current >= 3) {
        setError(`The connection to the server is unstable (${e.name === "AbortError" ? "no answer in 8 s" : e.message}). Retrying; the reading below is the last one received.`);
      }
    } finally {
      clearTimeout(timer);
      inFlight.current = false;
    }
  }, [deviceId, API_BASE, authToken]);

  useEffect(() => {
    setData(null);
    failures.current = 0;
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [load]);

  const record = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/movement/baseline`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 403) throw new Error("Only a system administrator or facility manager can record the baseline.");
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setMessage({ ok: true, text: "Baseline recorded. Movement is now judged against this empty-room reference." });
      load();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  };

  if (!deviceId) return null;
  const meta = STATES[data?.state] || STATES.NO_DATA;
  const blocks = data?.blocks || [];
  const thr = data?.threshold;
  const top = Math.max(...blocks, thr || 0, 0.001) * 1.15;

  return (
    <div className={`${sub} p-4 space-y-3`} data-testid="movement-indicator">
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-sm font-bold text-slate-900 dark:text-white">Is anything moving near the board?</div>
        <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full ${meta.tone}`} data-testid="movement-state">
          <span className="material-symbols-outlined text-[16px]">{meta.icon}</span>
          {meta.label}
        </span>
      </div>

      {error && <div className="text-xs text-rose-600">{error}</div>}
      {data && <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{data.headline}. {data.detail}</p>}
      {data?.reference === "default" && data.state !== "STALE" && (
        <p className="text-[11px] text-slate-500" data-testid="default-reference-note">
          Using the default reference, from a quiet-room recording with these boards. For the best accuracy in this room, record an empty-room
          baseline below.
        </p>
      )}
      {data?.reference === "room" && data?.activity_ratio != null && data.activity_ratio < 0.75 && data.state !== "STALE" && (
        <div className="text-xs rounded-lg px-3 py-2 bg-amber-50 text-amber-900 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-900" data-testid="baseline-suspect">
          The signal is well <strong>below</strong> the empty-room reference ({data.activity_ratio}×). A real empty room cannot be quieter than itself,
          so the baseline was most likely recorded while people were in the room, and every reading is being judged against the wrong reference.
          Record the baseline again when the room is empty.
        </div>
      )}
      {data?.activity_ratio != null && data.state !== "STALE" && (
        <p className="text-[11px] text-slate-500" data-testid="activity-level">
          Signal activity is <strong>{data.activity_ratio}×</strong> the empty-room level (1× = the empty room).
        </p>
      )}

      {blocks.length > 0 && data?.state !== "STALE" && (
        <div>
          <div className="relative h-16 flex items-end gap-1" role="img"
               aria-label="Signal fluctuation per second, newest on the right. The dashed line is the movement threshold.">
            {data?.baseline?.mean ? <div className="absolute left-0 right-0 border-t border-emerald-500/60" style={{ bottom: `${(data.baseline.mean / top) * 100}%` }} title="empty-room level" /> : null}
            {thr ? <div className="absolute left-0 right-0 border-t border-dashed border-slate-400/70" style={{ bottom: `${(thr / top) * 100}%` }} title="movement threshold" /> : null}
            {blocks.map((v, i) => (
              <div key={i} className="flex-1 min-w-[4px] rounded-t"
                   title={`fluctuation ${v}`}
                   style={{ height: `${Math.max(4, (v / top) * 100)}%`, background: thr ? (v > thr ? "#f59e0b" : "#10b981") : "#94a3b8" }} />
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>about {blocks.length} seconds ago</span>
            <span>{thr ? "green line = empty room, dashed line = movement" : "no reference yet, so the bars are not judged"}</span>
            <span>now</span>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {!confirming ? (
          <button type="button" onClick={() => { setConfirming(true); setMessage(null); }}
                  className="px-3 py-1.5 border rounded-full text-[11px] font-bold uppercase hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-white dark:border-slate-700">
            {data?.baseline ? "Record the baseline again" : "Record empty-room baseline"}
          </button>
        ) : (
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-700 dark:text-slate-200">
            <span>Leave the room and keep it still for about 15 seconds, then confirm.</span>
            <button type="button" disabled={busy} onClick={record}
                    className="px-3 py-1.5 bg-teal-600 text-white rounded-full text-[11px] font-bold uppercase disabled:opacity-50">
              {busy ? "Recording..." : "Room is empty: record"}
            </button>
            <button type="button" onClick={() => setConfirming(false)} className="text-[11px] underline text-slate-500">Cancel</button>
          </div>
        )}
        {data?.baseline && (
          <span className="text-[11px] text-slate-500">
            Reference recorded {new Date(data.baseline.captured_at).toLocaleString()} from {data.baseline.blocks} seconds of readings.
          </span>
        )}
      </div>
      {message && <div className={`text-xs ${message.ok ? "text-emerald-700 dark:text-emerald-300" : "text-rose-600"}`}>{message.text}</div>}

      {data?.caveats && (
        <ul className="list-disc pl-4 text-[11px] text-slate-500 space-y-0.5">
          {data.caveats.map((c) => <li key={c}>{c}</li>)}
        </ul>
      )}
    </div>
  );
}
