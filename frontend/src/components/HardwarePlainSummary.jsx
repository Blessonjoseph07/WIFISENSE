import React from "react";
import { SourceBadge } from "./DetectionBadges";
import MovementIndicator from "./MovementIndicator";
import OccupancyLearner from "./OccupancyLearner";

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

function Step({ n, text }) {
  return (
    <li className="flex gap-2.5 items-start">
      <span className="w-5 h-5 shrink-0 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 text-[11px] font-bold flex items-center justify-center">{n}</span>
      <span>{text}</span>
    </li>
  );
}

/**
 * Plain-language view of the LIVE HARDWARE mode. Live hardware is judged on what the Wi-Fi link can honestly show: whether the room
 * looks occupied and whether something is moving, against an empty-room reference. Fall detection is off for live hardware because
 * its model was trained on a public dataset and has not been validated in this room, so no "possible fall" is shown here.
 */
export default function HardwarePlainSummary({ devices, deviceId, authToken, API_BASE }) {
  const list = devices || [];
  const lastDevice = [...list].sort((a, b) => String(b.last_seen_at || "").localeCompare(String(a.last_seen_at || "")))[0];
  const lastHeard = since(lastDevice?.last_seen_at);
  const receiving = (() => {
    const d = parseUtc(lastDevice?.last_seen_at);
    return d ? Date.now() - d.getTime() <= 60 * 1000 : false;
  })();

  return (
    <div className={`${card} p-5 space-y-4`} data-testid="hardware-plain-summary">
      <div className="flex flex-wrap items-center gap-2.5">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">In plain words</h3>
        <SourceBadge source="live" />
        {list.length > 0 && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${receiving
            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"}`}>
            {receiving ? "board is sending data" : lastHeard ? `last heard ${lastHeard}` : "no data received yet"}
          </span>
        )}
      </div>

      {list.length === 0 && (
        <>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            No real sensor board is registered yet. When one is connected, this box will say in everyday words whether the room looks
            occupied and whether something is moving. Nothing is shown until a real board sends data, so you never see made-up numbers.
          </p>
          <ol className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            <Step n={1} text="One small Wi-Fi board sends a signal and a second one listens. Neither has a camera or a microphone." />
            <Step n={2} text="People in the room change that signal. The system compares it with how it looked when the room was empty." />
            <Step n={3} text="If the signal stays above the empty-room level the room is probably occupied; if it jumps around, something is moving." />
          </ol>
        </>
      )}

      {deviceId && <MovementIndicator deviceId={deviceId} authToken={authToken} API_BASE={API_BASE} />}
      {deviceId && <OccupancyLearner deviceId={deviceId} authToken={authToken} API_BASE={API_BASE} />}

      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
        <strong>What this means:</strong> this view tells you whether the room looks occupied and whether anything is moving. It does not
        count people, find where they are, or identify anyone. Fall detection is switched off for live hardware, because the fall model was
        trained on a public dataset and has not been checked in this room. Falls are shown only for recorded dataset replays, where the
        answers are known.
      </p>
    </div>
  );
}
