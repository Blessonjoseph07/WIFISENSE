import React from "react";

export default function SysAdminView({
  setIsRegistering = () => {},
  exportPersonnelCSV = () => {},
  activePersonnel = [],
  alerts = [],
  setCurrentView = () => {},
  handleAcknowledge = () => {},
  setShowResolveModal = () => {},
}) {
  const activeAlerts = alerts.filter((a) => a.status !== "resolved");

  return (
    <div className="flex flex-col gap-gutter text-left">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 font-label-caps text-label-caps mb-2">
            <span>System Config</span>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="text-teal-650 font-bold">Platform Administration</span>
          </div>
          <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            System Administrator Console
          </h1>
          <p className="text-slate-500 dark:text-slate-400 font-body-md text-body-md mt-1">
            Global governance, multi-tenant monitoring, and operational incident response.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentView("alerts")}
            className="border border-red-300 dark:border-red-900/50 text-red-600 dark:text-red-400 px-4 py-2 rounded-lg font-label-caps text-label-caps hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors flex items-center gap-1.5 font-semibold cursor-pointer shadow-xs"
          >
            <span className="material-symbols-outlined text-[18px]">history</span>
            Incident Queue ({activeAlerts.length})
          </button>
          <button
            onClick={() => setIsRegistering(true)}
            className="bg-teal-600 text-white px-4 py-2 rounded-lg font-label-caps text-label-caps hover:bg-teal-700 transition-colors flex items-center gap-1.5 shadow-sm font-semibold cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">person_add</span>
            Add New User
          </button>
        </div>
      </div>

      {/* Active Incidents Banner / Operational Triage */}
      {activeAlerts.length > 0 && (
        <div className="bg-red-50/70 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping"></span>
              <h3 className="font-bold text-sm text-red-900 dark:text-red-200 uppercase tracking-wide flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-red-600">emergency</span>
                Active Critical Incidents ({activeAlerts.length})
              </h3>
            </div>
            <button
              onClick={() => setCurrentView("alerts")}
              className="text-xs text-red-700 dark:text-red-300 font-bold hover:underline flex items-center gap-1 cursor-pointer"
            >
              View All In Incident Console <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeAlerts.slice(0, 4).map((alt) => (
              <div
                key={alt.id}
                className="bg-white dark:bg-slate-900 border border-red-100 dark:border-red-950/60 p-3 rounded-lg flex items-center justify-between gap-3 shadow-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      {alt.event_type.replace(/_/g, " ")}
                    </span>
                    <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                      alt.status === "new" ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300" : "bg-blue-100 text-blue-800"
                    }`}>
                      {alt.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{alt.message}</div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    <span className="material-symbols-outlined text-[15px] text-teal-600 dark:text-teal-400">visibility</span>
                    Oversight
                  </span>
                  <button
                    onClick={() => setCurrentView("alerts")}
                    className="px-2.5 py-1 text-xs border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 rounded font-semibold cursor-pointer transition-colors"
                  >
                    Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bento Grid Layout for Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-gutter">
        {/* Left/Main Column: Active Users Table */}
        <div className="xl:col-span-2 flex flex-col gap-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-sm">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900">
              <h2 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                Active Personnel
              </h2>
              <button
                onClick={exportPersonnelCSV}
                className="text-teal-600 dark:text-teal-400 font-label-caps text-label-caps hover:underline flex items-center gap-1 cursor-pointer"
              >
                Export CSV <span className="material-symbols-outlined text-[16px]">download</span>
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800">
                    <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                      User Details
                    </th>
                    <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                      Role & Scope
                    </th>
                    <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                      Permissions Profile
                    </th>
                    <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold text-right">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {activePersonnel.map((person) => (
                    <tr
                      key={person.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-teal-650 dark:text-teal-450 font-bold text-sm">
                            {(person.first_name?.[0] || "") + (person.last_name?.[0] || "")}
                          </div>
                          <div>
                            <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">
                              {person.first_name} {person.last_name}
                            </div>
                            <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">
                              ID: {person.id.slice(0, 8)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <span className="inline-flex items-center gap-1 font-label-caps text-label-caps text-teal-650 border border-teal-200/50 dark:border-teal-900/50 rounded px-2 py-0.5 w-max">
                            <span className="material-symbols-outlined text-[14px]">
                              shield_person
                            </span>{" "}
                            {person.role_name}
                          </span>
                          <span className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs">
                            {person.scope_description}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {person.permissions.map((perm, idx) => (
                            <span
                              key={idx}
                              className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono"
                            >
                              {perm}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-caps text-label-caps font-bold ${
                            person.is_active
                              ? "bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-450"
                              : "bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-450"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              person.is_active ? "bg-teal-500 animate-pulse" : "bg-red-500"
                            }`}
                          ></span>{" "}
                          {person.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {activePersonnel.length === 0 && (
                    <tr>
                      <td colSpan="4" className="p-4 text-center text-slate-500">
                        No personnel found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between text-xs">
              <span className="text-slate-550 dark:text-slate-400">
                Showing {activePersonnel.length} of {activePersonnel.length} active accounts
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Role Permissions Grid */}
        <div className="xl:col-span-1 flex flex-col gap-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col h-full">
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between">
              <div>
                <h2 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                  Role Matrix
                </h2>
                <p className="font-body-md text-slate-500 dark:text-slate-400 text-xs mt-0.5">
                  RBAC privilege matrix across system capabilities.
                </p>
              </div>
              <span className="material-symbols-outlined text-teal-600 text-[20px]">
                admin_panel_settings
              </span>
            </div>
            <div className="p-0 flex-1 overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 font-bold uppercase text-[10px] text-slate-400">
                    <th className="py-3 px-3.5 font-semibold">Capability</th>
                    <th className="py-3 px-2 text-center font-semibold">Admin</th>
                    <th className="py-3 px-2 text-center font-semibold">Manager</th>
                    <th className="py-3 px-2 text-center font-semibold">Staff</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {[
                    { cap: "Real-time CSI Telemetry", admin: true, mgr: true, staff: true },
                    { cap: "Fall & Safety Alert Triage", admin: true, mgr: true, staff: true },
                    { cap: "Facility & Room Hierarchy", admin: true, mgr: true, staff: false },
                    { cap: "Hardware Node Provisioning", admin: true, mgr: true, staff: false },
                    { cap: "RBAC & User Assignments", admin: true, mgr: false, staff: false },
                    { cap: "Family Access Moderation", admin: true, mgr: true, staff: false },
                    { cap: "Cross-Tenant System Config", admin: true, mgr: false, staff: false },
                  ].map((row, idx) => (
                    <tr
                      key={idx}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-2.5 px-3.5 font-medium text-slate-800 dark:text-slate-200 text-xs">
                        {row.cap}
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        {row.admin ? (
                          <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">
                            check_circle
                          </span>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-700 font-mono">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        {row.mgr ? (
                          <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">
                            check_circle
                          </span>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-700 font-mono">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-2 text-center">
                        {row.staff ? (
                          <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">
                            check_circle
                          </span>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-700 font-mono">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-3.5 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Standard Institutional Policy</span>
              <span className="text-teal-600 dark:text-teal-400 font-bold flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">lock</span> Enforced
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
