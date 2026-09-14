import React, { useState } from "react";
import ResidentProfileModal from "../components/ResidentProfileModal";

export default function CaregiverView({
  activeFallAlert = null,
  handleAcknowledge = () => {},
  setShowResolveModal = () => {},
  alerts = [],
  residents = [],
  healthRecords = {},
  rooms = [],
  occupancySummary = { occupied_room_details: [] },
  setCurrentView = () => {},
  authToken = "",
}) {
  const [selectedResidentId, setSelectedResidentId] = useState(null);
  const token = authToken || localStorage.getItem("token") || "";

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="mb-stack-lg flex justify-between items-end">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold flex items-center gap-2">
            <span className="material-symbols-outlined text-teal-600 text-3xl">health_and_safety</span>
            Elder Care & Safety
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Real-time resident monitoring, clinical profiles, emergency contacts, and fall protocol.
          </p>
        </div>
        <div className="text-xs font-bold text-slate-500 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          System Scan Status: Normal
        </div>
      </div>

      {/* Critical Alert Banner */}
      {activeFallAlert && (
        <div className="bg-red-50 border border-red-500 text-red-700 dark:bg-red-950/20 dark:text-red-400 rounded-lg p-4 mb-6 flex items-center justify-between shadow-sm pulse-animation">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined fill text-red-500 text-2xl">warning</span>
            <div>
              <h2 className="text-headline-sm font-headline-sm font-bold uppercase text-red-700">
                POTENTIAL FALL DETECTED - {activeFallAlert.message.split(" ")[0] || "Room"}
              </h2>
              <p className="text-body-md font-body-md">{activeFallAlert.message}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleAcknowledge(activeFallAlert.id)}
              className="px-4 py-2 bg-transparent border border-red-500 text-red-600 rounded font-body-md font-semibold hover:bg-red-500/10 transition-colors"
            >
              Acknowledge
            </button>
            <button
              onClick={() => setShowResolveModal(activeFallAlert.id)}
              className="px-4 py-2 bg-red-600 text-white rounded font-body-md font-semibold hover:opacity-90 transition-opacity"
            >
              Dispatch Help
            </button>
          </div>
        </div>
      )}

      {/* Dashboard Layout: 12-column Grid */}
      <div className="grid grid-cols-12 gap-gutter">
        {/* Left Column: Active Incidents & Assigned Residents (8 cols on desktop) */}
        <div className="col-span-12 xl:col-span-8 flex flex-col gap-gutter">
          {/* Active Incidents Table */}
          <section className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                Active Incidents
              </h3>
              <span
                className={`px-2 py-1 rounded text-label-caps font-label-caps ${
                  alerts.filter((a) => a.status !== "resolved").length > 0
                    ? "bg-red-50 text-red-600 font-bold"
                    : "bg-teal-50 text-teal-600 font-bold"
                }`}
              >
                {alerts.filter((a) => a.status !== "resolved").length} Active
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 uppercase">
                  <tr>
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Room</th>
                    <th className="px-5 py-3">Resident</th>
                    <th className="px-5 py-3">Type</th>
                    <th className="px-5 py-3">Time</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-body-md font-body-md">
                  {alerts
                    .filter((a) => a.status !== "resolved")
                    .map((a) => {
                      const assignedResident = residents.find((r) => r.room_id === a.room_id);
                      const residentConditions = assignedResident
                        ? healthRecords[assignedResident.id]?.conditions || []
                        : [];
                      return (
                        <tr key={a.id} className="bg-red-50/20 dark:bg-red-950/10">
                          <td className="px-5 py-4">
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-red-600"></span>
                              <span className="text-red-600 font-semibold">
                                {a.event_type === "Fall_Detected" ? "Critical" : "Warning"}
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-4 font-data-mono text-data-mono">
                            {rooms.find((r) => r.id === a.room_id)?.name || "Room"}
                          </td>
                          <td className="px-5 py-4">
                            <div className="font-semibold text-slate-900 dark:text-white">
                              {assignedResident
                                ? `${assignedResident.first_name} ${assignedResident.last_name}`
                                : "Unassigned"}
                            </div>
                            {residentConditions.filter((c) => c.is_active).length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {residentConditions
                                  .filter((c) => c.is_active)
                                  .map((c) => (
                                    <span
                                      key={c.condition_name}
                                      className="inline-flex items-center gap-1 bg-red-50 text-red-600 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-200"
                                    >
                                      <span className="material-symbols-outlined text-[10px]">
                                        medical_information
                                      </span>
                                      {c.condition_name}
                                    </span>
                                  ))}
                              </div>
                            )}
                          </td>
                          <td className="px-5 py-4">{a.event_type.replace("_", " ")}</td>
                          <td className="px-5 py-4 text-slate-500 font-data-mono text-data-mono">
                            {new Date(a.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="px-5 py-4 text-right">
                            {a.status === "new" && (
                              <button
                                onClick={() => handleAcknowledge(a.id)}
                                className="text-teal-650 hover:underline mr-3 font-semibold cursor-pointer"
                              >
                                Acknowledge
                              </button>
                            )}
                            <button
                              onClick={() => setShowResolveModal(a.id)}
                              className="px-3 py-1 bg-teal-600 text-white rounded hover:opacity-90 transition-opacity cursor-pointer font-semibold text-xs"
                            >
                              Resolve
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  {alerts.filter((a) => a.status !== "resolved").length === 0 && (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-slate-400 italic">
                        No pending health incidents. All clear.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Assigned Residents Grid */}
          <section>
            <div className="flex justify-between items-end mb-4">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                Assigned Residents Overview
              </h3>
              <div className="flex gap-2">
                <span className="flex items-center gap-1 text-label-caps font-label-caps text-slate-550">
                  <span className="w-2 h-2 bg-teal-500 rounded-full"></span> Monitored
                </span>
                <span className="flex items-center gap-1 text-label-caps font-label-caps text-slate-550">
                  <span className="w-2 h-2 bg-slate-300 rounded-full"></span> Vacant
                </span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {residents.map((res) => {
                const rm = rooms.find((r) => r.id === res.room_id);
                const isFall =
                  rm &&
                  occupancySummary.occupied_room_details.find((d) => d.room_id === rm.id)
                    ?.current_activity === "Fall_Detected";
                return (
                  <div
                    key={res.id}
                    onClick={() => {
                      setSelectedResidentId(res.id);
                    }}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col gap-3 hover:border-teal-500 transition-colors cursor-pointer group shadow-2xs hover:shadow-md"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center text-teal-700 dark:text-teal-400 font-headline-sm font-bold">
                          {res.first_name[0]}
                          {res.last_name[0]}
                        </div>
                        <div>
                          <h4 className="font-bold text-slate-900 dark:text-white">
                            {res.first_name} {res.last_name}
                          </h4>
                          <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                            <span>{rm?.name || "Unassigned"}</span>
                            {rm?.classification && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono">
                                {rm.classification}
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                      <span
                        className={`material-symbols-outlined ${
                          isFall ? "text-red-500 fill animate-bounce" : "text-teal-650"
                        }`}
                        title="Assigned Subject"
                      >
                        {isFall ? "emergency_home" : "home"}
                      </span>
                    </div>
                    {(() => {
                      const detail = occupancySummary.occupied_room_details.find(
                        (d) => d.room_id === res.room_id
                      );
                      const currAct = detail?.current_activity || "Resting";
                      const lastUp = detail?.last_updated;
                      return (
                        <div className="bg-slate-50 dark:bg-slate-950 rounded-lg p-3 mt-2 flex justify-between items-center text-xs">
                          <div>
                            <p className="text-[10px] font-bold text-slate-400 uppercase">
                              ACTIVITY STATUS
                            </p>
                            <p className="font-semibold text-slate-800 dark:text-white flex items-center gap-1 mt-0.5">
                              <span className="material-symbols-outlined text-[16px] text-teal-600">
                                {currAct === "Walking"
                                  ? "directions_walk"
                                  : currAct === "Sitting"
                                  ? "airline_seat_recline_normal"
                                  : currAct === "Fall_Detected"
                                  ? "warning"
                                  : "bed"}
                              </span>
                              {currAct.replace("_", " ")}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-[10px] font-bold text-slate-400 uppercase">
                              LAST DETECTED
                            </p>
                            <p className="font-data-mono text-slate-800 dark:text-white text-[11px] mt-0.5">
                              {lastUp
                                ? new Date(lastUp).toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                    second: "2-digit",
                                  })
                                : "Standby"}
                            </p>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                );
              })}
            </div>
          </section>
        </div>

        {/* Right Column: Alert History Sidebar (4 cols on desktop) */}
        <aside className="col-span-12 xl:col-span-4 flex flex-col gap-gutter">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm h-full flex flex-col">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold flex items-center gap-2">
                <span className="material-symbols-outlined text-slate-500">history</span>
                Alert Timeline
              </h3>
              <button
                onClick={() => setCurrentView("alerts")}
                className="text-teal-605 text-label-caps font-label-caps font-semibold hover:underline"
              >
                View All
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
              {alerts.map((al) => (
                <div
                  key={al.id}
                  className="relative pl-6 pb-4 border-l-2 border-slate-200 dark:border-slate-800 last:border-0 last:pb-0"
                >
                  <span
                    className={`absolute left-[-9px] top-0 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 ${
                      al.status === "resolved" ? "bg-slate-400" : "bg-red-500 animate-pulse"
                    }`}
                  ></span>
                  <div className="flex justify-between items-start mb-1 text-xs">
                    <span className="text-slate-400 font-data-mono">
                      {new Date(al.created_at).toLocaleTimeString()}
                    </span>
                    <span
                      className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded-full ${
                        al.status === "resolved"
                          ? "bg-slate-100 text-slate-600"
                          : "bg-red-50 text-red-600"
                      }`}
                    >
                      {al.status}
                    </span>
                  </div>
                  <p className="font-bold text-slate-900 dark:text-white text-sm">
                    {al.event_type.replace("_", " ")}
                  </p>
                  <p className="text-xs text-slate-550">
                    {rooms.find((r) => r.id === al.room_id)?.name || "Room"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* Resident Clinical & CSI Profile Modal */}
      {selectedResidentId && (
        <ResidentProfileModal
          residentId={selectedResidentId}
          onClose={() => setSelectedResidentId(null)}
          authToken={token}
        />
      )}
    </div>
  );
}
