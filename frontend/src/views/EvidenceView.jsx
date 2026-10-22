import React, { useCallback, useEffect, useState } from "react";
import { SourceBadge } from "../components/DetectionBadges";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";

const GRADES = {
  MEASURED: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  LIMITED: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  EXPERIMENTAL: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  OPEN: "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  NO: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
};
const GRADE_LABEL = { MEASURED: "MEASURED", LIMITED: "MEASURED, WITH LIMITS", EXPERIMENTAL: "EXPERIMENTAL", OPEN: "NOT MEASURED YET", NO: "NOT SUPPORTED" };

const pct = (x) => (x === null || x === undefined ? "—" : `${Math.round(x * 100)}%`);

function Chip({ ok, children }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${ok ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-rose-500"}`} />
      {children}
    </span>
  );
}

function Evidence({ title, badge, children, foot }) {
  return (
    <div className={`${card} p-5 flex flex-col`}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">{title}</h3>
        {badge}
      </div>
      <div className="flex-1">{children}</div>
      {foot && <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">{foot}</p>}
    </div>
  );
}

function Bar({ label, value, color }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-slate-600 dark:text-slate-300"><span>{label}</span><span className="font-mono">{value}</span></div>
      <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: value, background: color }} />
      </div>
    </div>
  );
}

