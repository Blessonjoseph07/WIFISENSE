import React, { useState, useEffect } from "react";

export default function FamilyPortalView({
  role = "",
  familyStatus = null,
  setFamilyStatus = () => {},
  selectedRequestResidentId = "",
  setSelectedRequestResidentId = () => {},
  residents = [],
  submitLinkRequest = () => {},
  setToastMessage = () => {},
  strictPrivacy = false,
  setStrictPrivacy = () => {},
  contextualVisibility = true,
  setContextualVisibility = () => {},
  authToken = "",
}) {
  const [connections, setConnections] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adminViewTab, setAdminViewTab] = useState("connections"); // "connections" | "subscriptions" | "preview"
  const [newRelationship, setNewRelationship] = useState("Son");
  const [newNotes, setNewNotes] = useState("");
  const [submittingConnection, setSubmittingConnection] = useState(false);

  const token = authToken || localStorage.getItem("token") || "";
  const isAdmin = role === "system_admin" || role === "organization_admin" || role === "facility_manager";

  const fetchConnectionsAndSubscriptions = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const connRes = await fetch("http://127.0.0.1:8000/family/connections", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (connRes.ok) {
        setConnections(await connRes.json());
      }

      const subRes = await fetch("http://127.0.0.1:8000/family/subscriptions", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (subRes.ok) {
        setSubscriptions(await subRes.json());
      }
    } catch (e) {
      console.warn("Failed to load family connections:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnectionsAndSubscriptions();
  }, [token]);

  const handleReviewConnection = async (connectionId, newStatus) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/family/connections/${connectionId}/review`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setToastMessage({
          type: "success",
          text: `Family connection status updated to: ${newStatus.toUpperCase()}`,
        });
        fetchConnectionsAndSubscriptions();
      } else {
        const err = await res.json();
        setToastMessage({ type: "error", text: err.detail || "Failed to update connection." });
      }
    } catch (e) {
      setToastMessage({ type: "error", text: "Network error updating connection." });
    }
  };

  const handleToggleSubscription = async (subId, currentStatus) => {
    const nextStatus = currentStatus === "ACTIVE" ? "PENDING" : "ACTIVE";
    try {
      const res = await fetch(`http://127.0.0.1:8000/family/subscriptions/${subId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) {
        setToastMessage({
          type: "success",
          text: `Subscription set to ${nextStatus}`,
        });
        fetchConnectionsAndSubscriptions();
      }
    } catch (e) {
      setToastMessage({ type: "error", text: "Failed to update subscription." });
    }
  };

  const handleCreateConnection = async (e) => {
    e.preventDefault();
    if (!selectedRequestResidentId) return;
    setSubmittingConnection(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/family/connections", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resident_id: selectedRequestResidentId,
          relationship: newRelationship,
          notes: newNotes,
        }),
      });
      if (res.ok) {
        setToastMessage({
          type: "success",
          text: "Connection request submitted. Awaiting Facility Manager approval.",
        });
        setSelectedRequestResidentId("");
        setNewNotes("");
        fetchConnectionsAndSubscriptions();
      } else {
        const err = await res.json();
        setToastMessage({ type: "error", text: err.detail || "Failed to submit request." });
      }
    } catch (e) {
      setToastMessage({ type: "error", text: "Network error submitting request." });
    } finally {
      setSubmittingConnection(false);
    }
  };

  // =========================================================================
  // ADMIN / FACILITY MANAGER VIEW
  // =========================================================================
  if (isAdmin) {
    return (
      <div className="space-y-6 text-left">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-teal-600 text-3xl">family_restroom</span>
              Family Portal Administration
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage multi-resident family connections, access verification, and subscription gating.
            </p>
          </div>
          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
            <button
              onClick={() => setAdminViewTab("connections")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                adminViewTab === "connections"
                  ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Connections ({connections.length})
            </button>
            <button
              onClick={() => setAdminViewTab("subscriptions")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                adminViewTab === "subscriptions"
                  ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Subscriptions ({subscriptions.length})
            </button>
            <button
              onClick={() => setAdminViewTab("preview")}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                adminViewTab === "preview"
                  ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Member Preview
            </button>
          </div>
        </div>

        {/* Tab 1: Connections Manager */}
        {adminViewTab === "connections" && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Elder-Care Resident Family Connections
              </h2>
              <button
                onClick={fetchConnectionsAndSubscriptions}
                className="text-xs font-bold text-teal-600 hover:underline flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[16px]">refresh</span> Refresh
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold text-slate-500 uppercase">
                  <tr>
                    <th className="px-5 py-3">Family User</th>
                    <th className="px-5 py-3">Relationship</th>
                    <th className="px-5 py-3">Linked Resident</th>
                    <th className="px-5 py-3">Room</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Subscription</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                  {connections.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="px-5 py-3.5">
                        <div className="font-bold text-slate-900 dark:text-white">
                          {c.family_user_name || "Family User"}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">{c.family_user_email}</div>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-slate-700 dark:text-slate-300">
                        {c.relationship}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="font-bold text-slate-900 dark:text-white">{c.resident_name}</span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 dark:text-slate-400">
                        {c.room_name}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            c.status === "approved"
                              ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300"
                              : c.status === "rejected"
                              ? "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400"
                              : "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 animate-pulse"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            c.subscription_status === "ACTIVE"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {c.subscription_status || "PENDING"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right space-x-2">
                        {c.status === "pending" && (
                          <>
                            <button
                              onClick={() => handleReviewConnection(c.id, "approved")}
                              className="px-3 py-1 bg-teal-600 text-white rounded text-[11px] font-bold hover:bg-teal-700 cursor-pointer"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReviewConnection(c.id, "rejected")}
                              className="px-3 py-1 bg-red-100 text-red-700 rounded text-[11px] font-bold hover:bg-red-200 cursor-pointer"
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {c.status === "approved" && (
                          <button
                            onClick={() => handleReviewConnection(c.id, "revoked")}
                            className="px-2.5 py-1 text-slate-400 hover:text-red-600 text-[11px] font-bold cursor-pointer"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {connections.length === 0 && (
                    <tr>
                      <td colSpan="7" className="p-8 text-center text-slate-400 italic">
                        No family connection requests logged.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Subscriptions Manager */}
        {adminViewTab === "subscriptions" && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Family Portal Subscriptions & Access Tier Gating
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold text-slate-500 uppercase">
                  <tr>
                    <th className="px-5 py-3">Subscription ID</th>
                    <th className="px-5 py-3">Plan Tier</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Started At</th>
                    <th className="px-5 py-3 text-right">Toggle Tier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                  {subscriptions.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="px-5 py-3.5 font-mono text-slate-500 text-[11px]">{s.id.slice(0, 8)}...</td>
                      <td className="px-5 py-3.5 font-bold text-teal-600 dark:text-teal-400">{s.plan}</td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            s.status === "ACTIVE"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-400 font-mono text-[11px]">
                        {s.started_at ? new Date(s.started_at).toLocaleDateString() : "Pending"}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => handleToggleSubscription(s.id, s.status)}
                          className={`px-3 py-1 rounded text-[11px] font-bold cursor-pointer ${
                            s.status === "ACTIVE"
                              ? "bg-amber-50 text-amber-700 hover:bg-amber-100"
                              : "bg-emerald-600 text-white hover:bg-emerald-700"
                          }`}
                        >
                          Set {s.status === "ACTIVE" ? "PENDING" : "ACTIVE"}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {subscriptions.length === 0 && (
                    <tr>
                      <td colSpan="5" className="p-8 text-center text-slate-400 italic">
                        No subscriptions found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Member Preview (Live Demo Mode) */}
        {adminViewTab === "preview" && (
          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
            <p className="text-xs text-slate-500 mb-4 font-semibold">
              Previewing the family member live portal view below:
            </p>
            {renderMemberPortal()}
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // FAMILY MEMBER USER VIEW
  // =========================================================================
  return renderMemberPortal();

  function renderMemberPortal() {
    const activeSub = subscriptions.find((s) => s.status === "ACTIVE") || (connections[0]?.subscription_status === "ACTIVE" ? { status: "ACTIVE" } : null);

    return (
      <div className="space-y-6 text-left">
        {/* Header with Connection & Subscription status */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-teal-600 text-3xl">family_restroom</span>
              Family Care Portal
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Zero-camera privacy-first RF sensing for your loved ones.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
              <span className="text-slate-400 font-semibold">Subscription:</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  activeSub
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                }`}
              >
                {activeSub ? "ACTIVE • CARE_MONTHLY" : "PENDING APPROVAL"}
              </span>
            </div>
          </div>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Privacy Guarantee Hero Card (Span 8) */}
          <div className="col-span-12 lg:col-span-8 bg-teal-50/40 dark:bg-teal-950/10 rounded-xl border border-slate-200 dark:border-slate-800 p-6 relative overflow-hidden flex flex-col justify-between shadow-sm">
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-800 mb-4">
                <span className="material-symbols-outlined text-[16px] text-teal-600">verified_user</span>
                <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase">
                  Zero Camera Ambient Sensing
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                Invisible Security. Zero Cameras. Absolute Dignity.
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mb-4">
                Wi-Fi CSI senses room presence and gait motion mathematically through 56 subcarrier signal reflections. No cameras or microphones are ever used.
              </p>
            </div>
            <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-white/80 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <span className="material-symbols-outlined text-teal-600 text-xl mb-1">videocam_off</span>
                <div className="font-bold text-xs text-slate-900 dark:text-white">No Optical Video</div>
                <div className="text-[10px] text-slate-500 mt-0.5">100% Visual Privacy</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <span className="material-symbols-outlined text-teal-600 text-xl mb-1">mic_off</span>
                <div className="font-bold text-xs text-slate-900 dark:text-white">No Audio Capture</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Zero Microphones</div>
              </div>
              <div className="bg-white/80 dark:bg-slate-900/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                <span className="material-symbols-outlined text-teal-600 text-xl mb-1">lock</span>
                <div className="font-bold text-xs text-slate-900 dark:text-white">Encrypted CSI</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Secure Facility Telemetry</div>
              </div>
            </div>
          </div>

          {/* Connect Another Resident Card (Span 4) */}
          <div className="col-span-12 lg:col-span-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 flex flex-col shadow-sm">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-1 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-teal-600 text-[18px]">person_add</span>
              Connect Elder Resident
            </h3>
            <p className="text-xs text-slate-500 mb-3">Submit link request for family authorization.</p>
            <form onSubmit={handleCreateConnection} className="space-y-3 text-xs flex-1 flex flex-col justify-between">
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Target Resident</label>
                <select
                  value={selectedRequestResidentId}
                  onChange={(e) => setSelectedRequestResidentId(e.target.value)}
                  required
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">-- Choose Resident --</option>
                  {residents.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.first_name} {r.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Your Relationship</label>
                <select
                  value={newRelationship}
                  onChange={(e) => setNewRelationship(e.target.value)}
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                >
                  <option value="Son">Son</option>
                  <option value="Daughter">Daughter</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Brother">Brother</option>
                  <option value="Sister">Sister</option>
                  <option value="Guardian">Guardian</option>
                  <option value="Other">Other Relative</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Verification Note</label>
                <input
                  type="text"
                  placeholder="e.g. Registered next-of-kin"
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                />
              </div>
              <button
                type="submit"
                disabled={submittingConnection}
                className="w-full py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 transition-colors cursor-pointer mt-2"
              >
                {submittingConnection ? "Submitting..." : "Submit Connection Request"}
              </button>
            </form>
          </div>

          {/* Resident Live Status Card (Span 6) */}
          <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col">
            <div className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-teal-600">health_and_safety</span>
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  Monitored Elder Safety Status
                </h3>
              </div>
              <span className="text-[10px] font-bold bg-teal-50 text-teal-700 px-2 py-0.5 rounded">
                Live Telemetry
              </span>
            </div>
            <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-base font-bold text-slate-900 dark:text-white">
                      {familyStatus?.resident?.first_name || "Annamma"} {familyStatus?.resident?.last_name || "Joseph"}
                    </h4>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                      Assigned: {familyStatus?.resident?.room_name || "Resident Room 204"}
                    </p>
                  </div>
                  <span className="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 px-3 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    {(familyStatus?.presence_status || "Safe").toUpperCase()}
                  </span>
                </div>
                <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3 flex justify-between items-center text-xs">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Current Activity</span>
                    <span className="font-bold text-slate-900 dark:text-white capitalize">
                      {familyStatus?.recent_activity?.activity?.replace("_", " ") || "Nominal Resting"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Last Shift Detection</span>
                    <span className="font-mono text-slate-600 dark:text-slate-400">
                      {familyStatus?.recent_activity?.timestamp
                        ? new Date(familyStatus.recent_activity.timestamp).toLocaleTimeString()
                        : "Synchronized"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Alert History */}
              <div className="flex-1">
                <h4 className="text-[11px] font-bold uppercase text-slate-400 mb-2">
                  Recent Incident History (Read-Only)
                </h4>
                <div className="space-y-2 max-h-[140px] overflow-y-auto">
                  {(familyStatus?.alerts || []).map((a) => (
                    <div
                      key={a.id}
                      className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs"
                    >
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white">
                          {a.event_type?.replace("_", " ")}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {new Date(a.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.status === "resolved"
                            ? "bg-slate-100 text-slate-600"
                            : "bg-red-50 text-red-600"
                        }`}
                      >
                        {a.status?.toUpperCase()}
                      </span>
                    </div>
                  ))}
                  {(!familyStatus?.alerts || familyStatus.alerts.length === 0) && (
                    <p className="text-xs text-slate-400 italic text-center p-3">
                      No warning incidents recorded.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Privacy Controls (Span 6) */}
          <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 flex flex-col justify-between shadow-sm">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white mb-1">
                Sharing Policy &amp; Safety Controls
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Strict privacy masks fine-grained coordinates according to resident consent.
              </p>
              <div className="space-y-3">
                <div
                  onClick={() => {
                    setStrictPrivacy(!strictPrivacy);
                    setToastMessage({
                      type: "success",
                      text: `Strict Privacy Mode: ${!strictPrivacy ? "ON" : "OFF"}`,
                    });
                  }}
                  className={`p-3 border rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                    strictPrivacy ? "border-teal-500 bg-teal-50/20" : "border-slate-200 dark:border-slate-800"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-teal-600">visibility_off</span>
                    <div>
                      <div className="font-bold text-xs text-slate-900 dark:text-white">Strict Privacy Mode</div>
                      <div className="text-[11px] text-slate-500">Mask presence coordinates to high-level status only</div>
                    </div>
                  </div>
                  <span className={`w-3 h-3 rounded-full ${strictPrivacy ? "bg-teal-600" : "bg-slate-300"}`}></span>
                </div>

                <div
                  onClick={() => {
                    setContextualVisibility(!contextualVisibility);
                    setToastMessage({
                      type: "success",
                      text: `Contextual Visibility: ${!contextualVisibility ? "ON" : "OFF"}`,
                    });
                  }}
                  className={`p-3 border rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                    contextualVisibility ? "border-teal-500 bg-teal-50/20" : "border-slate-200 dark:border-slate-800"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-teal-600">visibility</span>
                    <div>
                      <div className="font-bold text-xs text-slate-900 dark:text-white">Contextual Activity Stream</div>
                      <div className="text-[11px] text-slate-500">Show room activity classifications (walking, resting)</div>
                    </div>
                  </div>
                  <span className={`w-3 h-3 rounded-full ${contextualVisibility ? "bg-teal-600" : "bg-slate-300"}`}></span>
                </div>
              </div>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 mt-4">
              <div className="text-[10px] font-bold uppercase text-slate-400">Emergency Help Desk Contact</div>
              <div className="flex justify-between items-center mt-1 text-xs">
                <div>
                  <div className="font-bold text-slate-900 dark:text-white">St. Peter's Care Desk</div>
                  <div className="text-slate-500 font-mono text-[11px]">+91 4828 251122</div>
                </div>
                <a
                  href="tel:+914828251122"
                  className="px-3 py-1 bg-teal-600 text-white rounded text-xs font-bold hover:bg-teal-700 flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-[14px]">call</span>
                  Direct Desk
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
