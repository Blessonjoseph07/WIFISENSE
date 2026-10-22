import React, { useEffect, useMemo, useState } from "react";
import { SourceBadge } from "./DetectionBadges";

const fullName = (r) => `${r.first_name} ${r.last_name}`.trim();
const telHref = (p) => `tel:${String(p || "").replace(/[^+\d]/g, "")}`;

function Step({ n, title, hint, children }) {
  return (
    <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
      <div className="flex items-center gap-3 mb-3">
        <span className="w-6 h-6 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs font-bold flex items-center justify-center shrink-0">{n}</span>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{title}</h4>
          {hint && <p className="text-[11px] text-slate-500 dark:text-slate-400">{hint}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function CallButton({ phone, big }) {
  if (!phone) return <span className="text-[11px] text-slate-400">no number on file</span>;
  return (
    <a href={telHref(phone)}
      className={`inline-flex items-center gap-1.5 rounded-full font-bold transition-all hover:scale-[1.03] active:scale-95 ${big
        ? "px-4 py-2 text-sm bg-red-600 text-white shadow-md hover:bg-red-700"
        : "px-3 py-1 text-[11px] border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"}`}>
      <span className="material-symbols-outlined text-[16px]">call</span>
      Call {big ? phone : ""}
    </a>
  );
}

/**
 * Emergency protocol for ONE resident. Everything shown (contacts, medical summary, doctors) is read from that
 * resident's record; nothing is invented. The only action that sends anything is "Message doctors", and its result says
 * per doctor what was really delivered.
 */
export default function EmergencyProtocolModal({ onClose, residents = [], activeFallAlert = null, token, API_BASE, setToastMessage = () => {} }) {
  const candidates = useMemo(() => {
    const list = activeFallAlert ? residents.filter((r) => r.room_id === activeFallAlert.room_id) : residents;
    return [...list].sort((a, b) => fullName(a).localeCompare(fullName(b)));
  }, [residents, activeFallAlert]);

  const [selectedId, setSelectedId] = useState(() => (candidates.length === 1 ? candidates[0].id : ""));
  const [detail, setDetail] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [sending, setSending] = useState(false);
  const [note, setNote] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!selectedId) return undefined;
    let alive = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/residents/${selectedId}/profile-details`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (alive) { setDetail(data); setLoadError(null); }
      } catch (e) {
        if (alive) setLoadError(`Could not load this resident's record (${e.message}).`);
      }
    })();
    return () => { alive = false; };
  }, [selectedId, API_BASE, token]);

  const choose = (id) => {
    setSelectedId(id);
    setDetail(null);
    setLoadError(null);
    setResult(null);
  };

  const sendToDoctors = async () => {
    setSending(true);
    try {
      const res = await fetch(`${API_BASE}/medical/residents/${selectedId}/notify-doctors`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ alert_id: activeFallAlert?.id || null, note: note.trim() || null }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setResult(body);
      setToastMessage({ type: "success", text: body.summary });
    } catch (e) {
      setToastMessage({ type: "error", text: `Doctors were not notified: ${e.message}` });
    } finally {
      setSending(false);
    }
  };

  const contacts = detail?.emergency_contacts || [];
  const [primary, ...others] = contacts;
  const conditions = (detail?.health_conditions || []).filter((c) => c.is_active);
  const meds = detail?.prescriptions || [];
  const doctors = detail?.doctors || [];

  return (
    <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center p-3 sm:p-6 bg-slate-950/70 backdrop-blur-sm overflow-y-auto animate-fade-in" role="dialog" aria-modal="true" aria-label="Emergency protocol">
      <div className="w-full max-w-2xl rounded-3xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden my-4">
        <div className="h-1.5 bg-gradient-to-r from-red-500 via-red-600 to-red-500" />
        <div className="p-5 sm:p-6 space-y-4">
          <header className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="material-symbols-outlined text-red-600 text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>emergency</span>
                <h3 className="text-lg font-extrabold text-slate-900 dark:text-white tracking-tight">Emergency protocol</h3>
                {activeFallAlert && <SourceBadge source={activeFallAlert.source} />}
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-0.5">
                {detail ? <><strong>{fullName(detail)}</strong> · {detail.room_name}</> : activeFallAlert ? "Fall alert: who is it?" : "Choose the resident this is about."}
              </p>
              {activeFallAlert && <p className="text-[11px] text-slate-500 mt-0.5">{activeFallAlert.message}</p>}
            </div>
            <button type="button" onClick={onClose} aria-label="Close" className="p-2 rounded-full text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer">
              <span className="material-symbols-outlined">close</span>
            </button>
          </header>

          {candidates.length !== 1 && (
            <div>
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">{activeFallAlert ? "Residents in this room: who fell?" : "Resident"}</label>
              <div className="mt-1.5 flex flex-wrap gap-2">
                {candidates.length <= 6 ? candidates.map((r) => (
                  <button key={r.id} type="button" onClick={() => choose(r.id)} aria-pressed={selectedId === r.id}
                    className={`px-3.5 py-1.5 rounded-full text-sm font-semibold border transition-all cursor-pointer ${selectedId === r.id
                      ? "bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-900 shadow"
                      : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:border-slate-500"}`}>
                    {fullName(r)}
                  </button>
                )) : (
                  <select value={selectedId} onChange={(e) => choose(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm">
                    <option value="">Select a resident…</option>
                    {candidates.map((r) => <option key={r.id} value={r.id}>{fullName(r)}</option>)}
                  </select>
                )}
              </div>
            </div>
          )}

          {!selectedId && <p className="text-sm text-slate-500 text-center py-6">Pick the resident to see who to call and which doctors to inform.</p>}
          {loadError && <div className="p-3 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 text-sm" role="alert">{loadError}</div>}
          {selectedId && !detail && !loadError && <div className="h-40 rounded-2xl bg-slate-200/60 dark:bg-slate-800/50 animate-pulse" />}

          {detail && (
            <>
              <Step n="1" title="Call the closest relative first" hint="The emergency contact with the highest priority on this resident's record.">
                {primary ? (
                  <div className="rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/60 p-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-bold text-slate-900 dark:text-white">{primary.name} <span className="font-normal text-slate-500">· {primary.relationship}</span></div>
                      <div className="text-[11px] text-slate-500 font-mono truncate">{primary.email || "no email on file"} · {primary.availability || "availability not recorded"}</div>
                    </div>
                    <CallButton phone={primary.phone} big />
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 text-sm text-amber-800 dark:text-amber-200">
                    No emergency contact is on file for {fullName(detail)}. Add one in the resident profile.
                  </div>
                )}
                {others.length > 0 && (
                  <ul className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
                    {others.map((c) => (
                      <li key={c.id} className="py-2 flex items-center justify-between gap-3 text-sm">
                        <span className="min-w-0"><strong className="text-slate-800 dark:text-slate-100">{c.name}</strong> <span className="text-slate-500">· {c.relationship}</span></span>
                        <CallButton phone={c.phone} />
                      </li>
                    ))}
                  </ul>
                )}
              </Step>

              <Step n="2" title="Medical summary" hint="From the resident's record. Share it with the responders.">
                <div className="grid sm:grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-1">Active conditions</div>
                    {conditions.length ? (
                      <div className="flex flex-wrap gap-1.5">{conditions.map((c) => (
                        <span key={c.id} title={c.notes || ""} className="px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-semibold">{c.condition_name}</span>
                      ))}</div>
                    ) : <span className="text-slate-400 text-xs">none recorded</span>}
                  </div>
                  <div>
                    <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-1">Medication</div>
                    {meds.length ? (
                      <ul className="space-y-0.5 text-xs text-slate-700 dark:text-slate-200">{meds.slice(0, 6).map((m) => (
                        <li key={m.id}><strong>{m.medication_name}</strong> <span className="text-slate-500">{m.dosage}, {m.frequency}</span></li>
                      ))}</ul>
                    ) : <span className="text-slate-400 text-xs">none recorded</span>}
                  </div>
                </div>
              </Step>

              <Step n="3" title="Inform the doctors" hint="Sends a message to this resident's doctors. Approved doctors receive it in their portal; others by email if one is on file.">
                {doctors.length > 0 && (
                  <ul className="mb-3 divide-y divide-slate-100 dark:divide-slate-800">
                    {doctors.map((d) => (
                      <li key={d.id} className="py-2 flex items-center justify-between gap-3 text-sm">
                        <span className="min-w-0"><strong className="text-slate-800 dark:text-slate-100">{d.name}</strong> <span className="text-slate-500">· {d.specialty}{d.hospital ? ` · ${d.hospital}` : ""}</span></span>
                        <CallButton phone={d.phone} />
                      </li>
                    ))}
                  </ul>
                )}
                {!result ? (
                  <div className="space-y-2">
                    <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} placeholder="Optional note for the doctors"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm" aria-label="Note for the doctors" />
                    <button type="button" onClick={sendToDoctors} disabled={sending}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-200 text-white dark:text-slate-900 font-bold text-sm flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-60 cursor-pointer">
                      <span className="material-symbols-outlined text-[18px]">{sending ? "hourglass_top" : "send"}</span>
                      {sending ? "Sending…" : `Message doctors: ${fullName(detail)} has fallen`}
                    </button>
                  </div>
                ) : (
                  <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 p-3 text-sm">
                    <div className="font-bold text-emerald-900 dark:text-emerald-200 mb-1.5">{result.summary}</div>
                    {result.results.length === 0 && <p className="text-emerald-900/80 dark:text-emerald-200/80 text-xs">No doctor is linked to this resident, so nobody was messaged. Call the emergency contact above.</p>}
                    <ul className="space-y-1">
                      {result.results.map((r, i) => {
                        const ok = r.status.startsWith("delivered") || r.status.startsWith("email sent") || r.status.startsWith("already");
                        return (
                          <li key={i} className="flex items-start gap-2 text-xs">
                            <span className={`material-symbols-outlined text-[16px] ${ok ? "text-emerald-600" : "text-amber-600"}`}>{ok ? "check_circle" : "warning"}</span>
                            <span><strong>{r.doctor}</strong> <span className="text-slate-500">({r.specialty})</span>: {r.status}{r.phone && !ok ? ` · ${r.phone}` : ""}</span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </Step>
            </>
          )}

          <div className="flex justify-end pt-1">
            <button type="button" onClick={onClose} className="px-5 py-2 rounded-full border border-slate-300 dark:border-slate-700 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer">Close</button>
          </div>
        </div>
      </div>
    </div>
  );
}
