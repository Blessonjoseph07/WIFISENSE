import React, { useMemo } from "react";
import { SourceBadge } from "./DetectionBadges";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";

const parseUtc = (iso) => {
  if (!iso) return null;
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
};

const since = (iso) => {
  const d = parseUtc(iso);
  if (!d) return null;
  const s = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
  if (s < 90) return `${s} seconds ago`;
  if (s < 5400) return `${Math.round(s / 60)} minutes ago`;
  if (s < 172800) return `${Math.round(s / 3600)} hours ago`;
  return d.toLocaleDateString();
};

const isPossibleFall = (r) => /fall/i.test(r.activity || "") && !/no[_ ]?fall/i.test(r.activity || "");

function Dot({ color, title }) {
  return <span title={title} className="w-4 h-4 rounded-full inline-block" style={{ background: color }} />;
}

function Step({ n, text }) {
  return (
    <li className="flex gap-2.5 items-start">
      <span className="w-5 h-5 shrink-0 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 text-[11px] font-bold flex items-center justify-center">{n}</span>
      <span>{text}</span>
    </li>
  );
}

/**
 * Plain-language view of the LIVE HARDWARE mode for people who do not know what CSI is.
 * Live data has no answer key, so it never says whether a result is right: it says what the board sent, what the system
 * concluded, and that a person must check anything flagged. Every number comes from the detections the API returned.
 */
export default function HardwarePlainSummary({ rows, devices }) {
  // newest first from the API; the dots read left (older) to right (newer)
  const recent = useMemo(() => [...(rows || [])].slice(0, 40).reverse(), [rows]);
  const flagged = recent.filter(isPossibleFall).length;
  const clear = recent.length - flagged;
  const usable = recent.filter((r) => ["GOOD", "FAIR"].includes(String(r.signal_level || "").toUpperCase())).length;
  const lastDevice = [...(devices || [])].sort((a, b) => String(b.last_seen_at || "").localeCompare(String(a.last_seen_at || "")))[0];
  const lastHeard = since(recent.length ? recent[recent.length - 1].timestamp : lastDevice?.last_seen_at);
  const receiving = (() => {
    const d = parseUtc(lastDevice?.last_seen_at);
    return d ? Date.now() - d.getTime() <= 60 * 1000 : false;
  })();

  return (
    <div className={`${card} p-5 space-y-4`} data-testid="hardware-plain-summary">
      <div className="flex flex-wrap items-center gap-2.5">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">In plain words</h3>
        <SourceBadge source="live" />
        {(devices || []).length > 0 && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${receiving
            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"}`}>
            {receiving ? "board is sending data" : lastHeard ? `last heard ${lastHeard}` : "no data received yet"}
          </span>
        )}
      </div>

      {(devices || []).length === 0 && (
        <>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            No real sensor board is registered yet. When one is connected, this box will say in everyday words what it is seeing.
            Nothing is shown here until a real board sends data, so you never see made-up numbers.
          </p>
          <ol className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            <Step n={1} text="A small Wi-Fi board listens to how the room's Wi-Fi signal changes. It has no camera and no microphone." />
            <Step n={2} text="Every few seconds the system looks at about 250 of those signal readings and asks: does this pattern look like a fall?" />
            <Step n={3} text="If it does, the alert says only 'possible fall'. A caregiver checks the person before anyone acts." />
          </ol>
        </>
      )}

      {(devices || []).length > 0 && recent.length === 0 && (
        <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
          A board is registered, but it has not sent enough readings for a first result yet. The first result appears after about 250
          readings, which is a few seconds of data once the board is sending.
        </p>
      )}

      {recent.length > 0 && (
        <>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            The board was last heard {lastHeard}. In its latest {recent.length} checks, <strong>{clear}</strong> showed nothing unusual
            and <strong>{flagged}</strong> looked like a <strong>possible fall</strong>.
          </p>
          <div>
            <div className="flex flex-wrap gap-1.5" role="img" aria-label={`${clear} checks with nothing unusual, ${flagged} possible falls`}>
              {recent.map((r) => (
                isPossibleFall(r)
                  ? <Dot key={r.id} color="#f59e0b" title={`possible fall - needs a person to check (${new Date(parseUtc(r.timestamp) || 0).toLocaleTimeString()})`} />
                  : <Dot key={r.id} color="#10b981" title={`nothing unusual (${new Date(parseUtc(r.timestamp) || 0).toLocaleTimeString()})`} />
              ))}
            </div>
            <div className="text-[11px] text-slate-500 mt-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full align-middle mr-1" style={{ background: "#10b981" }} />nothing unusual
              <span className="inline-block w-2.5 h-2.5 rounded-full align-middle ml-3 mr-1" style={{ background: "#f59e0b" }} />possible fall: a person should check
              <span className="ml-3 text-slate-400">oldest on the left, newest on the right. One dot is one check of about 250 readings.</span>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            The Wi-Fi signal was good or fair (usable) in {usable} of {recent.length} checks; a weak signal makes a check less trustworthy.
            {" "}<strong>What this means:</strong> an amber dot is a request for a person to look, not proof that someone fell. Real hardware
            has no answer key, so this page cannot tell you whether a dot is right. That is why a person always verifies an alert.
          </p>
        </>
      )}
    </div>
  );
}
