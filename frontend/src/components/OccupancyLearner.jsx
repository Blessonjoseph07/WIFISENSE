import React, { useCallback, useEffect, useRef, useState } from "react";

const sub = "bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl";
const SECONDS = 30;

const INSTRUCTIONS = {
  empty: "Everyone leaves the area between the two boards.",
  still: "One person sits or lies still between the boards (on a chair or the bed), breathing normally.",
  walking: "One person walks back and forth between the boards at a normal pace.",
  few: "A few people (about 3 to 8) sit or move around normally.",
  busy: "A normal busy period with many people in the room.",
};
const COLORS = { empty: "#10b981", still: "#8b5cf6", walking: "#ec4899", few: "#0ea5e9", busy: "#f59e0b" };

/**
 * Phase 2 machine learning: teach the system what THIS room looks like (empty / someone still / someone walking / a few people /
 * busy) by recording short labelled segments, then it estimates the room state from the board's signal. It reports how well it did on recordings it had not seen.
 */
export default function OccupancyLearner({ deviceId, authToken, API_BASE }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [recording, setRecording] = useState(null);   // { label, left }
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const failures = useRef(0);
  const headers = { Authorization: `Bearer ${authToken}` };

  const load = useCallback(async () => {
    if (!deviceId || inFlight.current) return;
    inFlight.current = true;
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 8000);
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/occupancy`, { headers, signal: ctl.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
      failures.current = 0;
      setError(null);
    } catch (e) {
      failures.current += 1;
      if (failures.current >= 3) setError("The connection to the server is unstable. Retrying; what you see is the last answer received.");
    } finally {
      clearTimeout(timer);
      inFlight.current = false;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, API_BASE, authToken]);

  useEffect(() => {
    setData(null);
    failures.current = 0;
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, [load]);

  const post = async (path, body) => {
    const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}${path}`, {
      method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body || {}),
    });
    const out = await res.json().catch(() => ({}));
    if (res.status === 403) throw new Error("Only a system administrator or facility manager can do this.");
    if (!res.ok) throw new Error(out.detail || `HTTP ${res.status}`);
    return out;
  };

  const record = async (label) => {
    setMessage(null);
    for (let left = SECONDS; left > 0; left--) {
      setRecording({ label, left });
      await new Promise((r) => setTimeout(r, 1000));
    }
    setRecording({ label, left: 0 });
    try {
      const out = await post("/occupancy/capture", { label, seconds: SECONDS });
      setMessage({ ok: true, text: `Saved ${out.blocks_saved} blocks for "${label}".` });
      load();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setRecording(null);
    }
  };

  const train = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const out = await post("/occupancy/train");
      setMessage({ ok: out.evaluation.reliable, text: out.evaluation.reliable
        ? "Trained. It passed its own test on recordings it had not seen."
        : `Trained, but it is NOT reliable: ${out.evaluation.reason}.` });
      load();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    if (!window.confirm("Delete all recordings and the trained model for this board?")) return;
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/occupancy`, { method: "DELETE", headers });
      if (!res.ok) throw new Error(res.status === 403 ? "Only a system administrator or facility manager can do this." : `HTTP ${res.status}`);
      setMessage({ ok: true, text: "Cleared." });
      load();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    }
  };

  if (!deviceId) return null;
  const ev = data?.evaluation;
  const pred = data?.prediction;
  const idx = ev?.confusion?.labels || [];

  return (
    <details open className={`${sub} p-4`} data-testid="occupancy-learner">
      <summary className="cursor-pointer text-sm font-bold text-slate-900 dark:text-white">
        Learn this room <span className="ml-2 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300">machine learning</span>
      </summary>

      <div className="mt-3 space-y-4">
        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
          A model trained on someone else's data cannot know your classroom. So teach it: record about {SECONDS} seconds of each situation
          below, then press <strong>Train</strong>. It learns only from this room and this board position, and it tells you how well it did on
          recordings it had <em>not</em> used for learning. Record each situation once or twice for a better result.
        </p>

        <div className="space-y-2">
          {(data?.labels || []).map((l) => {
            const n = data.samples[l.id] || { sessions: 0, blocks: 0 };
            const active = recording?.label === l.id;
            return (
              <div key={l.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 dark:border-slate-700 p-2.5">
                <span className="w-3 h-3 rounded-full" style={{ background: COLORS[l.id] }} />
                <div className="min-w-[160px]">
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-100">{l.text}</div>
                  <div className="text-[11px] text-slate-500">{INSTRUCTIONS[l.id]}</div>
                </div>
                <div className="text-[11px] text-slate-500">{n.sessions} recording{n.sessions === 1 ? "" : "s"} · {n.blocks} blocks</div>
                <button type="button" disabled={!!recording}
                        onClick={() => record(l.id)}
                        className="ml-auto px-3 py-1.5 border rounded-full text-[11px] font-bold uppercase hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-white dark:border-slate-700 disabled:opacity-40">
                  {active ? `Recording... ${recording.left}s` : `Record ${SECONDS} s`}
                </button>
              </div>
            );
          })}
        </div>

        {recording && (
          <div className="text-xs rounded-lg px-3 py-2 bg-violet-50 text-violet-900 border border-violet-200 dark:bg-violet-950/30 dark:text-violet-200 dark:border-violet-900">
            Keep the room as described for <strong>{recording.left}</strong> more seconds: <strong>{INSTRUCTIONS[recording.label]}</strong>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <button type="button" disabled={busy || !data?.can_train || !!recording} onClick={train}
                  className="px-4 py-2 bg-teal-600 text-white rounded-full text-[11px] font-bold uppercase disabled:opacity-40">
            {busy ? "Training..." : "Train the model"}
          </button>
          <span className="text-[11px] text-slate-500">
            {data?.can_train ? "Ready to train." : `Record at least two situations, ${data?.min_blocks_per_label || 20}+ blocks each (one ${SECONDS}-second recording is enough).`}
          </span>
          {data?.samples && Object.values(data.samples).some((v) => v.blocks > 0) && (
            <button type="button" onClick={reset} className="ml-auto text-[11px] underline text-slate-500">Clear everything</button>
          )}
        </div>
        {data?.retrain_needed && (
          <div className="text-xs rounded-lg px-3 py-2 bg-amber-50 text-amber-900 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-900">
            The learner now also uses the shape of the signal, so recordings made before this update are ignored. Record each situation again, then train.
          </div>
        )}
        {message && <div className={`text-xs ${message.ok ? "text-emerald-700 dark:text-emerald-300" : "text-rose-600"}`}>{message.text}</div>}
        {error && <div className="text-xs text-amber-700">{error}</div>}

        {ev && (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 space-y-2" data-testid="occupancy-evaluation">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-100">How well did it do on recordings it had not seen?</span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${ev.reliable
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                : "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200"}`}>
                {ev.reliable ? "reliable enough" : "NOT reliable"}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              It was right on <strong>{Math.round(ev.heldout_accuracy * 100)}%</strong> of the held-out blocks. Just guessing the most common
              situation would give {Math.round(ev.majority_baseline * 100)}%.{ev.reason ? ` ${ev.reason}.` : ""}
            </p>
            <div className="overflow-x-auto">
              <table className="text-[11px] border-collapse">
                <thead>
                  <tr><th className="pr-3 text-left text-slate-400 font-normal">truth \ it said</th>{idx.map((l) => <th key={l} className="px-3 text-slate-500">{l}</th>)}</tr>
                </thead>
                <tbody>
                  {ev.confusion.matrix.map((row, i) => (
                    <tr key={idx[i]}>
                      <td className="pr-3 text-slate-500">{idx[i]}</td>
                      {row.map((v, j) => (
                        <td key={j} className={`px-3 text-center font-mono ${i === j ? "text-emerald-700 dark:text-emerald-300 font-bold" : "text-slate-500"}`}>{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-[10px] text-slate-400">{ev.note}</p>
          </div>
        )}

        {data?.trained && (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 space-y-2" data-testid="occupancy-prediction">
            <div className="text-xs font-bold text-slate-800 dark:text-slate-100">Current estimate for this room</div>
            {data.prediction_state === "READY" && pred ? (
              <>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-lg font-black" style={{ color: COLORS[pred.label] }} data-testid="occupancy-label">{pred.text}</span>
                  <span className="text-xs text-slate-500">{Math.round(pred.confidence * 100)}% sure, from the last {pred.blocks_used} seconds</span>
                </div>
                {Object.entries(pred.probabilities).map(([l, p]) => (
                  <div key={l} className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span className="w-14">{l}</span>
                    <div className="flex-1 h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden"><div className="h-full" style={{ width: `${p * 100}%`, background: COLORS[l] }} /></div>
                    <span className="w-9 text-right font-mono">{Math.round(p * 100)}%</span>
                  </div>
                ))}
                {!ev?.reliable && <div className="text-[11px] text-amber-700">This model did not pass its own test, so treat this as a guess, not a measurement.</div>}
              </>
            ) : (
              <div className="text-xs text-slate-500">{data.prediction_state === "NOT_SENDING" ? "The board is not sending, so there is no current estimate." : "Waiting for a few seconds of readings."}</div>
            )}
          </div>
        )}

        <ul className="list-disc pl-4 text-[11px] text-slate-500 space-y-0.5">
          {(data?.caveats || []).map((c) => <li key={c}>{c}</li>)}
        </ul>
      </div>
    </details>
  );
}
