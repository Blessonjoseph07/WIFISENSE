import React, { useState } from "react";
import { phoneProblem } from "../phone";

/**
 * The care home's helpline: the number approved family members see in the family portal. Only the facility's manager (or a system
 * administrator) can change it, and nothing is invented: a care home with no number shows "Helpline not set" to families.
 */
export default function HelplineSettings({ organizations = [], authToken, API_BASE, onSaved = () => {} }) {
  const homes = organizations.filter((o) => o.type === "ELDER_CARE");
  const [drafts, setDrafts] = useState({});
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(null);
  if (homes.length === 0) return null;

  const save = async (org) => {
    const value = (drafts[org.id] ?? org.contact_phone ?? "").trim();
    const problem = phoneProblem(value);
    if (problem) {
      setMessage({ ok: false, text: problem });
      return;
    }
    setBusy(org.id);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/organizations/${org.id}/contact`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({ contact_phone: value || null }),
      });
      const out = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(out.detail) ? out.detail.map((d) => d.msg).join(" ") : out.detail;
        throw new Error(detail || `HTTP ${res.status}`);
      }
      setMessage({ ok: true, text: value ? `Saved. Families of ${org.name} now see ${value}.` : `Cleared. Families of ${org.name} see that no helpline is set.` });
      onSaved();
    } catch (e) {
      setMessage({ ok: false, text: e.message });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xs" data-testid="helpline-settings">
      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-emerald-600">call</span>
        <h3 className="font-bold text-slate-900 dark:text-white text-sm">Care home helpline</h3>
      </div>
      <p className="text-xs text-slate-500 mt-1">The number family members call from their portal. Use the facility's real desk number.</p>
      <div className="mt-3 space-y-2">
        {homes.map((org) => {
          const draft = drafts[org.id];
          const problem = draft !== undefined ? phoneProblem(draft) : null;   // only judge what the manager typed
          const savedProblem = draft === undefined && org.contact_phone ? phoneProblem(org.contact_phone) : null;
          return (
          <div key={org.id} className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 min-w-[180px]">{org.name}</span>
            <input
              type="tel"
              value={drafts[org.id] ?? org.contact_phone ?? ""}
              onChange={(e) => setDrafts((d) => ({ ...d, [org.id]: e.target.value }))}
              placeholder="e.g. +91 481 2xx xxxx"
              className={`border rounded-lg px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white font-mono ${
                problem ? "border-rose-400 dark:border-rose-700" : "border-slate-200 dark:border-slate-700"}`}
              maxLength={24}
              aria-label={`Helpline for ${org.name}`}
              aria-invalid={Boolean(problem)}
            />
            <button type="button" disabled={busy === org.id || Boolean(problem)} onClick={() => save(org)}
                    className="px-3 py-1.5 bg-teal-600 text-white rounded-full text-[11px] font-bold uppercase disabled:opacity-50">
              {busy === org.id ? "Saving..." : "Save"}
            </button>
            {problem && <div className="basis-full text-[11px] text-rose-600 sm:pl-[188px]" role="alert">{problem}</div>}
            {savedProblem && (
              <div className="basis-full text-[11px] text-amber-700 sm:pl-[188px]" role="alert">
                The saved number is not valid ({savedProblem}), so families see "Helpline not set". Enter the correct number and save.
              </div>
            )}
          </div>
          );
        })}
      </div>
      {message && <div className={`mt-2 text-xs ${message.ok ? "text-emerald-700 dark:text-emerald-300" : "text-rose-600"}`}>{message.text}</div>}
    </div>
  );
}