export default function EvidenceView({ authToken, API_BASE }) {
  const [data, setData] = useState({ health: null, model: null, replay: null, live: null });
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    const get = async (path, auth = true) => {
      const res = await fetch(`${API_BASE}${path}`, auth ? { headers: { Authorization: `Bearer ${authToken}` } } : undefined);
      let body = null;
      try { body = await res.json(); } catch { /* an empty or non-JSON answer is treated as "no data" */ }
      return { ok: res.ok, status: res.status, body };
    };
    try {
      const [health, model, replay, devices] = await Promise.all([get("/health", false), get("/sensing/model-info"), get("/sensing/replay/summary"), get("/devices")]);
      let live = null;
      const liveDevice = (devices.body || []).find((d) => (d.allowed_source || "live") === "live");
      if (liveDevice) {
        const t = await get(`/sensing/devices/${liveDevice.id}/csi-telemetry`);
        if (t.ok) live = t.body;
      }
      setData({ health: health.body, model: model.ok ? model.body : null, replay: replay.ok ? replay.body : null, live });
      setError(null);
    } catch (e) {
      setError(`Could not load the evidence (${e.message}).`);
    }
  }, [API_BASE, authToken]);

  useEffect(() => {
    const first = setTimeout(load, 0);
    return () => clearTimeout(first);
  }, [load]);

  const { model, replay, live } = data;
  const health = data.health && data.health.status ? data.health : null; // an older server answers /health with an error body
  const ev = model?.evaluation;
  const replayed = replay && replay.windows_evaluated > 0;
  const liveOk = live && live.has_data;

  const rows = [
    { claim: "The pipeline runs end to end on recorded data and reproduces the offline experiment", grade: replayed ? "MEASURED" : "OPEN",
      evidence: replayed ? `Replay of the unseen person: ${replay.possible_fall_flagged_on_recorded_falls} of ${replay.recorded_fall_windows} recorded falls flagged, ${replay.false_alarms_on_recorded_non_falls} of ${replay.recorded_non_fall_windows} non-falls falsely flagged.` : "No replay has been run on this server yet (tools/replay_wifall.py)." },
    { claim: "Fall vs not-fall on a person the model never saw", grade: "LIMITED",
      evidence: ev ? `Balanced accuracy ${ev.person_averaged_balanced_accuracy} over ${model.n_training_clips ? "10 people, leave-one-person-out" : "all people"} (chance ${ev.chance_balanced_accuracy}). One dataset, one room, one transmitter.` : "Model information is not available." },
    { claim: "The system is a fall detector", grade: "NO",
      evidence: ev ? `It catches about ${pct(ev.person_averaged_fall_recall)} of falls and falsely flags about ${pct(ev.person_averaged_false_alarm_rate)} of non-falls on unseen people. The most it can do is raise a "possible fall" for a person to verify.` : "It can only raise a possible fall that a person must verify." },
    { claim: "CSI packets from this project's own ESP32-S3 boards reach the server", grade: liveOk ? "MEASURED" : "OPEN",
      evidence: liveOk ? `${live.packets_total} packets stored from ${live.mac_address}; RSSI ${live.last_packet?.rssi_dbm} dBm, noise floor ${live.last_packet?.noise_floor_dbm} dBm, channel ${live.last_packet?.channel}, about ${live.recent_window?.arrival_rate_hz ?? "—"} packets/s.` : "No live device has sent packets yet." },
    { claim: "Detection accuracy on this project's own boards and rooms", grade: "OPEN",
      evidence: "Requires recordings made with the project's hardware and an evaluation. None has been done, so no accuracy is claimed." },
    { claim: "A channel-activity indicator", grade: "EXPERIMENTAL",
      evidence: "The CSI packet stream page shows how much the radio channel is changing. It is not validated as presence or movement detection." },
    { claim: "Position or coordinates of a person", grade: "NO",
      evidence: "One transmitter-receiver pair measures the channel between two radios. Coordinates would need several receivers and calibration." },
    { claim: "Vital signs (breathing, heart rate)", grade: "NO", evidence: "Not implemented." },
    { claim: "Real payments", grade: "NO", evidence: `Not implemented. Payments are simulated (mode: ${health?.payments_mode || "sandbox"}).` },
  ];

  return (
    <div className="space-y-6 text-left" data-testid="evidence-view">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Evidence &amp; limits</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          What this system has actually measured, what it has not, and what it should not claim. Numbers on this page are read from this
          system's own data; where there is no data, it says so.
        </p>
      </div>

      {error && <div className="p-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm" role="alert">{error}</div>}

      <div className={`${card} p-4 flex flex-wrap items-center gap-2`}>
        <span className="text-xs font-semibold text-slate-500 mr-1">System checks</span>
        <Chip ok={health?.status === "ok"}>{health ? `Server ${health.status}` : "Health check unavailable"}</Chip>
        <Chip ok={health?.database === "ok"}>Database {health?.database || "unknown"}</Chip>
        <Chip ok={health?.detection_model === "loaded"}>Detection model {health?.detection_model || "unknown"}</Chip>
        <Chip ok={liveOk}>{liveOk ? "Hardware sending packets" : "No hardware packets yet"}</Chip>
        <span className="text-[11px] text-slate-400 ml-auto">payments: {health?.payments_mode || "—"} · environment: {health?.environment || "—"}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Evidence title="Unseen-person test of the detection model" badge={<span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${GRADES.LIMITED}`}>{GRADE_LABEL.LIMITED}</span>}
          foot={ev ? `${ev.protocol}. Per-person range ${ev.per_person_balanced_accuracy_min}–${ev.per_person_balanced_accuracy_max}.` : undefined}>
          {ev ? (
            <>
              <Bar label="Balanced accuracy" value={pct(ev.person_averaged_balanced_accuracy)} color="#0ea5e9" />
              <Bar label="Falls caught" value={pct(ev.person_averaged_fall_recall)} color="#10b981" />
              <Bar label="Non-falls falsely flagged" value={pct(ev.person_averaged_false_alarm_rate)} color="#f59e0b" />
              <div className="text-[11px] text-slate-400">Chance level for balanced accuracy is {pct(ev.chance_balanced_accuracy)}.</div>
            </>
          ) : <p className="text-sm text-slate-500">Model information is not available.</p>}
        </Evidence>

        <Evidence title="Replay of recorded data" badge={<SourceBadge source="dataset" />}
          foot={replayed ? "Recorded WiFall CSI of the held-out person, sent through the same pipeline as live packets. Dataset labels were recorded afterwards." : "Run tools/replay_wifall.py to fill this in."}>
          {replayed ? (
            <>
              <div className="flex gap-4 mb-3">
                <div><div className="text-3xl font-black font-mono text-emerald-600">{replay.possible_fall_flagged_on_recorded_falls}<span className="text-sm text-slate-500 font-normal"> / {replay.recorded_fall_windows}</span></div><div className="text-[11px] text-slate-500">falls flagged</div></div>
                <div><div className="text-3xl font-black font-mono text-amber-600">{replay.false_alarms_on_recorded_non_falls}<span className="text-sm text-slate-500 font-normal"> / {replay.recorded_non_fall_windows}</span></div><div className="text-[11px] text-slate-500">false alarms</div></div>
              </div>
              <Bar label="Precision of a flag" value={pct(replay.precision)} color="#6366f1" />
            </>
          ) : <p className="text-sm text-slate-500">Nothing replayed yet.</p>}
        </Evidence>

        <Evidence title="Own ESP32-S3 hardware link" badge={<SourceBadge source="live" />}
          foot={liveOk ? "Measured from packets this device actually sent. It shows the link works, not that detection is accurate in this room." : "Nothing is shown until a real device sends packets."}>
          {liveOk ? (
            <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
              <div><dt className="text-[11px] text-slate-400">Packets stored</dt><dd className="font-mono font-bold">{live.packets_total}</dd></div>
              <div><dt className="text-[11px] text-slate-400">Packets/s</dt><dd className="font-mono font-bold">{live.recent_window?.arrival_rate_hz ?? "—"}</dd></div>
              <div><dt className="text-[11px] text-slate-400">RSSI</dt><dd className="font-mono font-bold">{live.last_packet?.rssi_dbm} dBm</dd></div>
              <div><dt className="text-[11px] text-slate-400">Noise floor</dt><dd className="font-mono font-bold">{live.last_packet?.noise_floor_dbm} dBm</dd></div>
              <div><dt className="text-[11px] text-slate-400">Channel</dt><dd className="font-mono font-bold">{live.last_packet?.channel}</dd></div>
              <div><dt className="text-[11px] text-slate-400">Subcarriers</dt><dd className="font-mono font-bold">{live.last_packet?.subcarrier_count}</dd></div>
            </dl>
          ) : <p className="text-sm text-slate-500">No live device has sent packets yet.</p>}
        </Evidence>
      </div>

      <div className={`${card} overflow-hidden`}>
        <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Claims and their grade</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-slate-400 border-b border-slate-100 dark:border-slate-800">
                <th className="px-5 py-2.5 font-semibold">Claim</th><th className="px-3 py-2.5 font-semibold whitespace-nowrap">Grade</th><th className="px-5 py-2.5 font-semibold">Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {rows.map((r) => (
                <tr key={r.claim} className="align-top">
                  <td className="px-5 py-3 font-semibold text-slate-800 dark:text-slate-100 min-w-[14rem]">{r.claim}</td>
                  <td className="px-3 py-3 whitespace-nowrap"><span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${GRADES[r.grade]}`}>{GRADE_LABEL[r.grade]}</span></td>
                  <td className="px-5 py-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed min-w-[18rem]">{r.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] text-slate-400">
        Grades follow docs/sensing_modes.md. Demo, dataset replay and live hardware data are never mixed: each carries its own badge everywhere in the application.
      </p>
    </div>
  );
}
