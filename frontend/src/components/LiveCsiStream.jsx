import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SourceBadge } from "./DetectionBadges";

const POLL_MS = 1000;
const KEEP = 160; // packets kept for the waterfall

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";

// Viridis-like ramp, 0..1 -> rgb
const RAMP = [
  [68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37],
];
function ramp(t) {
  const x = Math.min(1, Math.max(0, t)) * (RAMP.length - 1);
  const i = Math.min(RAMP.length - 2, Math.floor(x));
  const f = x - i;
  const a = RAMP[i];
  const b = RAMP[i + 1];
  return `rgb(${Math.round(a[0] + (b[0] - a[0]) * f)},${Math.round(a[1] + (b[1] - a[1]) * f)},${Math.round(a[2] + (b[2] - a[2]) * f)})`;
}

const fmt = (v, d = 1, unit = "") => (v === null || v === undefined || Number.isNaN(v) ? "—" : `${Number(v).toFixed(d)}${unit}`);

function Tile({ label, value, hint }) {
  return (
    <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800" title={hint}>
      <div className="text-[10px] uppercase tracking-wide text-slate-400">{label}</div>
      <div className="font-mono text-lg text-slate-900 dark:text-white leading-tight mt-0.5">{value}</div>
    </div>
  );
}

function Waterfall({ packets }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    const W = c.width;
    const H = c.height;
    ctx.clearRect(0, 0, W, H);
    const rows = packets.filter((p) => p.amplitude);
    if (!rows.length) return;
    const n = rows[0].amplitude.length;
    let max = 1;
    rows.forEach((p) => p.amplitude.forEach((v) => { if (v > max) max = v; }));
    const colW = W / KEEP;
    const rowH = H / n;
    rows.forEach((p, ci) => {
      const x = (KEEP - rows.length + ci) * colW;
      p.amplitude.forEach((v, k) => {
        ctx.fillStyle = ramp(v / max);
        ctx.fillRect(x, H - (k + 1) * rowH, Math.ceil(colW) + 0.5, Math.ceil(rowH) + 0.5);
      });
    });
  }, [packets]);
  return <canvas ref={ref} width={640} height={208} className="w-full h-52 rounded-lg bg-slate-100 dark:bg-slate-950" aria-label="Amplitude waterfall: time across, subcarrier up" />;
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
      <text x="4" y="12" fontSize="10" fill="currentColor" opacity="0.5">{hi.toFixed(1)}</text>
      <text x="4" y={height - 4} fontSize="10" fill="currentColor" opacity="0.5">{lo.toFixed(1)}</text>
    </svg>
  );
}

export default function LiveCsiStream({ deviceId, authToken, API_BASE }) {
  const [snap, setSnap] = useState(null);
  const [buffer, setBuffer] = useState([]);
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState(null);
  const [distance, setDistance] = useState("");
  const [hoverK, setHoverK] = useState(null);
  const [now, setNow] = useState(0);
  const afterRef = useRef(0);

  const poll = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sensing/devices/${deviceId}/live?after_id=${afterRef.current}&window=60`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSnap(data);
      setNow(Date.now());
      setError(null);
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
    poll();
    const t = setInterval(poll, POLL_MS);
    return () => clearInterval(t);
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

  const rssiSeries = buffer.map((p) => p.rssi_dbm);
  const meanAmp = buffer.map((p) => (p.amplitude ? p.amplitude.reduce((a, b) => a + b, 0) / p.amplitude.length : null)).filter((v) => v !== null);
  const freqs = link?.subcarrier_frequency_mhz;
  const lambdas = link?.subcarrier_wavelength_cm;

  return (
    <div className={`${card} p-5 space-y-5`} data-testid="live-csi-stream">
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
          <p className="text-[11px] text-slate-500">{snap.packets_total} packets stored · refreshing every {POLL_MS / 1000} s · values below are computed from the packets this device sent.</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Tile label="Packet rate" value={fmt(stats.arrival_rate_hz, 1, " Hz")} hint="Packets per second as they arrived at the server" />
            <Tile label="Packet loss" value={fmt(stats.packet_loss_pct, 1, " %")} hint="Gaps in the device's sequence numbers" />
            <Tile label="RSSI" value={`${fmt(stats.rssi_mean_dbm, 1)} ±${fmt(stats.rssi_std_db, 1)} dBm`} />
            <Tile label="Noise floor" value={fmt(stats.noise_floor_mean_dbm, 1, " dBm")} />
            <Tile label="SNR" value={fmt(stats.snr_db, 1, " dB")} hint="RSSI minus noise floor" />
            <Tile label="Mean amplitude" value={fmt(stats.amplitude_mean, 1)} hint="Mean CSI amplitude over subcarriers and window (raw units)" />
            <Tile label="Amplitude variation" value={fmt(stats.amplitude_variation, 3)} hint="Std/mean over time, averaged over subcarriers. Rises when something moves on the link. A motion indicator, not a position." />
            <Tile label="Dominant fluctuation" value={fmt(stats.dominant_fluctuation_hz, 2, " Hz")} hint="Strongest frequency in the amplitude fluctuation over the window" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">Amplitude waterfall <span className="font-normal text-slate-400">(time → , subcarrier ↑)</span></div>
              <Waterfall packets={buffer} />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1 flex justify-between">
                <span>Latest packet: amplitude <span className="text-teal-600">━</span> and phase <span className="text-violet-600">━</span></span>
                <span className="font-normal text-slate-400">{hoverK !== null && freqs ? `subcarrier ${link.subcarrier_index[hoverK]} · ${freqs[hoverK]} MHz · λ ${lambdas[hoverK]} cm` : "hover the chart"}</span>
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
            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">RSSI over time <span className="font-normal text-slate-400">(dBm)</span></div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "rssi", values: rssiSeries }]} colors={["#2563eb"]} yLabel="RSSI over time" /></div>
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 mb-1">Mean amplitude over time</div>
              <div className="text-slate-900 dark:text-slate-100"><Lines series={[{ name: "amp", values: meanAmp }]} colors={["#0d9488"]} yLabel="Mean amplitude over time" /></div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs">
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

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs">
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
