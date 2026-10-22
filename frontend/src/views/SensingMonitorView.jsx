import React, { useCallback, useEffect, useMemo, useState } from "react";
import LiveCsiStream from "../components/LiveCsiStream";
import {
  ACTIVITY_LABEL,
  ConfidenceBadge,
  SignalBadge,
  SourceBadge,
  StatusChip,
} from "../components/DetectionBadges";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";

const MODES = [
  {
    id: "simulated",
    title: "DEMO",
    icon: "science",
    blurb: "Preview values that show how the system will behave before hardware is installed. Not measurements.",
    empty: "No demo detections yet. Use Simulate Fall / CSI to generate preview events.",
  },
  {
    id: "dataset",
    title: "DATASET REPLAY",
    icon: "history",
    blurb: "Real recorded CSI from a public dataset, replayed through the same authenticated pipeline. Not current sensing.",
    empty: "Nothing has been replayed yet. An administrator replays a recorded dataset with tools/replay_wifall.py.",
  },
  {
    id: "live",
    title: "LIVE HARDWARE",
    icon: "sensors",
    blurb: "Packets from authenticated ESP32-S3 devices. Nothing appears here until a real device sends a packet.",
    empty: "No packets have been received from authenticated hardware yet. This stays empty until a real device sends one.",
  },
];

const parseUtc = (iso) => {
  if (!iso) return null;
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
};
const fmtTime = (iso) => {
  const d = parseUtc(iso);
  return d ? d.toLocaleString([], { dateStyle: "medium", timeStyle: "medium" }) : "—";
};
const ago = (iso) => {
  const d = parseUtc(iso);
  if (!d) return "Never seen";
  const s = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
  if (s < 90) return `${s}s ago`;
  if (s < 5400) return `${Math.round(s / 60)} min ago`;
  return d.toLocaleString();
};
const isRecent = (iso) => {
  const d = parseUtc(iso);
  return d ? Date.now() - d.getTime() <= 5 * 60 * 1000 : false;
};
const activityName = (a) => ACTIVITY_LABEL[a] || (a || "").replace(/_/g, " ");

function Skeleton({ rows = 4 }) {
  return (
    <div className="space-y-2 animate-pulse" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 rounded-xl bg-slate-100 dark:bg-slate-800" />
      ))}
    </div>
  );
}

function Empty({ icon, text }) {
  return (
    <div className="py-10 text-center text-slate-400">
      <span className="material-symbols-outlined text-4xl block mb-2">{icon}</span>
      <p className="text-sm max-w-md mx-auto">{text}</p>
    </div>
  );
}

