import React from "react";

export default function DevicesView({
  devices = [],
  rooms = [],
  faultReports = [],
  nodeFilter = "ALL",
  setNodeFilter = () => {},
  setNewDevRmId = () => {},
  setShowAddDeviceModal = () => {},
  setSelectedFaultDevice = () => {},
  setShowReportFaultModal = () => {},
  handleServiceTicket = () => {},
}) {
  const corpDevices = devices.filter(
    (d) =>
      d.organization_type === "CORPORATE" ||
      (!d.firmware_version?.includes("EC") &&
        (d.organization_name?.includes("Amal") ||
          d.firmware_version?.includes("101") ||
          d.firmware_version?.includes("102") ||
          d.firmware_version?.includes("103")))
  );
  const careDevices = devices.filter(
    (d) =>
      d.organization_type === "ELDER_CARE" ||
      d.firmware_version?.includes("EC") ||
      d.organization_name?.includes("Peter") ||
      d.organization_name?.includes("Elder")
  );
  const activeTracerReports = faultReports.filter((r) => r.status !== "REPLACED_RESOLVED");

  let displayedDevices = devices;
  if (nodeFilter === "CORPORATE") displayedDevices = corpDevices;
  else if (nodeFilter === "ELDER_CARE") displayedDevices = careDevices;

  return (
    <div className="space-y-6 text-left">
      {/* Header with Classification Badge */}
      <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
              Sensing Node &amp; Device Management
            </h2>
            <span className="bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Hardware Classification
            </span>
          </div>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Multi-tenant ESP32 sensor fleet oversight, organization-type classification, hardware pairing
            tokens, and token tracer service desk.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (rooms.length > 0) {
                setNewDevRmId(rooms[0].id);
                setShowAddDeviceModal(true);
              } else {
                alert("Please create a room layout first.");
              }
            }}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold uppercase transition-colors shadow-sm flex items-center gap-1.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">add_circle</span>
            Register ESP Node
          </button>
        </div>
      </div>

      {/* Classification Metric Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setNodeFilter("ALL")}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            nodeFilter === "ALL"
              ? "bg-teal-50/60 dark:bg-teal-950/40 border-teal-500 shadow-xs"
              : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Total Fleet Nodes
            </span>
            <span className="material-symbols-outlined text-teal-600">sensors</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {devices.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">All active sensing receivers</div>
        </div>

        <div
          onClick={() => setNodeFilter("CORPORATE")}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            nodeFilter === "CORPORATE"
              ? "bg-indigo-50/60 dark:bg-indigo-950/40 border-indigo-500 shadow-xs"
              : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              Corporate Nodes
            </span>
            <span className="material-symbols-outlined text-indigo-600">domain</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {corpDevices.length}
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            Amal Jyothi College of Engineering
          </div>
        </div>

        <div
          onClick={() => setNodeFilter("ELDER_CARE")}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            nodeFilter === "ELDER_CARE"
              ? "bg-emerald-50/60 dark:bg-emerald-950/40 border-emerald-500 shadow-xs"
              : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Old Age Care Nodes
            </span>
            <span className="material-symbols-outlined text-emerald-600">health_and_safety</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {careDevices.length}
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            St. Peter's Elder Care Home
          </div>
        </div>

        <div
          onClick={() => setNodeFilter("TRACER")}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            nodeFilter === "TRACER"
              ? "bg-amber-50/60 dark:bg-amber-950/40 border-amber-500 shadow-xs"
              : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              Token Tracer Queries
            </span>
            <span className="material-symbols-outlined text-amber-600">bug_report</span>
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            {activeTracerReports.length}
            {activeTracerReports.length > 0 && (
              <span className="text-[10px] bg-amber-500 text-white font-bold px-2 py-0.5 rounded-full animate-pulse">
                ATTENTION
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-500">Fault tickets awaiting service</div>
        </div>
      </div>

      {/* Filter Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3 flex-wrap">
        <button
          onClick={() => setNodeFilter("ALL")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase transition-all cursor-pointer flex items-center gap-1.5 ${
            nodeFilter === "ALL"
              ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs"
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
          }`}
        >
          <span className="material-symbols-outlined text-[15px]">sensors</span>
          All Monitored Nodes ({devices.length})
        </button>

        <button
          onClick={() => setNodeFilter("CORPORATE")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase transition-all cursor-pointer flex items-center gap-1.5 ${
            nodeFilter === "CORPORATE"
              ? "bg-indigo-600 text-white shadow-xs"
              : "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-900 hover:bg-indigo-100"
          }`}
        >
          <span className="material-symbols-outlined text-[15px]">domain</span>
          Corporate Workplace (AJCE) ({corpDevices.length})
        </button>

        <button
          onClick={() => setNodeFilter("ELDER_CARE")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase transition-all cursor-pointer flex items-center gap-1.5 ${
            nodeFilter === "ELDER_CARE"
              ? "bg-emerald-600 text-white shadow-xs"
              : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 hover:bg-emerald-100"
          }`}
        >
          <span className="material-symbols-outlined text-[15px]">health_and_safety</span>
          Old Age Care Home (St. Peter's) ({careDevices.length})
        </button>

        <button
          onClick={() => setNodeFilter("TRACER")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold uppercase transition-all cursor-pointer flex items-center gap-1.5 ${
            nodeFilter === "TRACER"
              ? "bg-amber-600 text-white shadow-xs"
              : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900 hover:bg-amber-100"
          }`}
        >
          <span className="material-symbols-outlined text-[15px]">build</span>
          Hardware Token Tracer &amp; Service Desk ({faultReports.length})
        </button>
      </div>

      {/* View 1: Sensing Nodes Table with Classification & Pairing Token */}
      {nodeFilter !== "TRACER" && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                  <th className="p-4 text-left">ESP Node MAC &amp; Token</th>
                  <th className="p-4 text-left">Organization &amp; Classification</th>
                  <th className="p-4 text-left">Assigned Room &amp; Wing</th>
                  <th className="p-4 text-left">Firmware Version</th>
                  <th className="p-4 text-left">Node Status</th>
                  <th className="p-4 text-right">Actions &amp; Fault Tracer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {displayedDevices.map((dev) => {
                  const assignedRoom = rooms.find((r) => r.id === dev.room_id);
                  const isOnline =
                    dev.device_status === "ONLINE" || dev.status === "ONLINE" || !dev.status;
                  return (
                    <tr
                      key={dev.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center text-teal-600 dark:text-teal-400 font-bold">
                            <span className="material-symbols-outlined text-[20px]">router</span>
                          </div>
                          <div>
                            <div className="font-mono font-bold text-slate-900 dark:text-white">
                              {dev.mac_address}
                            </div>
                            <div className="text-[11px] font-mono text-teal-600 dark:text-teal-400 mt-0.5">
                              Token: {dev.hardware_token || "TK-ESP32-GEN01"}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <span className="font-semibold text-slate-900 dark:text-white">
                            {dev.organization_name ||
                              (dev.organization_type === "CORPORATE"
                                ? "Amal Jyothi College of Engineering"
                                : "St. Peter's Elder Care Home")}
                          </span>
                          <span
                            className={`inline-flex px-2 py-0.5 rounded text-[9px] font-bold uppercase w-max ${
                              dev.organization_type === "CORPORATE"
                                ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200"
                                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200"
                            }`}
                          >
                            {dev.organization_type || "EDGE_NODE"}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="font-medium text-slate-900 dark:text-white">
                          {assignedRoom ? assignedRoom.name : "Unassigned Room"}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {assignedRoom ? assignedRoom.room_type : "No space mapping"}
                        </div>
                      </td>
                      <td className="p-4 font-mono text-slate-600 dark:text-slate-300">
                        {dev.firmware_version || "v2.1.0"}
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            isOnline
                              ? "bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800"
                              : "bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isOnline ? "bg-teal-500 animate-pulse" : "bg-red-500"
                            }`}
                          ></span>
                          {isOnline ? "ONLINE" : "OFFLINE"}
                        </span>
                        {isOnline && (
                          <div className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                            <span className="text-teal-600 dark:text-teal-400 font-bold">56 SC</span> • -47 dBm • 94% SQ
                          </div>
                        )}
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedFaultDevice(dev);
                            setShowReportFaultModal(true);
                          }}
                          className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-950/70 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800 rounded-lg font-bold text-xs inline-flex items-center gap-1 cursor-pointer transition-colors"
                        >
                          <span className="material-symbols-outlined text-[14px]">
                            report_problem
                          </span>
                          Report Fault
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {displayedDevices.length === 0 && (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-slate-400 italic">
                      No ESP sensing nodes registered for this category filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* View 2: Hardware Token Tracer & Fault Service Desk */}
      {nodeFilter === "TRACER" && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 bg-slate-50/80 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-1.5">
                <span className="material-symbols-outlined text-amber-500">build_circle</span>
                Global Hardware Token Tracer &amp; Service Desk
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Active fault queries submitted by Corporate and Old Age Home admins for node service,
                CSI recalibration, or hardware replacement.
              </p>
            </div>
            <span className="text-[11px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-3 py-1 rounded-lg font-bold text-slate-700 dark:text-slate-300">
              {faultReports.length} Queries Logged
            </span>
          </div>

          {faultReports.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <span className="material-symbols-outlined text-4xl mb-2 text-slate-300 dark:text-slate-600">
                check_circle
              </span>
              <p className="font-bold text-sm">No Active Fault Reports</p>
              <p className="text-xs text-slate-400 mt-1">
                All ESP32 sensing nodes across Corporate and Old Age Home facilities are operational.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                    <th className="p-4 text-left">Tracer Token</th>
                    <th className="p-4 text-left">Target Node &amp; Room</th>
                    <th className="p-4 text-left">Classification Domain</th>
                    <th className="p-4 text-left">Issue Type &amp; Diagnosis</th>
                    <th className="p-4 text-left">Severity</th>
                    <th className="p-4 text-left">Service Status</th>
                    <th className="p-4 text-right">Global Admin Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {faultReports.map((rep) => (
                    <tr
                      key={rep.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors"
                    >
                      <td className="p-4 font-mono font-bold text-teal-600 dark:text-teal-400">
                        {rep.tracer_token || `TRC-${rep.id?.toString().slice(0, 6)}`}
                      </td>
                      <td className="p-4">
                        <div className="font-mono font-semibold text-slate-900 dark:text-white">
                          {rep.device_mac || "ESP-Node"}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {rep.room_name || "Facility Zone"}
                        </div>
                      </td>
                      <td className="p-4 font-semibold text-slate-700 dark:text-slate-300">
                        {rep.organization_type || "CORPORATE"}
                      </td>
                      <td className="p-4">
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {rep.issue_type?.replace(/_/g, " ")}
                        </div>
                        <div className="text-[11px] text-slate-500 max-w-xs truncate">
                          {rep.description}
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            rep.severity === "CRITICAL"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {rep.severity}
                        </span>
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            rep.status === "REPLACED_RESOLVED"
                              ? "bg-teal-50 text-teal-700"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {rep.status?.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        {rep.status !== "REPLACED_RESOLVED" && (
                          <button
                            onClick={() =>
                              handleServiceTicket(rep.id, "REPLACED_RESOLVED", "Node replaced and calibrated.")
                            }
                            className="px-2.5 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded text-xs font-bold transition-colors cursor-pointer"
                          >
                            Resolve Ticket
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
