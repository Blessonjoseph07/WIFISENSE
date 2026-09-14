import React, { useState, useEffect } from "react";

export default function CorporateView({
  exportCorporateAnalytics = () => {},
  occupancySummary = { vacant_rooms: 0, occupied_room_details: [] },
  generateRepurposingReport = () => {},
  authToken = "",
  setToastMessage = () => {},
  fetchAllData = () => {},
}) {
  const [unexpectedEvents, setUnexpectedEvents] = useState([]);
  const [energyRecommendations, setEnergyRecommendations] = useState([]);
  const [resolvedEnergyRooms, setResolvedEnergyRooms] = useState({});
  const [loadingRoomId, setLoadingRoomId] = useState(null);
  const [bulkLoading, setBulkLoading] = useState(false);

  const token = authToken || localStorage.getItem("token") || "";

  const fetchSchedulesAndEnergy = async () => {
    if (!token) return;
    try {
      const unexpRes = await fetch("http://127.0.0.1:8000/schedules/unexpected-occupancy", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (unexpRes.ok) {
        setUnexpectedEvents(await unexpRes.json());
      }

      const energyRes = await fetch("http://127.0.0.1:8000/schedules/energy-recommendations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (energyRes.ok) {
        setEnergyRecommendations(await energyRes.json());
      }
    } catch (e) {
      console.warn("Error fetching corporate schedule intelligence:", e);
    }
  };

  useEffect(() => {
    fetchSchedulesAndEnergy();
  }, [token]);

  const handleEnergyAction = async (roomId, action, roomName) => {
    if (!token) return;
    setLoadingRoomId(roomId);
    try {
      const res = await fetch(`http://127.0.0.1:8000/rooms/${roomId}/energy-action`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        const data = await res.json();
        if (action === "RESTORE_NORMAL") {
          setResolvedEnergyRooms((prev) => {
            const next = { ...prev };
            delete next[roomId];
            return next;
          });
          setToastMessage({
            type: "success",
            text: `Power restored for ${roomName}. Normal cooling & lighting active.`,
          });
        } else {
          setResolvedEnergyRooms((prev) => ({
            ...prev,
            [roomId]: {
              action,
              roomName,
              timestamp: new Date(),
            },
          }));
          setToastMessage({
            type: "success",
            text: `IoT Relay Command Dispatched: ${action.replace(/_/g, " ")} applied for ${roomName}. Power saved.`,
          });
        }
        await fetchSchedulesAndEnergy();
        fetchAllData();
      } else {
        const err = await res.json();
        setToastMessage({ type: "error", text: err.detail || "Failed to execute energy action." });
      }
    } catch (e) {
      setToastMessage({ type: "error", text: "Network error executing energy action." });
    } finally {
      setLoadingRoomId(null);
    }
  };

  const handleBulkEnergyAction = async (action = "ECO_STANDBY") => {
    if (!token) return;
    setBulkLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/schedules/energy-actions/bulk", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        const data = await res.json();
        const newlyResolved = {};
        energyRecommendations.forEach((r) => {
          newlyResolved[r.room_id] = { action, roomName: r.room_name, timestamp: new Date() };
        });
        setResolvedEnergyRooms((prev) => ({ ...prev, ...newlyResolved }));
        setToastMessage({
          type: "success",
          text: `Bulk Energy Relay: ${action.replace(/_/g, " ")} applied across ${data.affected_count || energyRecommendations.length} vacant rooms.`,
        });
        await fetchSchedulesAndEnergy();
        fetchAllData();
      }
    } catch (e) {
      setToastMessage({ type: "error", text: "Error dispatching bulk energy actions." });
    } finally {
      setBulkLoading(false);
    }
  };

  const occupiedRoomDetails = occupancySummary?.occupied_room_details || [];
  const activeEnergyCount = energyRecommendations.length;
  const resolvedCount = Object.keys(resolvedEnergyRooms).length;

  return (
    <div className="space-y-6 text-left">
      {/* Corporate Facility View Title Row */}
      <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold flex items-center gap-2">
            <span className="material-symbols-outlined text-teal-600 text-3xl">corporate_fare</span>
            Corporate Space &amp; Energy Intelligence
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Wi-Fi CSI Workspace Sensing, Idle HVAC / Lighting Power Mitigations &amp; Schedule Anomaly Detection.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportCorporateAnalytics}
            className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-bold uppercase hover:bg-teal-700 shadow-xs cursor-pointer flex items-center gap-1.5"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            Export Space Audit
          </button>
        </div>
      </div>

      {/* Util Bento Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-gutter">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="text-label-caps font-label-caps text-slate-400 mb-1">
            Peak Utilization Rate
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
            Space efficiency optimization candidates identified.
          </p>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="text-label-caps font-label-caps text-slate-400 mb-1">
            Energy Mitigation Rate
          </div>
          <div className="font-headline-lg text-teal-600 dark:text-teal-400 font-bold flex items-center gap-2">
            <span>{resolvedCount > 0 ? `${resolvedCount * 2.5 + 15}%` : "15%"}</span>
            {resolvedCount > 0 && (
              <span className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-mono px-2 py-0.5 rounded-full font-bold">
                +{resolvedCount * 2.4} kWh Saved
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {activeEnergyCount > 0
              ? `${activeEnergyCount} vacant room(s) running AC/lights awaiting shutdown.`
              : "All idle meeting rooms operating in Eco Standby."}
          </p>
        </div>
      </div>

      {/* Unexpected Occupancy Alert Banner if detected */}
      {unexpectedEvents.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <span className="p-2 bg-amber-500 text-white rounded-lg material-symbols-outlined text-xl">
              warning
            </span>
            <div>
              <h4 className="font-bold text-amber-900 dark:text-amber-200 text-sm">
                Schedule Discrepancy Detected ({unexpectedEvents.length} room{unexpectedEvents.length > 1 ? "s" : ""})
              </h4>
              <p className="text-xs text-amber-700 dark:text-amber-300/80">
                {unexpectedEvents.map((u) => `${u.room_name}: ${u.reason}`).join(" • ")}
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold bg-amber-200/80 dark:bg-amber-900 text-amber-900 dark:text-amber-200 px-2.5 py-1 rounded shrink-0">
            Wi-Fi CSI Motion Confirmed
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter items-start">
        {/* Meeting Rooms Table */}
        <div className="xl:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 font-bold text-slate-900 dark:text-white flex justify-between items-center">
            <span>Corporate Meeting Rooms &amp; Workspaces</span>
            <span className="text-xs font-normal text-slate-500">Wi-Fi CSI Subcarrier Sensing</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  <th className="p-4">Room &amp; Classification</th>
                  <th className="p-4">Capacity</th>
                  <th className="p-4">Schedule Expectation</th>
                  <th className="p-4">CSI State</th>
                  <th className="p-4 text-right">Operational Status &amp; Energy Control</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {occupiedRoomDetails.map((rm) => {
                  const unexpectedMatch = unexpectedEvents.find((u) => u.room_id === rm.room_id);
                  const isUnexpected = unexpectedMatch || rm.discrepancy === "UNEXPECTED_OCCUPANCY";

                  const isLocallyResolved = Boolean(resolvedEnergyRooms[rm.room_id]);
                  const energyMatch = energyRecommendations.find((e) => e.room_id === rm.room_id);
                  const hasEnergyAdvisory =
                    !isLocallyResolved &&
                    (energyMatch || (rm.energy_state && rm.energy_state.ac_status === "ON" && !rm.is_occupied));

                  return (
                    <tr
                      key={rm.room_id}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors ${
                        isUnexpected
                          ? "bg-amber-50/40 dark:bg-amber-950/20 border-l-4 border-l-amber-500"
                          : hasEnergyAdvisory
                          ? "bg-rose-50/30 dark:bg-rose-950/20"
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
                        ) : isLocallyResolved ? (
                          <div className="flex items-center justify-end gap-2">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                              <span className="material-symbols-outlined text-[14px]">eco</span>
                              Eco Standby (OFF)
                            </span>
                            <button
                              onClick={() => handleEnergyAction(rm.room_id, "RESTORE_NORMAL", rm.room_name)}
                              className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded text-[10px] font-bold cursor-pointer"
                              title="Restore AC power"
                            >
                              Restore
                            </button>
                          </div>
                        ) : hasEnergyAdvisory ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
                              <span className="material-symbols-outlined text-[14px]">power_off</span>
                              AC ON (Vacant)
                            </span>
                            <button
                              onClick={() => handleEnergyAction(rm.room_id, "ECO_STANDBY", rm.room_name)}
                              disabled={loadingRoomId === rm.room_id}
                              className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white rounded-lg text-xs font-bold shadow-xs transition-all flex items-center gap-1 cursor-pointer"
                              title="Send IoT BMS relay to shut off AC and lights"
                            >
                              <span className="material-symbols-outlined text-[13px]">power_settings_new</span>
                              {loadingRoomId === rm.room_id ? "Shutting off..." : "Shut Off"}
                            </button>
                          </div>
                        ) : rm.is_occupied ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-teal-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span> In Use
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

        {/* Smart Energy Efficiency & AI Recommendations Sidebar */}
        <div className="xl:col-span-4 flex flex-col gap-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold flex items-center gap-1.5">
                <span className="material-symbols-outlined text-amber-500 text-lg">bolt</span> Smart Energy Efficiency
              </h3>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                AI Action Desk
              </span>
            </div>

            {/* Bulk Action Button */}
            {activeEnergyCount > 0 && (
              <button
                onClick={() => handleBulkEnergyAction("ECO_STANDBY")}
                disabled={bulkLoading}
                className="w-full mb-3 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[16px]">power_settings_new</span>
                {bulkLoading ? "Applying Bulk Standby..." : `Shut Off All Vacant Rooms (${activeEnergyCount})`}
              </button>
            )}

            <div className="space-y-3 text-xs">
              {/* Active Energy Recommendations */}
              {energyRecommendations.map((rec) => (
                <div
                  key={rec.room_id}
                  className="p-3.5 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/40 rounded-xl space-y-2.5 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white text-sm">{rec.room_name}</span>
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 font-mono font-bold">
                        AC ON
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 font-mono font-bold">
                        LIGHTS ON
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-amber-900 dark:text-amber-200 leading-relaxed">
                    {rec.recommendation || `Room vacant for ${rec.vacant_duration_hours || 2} hours while HVAC/lighting remains active.`}
                  </p>

                  <div className="flex items-center justify-between pt-1 border-t border-amber-200/60 dark:border-amber-800/40 text-[10px] text-slate-500">
                    <span>Est. Waste: ~2.4 kWh/hr</span>
                    <span className="text-amber-700 dark:text-amber-300 font-bold">CSI Detected: Vacant</span>
                  </div>

                  {/* Direct Action Controls */}
                  <div className="grid grid-cols-3 gap-1.5 pt-1">
                    <button
                      onClick={() => handleEnergyAction(rec.room_id, "SHUT_OFF_AC", rec.room_name)}
                      disabled={loadingRoomId === rec.room_id}
                      className="py-1.5 px-2 bg-white dark:bg-slate-800 hover:bg-amber-50 border border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-200 rounded font-bold text-[10px] flex items-center justify-center gap-1 cursor-pointer transition-colors shadow-2xs"
                    >
                      <span className="material-symbols-outlined text-[13px]">mode_fan_off</span>
                      Shut AC
                    </button>
                    <button
                      onClick={() => handleEnergyAction(rec.room_id, "SHUT_OFF_LIGHTS", rec.room_name)}
                      disabled={loadingRoomId === rec.room_id}
                      className="py-1.5 px-2 bg-white dark:bg-slate-800 hover:bg-amber-50 border border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-200 rounded font-bold text-[10px] flex items-center justify-center gap-1 cursor-pointer transition-colors shadow-2xs"
                    >
                      <span className="material-symbols-outlined text-[13px]">light_off</span>
                      Shut Lights
                    </button>
                    <button
                      onClick={() => handleEnergyAction(rec.room_id, "ECO_STANDBY", rec.room_name)}
                      disabled={loadingRoomId === rec.room_id}
                      className="py-1.5 px-2 bg-teal-600 hover:bg-teal-700 text-white rounded font-bold text-[10px] flex items-center justify-center gap-1 cursor-pointer transition-colors shadow-2xs"
                    >
                      <span className="material-symbols-outlined text-[13px]">power_settings_new</span>
                      Eco Standby
                    </button>
                  </div>
                </div>
              ))}

              {/* Locally Resolved / Eco-Active Cards */}
              {Object.entries(resolvedEnergyRooms).map(([rId, item]) => (
                <div
                  key={rId}
                  className="p-3 bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800/60 rounded-xl space-y-1.5 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white text-xs">{item.roomName}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200 flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">check_circle</span>
                      Eco Standby Active
                    </span>
                  </div>
                  <p className="text-[11px] text-emerald-800 dark:text-emerald-300">
                    IoT command executed: AC &amp; Lights powered off. 2.4 kWh energy waste prevented.
                  </p>
                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => handleEnergyAction(rId, "RESTORE_NORMAL", item.roomName)}
                      className="text-[10px] text-slate-500 hover:text-slate-800 underline font-semibold cursor-pointer"
                    >
                      Restore Power
                    </button>
                  </div>
                </div>
              ))}

              {energyRecommendations.length === 0 && Object.keys(resolvedEnergyRooms).length === 0 && (
                <div className="p-6 bg-slate-50 dark:bg-slate-950 rounded-xl text-slate-400 italic text-center space-y-1">
                  <span className="material-symbols-outlined text-3xl text-emerald-500">energy_savings_leaf</span>
                  <p className="text-xs font-bold text-slate-700 dark:text-slate-300">All Spaces Energy Optimized</p>
                  <p className="text-[11px] text-slate-400">
                    No vacant rooms detected with unmitigated HVAC or active lighting.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold mb-3">
              Underutilized Spaces
            </h3>
            <div className="space-y-2.5">
              <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg">
                <div className="font-bold text-xs text-slate-900 dark:text-white">MCA Seminar Hall</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Average Utilization: 8.5% (Classification: Seminar Hall)</div>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg">
                <div className="font-bold text-xs text-slate-900 dark:text-white">Faculty Staff Room A</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Average Utilization: 11.2% (Classification: Office)</div>
              </div>
            </div>
            <button
              onClick={generateRepurposingReport}
              className="w-full mt-4 bg-teal-600 text-white py-2 rounded-lg text-xs font-bold uppercase hover:bg-teal-700 shadow-sm cursor-pointer"
            >
              Generate Space Repurposing Audit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
