import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SourceBadge } from "./DetectionBadges";

const POLL_MS = 1000;
const KEEP = 600; // packets kept for the waterfalls (several seconds at ~90 packets/s)
const HISTORY = 300; // one-second statistics kept for the trend charts

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";
const panel = "p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800";
const heading = "text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1";

// Viridis-like ramp for amplitude, 0..1 -> rgb
const RAMP = [
  [68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37],
];
function ramp(t, stops = RAMP) {
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x));
  const f = x - i;
  const a = stops[i];
  const b = stops[i + 1];
  return `rgb(${Math.round(a[0] + (b[0] - a[0]) * f)},${Math.round(a[1] + (b[1] - a[1]) * f)},${Math.round(a[2] + (b[2] - a[2]) * f)})`;
}
// Diverging ramp for phase: blue (negative) - white - red (positive)
const DIVERGE = [[37, 99, 235], [147, 197, 253], [248, 250, 252], [252, 165, 165], [220, 38, 38]];

const fmt = (v, d = 1, unit = "") => (v === null || v === undefined || Number.isNaN(v) ? "—" : `${Number(v).toFixed(d)}${unit}`);
const median = (arr) => {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
};

function Tile({ label, value, hint }) {
  return (
    <div className={panel} title={hint}>
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="font-mono text-lg text-slate-900 dark:text-white leading-tight mt-0.5">{value}</div>
    </div>
  );
}

function Meter({ title, valueText, fraction, color, left, right, note }) {
  const pct = Math.round(Math.min(1, Math.max(0, fraction ?? 0)) * 100);
  return (
    <div className={panel}>
      <div className="flex items-baseline justify-between gap-2">
        <div className="text-xs font-semibold text-slate-700 dark:text-slate-200">{title}</div>
        <div className="font-mono text-sm text-slate-900 dark:text-white">{valueText}</div>
      </div>
      <div className="mt-2 h-3 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden" role="meter" aria-label={title} aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="flex justify-between text-[10px] text-slate-400 mt-1"><span>{left}</span><span>{right}</span></div>
      {note && <p className="text-[10px] text-slate-400 mt-1">{note}</p>}
    </div>
  );
}

function Waterfall({ packets, field }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    const W = c.width;
    const H = c.height;
    ctx.clearRect(0, 0, W, H);
    const rows = packets.filter((p) => p[field]);
    if (!rows.length) return;
    const n = rows[0][field].length;
    let max = 1;
    if (field === "amplitude") rows.forEach((p) => p.amplitude.forEach((v) => { if (v > max) max = v; }));
    const colW = W / KEEP;
    const rowH = H / n;
    rows.forEach((p, ci) => {
      const x = (KEEP - rows.length + ci) * colW;
      p[field].forEach((v, k) => {
        ctx.fillStyle = field === "amplitude" ? ramp(v / max) : ramp((Math.max(-1, Math.min(1, v)) + 1) / 2, DIVERGE);
        ctx.fillRect(x, H - (k + 1) * rowH, Math.ceil(colW) + 0.5, Math.ceil(rowH) + 0.5);
      });
    });
  }, [packets, field]);
  return <canvas ref={ref} width={960} height={260} className="w-full h-64 rounded-lg bg-slate-100 dark:bg-slate-950" aria-label={`${field} waterfall: time across, subcarrier up`} />;
}

function Lines({ series, height = 120, colors, yLabel }) {
  const W = 640;
  const all = series.flatMap((s) => s.values);
  if (!all.length) return null;
  let lo = Math.min(...all);
  let hi = Math.max(...all);
  if (hi - lo < 1e-6) { hi += 1; lo -= 1; }
  const pad = (hi - lo) * 0.08;
  lo -= pad; hi += pad;
  const path = (vals) => vals.map((v, i) => `${i ? "L" : "M"}${((i / Math.max(1, vals.length - 1)) * W).toFixed(1)},${(height - ((v - lo) / (hi - lo)) * height).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${height}`} className="w-full" style={{ height }} role="img" aria-label={yLabel}>
      <line x1="0" x2={W} y1={height - ((0 - lo) / (hi - lo)) * height} y2={height - ((0 - lo) / (hi - lo)) * height} stroke="currentColor" strokeOpacity="0.12" />
      {series.map((s, i) => <path key={s.name} d={path(s.values)} fill="none" stroke={colors[i]} strokeWidth="1.6" />)}
      <text x="4" y="12" fontSize="10" fill="currentColor" opacity="0.5">{hi.toFixed(2)}</text>
      <text x="4" y={height - 4} fontSize="10" fill="currentColor" opacity="0.5">{lo.toFixed(2)}</text>
    </svg>
  );
}

