import React from "react";

export default function CorporateView({
  exportCorporateAnalytics = () => {},
  occupancySummary = { vacant_rooms: 0, occupied_room_details: [] },
  generateRepurposingReport = () => {},
}) {
  const occupiedRoomDetails = occupancySummary?.occupied_room_details || [];

  return (
    <div className="space-y-6 text-left">
      {/* Corporate Facility View Title Row */}
      <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            Corporate Overview
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Meeting Room Occupancy and Underutilized Spaces Management.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportCorporateAnalytics}
            className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow cursor-pointer"
          >
            Export Analytics
          </button>
        </div>
      </div>

      {/* Util Bento Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-gutter">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="text-label-caps font-label-caps text-slate-400 mb-1">
            Peak Utilization
          </div>
          <div className="font-headline-lg text-slate-900 dark:text-white font-bold">88%</div>
          <div className="w-full bg-slate-100 dark:bg-slate-850 h-2 rounded-full mt-3 overflow-hidden">
            <div className="bg-teal-600 h-full rounded-full" style={{ width: "88%" }}></div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="text-label-caps font-label-caps text-slate-400 mb-1">
            Underutilized Spaces
          </div>
          <div className="font-headline-lg text-slate-900 dark:text-white font-bold">
            {occupancySummary?.vacant_rooms || 0} rooms
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Space efficiency optimizations identified.
          </p>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="text-label-caps font-label-caps text-slate-400 mb-1">
            Potential Savings
          </div>
          <div className="font-headline-lg text-teal-600 dark:text-teal-400 font-bold">15%</div>
          <p className="text-xs text-slate-500 mt-2">
            Idle HVAC and lighting energy recovery rate.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter items-start">
        {/* Meeting Rooms Table */}
        <div className="xl:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 font-bold text-slate-900 dark:text-white">
            Real-time Meeting Room Status
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  <th className="p-4">Room & Classification</th>
                  <th className="p-4">Capacity</th>
                  <th className="p-4">Expected State</th>
                  <th className="p-4">Wi-Fi Sensing</th>
                  <th className="p-4 text-right">Operational Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {occupiedRoomDetails.map((rm) => {
                  const isUnexpected = rm.discrepancy === "UNEXPECTED_OCCUPANCY";
                  const hasEnergyAdvisory =
                    rm.energy_state && rm.energy_state.ac_status === "ON" && !rm.is_occupied;
                  return (
                    <tr
                      key={rm.room_id}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors ${
                        isUnexpected
                          ? "bg-amber-50/30 dark:bg-amber-950/20 border-l-4 border-l-amber-500"
                          : ""
                      }`}
                    >
                      <td className="p-4">
                        <div className="font-headline-sm text-[13px] leading-tight text-slate-900 dark:text-white font-bold">
                          {rm.room_name}
                        </div>
                        <div className="mt-1 flex items-center gap-2">
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                            {rm.classification || rm.room_type}
                          </span>
                          {rm.last_updated && (
                            <span className="text-[9px] text-slate-400 font-mono">
                              Updated{" "}
                              {new Date(rm.last_updated).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                                second: "2-digit",
                              })}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-slate-700 dark:text-slate-300 font-medium">
                        {rm.capacity || 1} seats
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold ${
                            rm.expected_state === "Occupied"
                              ? "bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              rm.expected_state === "Occupied" ? "bg-blue-500" : "bg-slate-400"
                            }`}
                          ></span>
                          {rm.expected_state || (rm.is_occupied ? "Occupied" : "Vacant")}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-medium">
                          <span className="material-symbols-outlined text-sm text-teal-600 dark:text-teal-400">
                            {rm.current_activity === "Walking"
                              ? "directions_walk"
                              : rm.current_activity === "Sitting"
                              ? "airline_seat_recline_normal"
                              : rm.current_activity === "Presence"
                              ? "sensors"
                              : "door_open"}
                          </span>
                          <span>{rm.current_activity?.replace("_", " ") || "Empty"}</span>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        {isUnexpected ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700 animate-pulse">
                            <span className="material-symbols-outlined text-[14px]">warning</span>{" "}
                            Unexpected Occupancy
                          </span>
                        ) : hasEnergyAdvisory ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
                            <span className="material-symbols-outlined text-[14px]">
                              power_off
                            </span>{" "}
                            AC ON (Vacant)
                          </span>
                        ) : rm.is_occupied ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-teal-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span>{" "}
                            In Use
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-500">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Standby
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {occupiedRoomDetails.length === 0 && (
                  <tr>
                    <td colSpan="5" className="p-6 text-center text-slate-500">
                      No corporate rooms discovered.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Underutilized spaces & Energy Efficiency recommendations */}
        <div className="xl:col-span-4 flex flex-col gap-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold flex items-center gap-1.5">
                <span className="material-symbols-outlined text-amber-500 text-lg">bolt</span> Smart
                Energy Efficiency
              </h3>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                AI Recommended
              </span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 rounded-lg">
                <div className="font-bold text-amber-900 dark:text-amber-200 flex items-center justify-between">
                  <span>Board Meeting Room B</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-200/60 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-mono">
                    AC ON
                  </span>
                </div>
                <p className="text-[11px] text-amber-800 dark:text-amber-300/80 mt-1 leading-relaxed">
                  Room has remained vacant for 2.5 hours while AC is ON. Consider turning off AC to
                  improve energy efficiency.
                </p>
              </div>

              <div className="p-3 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-800/40 rounded-lg">
                <div className="font-bold text-blue-900 dark:text-blue-200 flex items-center justify-between">
                  <span>Smart Classroom 102</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-200/60 dark:bg-blue-900/60 text-blue-800 dark:text-blue-300 font-mono">
                    HVAC ACTIVE
                  </span>
                </div>
                <p className="text-[11px] text-blue-800 dark:text-blue-300/80 mt-1 leading-relaxed">
                  Room vacant for 1.8 hours with HVAC running. Auto-standby recommended.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold mb-3">
              Underutilized Spaces
            </h3>
            <div className="space-y-2.5">
              <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg">
                <div className="font-bold text-xs text-slate-900 dark:text-white">
                  MCA Seminar Hall
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  Average Utilization: 8.5% (Classification: Seminar Hall)
                </div>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg">
                <div className="font-bold text-xs text-slate-900 dark:text-white">
                  Faculty Staff Room A
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  Average Utilization: 11.2% (Classification: Office)
                </div>
              </div>
            </div>
            <button
              onClick={generateRepurposingReport}
              className="w-full mt-4 bg-teal-600 text-white py-2 rounded-lg text-xs font-bold uppercase hover:bg-teal-700 shadow-sm cursor-pointer"
            >
              Generate Repurposing Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
