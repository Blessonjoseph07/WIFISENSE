import React, { useCallback, useEffect, useState } from "react";
import { API_BASE } from "../config";


const STATUS_STYLE = {
  SCHEDULED: "bg-sky-100 text-sky-800",
  COMPLETED: "bg-emerald-100 text-emerald-800",
  CANCELLED: "bg-slate-200 text-slate-600",
  GIVEN: "bg-emerald-100 text-emerald-800",
  MISSED: "bg-amber-100 text-amber-800",
  REFUSED: "bg-red-100 text-red-800",
};

const inputCls =
  "w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white";
const btnCls =
  "px-3 py-1.5 text-xs font-bold rounded-lg bg-teal-600 hover:bg-teal-700 text-white disabled:opacity-50 transition";
const ghostBtn =
  "px-2 py-1 text-[10px] font-bold rounded border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition";

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "";
}

/**
 * Real stored care records for one resident: doctors, appointments, medication log.
 * Everything shown here is entered by staff through the API. Nothing is simulated.
 */
export default function CareRecordsPanel({ residentId, authToken }) {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [medLog, setMedLog] = useState([]);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  const [docForm, setDocForm] = useState({ name: "", specialty: "", hospital: "", phone: "" });
  const [apptForm, setApptForm] = useState({ scheduled_at: "", purpose: "", doctor_id: "" });

  const call = useCallback(
    async (path, method = "GET", body) => {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        const detail = Array.isArray(data?.detail)
          ? data.detail.map((d) => d.msg).join("; ")
          : data?.detail;
        throw new Error(detail || `Request failed (HTTP ${res.status})`);
      }
      return data;
    },
    [authToken]
  );

  const load = useCallback(async () => {
    try {
      const [d, a, p, m] = await Promise.all([
        call(`/residents/${residentId}/doctors`),
        call(`/residents/${residentId}/appointments`),
        call(`/residents/${residentId}/prescriptions`),
        call(`/residents/${residentId}/medication-log?limit=15`),
      ]);
      setDoctors(d);
      setAppointments(a);
      setPrescriptions(p);
      setMedLog(m);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [call, residentId]);

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

  const addDoctor = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/residents/${residentId}/doctors`, "POST", {
        resident_id: residentId,
        name: docForm.name.trim(),
        specialty: docForm.specialty.trim(),
        hospital: docForm.hospital.trim() || null,
        phone: docForm.phone.trim() || null,
      });
      setDocForm({ name: "", specialty: "", hospital: "", phone: "" });
    }, "Doctor added.");
  };

  const addAppointment = (e) => {
    e.preventDefault();
    act(async () => {
      await call(`/residents/${residentId}/appointments`, "POST", {
        scheduled_at: new Date(apptForm.scheduled_at).toISOString(),
        purpose: apptForm.purpose.trim(),
        doctor_id: apptForm.doctor_id || null,
      });
      setApptForm({ scheduled_at: "", purpose: "", doctor_id: "" });
    }, "Appointment scheduled.");
  };

  const setApptStatus = (id, status) =>
    act(() => call(`/appointments/${id}`, "PATCH", { status }), `Appointment marked ${status.toLowerCase()}.`);

  const removeDoctor = (id) => {
    if (!window.confirm("Remove this doctor? Appointment history is kept.")) return;
    act(() => call(`/doctors/${id}`, "DELETE"), "Doctor removed.");
  };

  const logDose = (rxId, status) =>
    act(() => call(`/prescriptions/${rxId}/administer`, "POST", { status }), `Dose recorded as ${status}.`);

  const activeRx = prescriptions.filter((rx) => !rx.end_date || new Date(rx.end_date) >= new Date());

  return (
    <div className="space-y-5 text-xs" data-testid="care-records-panel">
      <p className="text-[11px] text-slate-500">
        Records on this tab are entered by staff and stored in the database. They are not sensor output.
      </p>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg font-semibold border border-red-200" role="alert">
          {error}
        </div>
      )}
      {notice && !error && (
        <div className="p-3 bg-emerald-50 text-emerald-800 rounded-lg font-semibold border border-emerald-200" role="status">
          {notice}
        </div>
      )}

      {/* Appointments */}
      <section>
        <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Appointments</h4>
        <form onSubmit={addAppointment} className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-3">
          <input
            type="datetime-local"
            required
            className={inputCls}
            value={apptForm.scheduled_at}
            onChange={(e) => setApptForm({ ...apptForm, scheduled_at: e.target.value })}
            aria-label="Appointment date and time"
          />
          <input
            required
            maxLength={200}
            placeholder="Purpose (e.g. BP review)"
            className={inputCls}
            value={apptForm.purpose}
            onChange={(e) => setApptForm({ ...apptForm, purpose: e.target.value })}
          />
          <select
            className={inputCls}
            value={apptForm.doctor_id}
            onChange={(e) => setApptForm({ ...apptForm, doctor_id: e.target.value })}
            aria-label="Doctor"
          >
            <option value="">No doctor selected</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.specialty})
              </option>
            ))}
          </select>
          <button type="submit" className={btnCls} disabled={busy}>
            Schedule
          </button>
        </form>
        <div className="space-y-2">
          {appointments.length === 0 && <p className="text-slate-400 italic">No appointments recorded.</p>}
          {appointments.map((a) => (
            <div key={a.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg flex justify-between items-start gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <strong className="text-slate-900 dark:text-white">{a.purpose}</strong>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${STATUS_STYLE[a.status] || ""}`}>{a.status}</span>
                </div>
                <p className="text-slate-500 text-[11px] mt-0.5">
                  {fmt(a.scheduled_at)}
                  {a.doctor_name ? ` • ${a.doctor_name}` : ""}
                </p>
                {a.notes && <p className="text-slate-500 italic text-[11px] mt-0.5">"{a.notes}"</p>}
              </div>
              {a.status === "SCHEDULED" && (
                <div className="flex gap-1 shrink-0">
                  <button className={ghostBtn} disabled={busy} onClick={() => setApptStatus(a.id, "COMPLETED")}>
                    Complete
                  </button>
                  <button className={ghostBtn} disabled={busy} onClick={() => setApptStatus(a.id, "CANCELLED")}>
                    Cancel
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Doctors */}
      <section>
        <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Doctors</h4>
        <form onSubmit={addDoctor} className="grid grid-cols-1 md:grid-cols-5 gap-2 mb-3">
          <input required placeholder="Name" className={inputCls} value={docForm.name} onChange={(e) => setDocForm({ ...docForm, name: e.target.value })} />
          <input required placeholder="Specialty" className={inputCls} value={docForm.specialty} onChange={(e) => setDocForm({ ...docForm, specialty: e.target.value })} />
          <input placeholder="Hospital / clinic" className={inputCls} value={docForm.hospital} onChange={(e) => setDocForm({ ...docForm, hospital: e.target.value })} />
          <input placeholder="Phone" className={inputCls} value={docForm.phone} onChange={(e) => setDocForm({ ...docForm, phone: e.target.value })} />
          <button type="submit" className={btnCls} disabled={busy}>
            Add doctor
          </button>
        </form>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {doctors.length === 0 && <p className="text-slate-400 italic">No doctors assigned.</p>}
          {doctors.map((d) => (
            <div key={d.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg flex justify-between items-start">
              <div>
                <p className="font-bold text-slate-900 dark:text-white">{d.name}</p>
                <p className="text-slate-500 text-[11px]">
                  {d.specialty} • {d.hospital || "Clinic not recorded"}
                </p>
                {d.phone && <p className="font-mono text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">{d.phone}</p>}
              </div>
              <button className={ghostBtn} disabled={busy} onClick={() => removeDoctor(d.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Medication log */}
      <section>
        <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Medication administration</h4>
        <div className="space-y-2 mb-3">
          {activeRx.length === 0 && <p className="text-slate-400 italic">No active prescriptions.</p>}
          {activeRx.map((rx) => (
            <div key={rx.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg flex justify-between items-center gap-3">
              <div>
                <strong className="text-slate-900 dark:text-white">
                  {rx.medication_name} ({rx.dosage})
                </strong>
                <p className="text-slate-500 text-[11px]">{rx.frequency}</p>
              </div>
              <div className="flex gap-1 shrink-0">
                {["GIVEN", "MISSED", "REFUSED"].map((s) => (
                  <button key={s} className={ghostBtn} disabled={busy} onClick={() => logDose(rx.id, s)}>
                    {s[0] + s.slice(1).toLowerCase()}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-1">
          {medLog.map((l) => (
            <div key={l.id} className="flex justify-between p-2 rounded bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800 font-mono">
              <span className="text-slate-500">{fmt(l.administered_at)}</span>
              <span className="font-bold text-slate-800 dark:text-white">{l.medication_name}</span>
              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${STATUS_STYLE[l.status] || ""}`}>{l.status}</span>
              <span className="text-slate-500">{l.administered_by_name || "—"}</span>
            </div>
          ))}
          {medLog.length === 0 && <p className="text-slate-400 italic">No doses logged yet.</p>}
        </div>
      </section>
    </div>
  );
}
