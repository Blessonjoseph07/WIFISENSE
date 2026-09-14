import React, { useState, useEffect } from "react";

export default function ResidentProfileModal({ residentId, onClose, authToken }) {
  const [activeTab, setActiveTab] = useState("personal"); // personal, medical, safety, contacts
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!residentId || !authToken) return;
    setLoading(true);
    fetch(`http://127.0.0.1:8000/residents/${residentId}/profile-details`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: Access Denied or Resident Not Found`);
        return res.json();
      })
      .then((data) => {
        setProfile(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [residentId, authToken]);

  if (!residentId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in text-left">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-lg shadow-sm">
              {profile ? profile.first_name[0] + profile.last_name[0] : "R"}
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                {profile ? `${profile.first_name} ${profile.last_name}` : "Resident Profile"}
              </h3>
              <p className="text-xs text-slate-500 font-mono">
                {profile?.room_name || "Suite"} • Status: {profile?.resident_status || "Active"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-900/50 px-6 gap-2">
          {[
            { id: "personal", label: "Personal", icon: "person" },
            { id: "medical", label: "Medical Records", icon: "medical_services" },
            { id: "safety", label: "Safety & CSI", icon: "health_and_safety" },
            { id: "contacts", label: "Emergency Contacts", icon: "contact_phone" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-3.5 text-xs font-bold flex items-center gap-1.5 border-b-2 transition-all ${
                activeTab === tab.id
                  ? "border-teal-600 text-teal-600 dark:text-teal-400 bg-white dark:bg-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              <span className="material-symbols-outlined text-sm">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {loading && (
            <div className="p-8 text-center text-slate-400">Loading resident details...</div>
          )}

          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm font-semibold border border-red-200">
              {error}
            </div>
          )}

          {profile && !loading && (
            <>
              {/* TAB 1: PERSONAL INFORMATION */}
              {activeTab === "personal" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        FULL NAME
                      </span>
                      <span className="font-semibold text-slate-900 dark:text-white text-sm">
                        {profile.first_name} {profile.last_name}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        DATE OF BIRTH
                      </span>
                      <span className="font-semibold text-slate-900 dark:text-white text-sm">
                        {profile.date_of_birth
                          ? new Date(profile.date_of_birth).toLocaleDateString()
                          : "Recorded at admission"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        ASSIGNED ROOM
                      </span>
                      <span className="font-semibold text-slate-900 dark:text-white text-sm font-mono">
                        {profile.room_name}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        RESIDENCE STATUS
                      </span>
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600 text-xs mt-0.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        {profile.resident_status}
                      </span>
                    </div>
                  </div>

                  <div className="border border-slate-200 dark:border-slate-800 p-4 rounded-xl">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">
                      Care Facility Placement
                    </h4>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      Resident is admitted under continuous elder-care monitoring. Wi-Fi CSI sensing node is provisioned in {profile.room_name} to ensure non-invasive privacy-preserving safety tracking.
                    </p>
                  </div>
                </div>
              )}

              {/* TAB 2: MEDICAL INFORMATION */}
              {activeTab === "medical" && (
                <div className="space-y-4 text-xs">
                  {/* Health Conditions */}
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-teal-600 text-base">monitor_heart</span>
                      Active Clinical Conditions
                    </h4>
                    <div className="space-y-2">
                      {profile.health_conditions.length > 0 ? (
                        profile.health_conditions.map((c) => (
                          <div key={c.id} className="p-3 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-lg">
                            <span className="font-bold text-slate-900 dark:text-white text-xs">{c.condition_name}</span>
                            {c.notes && <p className="text-slate-500 text-[11px] mt-0.5">{c.notes}</p>}
                          </div>
                        ))
                      ) : (
                        <p className="text-slate-400 italic">No chronic conditions logged.</p>
                      )}
                    </div>
                  </div>

                  {/* Doctors */}
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-teal-600 text-base">stethoscope</span>
                      Assigned Medical Officers & Specialists
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {profile.doctors.map((d) => (
                        <div key={d.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900">
                          <p className="font-bold text-slate-900 dark:text-white">{d.name}</p>
                          <p className="text-slate-500 text-[11px]">{d.specialty} • {d.hospital || "Medical Clinic"}</p>
                          {d.phone && <p className="text-slate-600 dark:text-slate-300 font-mono text-[11px] mt-1">{d.phone}</p>}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Hospital Visits */}
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-teal-600 text-base">local_hospital</span>
                      Recent Clinical Visits & Assessments
                    </h4>
                    <div className="space-y-2">
                      {profile.hospital_visits.map((v) => (
                        <div key={v.id} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-800/30">
                          <div className="flex justify-between items-start">
                            <strong className="text-slate-900 dark:text-white">{v.hospital_name}</strong>
                            <span className="text-[10px] font-mono text-slate-400">{new Date(v.visit_date).toLocaleDateString()}</span>
                          </div>
                          <p className="text-slate-600 dark:text-slate-300 text-[11px] mt-0.5">{v.reason}</p>
                          {v.doctor_notes && <p className="text-slate-500 italic text-[11px] mt-1">"{v.doctor_notes}"</p>}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Lab Reports & Prescriptions */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Lab Test Results</h4>
                      <div className="space-y-2">
                        {profile.lab_reports.map((lr) => (
                          <div key={lr.id} className="p-2.5 border border-slate-200 dark:border-slate-800 rounded-lg">
                            <div className="flex justify-between">
                              <span className="font-bold text-slate-800 dark:text-white">{lr.test_name}</span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${lr.flag === "ELEVATED" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>
                                {lr.flag}
                              </span>
                            </div>
                            <p className="font-mono text-[11px] text-slate-600 dark:text-slate-300 mt-1">{lr.result_summary}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Prescription Regimen</h4>
                      <div className="space-y-2">
                        {profile.prescriptions.map((rx) => (
                          <div key={rx.id} className="p-2.5 border border-slate-200 dark:border-slate-800 rounded-lg">
                            <span className="font-bold text-slate-800 dark:text-white">{rx.medication_name} ({rx.dosage})</span>
                            <p className="text-slate-500 text-[11px] mt-0.5">{rx.frequency}</p>
                            {rx.prescribing_doctor && <p className="text-slate-400 text-[10px]">Rx by: {rx.prescribing_doctor}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: SAFETY & TELEMETRY */}
              {activeTab === "safety" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">CURRENT ACTIVITY</span>
                      <span className="font-bold text-base text-slate-900 dark:text-white mt-0.5 block">{profile.current_activity}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">SAFETY STATUS</span>
                      <span className={`font-bold text-base mt-0.5 block ${profile.safety_status === "EMERGENCY" ? "text-red-600" : "text-emerald-600"}`}>
                        {profile.safety_status}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">ACTIVE ALERTS</span>
                      <span className="font-bold text-base text-slate-900 dark:text-white mt-0.5 block">
                        {profile.active_alert ? "1 Active" : "None (Normal)"}
                      </span>
                    </div>
                  </div>

                  {profile.latest_sensing_event && (
                    <div className="p-4 border border-teal-200 dark:border-teal-900/50 bg-teal-50/40 dark:bg-teal-950/20 rounded-xl text-xs">
                      <h4 className="font-bold text-teal-800 dark:text-teal-300 text-sm mb-2 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-base">sensors</span>
                        Wi-Fi CSI Signal Telemetry (RuView-inspired)
                      </h4>
                      <div className="grid grid-cols-4 gap-2 font-mono">
                        <div>
                          <span className="text-slate-400 text-[10px] block">SIGNAL QUALITY</span>
                          <strong className="text-teal-700 dark:text-teal-400 text-sm">{profile.latest_sensing_event.signal_quality}%</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">SUBCARRIERS</span>
                          <strong className="text-slate-700 dark:text-slate-200 text-sm">{profile.latest_sensing_event.subcarriers}</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">RSSI</span>
                          <strong className="text-slate-700 dark:text-slate-200 text-sm">{profile.latest_sensing_event.rssi} dBm</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">CONFIDENCE</span>
                          <strong className="text-teal-700 dark:text-teal-400 text-sm">{Math.round(profile.latest_sensing_event.confidence * 100)}%</strong>
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm mb-2">Recent Spatial Telemetry Log</h4>
                    <div className="space-y-1 text-xs">
                      {profile.recent_activity_history.map((ev, idx) => (
                        <div key={idx} className="flex justify-between p-2 rounded bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800 font-mono">
                          <span className="text-slate-500">{ev.timestamp}</span>
                          <span className="font-bold text-slate-800 dark:text-white">{ev.activity}</span>
                          <span className="text-teal-600 font-semibold">{ev.confidence}% conf</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: EMERGENCY CONTACTS */}
              {activeTab === "contacts" && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-xs text-slate-500">
                      Every resident has designated emergency contacts. Telephony actions open native device dialer via <code className="text-teal-600">tel:</code> link.
                    </p>
                  </div>
                  {profile.emergency_contacts.map((c) => (
                    <div key={c.id} className="p-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-800/30 flex justify-between items-center text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <strong className="text-slate-900 dark:text-white text-sm">{c.name}</strong>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 dark:bg-teal-900/60 text-teal-800 dark:text-teal-300">
                            Priority {c.priority}
                          </span>
                        </div>
                        <p className="text-slate-500 mt-0.5">
                          Relationship: <strong className="text-slate-700 dark:text-slate-300">{c.relationship}</strong> • {c.availability}
                        </p>
                        <p className="font-mono text-slate-700 dark:text-slate-300 mt-1 font-semibold">{c.phone}</p>
                      </div>
                      <a
                        href={`tel:${c.phone.replace(/[^0-9+]/g, "")}`}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold flex items-center gap-1.5 shadow-sm transition"
                      >
                        <span className="material-symbols-outlined text-sm">call</span>
                        Call
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-bold border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            Close Profile
          </button>
        </div>
      </div>
    </div>
  );
}
