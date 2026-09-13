import React from "react";

export default function ResidentsView({
  residents = [],
  rooms = [],
  accessRequests = [],
  setNewResRmId = () => {},
  setShowAddResidentModal = () => {},
  triggerEmergencyProtocol = () => {},
  setCurrentView = () => {},
}) {
  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            Resident Accounts
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Auditing active monitored profiles, emergency contacts, and room assignments.
          </p>
        </div>
        <button
          onClick={() => {
            if (rooms.length > 0) {
              setNewResRmId(rooms[0].id);
              setShowAddResidentModal(true);
            } else {
              alert("Please create a room first.");
            }
          }}
          className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow cursor-pointer"
        >
          Add Resident Record
        </button>
      </div>

      {/* Residents table list */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 font-bold uppercase">
                <th className="p-4">Resident Subject</th>
                <th className="p-4">Assigned Location</th>
                <th className="p-4">Family Emergency Contact</th>
                <th className="p-4">Link Status</th>
                <th className="p-4 text-right">Emergency Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {residents.map((res) => {
                const assignedRoom = rooms.find((r) => r.id === res.room_id);
                const req = accessRequests.find((a) => a.resident_id === res.id);
                return (
                  <tr
                    key={res.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center text-teal-650 dark:text-teal-400 font-bold text-sm">
                          {(res.first_name?.[0] || "") + (res.last_name?.[0] || "")}
                        </div>
                        <div>
                          <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">
                            {res.first_name} {res.last_name}
                          </div>
                          <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">
                            DOB: {res.date_of_birth ? new Date(res.date_of_birth).toLocaleDateString() : "N/A"} • ID: {res.id.slice(0, 8)}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {assignedRoom ? assignedRoom.name : "Unassigned"}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {assignedRoom ? assignedRoom.room_type || assignedRoom.classification : "No Room"}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {res.emergency_contact_name || "None Listed"}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {res.emergency_contact_phone || res.emergency_contact_email || "N/A"}
                      </div>
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                          req?.status === "pending"
                            ? "bg-amber-50 text-amber-600 border border-amber-200"
                            : req?.status === "approved"
                            ? "bg-teal-50 text-teal-600 border border-teal-200"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {req ? `Family Link: ${req.status.toUpperCase()}` : "Monitored Profile"}
                      </span>
                    </td>
                    <td className="p-4 text-right space-x-2">
                      <button
                        onClick={() => setCurrentView("occupancy")}
                        className="px-2.5 py-1 text-xs font-bold text-teal-600 border border-teal-300 dark:border-teal-700 hover:bg-teal-50 dark:hover:bg-teal-950/40 rounded transition-colors cursor-pointer"
                      >
                        Inspect Room
                      </button>
                      <button
                        onClick={triggerEmergencyProtocol}
                        className="px-2.5 py-1 text-xs font-bold bg-red-600 text-white hover:bg-red-700 rounded shadow-xs transition-colors cursor-pointer"
                      >
                        Dispatch Emergency
                      </button>
                    </td>
                  </tr>
                );
              })}
              {residents.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-400 italic">
                    No resident records registered.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
