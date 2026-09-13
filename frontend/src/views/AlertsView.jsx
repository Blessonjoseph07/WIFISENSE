import React from "react";

export default function AlertsView({
  alerts = [],
  rooms = [],
  handleAcknowledge = () => {},
  setShowResolveModal = () => {},
}) {
  return (
    <div className="space-y-6 text-left">
      {/* Page Title */}
      <div className="flex justify-between items-end mb-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            Alert Management
          </h2>
          <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">
            Monitor, acknowledge, and resolve active environmental anomalies.
          </p>
        </div>
        <div className="text-body-md font-body-md text-slate-500 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          Live System Health: Nominal
        </div>
      </div>

      {/* Bento Grid Layout for Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
        {/* Pending Alerts Table (Spans 2 columns) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
              <span className="material-symbols-outlined text-red-500">warning</span>
              Pending Alerts
            </h3>
            <span className="bg-red-50 text-red-600 px-2.5 py-1 rounded text-label-caps font-label-caps font-bold">
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
                                : "bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300"
                            }`}
                          >
                            {alert.status}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {alert.status === "new" && (
                              <button
                                onClick={() => handleAcknowledge(alert.id)}
                                className="text-teal-650 dark:text-teal-400 hover:underline font-semibold cursor-pointer text-xs"
                              >
                                Acknowledge
                              </button>
                            )}
                            <button
                              onClick={() => setShowResolveModal(alert.id)}
                              className="px-2.5 py-1 bg-teal-600 text-white rounded text-xs font-semibold hover:bg-teal-700 transition-colors cursor-pointer"
                            >
                              Resolve
                            </button>
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
                  className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 pb-4 text-left"
                >
                  <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-800 border-2 border-white dark:border-slate-900"></div>
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                      {rooms.find((r) => r.id === a.room_id)?.name || "Room"} Details
                    </h4>
                    <span className="text-data-mono font-data-mono text-slate-455">
                      {new Date(a.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-500 mb-2">Verified safe. Alert cleared.</p>
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
    </div>
  );
}
