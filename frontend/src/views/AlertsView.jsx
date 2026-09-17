import React, { useState } from "react";

export default function AlertsView({
  alerts = [],
  rooms = [],
  handleAcknowledge = () => {},
  setShowResolveModal = () => {},
  authToken = "",
  API_BASE = "http://127.0.0.1:8000",
  role = "",
  isSystemAdmin = false,
  appContext = "",
}) {
  const isCareOps =
    appContext === "ELDER_CARE" &&
    !isSystemAdmin &&
    role !== "system_admin" &&
    (role === "facility_manager" || role === "caregiver" || role === "organization_admin");

  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const handleOpenDetail = async (alertId) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedDetail(data);
      } else {
        // Fallback to local alert data
        const local = alerts.find((a) => a.id === alertId);
        const room = rooms.find((r) => r.id === local?.room_id);
        setSelectedDetail({
          ...local,
          room_name: room?.name || "Assigned Room",
        });
      }
    } catch (err) {
      console.warn("Failed to fetch alert detail:", err);
      const local = alerts.find((a) => a.id === alertId);
      const room = rooms.find((r) => r.id === local?.room_id);
      setSelectedDetail({
        ...local,
        room_name: room?.name || "Assigned Room",
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div className="space-y-6 text-left">
      {/* Page Title */}
      <div className="flex justify-between items-end mb-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            Alert & Incident Management
          </h2>
          <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">
            Monitor platform-wide incidents, inspect context, and execute operational intervention.
          </p>
        </div>
        <div className="text-body-md font-body-md text-slate-500 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          Live Incident Monitoring: Active
        </div>
      </div>

      {/* Bento Grid Layout for Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
        {/* Pending Alerts Table (Spans 2 columns) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
              <span className="material-symbols-outlined text-red-500">warning</span>
              Pending & Active Alerts
            </h3>
            <span className="bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300 px-2.5 py-1 rounded text-label-caps font-label-caps font-bold">
              {alerts.filter((a) => a.status !== "resolved").length} Active
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-slate-100 dark:bg-slate-850 text-slate-500 dark:text-slate-400 text-label-caps font-label-caps uppercase font-semibold">
                <tr>
                  <th className="p-4">Location/Target</th>
                  <th className="p-4">Event Type</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {alerts
                  .filter((a) => a.status !== "resolved")
                  .map((alert) => {
                    const room = rooms.find((r) => r.id === alert.room_id);
                    const isCritical =
                      alert.severity === "CRITICAL" || alert.event_type === "Fall_Detected";
                    return (
                      <tr
                        key={alert.id}
                        className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors"
                      >
                        <td className="p-4">
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {room?.name || "Room Location"}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            ID: {alert.id.slice(0, 8)}
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">
                            {alert.event_type.replace(/_/g, " ")}
                          </span>
                          <div className="text-[11px] text-slate-500 line-clamp-1 max-w-xs">
                            {alert.message}
                          </div>
                        </td>
                        <td className="p-4 text-slate-500 font-data-mono text-data-mono">
                          {new Date(alert.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>
                        <td className="p-4">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              isCritical
                                ? "bg-red-50 text-red-600 border border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900"
                                : "bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900"
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isCritical ? "bg-red-500 animate-ping" : "bg-amber-500"
                              }`}
                            ></span>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="p-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              alert.status === "new"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300"
                                : alert.status === "responding"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300"
                            }`}
                          >
                            {alert.status}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleOpenDetail(alert.id)}
                              className="px-2.5 py-1 text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-xs font-semibold transition-colors cursor-pointer"
                              title="Inspect Incident Details"
                            >
                              Details
                            </button>
                            {isCareOps ? (
                              <>
                                {alert.status === "new" && (
                                  <button
                                    onClick={() => handleAcknowledge(alert.id)}
                                    className="px-2.5 py-1 text-teal-650 dark:text-teal-400 border border-teal-500/40 hover:bg-teal-50 dark:hover:bg-teal-950/30 rounded font-semibold cursor-pointer text-xs transition-colors"
                                  >
                                    Acknowledge
                                  </button>
                                )}
                                <button
                                  onClick={() => setShowResolveModal(alert.id)}
                                  className="px-2.5 py-1 bg-teal-600 text-white rounded text-xs font-semibold hover:bg-teal-700 transition-colors cursor-pointer shadow-xs"
                                >
                                  Resolve
                                </button>
                              </>
                            ) : (
                              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium italic flex items-center gap-1">
                                <span className="material-symbols-outlined text-[14px] text-teal-600 dark:text-teal-400">visibility</span>
                                Oversight
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                {alerts.filter((a) => a.status !== "resolved").length === 0 && (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-slate-400 italic">
                      No active environmental or fall alerts. All areas nominal.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Resolution History / Activity Stream */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-[500px] shadow-sm text-xs">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
              <span className="material-symbols-outlined text-teal-605">check_circle</span>
              Resolution History
            </h3>
          </div>
          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            {alerts
              .filter((a) => a.status === "resolved")
              .map((a) => (
                <div
                  key={a.id}
                  className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 pb-4 text-left group"
                >
                  <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900"></div>
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                      {rooms.find((r) => r.id === a.room_id)?.name || "Room"} Details
                    </h4>
                    <span className="text-data-mono font-data-mono text-slate-400">
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-500 mb-2">{a.message || "Verified safe. Alert cleared."}</p>
                  <button
                    onClick={() => handleOpenDetail(a.id)}
                    className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold hover:underline cursor-pointer flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[13px]">visibility</span> View Full Incident Audit
                  </button>
                </div>
              ))}
            {alerts.filter((a) => a.status === "resolved").length === 0 && (
              <div className="p-8 text-center text-slate-400 italic">
                No resolved log database entries found.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alert Details Modal */}
      {selectedDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden text-left">
            {/* Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950">
              <div className="flex items-center gap-3">
                <span className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white shadow-xs ${
                  selectedDetail.severity === "CRITICAL" ? "bg-red-600" : "bg-amber-500"
                }`}>
                  <span className="material-symbols-outlined text-[20px]">
                    {selectedDetail.event_type === "Fall_Detected" ? "emergency" : "warning"}
                  </span>
                </span>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    {selectedDetail.event_type.replace(/_/g, " ")} Incident
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    ID: {selectedDetail.id}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  selectedDetail.status === "new"
                    ? "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300"
                    : selectedDetail.status === "resolved"
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300"
                    : "bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300"
                }`}>
                  {selectedDetail.status}
                </span>
                <button
                  onClick={() => setSelectedDetail(null)}
                  className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center transition cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            </div>

            {/* Content Body */}
            <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto text-xs">
              {/* Context Summary Grid */}
              <div className="grid grid-cols-2 gap-3 bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800">
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Location</div>
                  <div className="font-semibold text-slate-900 dark:text-white mt-0.5 text-sm">
                    {selectedDetail.room_name || "Assigned Room"}
                  </div>
                  <div className="text-slate-500 mt-0.5">
                    {selectedDetail.building_name || "Main Facility"} • Floor {selectedDetail.floor_number ?? "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Organization & Context</div>
                  <div className="font-semibold text-slate-900 dark:text-white mt-0.5 text-sm">
                    {selectedDetail.organization_name || "WIFISENSE Network"}
                  </div>
                  <div className="text-slate-500 mt-0.5">
                    Context: <span className="font-mono font-bold text-teal-600 dark:text-teal-400">{selectedDetail.organization_type || "SYSTEM"}</span>
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Detected Timestamp</div>
                  <div className="font-mono text-slate-700 dark:text-slate-300 mt-0.5">
                    {new Date(selectedDetail.created_at).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Resident Under Care</div>
                  <div className="font-semibold text-slate-900 dark:text-white mt-0.5">
                    {selectedDetail.resident_name || "N/A (Spatial Area)"}
                  </div>
                </div>
              </div>

              {/* Message */}
              <div className="p-3 bg-red-50/60 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 rounded-xl text-red-900 dark:text-red-200">
                <div className="text-[10px] uppercase font-bold text-red-600 mb-0.5">Incident Dispatch Message</div>
                <p className="font-medium text-xs">{selectedDetail.message}</p>
              </div>

              {/* Emergency Contact Information (If available for resident) */}
              {selectedDetail.emergency_contact && (
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[14px] text-teal-600">contact_phone</span>
                      Primary Emergency Contact
                    </span>
                    <span className="text-[10px] bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded font-mono">
                      Priority {selectedDetail.emergency_contact.priority}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white text-sm">
                        {selectedDetail.emergency_contact.name} ({selectedDetail.emergency_contact.relationship})
                      </div>
                      <div className="text-slate-500 font-mono mt-0.5">
                        {selectedDetail.emergency_contact.phone}
                      </div>
                    </div>
                    <a
                      href={`tel:${selectedDetail.emergency_contact.phone.replace(/[^0-9+]/g, "")}`}
                      className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg font-bold text-xs hover:bg-emerald-700 transition-colors flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[14px]">call</span> Call
                    </a>
                  </div>
                </div>
              )}

              {/* Acknowledgement & Resolution Attribution */}
              {selectedDetail.acknowledgement && (
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl space-y-2">
                  <div className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[14px] text-teal-600">verified_user</span>
                    Operational Attribution & Lifecycle
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-slate-400">Acknowledged By:</span>{" "}
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {selectedDetail.acknowledgement.user_name || selectedDetail.acknowledgement.user_email || selectedDetail.acknowledgement.user_id || "Staff Officer"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400">Acknowledged At:</span>{" "}
                      <span className="font-mono text-slate-700 dark:text-slate-300">
                        {new Date(selectedDetail.acknowledgement.acknowledged_at).toLocaleString()}
                      </span>
                    </div>
                    {selectedDetail.acknowledgement.resolved_at && (
                      <div className="col-span-2 pt-1 border-t border-slate-200 dark:border-slate-700">
                        <div>
                          <span className="text-slate-400">Resolved At:</span>{" "}
                          <span className="font-mono text-slate-700 dark:text-slate-300">
                            {new Date(selectedDetail.acknowledgement.resolved_at).toLocaleString()}
                          </span>
                        </div>
                        {selectedDetail.acknowledgement.resolution_notes && (
                          <div className="mt-1 text-slate-700 dark:text-slate-300 italic bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-800">
                            "{selectedDetail.acknowledgement.resolution_notes}"
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
              <button
                type="button"
                onClick={() => setSelectedDetail(null)}
                className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              >
                Close
              </button>
              {isCareOps ? (
                <div className="flex gap-2">
                  {selectedDetail.status === "new" && (
                    <button
                      onClick={async () => {
                        await handleAcknowledge(selectedDetail.id);
                        setSelectedDetail((prev) => ({ ...prev, status: "acknowledged" }));
                      }}
                      className="px-3 py-2 border border-teal-500 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/30 rounded-lg text-xs font-bold uppercase transition cursor-pointer"
                    >
                      Acknowledge
                    </button>
                  )}
                  {selectedDetail.status !== "resolved" && (
                    <button
                      onClick={() => {
                        const id = selectedDetail.id;
                        setSelectedDetail(null);
                        setShowResolveModal(id);
                      }}
                      className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold uppercase transition cursor-pointer shadow-sm"
                    >
                      Resolve Incident
                    </button>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold">
                  <span className="material-symbols-outlined text-sm text-teal-600 dark:text-teal-400">visibility</span>
                  <span>GLOBAL OVERSIGHT — Monitoring incident response</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