export default function SensingMonitorView({ authToken, API_BASE, devices = [], rooms = [] }) {
  const [mode, setMode] = useState("simulated");
  const [history, setHistory] = useState({ simulated: null, dataset: null, live: null });
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [replay, setReplay] = useState(null);
  const [model, setModel] = useState(null);
  const [showModel, setShowModel] = useState(false);
  const [error, setError] = useState(null);

  const get = useCallback(
    async (path) => {
      const res = await fetch(`${API_BASE}${path}`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    },
    [API_BASE, authToken]
  );

  const loadHistory = useCallback(async () => {
    try {
      const [simulated, dataset, live] = await Promise.all(
        MODES.map((m) => get(`/sensing/history?source=${m.id}&limit=50`))
      );
      setHistory({ simulated, dataset, live });
      setError(null);
    } catch (e) {
      setError(`Could not load detections (${e.message}).`);
    }
  }, [get]);

  useEffect(() => {
    loadHistory();
    const t = setInterval(loadHistory, 5000);
    return () => clearInterval(t);
  }, [loadHistory]);

  useEffect(() => {
    get("/sensing/model-info").then(setModel).catch(() => setModel(null));
  }, [get]);

  useEffect(() => {
    if (mode !== "dataset") return undefined;
    const load = () => get("/sensing/replay/summary").then(setReplay).catch(() => setReplay(null));
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [mode, get]);

  const modeDevices = useMemo(
    () => devices.filter((d) => (d.allowed_source || "live") === mode),
    [devices, mode]
  );

  useEffect(() => {
    setSelectedDevice(null);
    setTelemetry(null);
  }, [mode]);

  useEffect(() => {
    if (!selectedDevice) return undefined;
    const load = () => get(`/sensing/devices/${selectedDevice}/csi-telemetry`).then(setTelemetry).catch(() => setTelemetry(null));
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [selectedDevice, get]);

  const roomName = (id) => rooms.find((r) => r.id === id)?.name;
  const rows = history[mode];
  const modeMeta = MODES.find((m) => m.id === mode);
  const evalForDataset = replay?.by_dataset || {};

  return (
    <div className="space-y-6 text-left" data-testid="sensing-monitor">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Sensing Monitor</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Where each value comes from: demo preview, recorded dataset replay, or live ESP32 hardware. They are never mixed.
        </p>
      </div>

      {error && <div className="p-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm font-medium" role="alert">{error}</div>}

      {/* Mode selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {MODES.map((m) => {
          const list = history[m.id];
          const devs = devices.filter((d) => (d.allowed_source || "live") === m.id);
          const active = mode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              aria-pressed={active}
              className={`${card} p-5 text-left transition hover:shadow-md ${active ? "ring-2 ring-teal-500" : ""}`}
            >
              <div className="flex items-center justify-between mb-2">
                <SourceBadge source={m.id} />
                <span className="material-symbols-outlined text-slate-400">{m.icon}</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed min-h-[48px]">{m.blurb}</p>
              <div className="flex gap-4 mt-3 text-xs">
                <span><strong className="text-slate-900 dark:text-white text-base">{list === null ? "…" : list.length >= 50 ? "50+" : list.length}</strong> <span className="text-slate-500">recent detections</span></span>
                <span><strong className="text-slate-900 dark:text-white text-base">{devs.length}</strong> <span className="text-slate-500">devices</span></span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="space-y-6">
        {/* Devices + telemetry */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
          <div className={`${card} p-5`}>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Devices in this mode</h3>
            {modeDevices.length === 0 ? (
              <Empty icon="router" text={mode === "live" ? "No device is registered for live hardware yet." : "No device is registered in this mode."} />
            ) : (
              <div className="space-y-2">
                {modeDevices.map((d) => {
                  const online = d.device_status === "ONLINE" && isRecent(d.last_seen_at);
                  return (
                    <button
                      key={d.id}
                      type="button"
                      onClick={() => setSelectedDevice(d.id)}
                      className={`w-full text-left p-3 rounded-xl border transition ${selectedDevice === d.id ? "border-teal-500 bg-teal-50 dark:bg-teal-950/30" : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">{d.mac_address}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${online ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
                          {online ? "ONLINE" : d.last_seen_at ? "OFFLINE" : "NEVER SEEN"}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{roomName(d.room_id) || "Unassigned"} · {(d.allowed_source || "live") === "simulated" ? "last demo event" : "last packet"} {ago(d.last_seen_at)}</div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {selectedDevice && (
            <div className={`${card} p-5`} data-testid="device-telemetry">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">What this device really sent</h3>
              {!telemetry ? (
                <Skeleton rows={3} />
              ) : (
                <>
                  <p className="text-[11px] text-slate-500 mb-3">{telemetry.data_statement}</p>
                  {!telemetry.has_data ? (
                    <Empty icon="signal_cellular_off" text="No packets received from this device." />
                  ) : (
                    <div className="space-y-3 text-xs">
                      <dl className="grid grid-cols-2 gap-x-3 gap-y-2">
                        <div><dt className="text-slate-400">Last packet</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{fmtTime(telemetry.last_packet.timestamp)}</dd></div>
                        <div><dt className="text-slate-400">Packets stored</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{telemetry.packets_total}</dd></div>
                        <div><dt className="text-slate-400">RSSI</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{telemetry.last_packet.rssi_dbm} dBm</dd></div>
                        <div><dt className="text-slate-400">Noise floor</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{telemetry.last_packet.noise_floor_dbm ?? "—"} dBm</dd></div>
                        <div><dt className="text-slate-400">Subcarriers</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{telemetry.last_packet.subcarrier_count}</dd></div>
                        <div><dt className="text-slate-400">Channel</dt><dd className="font-mono text-slate-800 dark:text-slate-200">{telemetry.last_packet.channel ?? "—"}</dd></div>
                      </dl>
                      {telemetry.amplitude_last_packet && (
                        <div>
                          <div className="text-slate-400 mb-1">Amplitude per subcarrier (last packet)</div>
                          <div className="h-16 flex items-end gap-px bg-slate-50 dark:bg-slate-950 rounded-lg p-1" aria-label="Amplitude per subcarrier">
                            {(() => {
                              const max = Math.max(...telemetry.amplitude_last_packet, 1);
                              return telemetry.amplitude_last_packet.map((v, i) => (
                                <div key={i} className="flex-1 bg-teal-500/80 rounded-t" style={{ height: `${Math.max(4, (v / max) * 100)}%` }} />
                              ));
                            })()}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {selectedDevice && <LiveCsiStream key={selectedDevice} deviceId={selectedDevice} authToken={authToken} API_BASE={API_BASE} />}

        {/* Detections */}
        <div className="space-y-4">
          <div className={`${card} p-5`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                Detections <SourceBadge source={mode} />
              </h3>
              <span className="text-[11px] text-slate-400">refreshes every 5 s</span>
            </div>
            {rows === null ? (
              <Skeleton />
            ) : rows.length === 0 ? (
              <Empty icon={modeMeta.icon} text={modeMeta.empty} />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-[10px] uppercase tracking-wide text-slate-400 border-b border-slate-100 dark:border-slate-800">
                      <th className="py-2 pr-3">Time</th>
                      <th className="py-2 pr-3">Room · device</th>
                      <th className="py-2 pr-3">Detection</th>
                      <th className="py-2 pr-3">Confidence</th>
                      <th className="py-2 pr-3">Signal</th>
                      <th className="py-2 pr-3">RSSI / noise</th>
                      <th className="py-2 pr-3">Status</th>
                      {mode === "dataset" && <th className="py-2">Recorded label</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {rows.map((r) => (
                      <tr key={r.id} className="align-top">
                        <td className="py-2.5 pr-3 font-mono text-slate-600 dark:text-slate-300 whitespace-nowrap">{fmtTime(r.timestamp)}</td>
                        <td className="py-2.5 pr-3">
                          <div className="font-semibold text-slate-800 dark:text-slate-200">{r.room_name}</div>
                          <div className="font-mono text-[10px] text-slate-400">{r.device_mac || r.device_id.slice(0, 8)}</div>
                        </td>
                        <td className="py-2.5 pr-3 font-semibold text-slate-800 dark:text-slate-200">{activityName(r.activity)}</td>
                        <td className="py-2.5 pr-3">
                          <ConfidenceBadge level={r.confidence_level} confidence={r.confidence} source={r.source} />
                          {r.fall_score !== null && r.fall_score !== undefined && (
                            <div className="text-[10px] text-slate-400 mt-0.5" title="How fall-like the window looked to the model (0-1). Uncalibrated, not the probability of a fall">fall-likeness {r.fall_score}</div>
                          )}
                        </td>
                        <td className="py-2.5 pr-3"><SignalBadge level={r.signal_level} quality={r.signal_quality} /></td>
                        <td className="py-2.5 pr-3 font-mono text-slate-600 dark:text-slate-300 whitespace-nowrap">
                          {r.rssi} dBm{r.noise_floor !== null && r.noise_floor !== undefined ? ` / ${r.noise_floor}` : ""}
                          {r.subcarrier_count ? <div className="text-[10px] text-slate-400">{r.subcarrier_count} subcarriers · {r.window_packets} packets</div> : null}
                        </td>
                        <td className="py-2.5 pr-3"><StatusChip item={r} /></td>
                        {mode === "dataset" && (
                          <td className="py-2.5">
                            {r.recorded_label ? (
                              <span className="font-semibold text-slate-700 dark:text-slate-200">{r.recorded_label}</span>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="text-[11px] text-slate-400 mt-3">
              Confidence is the model's score for the class it chose. Signal quality describes the radio link, not whether the
              detection is right. Both are heuristics, not validated probabilities.
            </p>
          </div>

          {mode === "dataset" && replay && replay.windows_evaluated > 0 && (
            <div className={`${card} p-5`} data-testid="replay-evaluation">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Replay check: recorded label vs the system's result</h3>
              <div className="space-y-3">
                {Object.entries(evalForDataset).map(([name, v]) => (
                  <div key={name} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800">
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">{name}</div>
                    <div className="grid grid-cols-2 gap-3 mt-2 text-xs">
                      <div>
                        <div className="text-slate-400">Recorded falls flagged as possible fall</div>
                        <div className="font-mono text-base text-slate-900 dark:text-white">{v.falls_flagged} of {v.recorded_falls}</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Non-falls falsely flagged</div>
                        <div className="font-mono text-base text-slate-900 dark:text-white">{v.non_falls_flagged} of {v.non_falls}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-3">{replay.statement}</p>
            </div>
          )}
        </div>
      </div>

      {/* About the model */}
      <div className={`${card} p-5`}>
        <button type="button" onClick={() => setShowModel(!showModel)} className="w-full flex items-center justify-between text-left" aria-expanded={showModel}>
          <span className="text-sm font-semibold text-slate-900 dark:text-white">About the detection model and its limits</span>
          <span className="material-symbols-outlined text-slate-400">{showModel ? "expand_less" : "expand_more"}</span>
        </button>
        {showModel && (
          <div className="mt-3 text-xs space-y-2 text-slate-600 dark:text-slate-300">
            {!model || !model.available ? (
              <p>The detection model is not available.</p>
            ) : (
              <>
                <p><strong>Trained on:</strong> {model.trained_on}</p>
                <p>
                  <strong>On a person it had never seen:</strong> balanced accuracy {model.evaluation.person_averaged_balanced_accuracy} (0.50 is chance),
                  catching about {Math.round(model.evaluation.person_averaged_fall_recall * 100)}% of falls and falsely flagging about{" "}
                  {Math.round(model.evaluation.person_averaged_false_alarm_rate * 100)}% of non-falls.
                </p>
                <p><strong>Score:</strong> {model.score_meaning}</p>
                <ul className="list-disc pl-5 space-y-1">{model.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
