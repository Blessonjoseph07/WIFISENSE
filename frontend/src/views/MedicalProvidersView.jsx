import React, { useCallback, useEffect, useState } from "react";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";
const input =
  "w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40";
const primaryBtn =
  "px-3.5 py-2 text-xs font-semibold rounded-xl bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 transition cursor-pointer";
const ghostBtn =
  "px-3 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition cursor-pointer";

const STATUS_STYLE = {
  PENDING: "bg-amber-50 text-amber-700 border-amber-200",
  APPROVED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  SUSPENDED: "bg-red-50 text-red-700 border-red-200",
  REJECTED: "bg-slate-100 text-slate-600 border-slate-200",
};

const fmtDate = (d) => (d ? new Date(d).toLocaleDateString([], { dateStyle: "medium" }) : "");

/** Organization staff: approve doctors and decide exactly which residents each doctor may see. */
export default function MedicalProvidersView({ authToken, API_BASE, residents = [] }) {
  const [providers, setProviders] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [notes, setNotes] = useState({});
  const [pick, setPick] = useState({});
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  const call = useCallback(
    async (path, method = "GET", body) => {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const detail = Array.isArray(data?.detail) ? data.detail.map((d) => d.msg).join("; ") : data?.detail;
        throw new Error(detail || `Request failed (HTTP ${res.status})`);
      }
      return data;
    },
    [API_BASE, authToken]
  );

  const load = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([call("/medical/providers"), call("/medical/assignments")]);
      setProviders(p);
      setAssignments(a);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [call]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (fn, okMessage) => {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await load();
      setError(null);
      setNotice(okMessage);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const review = (id, decision) =>
    act(
      () => call(`/medical/providers/${id}/review`, "PATCH", { decision, note: (notes[id] || "").trim() || null }),
      decision === "APPROVE" ? "Doctor approved." : decision === "REJECT" ? "Application rejected." : "Doctor suspended."
    );

  const assign = (id) =>
    act(async () => {
      if (!pick[id]) throw new Error("Choose a resident first.");
      await call("/medical/assignments", "POST", { doctor_profile_id: id, resident_id: pick[id] });
      setPick({ ...pick, [id]: "" });
    }, "Resident assigned. The doctor can now open their record.");

  const revoke = (assignmentId) => act(() => call(`/medical/assignments/${assignmentId}`, "DELETE"), "Assignment revoked. Access removed immediately.");

  const pending = providers.filter((p) => p.status === "PENDING");
  const others = providers.filter((p) => p.status !== "PENDING");

  return (
    <div className="space-y-6 text-left" data-testid="medical-providers">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Medical providers</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Approve doctors for your organization, then assign the residents each doctor may see. Doctors never see unassigned residents.
        </p>
      </div>

      {error && <div className="p-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm font-medium" role="alert">{error}</div>}
      {notice && !error && <div className="p-3 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-sm font-medium" role="status">{notice}</div>}

      <section className={`${card} p-5`}>
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Pending applications ({pending.length})</h3>
        <div className="space-y-3">
          {pending.length === 0 && <p className="text-sm text-slate-400 italic">No applications waiting.</p>}
          {pending.map((p) => (
            <div key={p.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800">
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{p.doctor_name}</div>
                  <div className="text-xs text-slate-500">
                    {p.specialty} · {p.clinic_name} · Licence {p.license_number}
                  </div>
                  <div className="text-xs text-slate-400">{p.email} · applied {fmtDate(p.created_at)}</div>
                </div>
                <span className={`self-start px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase ${STATUS_STYLE.PENDING}`}>Pending</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-2">Check the licence number yourself before approving. The system does not verify it against any registry.</p>
              <div className="flex flex-wrap gap-2 mt-3">
                <input className={`${input} md:flex-1`} placeholder="Note (required to reject)" value={notes[p.id] || ""} onChange={(e) => setNotes({ ...notes, [p.id]: e.target.value })} />
                <button type="button" disabled={busy} onClick={() => review(p.id, "APPROVE")} className={primaryBtn}>Approve</button>
                <button type="button" disabled={busy} onClick={() => review(p.id, "REJECT")} className={ghostBtn}>Reject</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={`${card} p-5`}>
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">Doctors ({others.length})</h3>
        <div className="space-y-4">
          {others.length === 0 && <p className="text-sm text-slate-400 italic">No reviewed doctors yet.</p>}
          {others.map((p) => {
            const mine = assignments.filter((a) => a.doctor_profile_id === p.id && a.status === "ACTIVE");
            return (
              <div key={p.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <div className="flex flex-wrap justify-between gap-2">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">{p.doctor_name}</div>
                    <div className="text-xs text-slate-500">{p.specialty} · {p.clinic_name}</div>
                    {p.review_note && <div className="text-xs italic text-slate-400 mt-0.5">"{p.review_note}"</div>}
                  </div>
                  <span className={`self-start px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase ${STATUS_STYLE[p.status]}`}>{p.status}</span>
                </div>

                {p.status === "APPROVED" && (
                  <>
                    <div className="mt-3 text-xs font-semibold text-slate-600 dark:text-slate-300">Assigned residents</div>
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {mine.length === 0 && <span className="text-xs text-slate-400 italic">None. This doctor cannot see any resident.</span>}
                      {mine.map((a) => (
                        <span key={a.id} className="inline-flex items-center gap-1.5 pl-3 pr-1 py-1 rounded-full bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-900 text-xs font-semibold text-teal-800 dark:text-teal-200">
                          {a.resident_name}
                          <button type="button" disabled={busy} onClick={() => revoke(a.id)} className="w-5 h-5 rounded-full hover:bg-teal-100 dark:hover:bg-teal-900 cursor-pointer" aria-label={`Revoke ${a.resident_name}`} title="Revoke access">×</button>
                        </span>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      <select className={`${input} md:flex-1`} value={pick[p.id] || ""} onChange={(e) => setPick({ ...pick, [p.id]: e.target.value })} aria-label={`Resident to assign to ${p.doctor_name}`}>
                        <option value="">Choose a resident…</option>
                        {residents
                          .filter((r) => !mine.some((a) => a.resident_id === r.id))
                          .map((r) => (
                            <option key={r.id} value={r.id}>{r.first_name} {r.last_name}</option>
                          ))}
                      </select>
                      <button type="button" disabled={busy} onClick={() => assign(p.id)} className={primaryBtn}>Assign</button>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                      <input className={`${input} md:flex-1`} placeholder="Note (required to suspend)" value={notes[p.id] || ""} onChange={(e) => setNotes({ ...notes, [p.id]: e.target.value })} />
                      <button type="button" disabled={busy} onClick={() => review(p.id, "SUSPEND")} className={ghostBtn}>Suspend</button>
                    </div>
                  </>
                )}

                {p.status === "SUSPENDED" && (
                  <div className="mt-3">
                    <button type="button" disabled={busy} onClick={() => review(p.id, "APPROVE")} className={primaryBtn}>Reinstate</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
