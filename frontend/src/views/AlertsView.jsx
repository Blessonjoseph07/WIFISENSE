import React, { useState } from "react";

export default function AlertsView({
  alerts = [],
  rooms = [],
  floors = [],
  buildings = [],
  organizations = [],
  residents = [],
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

  const [contextFilter, setContextFilter] = useState("ALL"); // "ALL" | "ELDER_CARE" | "CORPORATE"
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const getAlertContext = (alert) => {
    if (alert.organization_type) {
      return {
        type: alert.organization_type, // "ELDER_CARE" or "CORPORATE"
        orgName: alert.organization_name || "Facility",
        roomName: alert.room_name || "Assigned Room",
        residentName: alert.resident_name || null,
        buildingName: alert.building_name || "",
      };
    }
    const room = rooms.find((r) => r.id === alert.room_id);
    const floor = floors.find((f) => f.id === room?.floor_id);
    const bld = buildings.find((b) => b.id === floor?.building_id);
    const org = organizations.find((o) => o.id === bld?.organization_id);
    const res = residents.find((rs) => rs.room_id === room?.id);
    return {
      type: org?.type || "ELDER_CARE",
      orgName: org?.name || "Facility",
      roomName: room?.name || "Assigned Room",
      buildingName: bld?.name || "",
      residentName: org?.type === "ELDER_CARE" && res ? `${res.first_name} ${res.last_name}` : null,
    };
  };

  const activeAlerts = alerts.filter((a) => a.status !== "resolved");
  const countAll = activeAlerts.length;
  const countElder = activeAlerts.filter((a) => getAlertContext(a).type === "ELDER_CARE").length;
  const countCorp = activeAlerts.filter((a) => getAlertContext(a).type === "CORPORATE").length;

  const filteredActiveAlerts = activeAlerts.filter((a) => {
    if (contextFilter === "ALL") return true;
    return getAlertContext(a).type === contextFilter;
  });

  const resolvedAlerts = alerts.filter((a) => a.status === "resolved");
  const filteredResolvedAlerts = resolvedAlerts.filter((a) => {
    if (contextFilter === "ALL") return true;
    return getAlertContext(a).type === contextFilter;
  });

  const handleOpenDetail = async (alertId) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedDetail(data);
      } else {
        // Fallback to local alert data
        const local = alerts.find((a) => a.id === alertId);
        const ctx = getAlertContext(local || {});
        setSelectedDetail({
          ...local,
          room_name: ctx.roomName,
          organization_name: ctx.orgName,
          organization_type: ctx.type,
          resident_name: ctx.residentName,
        });
      }
    } catch (err) {
      console.warn("Failed to fetch alert detail:", err);
      const local = alerts.find((a) => a.id === alertId);
      const ctx = getAlertContext(local || {});
      setSelectedDetail({
        ...local,
        room_name: ctx.roomName,
        organization_name: ctx.orgName,
        organization_type: ctx.type,
        resident_name: ctx.residentName,
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
            Monitor platform-wide incidents, inspect telemetry context, and maintain operational oversight.
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
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-red-500">warning</span>
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                Pending & Active Alerts
              </h3>
              <span className="bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300 px-2 py-0.5 rounded text-[11px] font-bold">
                {filteredActiveAlerts.length} Active
              </span>
            </div>

            {/* Classification Filter Tabs: ALL, ELDER CARE, CORPORATE */}
            <div className="flex items-center gap-1 p-1 bg-slate-200/70 dark:bg-slate-850 rounded-lg text-xs self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setContextFilter("ALL")}
                className={`px-3 py-1 rounded-md font-bold transition-all cursor-pointer ${
                  contextFilter === "ALL"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                }`}
              >
                ALL ({countAll})
              </button>
              <button
                type="button"
                onClick={() => setContextFilter("ELDER_CARE")}
                className={`px-3 py-1 rounded-md font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  contextFilter === "ELDER_CARE"
                    ? "bg-teal-600 text-white shadow-xs"
                    : "text-slate-500 hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-300"
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                ELDER CARE ({countElder})
              </button>
              <button
                type="button"
                onClick={() => setContextFilter("CORPORATE")}
                className={`px-3 py-1 rounded-md font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  contextFilter === "CORPORATE"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-300"
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                CORPORATE ({countCorp})
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-slate-100 dark:bg-slate-850 text-slate-500 dark:text-slate-400 text-label-caps font-label-caps uppercase font-semibold">
                <tr>
                  <th className="p-4">Context & Org</th>
                  <th className="p-4">Location / Target</th>
                  <th className="p-4">Event Type</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredActiveAlerts.map((alert) => {
                  const ctx = getAlertContext(alert);
                  const isElder = ctx.type === "ELDER_CARE";
                  const isCritical =
                    alert.severity === "CRITICAL" || alert.event_type === "Fall_Detected";
                  return (
                    <tr
                      key={alert.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors"
                    >
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <span
                            className={`inline-flex items-center w-fit px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider ${
                              isElder
                                ? "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                                : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                            }`}
                          >
                            {isElder ? "ELDER CARE" : "CORPORATE"}
                          </span>
                          <span className="font-semibold text-slate-800 dark:text-slate-200 text-xs">
                            {ctx.orgName}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {ctx.roomName}
                        </div>
                        {isElder && ctx.residentName ? (
                          <div className="text-[11px] font-medium text-teal-650 dark:text-teal-400 flex items-center gap-1 mt-0.5">
                            <span className="material-symbols-outlined text-[13px]">person</span>
                            <span>{ctx.residentName}</span>
                          </div>
                        ) : (
                          <div className="text-[10px] text-slate-400 font-mono">
                            ID: {alert.id.slice(0, 8)}
                          </div>
                        )}
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
                            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium italic flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                              <span className="material-symbols-outlined text-[14px] text-teal-600 dark:text-teal-400">visibility</span>
                              Oversight
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {filteredActiveAlerts.length === 0 && (
                  <tr>
                    <td colSpan="7" className="p-8 text-center text-slate-400 italic">
                      No active alerts in {contextFilter === "ALL" ? "platform queue" : contextFilter === "ELDER_CARE" ? "Elder Care scope" : "Corporate scope"}. All areas nominal.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Resolution History / Activity Stream */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-[500px] shadow-sm text-xs">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-center justify-between">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
              <span className="material-symbols-outlined text-teal-605">check_circle</span>
              Resolution History
            </h3>
            <span className="text-slate-400 text-xs font-semibold">
              ({filteredResolvedAlerts.length})
            </span>
          </div>
          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            {filteredResolvedAlerts.map((a) => {
              const ctx = getAlertContext(a);
              const isElder = ctx.type === "ELDER_CARE";
              return (
                <div
                  key={a.id}
                  className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 pb-4 text-left group"
                >
                  <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900"></div>
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span
                          className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded uppercase ${
                            isElder
                              ? "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300"
                              : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
                          }`}
                        >
                          {isElder ? "ELDER CARE" : "CORPORATE"}
                        </span>
                        <span className="font-bold text-slate-900 dark:text-white text-sm">
                          {ctx.roomName}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500">{ctx.orgName}</div>
                    </div>
                    <span className="text-data-mono font-data-mono text-slate-400">
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-500 mb-2">{a.message || "Verified safe. Alert cleared."}</p>
                  <button
                    onClick={() => handleOpenDetail(a.id)}
                    className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold hover:underline cursor-pointer flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[13px]">visibility</span> View Incident Details
                  </button>
                </div>
              );
            })}
            {filteredResolvedAlerts.length === 0 && (
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
                <span
                  className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white shadow-xs ${
                    selectedDetail.severity === "CRITICAL" ? "bg-red-600" : "bg-amber-500"
                  }`}
                >
                  <span className="material-symbols-outlined text-xl">
                    {selectedDetail.severity === "CRITICAL" ? "crisis_alert" : "warning"}
                  </span>
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider ${
                        selectedDetail.organization_type === "ELDER_CARE"
                          ? "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                          : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                      }`}
                    >
                      {selectedDetail.organization_type === "ELDER_CARE" ? "ELDER CARE" : "CORPORATE"}
                    </span>
                    <h3 className="font-bold text-slate-900 dark:text-white text-base">
                      {selectedDetail.event_type ? selectedDetail.event_type.replace(/_/g, " ") : "Incident Alert"}
                    </h3>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Incident ID: <span className="font-mono">{selectedDetail.id}</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs uppercase font-mono px-2 py-0.5 rounded font-bold ${
                    selectedDetail.status === "new"
                      ? "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300"
                      : selectedDetail.status === "responding"
                      ? "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300"
                      : selectedDetail.status === "resolved"
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300"
                      : "bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300"
                  }`}
                >
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
                  <div className="text-slate-500 mt-0.5 flex items-center gap-1.5">
                    Context:
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        selectedDetail.organization_type === "ELDER_CARE"
                          ? "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                          : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                      }`}
                    >
                      {selectedDetail.organization_type === "ELDER_CARE" ? "ELDER CARE" : "CORPORATE"}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Detected Timestamp</div>
                  <div className="font-mono text-slate-700 dark:text-slate-300 mt-0.5">
                    {new Date(selectedDetail.created_at).toLocaleString()}
                  </div>
                </div>
                {selectedDetail.organization_type === "ELDER_CARE" ? (
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Resident Under Care</div>
                    <div className="font-semibold text-slate-900 dark:text-white mt-0.5">
                      {selectedDetail.resident_name || "Unassigned / Common Area"}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Space Classification</div>
                    <div className="font-semibold text-slate-900 dark:text-white mt-0.5">
                      Commercial Facility Node
                    </div>
                  </div>
                )}
              </div>

              {/* Message */}
              <div className="p-3 bg-red-50/60 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 rounded-xl text-red-900 dark:text-red-200">
                <div className="text-[10px] uppercase font-bold text-red-600 mb-0.5">Incident Dispatch Message</div>
                <p className="font-medium text-xs">{selectedDetail.message}</p>
              </div>

              {/* Emergency Contact Information (Strictly for Elder Care residents only) */}
              {selectedDetail.organization_type === "ELDER_CARE" && selectedDetail.emergency_contact && (
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
                        {selectedDetail.acknowledgement.user_name ||
                          selectedDetail.acknowledgement.user_email ||
                          selectedDetail.acknowledgement.user_id ||
                          "Staff Officer"}
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