function SubcarrierBars({ values, indices }) {
  if (!values?.length) return null;
  const max = Math.max(...values, 1e-9);
  const med = median(values) || 0;
  return (
    <div>
      <div className="h-28 flex items-end gap-px bg-slate-100 dark:bg-slate-950 rounded-lg p-1.5" role="img" aria-label="Amplitude variation per subcarrier">
        {values.map((v, i) => (
          <div key={i} className="flex-1 rounded-t" title={`subcarrier ${indices?.[i] ?? i}: variation ${v.toFixed(3)}`}
            style={{ height: `${Math.max(3, (v / max) * 100)}%`, background: v > med * 1.6 ? "#f59e0b" : "#14b8a6" }} />
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-slate-400 mt-1"><span>subcarrier {indices?.[0] ?? 0}</span><span>0 (DC, not sent)</span><span>{indices?.[values.length - 1] ?? values.length - 1}</span></div>
    </div>
  );
}

function Phasors({ amplitude, phase }) {
  if (!amplitude?.length || !phase?.length) return null;
  const size = 240;
  const c = size / 2;
  const max = Math.max(...amplitude, 1);
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[260px] mx-auto text-slate-900 dark:text-slate-100" role="img" aria-label="Subcarrier phasors: amplitude as distance, sanitised phase as angle">
      {[0.5, 1].map((f) => <circle key={f} cx={c} cy={c} r={(c - 14) * f} fill="none" stroke="currentColor" strokeOpacity="0.12" />)}
      <line x1="8" x2={size - 8} y1={c} y2={c} stroke="currentColor" strokeOpacity="0.12" />
      <line x1={c} x2={c} y1="8" y2={size - 8} stroke="currentColor" strokeOpacity="0.12" />
      {amplitude.map((a, i) => {
        const r = (a / max) * (c - 14);
        return <circle key={i} cx={c + r * Math.cos(phase[i])} cy={c - r * Math.sin(phase[i])} r="3.2" fill={ramp(i / (amplitude.length - 1))} stroke="white" strokeWidth="0.5" />;
      })}
    </svg>
  );
}

export default function LiveCsiStream({ deviceId, authToken, API_BASE }) {
  const [snap, setSnap] = useState(null);
  const [buffer, setBuffer] = useState([]);
  const [history, setHistory] = useState([]);
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState(null);
  const [distance, setDistance] = useState("");
  const [hoverK, setHoverK] = useState(null);
  const [field, setField] = useState("amplitude");
  const [now, setNow] = useState(0);
  const afterRef = useRef(0);
  const rootRef = useRef(null);

  useEffect(() => {
    rootRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const poll = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/live?after_id=${afterRef.current}&window=60`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const stamp = Date.now();
      setSnap(data);
      setNow(stamp);
      setError(null);
      if (data.has_data && data.stats) {
        setHistory((prev) => [...prev, {
          t: stamp, variation: data.stats.amplitude_variation, rate: data.stats.arrival_rate_hz, snr: data.stats.snr_db,
        }].slice(-HISTORY));
      }
      if (data.packets.length) {
        afterRef.current = data.latest_id;
        setBuffer((prev) => [...prev, ...data.packets].slice(-KEEP));
      }
    } catch (e) {
      setError(`Stream interrupted (${e.message}). Retrying…`);
    }
  }, [API_BASE, authToken, deviceId]);

  useEffect(() => {
    if (paused) return undefined;
    const first = setTimeout(poll, 0);
    const t = setInterval(poll, POLL_MS);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [poll, paused]);

  const last = buffer[buffer.length - 1];
  const link = snap?.link;
  const stats = snap?.stats;
  const lastSeenMs = snap?.last_seen_at && now ? now - new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(snap.last_seen_at) ? snap.last_seen_at : `${snap.last_seen_at}Z`).getTime() : null;
  const flowing = lastSeenMs !== null && lastSeenMs < 8000 && !paused;

  const fresnel = useMemo(() => {
    const d = parseFloat(distance);
    if (!link?.wavelength_cm || !d || d <= 0) return null;
    return 0.5 * Math.sqrt((link.wavelength_cm / 100) * d);
  }, [distance, link]);

  const variations = useMemo(() => history.map((h) => h.variation).filter((v) => v !== null && v !== undefined), [history]);
  const baseline = useMemo(() => median(variations), [variations]);
  const currentVar = variations[variations.length - 1];
  const ratio = baseline && currentVar !== undefined ? currentVar / baseline : null;
  const calibrating = variations.length < 15;

  const rssiSeries = buffer.map((p) => p.rssi_dbm);
  const meanAmp = buffer.map((p) => (p.amplitude ? p.amplitude.reduce((a, b) => a + b, 0) / p.amplitude.length : null)).filter((v) => v !== null);
  const rateSeries = history.map((h) => h.rate).filter((v) => v !== null && v !== undefined);
  const freqs = link?.subcarrier_frequency_mhz;
  const lambdas = link?.subcarrier_wavelength_cm;
  const snr = stats?.snr_db;

  return (
    <div ref={rootRef} className={`${card} p-5 space-y-5 scroll-mt-20`} data-testid="live-csi-stream">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">CSI packet stream</h3>
          {snap && <SourceBadge source={snap.provenance} />}
          <span className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full ${flowing ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${flowing ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}`} />
            {paused ? "PAUSED" : flowing ? "RECEIVING" : snap?.has_data ? "NO RECENT PACKETS" : "NO PACKETS YET"}
          </span>
          <span className="font-mono text-[11px] text-slate-500 truncate">{snap?.mac_address}</span>
        </div>
        <button type="button" onClick={() => setPaused((p) => !p)} className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
          {paused ? "Resume" : "Pause"}
        </button>
      </div>

      {error && <div className="p-2.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-xs" role="alert">{error}</div>}

      {!snap ? (
        <div className="h-40 rounded-xl bg-slate-100 dark:bg-slate-800/50 animate-pulse" />
      ) : !snap.has_data ? (
        <div className="py-10 text-center text-sm text-slate-500">
          <span className="material-symbols-outlined text-3xl text-slate-300 block mb-2">signal_cellular_off</span>
          No packets have arrived from this device. Nothing is shown until the hardware sends data.
        </div>
      ) : (
        <>
          <p className="text-[11px] text-slate-500">{snap.packets_total} packets stored · refreshing every {POLL_MS / 1000} s · every value below is computed from the packets this device sent.</p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Meter
              title="Channel activity"
              valueText={calibrating ? "calibrating…" : `×${fmt(ratio, 2)}`}
              fraction={calibrating || ratio === null ? 0 : ratio / 3}
              color={ratio !== null && !calibrating && ratio > 1.6 ? "linear-gradient(90deg,#f59e0b,#ef4444)" : "linear-gradient(90deg,#14b8a6,#22c55e)"}
              left="calm"
              right="much more than usual"
              note="Amplitude variation now compared with this page's typical level since it was opened. It shows that the radio channel is changing, not what is changing or where."
            />
            <Meter
              title="Signal quality (SNR)"
              valueText={fmt(snr, 1, " dB")}
              fraction={snr === null || snr === undefined ? 0 : snr / 60}
              color={snr !== null && snr !== undefined && snr < 20 ? "linear-gradient(90deg,#ef4444,#f59e0b)" : "linear-gradient(90deg,#3b82f6,#6366f1)"}
              left="0 dB"
              right="60 dB"
              note="Signal strength minus noise floor on the receiver. Below about 20 dB the measurements get unreliable."
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Tile label="Packet rate" value={fmt(stats.arrival_rate_hz, 1, " Hz")} hint="Packets per second as they arrived at the server (batching makes this read higher than the device's own rate)" />
            <Tile label="Packet loss" value={fmt(stats.packet_loss_pct, 1, " %")} hint="Gaps in the device's sequence numbers" />
            <Tile label="RSSI" value={`${fmt(stats.rssi_mean_dbm, 1)} ±${fmt(stats.rssi_std_db, 1)} dBm`} />
            <Tile label="Noise floor" value={fmt(stats.noise_floor_mean_dbm, 1, " dBm")} />
            <Tile label="Mean amplitude" value={fmt(stats.amplitude_mean, 1)} hint="Mean CSI amplitude over subcarriers and window (raw units)" />
            <Tile label="Amplitude variation" value={fmt(stats.amplitude_variation, 3)} hint="Std/mean over time, averaged over subcarriers. Rises when something changes on the link. A motion indicator, not a position." />
            <Tile label="Dominant fluctuation" value={fmt(stats.dominant_fluctuation_hz, 2, " Hz")} hint="Strongest frequency in the amplitude fluctuation over the window" />
            <Tile label="Packets in view" value={`${buffer.length}`} hint="Packets drawn in the waterfall" />
          </div>

          <div>
            <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
              <div className={heading}>
                {field === "amplitude" ? "Amplitude" : "Phase"} waterfall <span className="font-normal text-slate-400">(each column is one packet, newest on the right; each row is one subcarrier)</span>
              </div>
              <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-xs font-semibold" role="tablist" aria-label="Waterfall quantity">
                {["amplitude", "phase"].map((f) => (
                  <button key={f} type="button" role="tab" aria-selected={field === f} onClick={() => setField(f)}
                    className={`px-3 py-1 cursor-pointer ${field === f ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"}`}>
                    {f === "amplitude" ? "Amplitude" : "Phase"}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2 items-stretch">
              <div className="flex flex-col justify-between text-[10px] text-slate-400 font-mono py-1 text-right w-8 shrink-0">
                <span>+26</span><span>0</span><span>−26</span>
              </div>
              <div className="flex-1 min-w-0"><Waterfall packets={buffer} field={field} /></div>
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-1 pl-10">
              <span>older</span>
              <span>{field === "amplitude" ? "dark = weak, bright = strong" : "blue = negative, red = positive (sanitised phase, radians)"}</span>
              <span>newest</span>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <div>
              <div className={heading}>Which subcarriers are changing <span className="font-normal text-slate-400">(variation per subcarrier)</span></div>
              <SubcarrierBars values={stats.per_subcarrier_variation} indices={link.subcarrier_index} />
              <p className="text-[10px] text-slate-400 mt-1">Amber bars change much more than the typical subcarrier.</p>
            </div>
            <div>
              <div className={heading}>Subcarrier phasors <span className="font-normal text-slate-400">(latest packet)</span></div>
              <Phasors amplitude={last?.amplitude} phase={last?.phase} />
              <p className="text-[10px] text-slate-400 mt-1">Distance from the centre is amplitude, angle is sanitised phase; colour runs from the first to the last subcarrier.</p>
            </div>
            <div>
              <div className={`${heading} flex justify-between`}>
                <span>Latest packet: amplitude <span className="text-teal-600">━</span> and phase <span className="text-violet-600">━</span></span>
                <span className="font-normal text-slate-400">{hoverK !== null && freqs ? `sc ${link.subcarrier_index[hoverK]} · ${freqs[hoverK]} MHz · λ ${lambdas[hoverK]} cm` : "hover"}</span>
              </div>
              <div
                className="text-slate-900 dark:text-slate-100 relative"
                onMouseMove={(e) => {
                  const r = e.currentTarget.getBoundingClientRect();
                  const n = last?.amplitude?.length || 0;
                  if (n) setHoverK(Math.min(n - 1, Math.max(0, Math.floor(((e.clientX - r.left) / r.width) * n))));
                }}
                onMouseLeave={() => setHoverK(null)}
              >
                {last?.amplitude && <Lines series={[{ name: "amplitude", values: last.amplitude }]} colors={["#0d9488"]} height={96} yLabel="Amplitude per subcarrier" />}
                {last?.phase && <Lines series={[{ name: "phase", values: last.phase }]} colors={["#7c3aed"]} height={96} yLabel="Sanitised phase per subcarrier (radians)" />}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <div className={heading}>Amplitude variation over time <span className="font-normal text-slate-400">(one point per second)</span></div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "variation", values: variations }]} colors={["#f59e0b"]} yLabel="Amplitude variation over time" /></div>
            </div>
            <div>
              <div className={heading}>Mean amplitude over time</div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "amp", values: meanAmp }]} colors={["#0d9488"]} yLabel="Mean amplitude over time" /></div>
            </div>
            <div>
              <div className={heading}>RSSI over time <span className="font-normal text-slate-400">(dBm)</span></div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "rssi", values: rssiSeries }]} colors={["#2563eb"]} yLabel="RSSI over time" /></div>
            </div>
            <div>
              <div className={heading}>Packet rate over time <span className="font-normal text-slate-400">(Hz at the server)</span></div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "rate", values: rateSeries }]} colors={["#6366f1"]} yLabel="Packet rate over time" /></div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className={`${panel} text-xs`}>
              <div className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Radio link</div>
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                <div><dt className="text-slate-400">Channel</dt><dd className="font-mono">{link.channel ?? "—"}</dd></div>
                <div><dt className="text-slate-400">Center frequency</dt><dd className="font-mono">{fmt(link.center_frequency_mhz, 0, " MHz")}</dd></div>
                <div><dt className="text-slate-400">Wavelength</dt><dd className="font-mono">{fmt(link.wavelength_cm, 2, " cm")}</dd></div>
                <div><dt className="text-slate-400">Bandwidth</dt><dd className="font-mono">{link.bandwidth_mhz ?? "—"} MHz</dd></div>
                <div><dt className="text-slate-400">Subcarrier spacing</dt><dd className="font-mono">{fmt(link.subcarrier_spacing_khz, 1, " kHz")}</dd></div>
                <div><dt className="text-slate-400">Subcarriers</dt><dd className="font-mono">{last?.amplitude?.length ?? "—"}</dd></div>
                <div><dt className="text-slate-400">Receiver (this device)</dt><dd className="font-mono">{snap.mac_address}</dd></div>
                <div><dt className="text-slate-400">Transmitter</dt><dd className="font-mono">{last?.meta?.src_mac ?? "not reported"}</dd></div>
              </dl>
              <div className="mt-3 flex items-center gap-2">
                <label htmlFor="tx-rx-distance" className="text-slate-500">TX–RX distance (m)</label>
                <input id="tx-rx-distance" inputMode="decimal" value={distance} onChange={(e) => setDistance(e.target.value)} placeholder="e.g. 4"
                  className="w-20 px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 font-mono" />
                {fresnel !== null && <span className="text-slate-600 dark:text-slate-300">first Fresnel zone radius at midpoint ≈ <strong className="font-mono">{(fresnel * 100).toFixed(0)} cm</strong></span>}
              </div>
              <p className="text-[10px] text-slate-400 mt-2">{link.derived_from}. The distance is what you type; it is not measured.</p>
            </div>

            <div className={`${panel} text-xs`}>
              <div className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Latest packet</div>
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                <div><dt className="text-slate-400">Sequence</dt><dd className="font-mono">{last?.seq ?? "—"}</dd></div>
                <div><dt className="text-slate-400">Device timestamp</dt><dd className="font-mono">{last?.timestamp ? new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(last.timestamp) ? last.timestamp : `${last.timestamp}Z`).toLocaleTimeString() : "—"}</dd></div>
                <div><dt className="text-slate-400">RSSI / noise</dt><dd className="font-mono">{last?.rssi_dbm} / {last?.noise_floor_dbm ?? "—"} dBm</dd></div>
                <div><dt className="text-slate-400">SNR</dt><dd className="font-mono">{fmt(last?.snr_db, 0, " dB")}</dd></div>
                {last?.meta && Object.entries(last.meta).filter(([k]) => k !== "src_mac").map(([k, v]) => (
                  <div key={k}><dt className="text-slate-400">{k}</dt><dd className="font-mono">{String(v)}</dd></div>
                ))}
              </dl>
              <p className="text-[10px] text-slate-400 mt-3">
                {snap.limits}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
