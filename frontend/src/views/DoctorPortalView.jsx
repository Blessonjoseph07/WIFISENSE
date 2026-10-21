import React, { useCallback, useEffect, useState } from "react";
import { ConfidenceBadge, SourceBadge, VerificationChip } from "../components/DetectionBadges";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";
const input =
  "w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40";
const primaryBtn =
  "px-4 py-2 text-sm font-semibold rounded-xl bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 transition cursor-pointer";
const ghostBtn =
  "px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer";

const SEVERITY_STYLE = {
  SEVERE: "bg-red-50 text-red-700 border-red-200",
  MODERATE: "bg-amber-50 text-amber-700 border-amber-200",
  MILD: "bg-slate-100 text-slate-600 border-slate-200",
};

const fmt = (d) => (d ? new Date(d).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "");
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString([], { dateStyle: "medium" }) : "");

export default function DoctorPortalView({ authToken, API_BASE }) {
  const [profile, setProfile] = useState(null);
  const [residents, setResidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [record, setRecord] = useState(null);
  const [tab, setTab] = useState("overview");
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  const [consult, setConsult] = useState({ reason: "", notes: "", follow_up_date: "" });
  const [allergy, setAllergy] = useState({ allergen: "", reaction: "", severity: "MODERATE" });
  const [condition, setCondition] = useState({ condition_name: "", notes: "" });
  const [rx, setRx] = useState({ medication_name: "", dosage: "", frequency: "" });

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

  const loadOverview = useCallback(async () => {
    try {
      const [p, r, a] = await Promise.all([call("/medical/me"), call("/medical/my-residents"), call("/medical/my-alerts?limit=10")]);
      setProfile(p);
      setResidents(r);
      setAlerts(a);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [call]);

  const loadRecord = useCallback(
    async (id) => {
      try {
        setRecord(await call(`/medical/residents/${id}/record`));
        setError(null);
      } catch (e) {
        setRecord(null);
        setError(e.message);
      }
    },
    [call]
  );

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    if (selectedId) loadRecord(selectedId);
  }, [selectedId, loadRecord]);

  const act = async (fn, okMessage) => {
    setBusy(true);
    setNotice(null);
    try {
      await fn();
      await loadRecord(selectedId);
      setNotice(okMessage);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const submitConsult = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/medical/residents/${selectedId}/consultations`, "POST", {
        reason: consult.reason.trim(),
        notes: consult.notes.trim() || null,
        follow_up_date: consult.follow_up_date ? new Date(consult.follow_up_date).toISOString() : null,
      });
      setConsult({ reason: "", notes: "", follow_up_date: "" });
    }, "Consultation recorded.");
  };

  const submitAllergy = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/medical/residents/${selectedId}/allergies`, "POST", {
        allergen: allergy.allergen.trim(),
        reaction: allergy.reaction.trim() || null,
        severity: allergy.severity,
      });
      setAllergy({ allergen: "", reaction: "", severity: "MODERATE" });
    }, "Allergy recorded.");
  };

  const submitCondition = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/medical/residents/${selectedId}/conditions`, "POST", {
        condition_name: condition.condition_name.trim(),
        notes: condition.notes.trim() || null,
      });
      setCondition({ condition_name: "", notes: "" });
    }, "Condition recorded.");
  };

  const submitRx = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/medical/residents/${selectedId}/prescriptions`, "POST", {
        medication_name: rx.medication_name.trim(),
        dosage: rx.dosage.trim(),
        frequency: rx.frequency.trim(),
      });
      setRx({ medication_name: "", dosage: "", frequency: "" });
    }, "Medication recorded.");
  };

  const toggleFollowUp = (c) =>
    act(() => call(`/medical/consultations/${c.id}/follow-up`, "PATCH", { done: !c.follow_up_done }), "Follow-up updated.");

  const needsAttention = alerts.filter((a) => a.requires_verification || a.status !== "resolved").length;

  return (
    <div className="space-y-6 text-left" data-testid="doctor-portal">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Medical portal</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {profile ? `${profile.clinic_name} · ${profile.specialty} · ${profile.organization_name}` : "Your assigned residents"}
          </p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
          You can only see residents assigned to you
        </span>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm font-medium" role="alert">
          {error}
        </div>
      )}
      {notice && !error && (
        <div className="p-3 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-sm font-medium" role="status">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: residents + alerts */}
        <div className="space-y-4">
          <div className={`${card} p-4`}>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">My residents ({residents.length})</h3>
            <div className="space-y-2">
              {residents.length === 0 && <p className="text-sm text-slate-400 italic">No residents assigned yet. Ask the care organization to assign you.</p>}
              {residents.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => {
                    setSelectedId(r.id);
                    setTab("overview");
                    setNotice(null);
                  }}
                  className={`w-full text-left p-3 rounded-xl border transition cursor-pointer ${
                    selectedId === r.id
                      ? "border-teal-500 bg-teal-50 dark:bg-teal-950/30"
                      : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  }`}
                >
                  <div className="font-semibold text-sm text-slate-900 dark:text-white">{r.name}</div>
                  <div className="text-xs text-slate-500">{r.room_name || "Room not recorded"}</div>
                </button>
              ))}
            </div>
          </div>

          <div className={`${card} p-4`}>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">Fall alerts for my residents</h3>
            <p className="text-xs text-slate-500 mb-3">{needsAttention} need attention</p>
            <div className="space-y-2">
              {alerts.length === 0 && <p className="text-sm text-slate-400 italic">No fall alerts.</p>}
              {alerts.map((a) => (
                <div key={a.alert_id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                  <div className="flex justify-between gap-2">
                    <span className="font-semibold text-sm text-slate-900 dark:text-white">{a.resident_name}</span>
                    <span className="text-[11px] text-slate-500">{fmt(a.created_at)}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    <SourceBadge source={a.source} />
                    <ConfidenceBadge level={a.confidence_level} confidence={a.confidence} />
                    <VerificationChip alert={a} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: record */}
        <div className="lg:col-span-2">
          {!selectedId && (
            <div className={`${card} p-10 text-center text-slate-400`}>
              <span className="material-symbols-outlined text-4xl block mb-2">stethoscope</span>
              Select a resident to open their medical record.
            </div>
          )}

          {selectedId && record && (
            <div className={`${card} overflow-hidden`}>
              <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">{record.resident.name}</h3>
                <p className="text-xs text-slate-500">
                  {record.resident.room_name || "Room not recorded"}
                  {record.resident.date_of_birth ? ` · Born ${fmtDate(record.resident.date_of_birth)}` : ""}
                </p>
              </div>

              <div className="flex gap-1 px-4 pt-3 border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
                {[
                  ["overview", "Overview"],
                  ["consultations", "Consultations"],
                  ["add", "Add record"],
                  ["alerts", "Fall alerts"],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setTab(id)}
                    className={`px-3 py-2 text-sm font-semibold border-b-2 transition cursor-pointer whitespace-nowrap ${
                      tab === id ? "border-teal-600 text-teal-700 dark:text-teal-300" : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="p-6 space-y-6 text-sm">
                {tab === "overview" && (
                  <>
                    <section>
                      <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Allergies</h4>
                      <div className="flex flex-wrap gap-2">
                        {record.allergies.length === 0 && <span className="text-slate-400 italic">None recorded.</span>}
                        {record.allergies.map((a) => (
                          <span key={a.id} className={`px-2.5 py-1 rounded-full border text-xs font-semibold ${SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.MILD}`}>
                            {a.allergen}
                            {a.reaction ? ` · ${a.reaction}` : ""} · {a.severity.toLowerCase()}
                          </span>
                        ))}
                      </div>
                    </section>
                    <section>
                      <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Conditions</h4>
                      <ul className="space-y-1.5">
                        {record.conditions.length === 0 && <li className="text-slate-400 italic">None recorded.</li>}
                        {record.conditions.map((c) => (
                          <li key={c.id}>
                            <span className="font-medium text-slate-800 dark:text-slate-200">{c.name}</span>
                            {c.notes && <span className="text-slate-500"> — {c.notes}</span>}
                          </li>
                        ))}
                      </ul>
                    </section>
                    <section>
                      <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Medications</h4>
                      <ul className="space-y-1.5">
                        {record.prescriptions.length === 0 && <li className="text-slate-400 italic">None recorded.</li>}
                        {record.prescriptions.map((p) => (
                          <li key={p.id}>
                            <span className="font-medium text-slate-800 dark:text-slate-200">
                              {p.medication} ({p.dosage})
                            </span>
                            <span className="text-slate-500"> — {p.frequency}{p.prescribed_by ? ` · by ${p.prescribed_by}` : ""}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                    <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Lab results</h4>
                        <ul className="space-y-1.5">
                          {record.lab_reports.length === 0 && <li className="text-slate-400 italic">None recorded.</li>}
                          {record.lab_reports.map((l) => (
                            <li key={l.id} className="text-slate-700 dark:text-slate-300">
                              {l.test}: {l.result} <span className="text-slate-400">({l.flag})</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Hospital visits</h4>
                        <ul className="space-y-1.5">
                          {record.hospital_visits.length === 0 && <li className="text-slate-400 italic">None recorded.</li>}
                          {record.hospital_visits.map((v) => (
                            <li key={v.id} className="text-slate-700 dark:text-slate-300">
                              {fmtDate(v.date)} · {v.hospital}: {v.reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </section>
                  </>
                )}

                {tab === "consultations" && (
                  <div className="space-y-3">
                    {record.consultations.length === 0 && <p className="text-slate-400 italic">No consultations recorded.</p>}
                    {record.consultations.map((c) => (
                      <div key={c.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                        <div className="flex justify-between gap-3">
                          <div>
                            <div className="font-semibold text-slate-900 dark:text-white">{c.reason}</div>
                            <div className="text-xs text-slate-500">
                              {fmt(c.consulted_at)} · {c.doctor_name}
                            </div>
                          </div>
                          {c.follow_up_date && (
                            <button type="button" disabled={busy} onClick={() => toggleFollowUp(c)} className={ghostBtn}>
                              {c.follow_up_done ? "Follow-up done" : `Follow-up ${fmtDate(c.follow_up_date)}`}
                            </button>
                          )}
                        </div>
                        {c.notes && <p className="mt-2 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{c.notes}</p>}
                      </div>
                    ))}
                  </div>
                )}

                {tab === "add" && (
                  <div className="space-y-8">
                    <form onSubmit={submitConsult} className="space-y-3">
                      <h4 className="font-semibold text-slate-900 dark:text-white">Consultation and doctor notes</h4>
                      <input required className={input} placeholder="Reason for visit" value={consult.reason} onChange={(e) => setConsult({ ...consult, reason: e.target.value })} />
                      <textarea rows={3} className={input} placeholder="Doctor notes" value={consult.notes} onChange={(e) => setConsult({ ...consult, notes: e.target.value })} />
                      <label className="block text-xs text-slate-500">
                        Follow-up date (optional)
                        <input type="datetime-local" className={`${input} mt-1`} value={consult.follow_up_date} onChange={(e) => setConsult({ ...consult, follow_up_date: e.target.value })} />
                      </label>
                      <button type="submit" disabled={busy} className={primaryBtn}>Save consultation</button>
                    </form>

                    <form onSubmit={submitAllergy} className="grid grid-cols-1 md:grid-cols-4 gap-2 items-end">
                      <h4 className="font-semibold text-slate-900 dark:text-white md:col-span-4">Allergy</h4>
                      <input required className={input} placeholder="Allergen" value={allergy.allergen} onChange={(e) => setAllergy({ ...allergy, allergen: e.target.value })} />
                      <input className={input} placeholder="Reaction" value={allergy.reaction} onChange={(e) => setAllergy({ ...allergy, reaction: e.target.value })} />
                      <select className={input} value={allergy.severity} onChange={(e) => setAllergy({ ...allergy, severity: e.target.value })} aria-label="Severity">
                        <option value="MILD">Mild</option>
                        <option value="MODERATE">Moderate</option>
                        <option value="SEVERE">Severe</option>
                      </select>
                      <button type="submit" disabled={busy} className={primaryBtn}>Add allergy</button>
                    </form>

                    <form onSubmit={submitCondition} className="grid grid-cols-1 md:grid-cols-3 gap-2 items-end">
                      <h4 className="font-semibold text-slate-900 dark:text-white md:col-span-3">Condition</h4>
                      <input required className={input} placeholder="Condition" value={condition.condition_name} onChange={(e) => setCondition({ ...condition, condition_name: e.target.value })} />
                      <input className={input} placeholder="Notes" value={condition.notes} onChange={(e) => setCondition({ ...condition, notes: e.target.value })} />
                      <button type="submit" disabled={busy} className={primaryBtn}>Add condition</button>
                    </form>

                    <form onSubmit={submitRx} className="grid grid-cols-1 md:grid-cols-4 gap-2 items-end">
                      <h4 className="font-semibold text-slate-900 dark:text-white md:col-span-4">Medication</h4>
                      <input required className={input} placeholder="Medication" value={rx.medication_name} onChange={(e) => setRx({ ...rx, medication_name: e.target.value })} />
                      <input required className={input} placeholder="Dosage" value={rx.dosage} onChange={(e) => setRx({ ...rx, dosage: e.target.value })} />
                      <input required className={input} placeholder="Frequency" value={rx.frequency} onChange={(e) => setRx({ ...rx, frequency: e.target.value })} />
                      <button type="submit" disabled={busy} className={primaryBtn}>Add medication</button>
                    </form>
                  </div>
                )}

                {tab === "alerts" && (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-500">
                      Falls detected in this resident's room. Detections that are simulated or low-confidence are marked and need staff verification.
                    </p>
                    {record.recent_fall_alerts.length === 0 && <p className="text-slate-400 italic">No fall alerts.</p>}
                    {record.recent_fall_alerts.map((a) => (
                      <div key={a.alert_id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                        <div className="text-xs text-slate-500">{fmt(a.created_at)} · {a.status}</div>
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          <SourceBadge source={a.source} />
                          <ConfidenceBadge level={a.confidence_level} confidence={a.confidence} />
                          <VerificationChip alert={a} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
