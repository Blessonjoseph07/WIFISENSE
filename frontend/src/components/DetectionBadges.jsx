import React, { useState } from "react";

/**
 * Shared presentation of detection evidence: confidence, signal quality, data source and staff verification.
 * Levels (HIGH/MEDIUM/LOW, GOOD/FAIR/POOR) are computed by the backend from the raw numbers; this file only displays them.
 */

const LEVEL_STYLE = {
  HIGH: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900",
  GOOD: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900",
  FAIR: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900",
  LOW: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900",
  POOR: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900",
  UNKNOWN: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

const SOURCE_META = {
  simulated: { label: "Simulated", cls: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950/40 dark:text-violet-300 dark:border-violet-900", icon: "science" },
  dataset: { label: "Dataset replay", cls: "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900", icon: "history" },
  live: { label: "Live CSI", cls: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900", icon: "sensors" },
};

const chip = "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wide";

const titleCase = (s) => (s ? s.charAt(0) + s.slice(1).toLowerCase() : "");

export function ConfidenceBadge({ level = "UNKNOWN", confidence = null }) {
  const pct = confidence === null || confidence === undefined ? null : Math.round(confidence * 100);
  return (
    <span className={`${chip} ${LEVEL_STYLE[level] || LEVEL_STYLE.UNKNOWN}`} title="Detection confidence">
      {level === "UNKNOWN" ? "Confidence unknown" : `${titleCase(level)} confidence${pct !== null ? ` · ${pct}%` : ""}`}
    </span>
  );
}

export function SignalBadge({ level = "UNKNOWN", quality = null }) {
  return (
    <span className={`${chip} ${LEVEL_STYLE[level] || LEVEL_STYLE.UNKNOWN}`} title="Signal quality">
      {level === "UNKNOWN" ? "Signal unknown" : `${titleCase(level)} signal${quality !== null && quality !== undefined ? ` · ${quality}` : ""}`}
    </span>
  );
}

export function SourceBadge({ source = "simulated" }) {
  const meta = SOURCE_META[source] || SOURCE_META.simulated;
  return (
    <span className={`${chip} ${meta.cls}`} title="Where this data came from">
      <span className="material-symbols-outlined text-[12px]">{meta.icon}</span>
      {meta.label}
    </span>
  );
}

export function VerificationChip({ alert }) {
  if (alert.verification_status === "CONFIRMED") {
    return <span className={`${chip} ${LEVEL_STYLE.HIGH}`}>Confirmed by staff</span>;
  }
  if (alert.verification_status === "DISMISSED") {
    return <span className={`${chip} ${LEVEL_STYLE.UNKNOWN}`}>Dismissed</span>;
  }
  if (alert.requires_verification) {
    return (
      <span className={`${chip} ${LEVEL_STYLE.MEDIUM}`}>
        <span className="material-symbols-outlined text-[12px]">pending_actions</span>
        Verification required
      </span>
    );
  }
  return null;
}

/** Compact chip row for table rows and cards. */
export function DetectionChips({ alert }) {
  return (
    <div className="flex flex-wrap gap-1 mt-1">
      <SourceBadge source={alert.source} />
      <ConfidenceBadge level={alert.confidence_level} confidence={alert.confidence} />
      <SignalBadge level={alert.signal_level} quality={alert.signal_quality} />
      <VerificationChip alert={alert} />
    </div>
  );
}

/** Full evidence block for the alert detail view. */
export function DetectionEvidence({ alert }) {
  return (
    <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
      <div className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[14px] text-teal-600">query_stats</span>
        Detection evidence
      </div>
      <DetectionChips alert={alert} />
      <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
        <div>
          <span className="text-slate-400">Device:</span>{" "}
          <span className="font-mono text-slate-700 dark:text-slate-300">{alert.device_mac || "Not recorded"}</span>
        </div>
        <div>
          <span className="text-slate-400">Detected:</span>{" "}
          <span className="font-mono text-slate-700 dark:text-slate-300">{new Date(alert.created_at).toLocaleString()}</span>
        </div>
      </div>
      {alert.confidence_level === "UNKNOWN" && (
        <p className="text-[11px] text-slate-500">
          This alert carries no sensing evidence (for example demo or manually created data), so it cannot be treated as a confirmed detection.
        </p>
      )}
      {alert.source !== "live" && (
        <p className="text-[11px] text-violet-700 dark:text-violet-300">
          {alert.source === "dataset" ? "Replayed from a recorded dataset." : "Simulated for demonstration. Not captured from a real person."}
        </p>
      )}
    </div>
  );
}

/** Confirm / dismiss control. Shows the recorded outcome once a decision exists. */
export function VerificationPanel({ alert, canVerify, authToken, API_BASE, onVerified }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (alert.verification_status !== "UNVERIFIED") {
    return (
      <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl text-[11px] space-y-1">
        <div className="text-[10px] uppercase font-bold text-slate-500">Verification outcome</div>
        <VerificationChip alert={alert} />
        <p className="text-slate-600 dark:text-slate-300">
          {alert.verified_by_name ? `By ${alert.verified_by_name}` : "By staff"}
          {alert.verified_at ? ` · ${new Date(alert.verified_at.endsWith("Z") ? alert.verified_at : `${alert.verified_at}Z`).toLocaleString()}` : ""}
        </p>
        {alert.verification_note && <p className="italic text-slate-600 dark:text-slate-300">"{alert.verification_note}"</p>}
      </div>
    );
  }

  const submit = async (outcome) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/alerts/${alert.id}/verify`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ outcome, note: note.trim() || null }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const detail = Array.isArray(data?.detail) ? data.detail.map((d) => d.msg).join("; ") : data?.detail;
        throw new Error(detail || `Request failed (HTTP ${res.status})`);
      }
      onVerified(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className={`p-3.5 rounded-xl border space-y-2 ${
        alert.requires_verification
          ? "bg-amber-50/70 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/50"
          : "bg-slate-50 border-slate-200 dark:bg-slate-800/40 dark:border-slate-800"
      }`}
    >
      <div className="text-[10px] uppercase font-bold text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[14px] text-amber-600">pending_actions</span>
        {alert.requires_verification ? "Verification required" : "Staff verification"}
      </div>
      <p className="text-[11px] text-slate-600 dark:text-slate-300">
        {alert.requires_verification
          ? "Confidence or signal quality is not good enough to treat this as a confirmed event. Check on the resident, then record the outcome."
          : "Record whether this detection was correct. Outcomes are kept for later accuracy analysis."}
      </p>
      {canVerify ? (
        <>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={500}
            rows={2}
            placeholder="Note (required to dismiss)"
            className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
            aria-label="Verification note"
          />
          {error && (
            <div className="text-[11px] text-red-700 font-semibold" role="alert">
              {error}
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => submit("CONFIRMED")}
              className="px-3 py-1.5 text-xs font-bold rounded-lg bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 transition cursor-pointer"
            >
              Confirm detection
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => submit("DISMISSED")}
              className="px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition cursor-pointer"
            >
              Dismiss as false alarm
            </button>
          </div>
        </>
      ) : (
        <p className="text-[11px] italic text-slate-500">Only care staff of this organization can record the outcome.</p>
      )}
    </div>
  );
}
