import React from "react";
import SubcarrierWaveformStream from "../components/SubcarrierWaveformStream";

export default function CentralMonitoringView({
  occupancySummary = { occupied_room_details: [], occupied_rooms: 0, total_rooms: 0 },
  residents = [],
  devices = [],
  appContext = "",
  activeTelemetryActivity = "Empty",
}) {
  const roomDetails = occupancySummary?.occupied_room_details || [];

  return (
    <div className="space-y-6">
      {/* Central Monitoring Dashboard Title Row */}
      <div className="mb-stack-lg flex items-end justify-between">
        <div className="text-left">
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white tracking-tight">
            Central Monitoring
          </h2>
          <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">
            Real-time floor visibility and device telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded border border-slate-200 dark:border-slate-800">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
          System Live
        </div>
      </div>

      {/* Central Monitoring Bento Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter items-start">
        {/* Live Feed Table (Spans 8 columns) */}
        <div className="xl:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-between items-center text-left">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
              Live Feed
            </h3>
            <span className="material-symbols-outlined text-slate-400">filter_list</span>
          </div>

          <div className="overflow-x-auto text-left">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800">
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                    Location / Subject
                  </th>
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                    Status
                  </th>
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                    Activity
                  </th>
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                    Fall Risk
                  </th>
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">
                    Telemetry
                  </th>
                  <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold text-right">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-body-md font-body-md">
                {roomDetails.map((rm) => {
                  const isAlert = rm.is_occupied && rm.current_activity === "Fall_Detected";
                  const isWarning = rm.is_occupied && rm.current_activity === "Sitting";
                  return (
                    <tr
                      key={rm.room_id}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                        isAlert
                          ? "bg-red-50/20 dark:bg-red-950/10 border-l-4 border-l-red-500"
                          : isWarning
                          ? "bg-amber-50/20 dark:bg-amber-950/10"
                          : ""
                      }`}
                    >
                      <td className="p-4">
                        <div className="font-headline-sm text-slate-900 dark:text-white font-semibold flex items-center gap-2">
                          <span>{rm.room_name}</span>
                          {rm.classification && (
                            <span className="text-[10px] font-semibold px-2 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                              {rm.classification}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {residents
                            .filter((res) => res.room_id === rm.room_id)
                            .map((r) => `${r.first_name} ${r.last_name}`)
                            .join(", ") ||
                            (appContext === "CORPORATE"
                              ? rm.classification || rm.room_type
                              : "Common Facility")}
                        </div>
                      </td>
                      <td className="p-4">
                        {rm.is_occupied ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-50 dark:bg-teal-950/30 text-teal-650 dark:text-teal-400 text-xs font-bold uppercase tracking-wider">
                            <span className="material-symbols-outlined text-[14px]">person</span>
                            Occupied
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-bold uppercase tracking-wider">
                            <span className="material-symbols-outlined text-[14px]">chair</span>
                            Vacant
                          </span>
                        )}
                      </td>
                      <td className="p-4 text-slate-800 dark:text-slate-355">
                        {rm.is_occupied ? (
                          <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-slate-400">
                              {rm.current_activity === "Walking"
                                ? "directions_walk"
                                : rm.current_activity === "Sitting"
                                ? "bed"
                                : "warning"}
                            </span>
                            {rm.current_activity.replace("_", " ")}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic text-sm">No activity</span>
                        )}
                      </td>
                      <td className="p-4">
                        {rm.is_occupied ? (
                          rm.current_activity === "Fall_Detected" ? (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-red-500 rounded bg-red-600 text-white font-medium text-xs animate-pulse">
                              Detected
                            </span>
                          ) : rm.current_activity === "Sitting" ? (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-amber-300 dark:border-amber-700 rounded bg-amber-500 text-white font-medium text-xs">
                              <span className="material-symbols-outlined text-[16px]">warning</span> Warning
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-slate-200 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 text-xs font-semibold">
                              <span className="w-2 h-2 rounded-full bg-teal-500"></span> Safe
                            </span>
                          )
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 font-medium">
                          <span className="material-symbols-outlined text-[16px] text-teal-600 dark:text-teal-400">
                            wifi
                          </span>
                          {devices.find((d) => d.room_id === rm.room_id)?.firmware_version ||
                            "ESP-Node"}
                        </div>
                      </td>
                      <td className="p-4 text-right font-data-mono text-data-mono text-slate-500 dark:text-slate-400">
                        {rm.is_occupied ? new Date().toLocaleTimeString() + ".112" : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 text-right text-xs text-slate-500 dark:text-slate-400">
            Active monitoring grid: {occupancySummary?.occupied_rooms || 0} of{" "}
            {occupancySummary?.total_rooms || 0} rooms occupied
          </div>
        </div>

        {/* Side Diagnostics Panel (Spans 4 columns) */}
        <div className="xl:col-span-4 flex flex-col gap-gutter text-left">
          {/* Device Diagnostics Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
                <span className="material-symbols-outlined text-teal-600 dark:text-teal-400">
                  query_stats
                </span>
                Device Diagnostics
              </h3>
              <span className="text-label-caps font-label-caps bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded text-slate-500 border border-slate-200 dark:border-slate-700">
                ESP32-S3
              </span>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 border-b border-slate-100 dark:border-slate-800 pb-4">
              Real-time Channel State Information (CSI) variance monitoring for network stability.
            </p>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850">
                <div className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-1">
                  Signal Var (σ²)
                </div>
                <div className="font-data-mono text-[20px] font-bold text-slate-850 dark:text-white">
                  {activeTelemetryActivity === "Walking"
                    ? "12.45"
                    : activeTelemetryActivity === "Sitting"
                    ? "1.12"
                    : activeTelemetryActivity === "Fall_Detected"
                    ? "89.45"
                    : "0.08"}
                </div>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850">
                <div className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-1">
                  Packet Drop
                </div>
                <div className="font-data-mono text-[20px] font-bold text-teal-650">0.02%</div>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850 col-span-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-label-caps font-label-caps text-slate-400">SNR Quality</span>
                  <span className="font-data-mono text-sm text-slate-700 dark:text-slate-300">
                    32 dB
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div className="bg-teal-500 h-1.5 rounded-full" style={{ width: "85%" }}></div>
                </div>
              </div>
            </div>

            {/* Subcarriers Waveform Bars visualization (Isolated local re-render) */}
            <SubcarrierWaveformStream activeActivity={activeTelemetryActivity} />
          </div>

          {/* Environmental Context Card */}
          <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs">
            <h4 className="text-body-md font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">thermostat</span> Environmental
              Context
            </h4>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400">Floor Interference</span>
                <span className="font-data-mono bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-750 text-slate-700 dark:text-slate-300">
                  Low
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-slate-400">Active Anchors</span>
                <span className="font-data-mono text-slate-700 dark:text-slate-350">
                  {devices.filter((d) => d.device_status === "ONLINE").length} / {devices.length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
