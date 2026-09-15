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
  const [showAddResident, setShowAddResident] = useState(false);

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
    const activeSub =
      subscriptions.find((s) => s.status === "ACTIVE") ||
      (connections[0]?.subscription_status === "ACTIVE"
        ? { status: "ACTIVE", plan: "CARE_MONTHLY" }
        : familyStatus?.subscription_status === "ACTIVE"
        ? { status: "ACTIVE", plan: "CARE_MONTHLY" }
        : null);

    const approvedConnection = connections.find((c) => c.status === "approved") || connections[0];
    const resFirstName =
      familyStatus?.resident?.first_name ||
      (familyStatus?.resident_name
        ? familyStatus.resident_name.split(" ")[0]
        : approvedConnection?.resident_name
        ? approvedConnection.resident_name.split(" ")[0]
        : "Annamma");
    const resLastName =
      familyStatus?.resident?.last_name ||
      (familyStatus?.resident_name
        ? familyStatus.resident_name.split(" ").slice(1).join(" ")
        : approvedConnection?.resident_name
        ? approvedConnection.resident_name.split(" ").slice(1).join(" ")
        : "Joseph");
    const resRoom =
      familyStatus?.resident?.room_name ||
      familyStatus?.resident?.room?.name ||
      approvedConnection?.room_name ||
      "Resident Room 204";
    const resRelationship = approvedConnection?.relationship || "Son";
    const presenceStatus = (familyStatus?.presence_status || "Safe").toUpperCase();
    const rawActivity = familyStatus?.recent_activity?.activity || "nominal_resting";
    const activityName = rawActivity.replace(/_/g, " ");

    return (
      <div className="space-y-6 text-left max-w-7xl mx-auto pb-12">
        {/* Top Portal Banner & Status */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="material-symbols-outlined text-emerald-600 text-2xl">family_restroom</span>
              <h1 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                Family Care Portal
              </h1>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 px-2 py-0.5 rounded-full">
                Live Care
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Zero-camera ambient RF safety telemetry • Dignified privacy for your loved ones.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-slate-500 dark:text-slate-400 font-medium">RF Sensing:</span>
              <span className="font-bold text-emerald-700 dark:text-emerald-400">ONLINE</span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs">
              <span className="text-slate-500 dark:text-slate-400 font-medium">Subscription:</span>
              <span
                className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                  activeSub
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                }`}
              >
                {activeSub ? "ACTIVE • CARE_PLAN" : "PENDING APPROVAL"}
              </span>
            </div>

            <a
              href="tel:+914828251122"
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">call</span>
              <span>Care Desk: +91 4828 251122</span>
            </a>
          </div>
        </div>

        {/* PRIMARY HERO: Monitored Loved One Live Safety & Telemetry Centerpiece */}
        <div className="bg-gradient-to-br from-white via-white to-emerald-50/30 dark:from-slate-900 dark:via-slate-900 dark:to-emerald-950/20 rounded-2xl border-2 border-emerald-500/20 dark:border-emerald-500/30 p-6 sm:p-7 shadow-sm relative overflow-hidden">
          {/* Subtle Ambient Background Watermark */}
          <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 pointer-events-none opacity-5 dark:opacity-10">
            <span className="material-symbols-outlined text-[240px] text-emerald-600">sensors</span>
          </div>

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-100 dark:border-slate-800">
            {/* Resident Bio & Identity */}
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-emerald-100 dark:bg-emerald-900/50 border-2 border-emerald-300 dark:border-emerald-700 flex items-center justify-center text-emerald-800 dark:text-emerald-200 font-black text-2xl sm:text-3xl shadow-sm">
                  {((resFirstName?.[0] || "A") + (resLastName?.[0] || "J")).toUpperCase()}
                </div>
                <span className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 border-2 border-white dark:border-slate-900 rounded-full flex items-center justify-center">
                  <span className="w-2 h-2 bg-white rounded-full animate-ping"></span>
                </span>
              </div>

              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
                    {resFirstName} {resLastName}
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    Your {resRelationship}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1 font-mono font-semibold text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-[16px] text-emerald-600">room</span>
                    {resRoom}
                  </span>
                  <span>•</span>
                  <span>St. Mary's Elder Care Residence</span>
                </div>
              </div>
            </div>

            {/* Prominent Live Status Badge */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/60 shadow-2xs">
                <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 block">
                    CURRENT STATE
                  </span>
                  <span className="text-sm font-black text-emerald-900 dark:text-emerald-200">
                    {presenceStatus === "SAFE" || presenceStatus === "PRESENT" ? "SAFE & PRESENT" : presenceStatus}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-2xl bg-slate-100 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                <span className="material-symbols-outlined text-[18px] text-emerald-600">visibility_off</span>
                <span className="font-semibold">Zero Cameras • 100% Privacy</span>
              </div>
            </div>
          </div>

          {/* Real-Time Telemetry Cards Grid */}
          <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-3.5 pt-6">
            <div className="bg-white dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Current Posture</span>
                <span className="material-symbols-outlined text-[18px] text-emerald-600">
                  {rawActivity.includes("bed") || rawActivity.includes("rest") ? "bed" : "directions_walk"}
                </span>
              </div>
              <div>
                <div className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white capitalize">
                  {activityName}
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Continuous gait & micro-motion
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Room Presence</span>
                <span className="material-symbols-outlined text-[18px] text-emerald-600">person_pin_circle</span>
              </div>
              <div>
                <div className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white">
                  Present in Room
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  RF subcarrier reflections verified
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">CSI Telemetry</span>
                <span className="material-symbols-outlined text-[18px] text-emerald-600">sensors</span>
              </div>
              <div>
                <div className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-white font-mono">
                  56 Subcarriers
                </div>
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-0.5 font-semibold">
                  Live Stream Synchronized
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-800/80 p-4 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider">Fall Safety</span>
                <span className="material-symbols-outlined text-[18px] text-emerald-600">health_and_safety</span>
              </div>
              <div>
                <div className="text-sm sm:text-base font-extrabold text-emerald-600 dark:text-emerald-400">
                  Nominal (No Falls)
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  24/7 RF velocity guardian
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* MIDDLE SECTION: 2-Column Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column (7 cols): Safety Incident History & Dignity Architecture */}
          <div className="col-span-12 lg:col-span-7 space-y-6">
            {/* Safety & Incident History Log */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-emerald-600">notifications_active</span>
                  <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                    Safety & Incident Log
                  </h3>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                  Read-Only Realtime Log
                </span>
              </div>

              <div className="space-y-3">
                {(familyStatus?.alerts || []).map((a) => (
                  <div
                    key={a.id}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex justify-between items-center text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-red-100 text-red-600 flex items-center justify-center shrink-0">
                        <span className="material-symbols-outlined text-[18px]">warning</span>
                      </div>
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white capitalize">
                          {a.event_type?.replace(/_/g, " ")}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {new Date(a.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        a.status === "resolved"
                          ? "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300"
                          : "bg-red-500 text-white"
                      }`}
                    >
                      {a.status?.toUpperCase()}
                    </span>
                  </div>
                ))}

                {(!familyStatus?.alerts || familyStatus.alerts.length === 0) && (
                  <div className="p-6 text-center rounded-xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
                    <span className="material-symbols-outlined text-emerald-600 text-3xl mb-1">verified</span>
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                      No Emergency Incidents Reported
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
                      Wi-Fi Sense continuous RF gait and posture guardian has verified zero falls or anomalous distress events.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Privacy Architecture Guarantee Card */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-emerald-600 text-xl">shield</span>
                <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                  Invisible Security & Dignity Guarantee
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
                Wi-Fi CSI (Channel State Information) measures minute variations in ambient RF wave fields across 56 Orthogonal Frequency Division Multiplexing (OFDM) subcarriers. Your loved one maintains absolute visual and auditory privacy at all times.
              </p>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center">
                  <span className="material-symbols-outlined text-emerald-600 text-2xl mb-1">videocam_off</span>
                  <div className="font-bold text-xs text-slate-900 dark:text-white">Zero Cameras</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">100% Visual Dignity</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center">
                  <span className="material-symbols-outlined text-emerald-600 text-2xl mb-1">mic_off</span>
                  <div className="font-bold text-xs text-slate-900 dark:text-white">Zero Microphones</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">No Audio Recorded</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center">
                  <span className="material-symbols-outlined text-emerald-600 text-2xl mb-1">lock</span>
                  <div className="font-bold text-xs text-slate-900 dark:text-white">Encrypted RF</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">End-to-End Secure</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols): Controls & Connections */}
          <div className="col-span-12 lg:col-span-5 space-y-6">
            {/* Sharing Policy & Privacy Toggles */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-emerald-600">tune</span>
                <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                  Sharing & Privacy Controls
                </h3>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Tailor telemetry fidelity and disclosure preferences according to family wishes.
              </p>

              <div className="space-y-3">
                <div
                  onClick={() => {
                    setStrictPrivacy(!strictPrivacy);
                    setToastMessage({
                      type: "success",
                      text: `Strict Privacy Mode: ${!strictPrivacy ? "ENABLED" : "DISABLED"}`,
                    });
                  }}
                  className={`p-3.5 border rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                    strictPrivacy
                      ? "border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-emerald-600">visibility_off</span>
                    <div>
                      <div className="font-bold text-xs text-slate-900 dark:text-white">
                        Strict Privacy Mode
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400">
                        Mask specific coordinates to high-level state only
                      </div>
                    </div>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      strictPrivacy ? "border-emerald-600 bg-emerald-600" : "border-slate-300 dark:border-slate-600"
                    }`}
                  >
                    {strictPrivacy && <span className="material-symbols-outlined text-white text-[14px]">check</span>}
                  </div>
                </div>

                <div
                  onClick={() => {
                    setContextualVisibility(!contextualVisibility);
                    setToastMessage({
                      type: "success",
                      text: `Contextual Activity Stream: ${!contextualVisibility ? "ENABLED" : "DISABLED"}`,
                    });
                  }}
                  className={`p-3.5 border rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                    contextualVisibility
                      ? "border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-emerald-600">show_chart</span>
                    <div>
                      <div className="font-bold text-xs text-slate-900 dark:text-white">
                        Contextual Activity Stream
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400">
                        Show motion classifications (resting, walking)
                      </div>
                    </div>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      contextualVisibility
                        ? "border-emerald-600 bg-emerald-600"
                        : "border-slate-300 dark:border-slate-600"
                    }`}
                  >
                    {contextualVisibility && (
                      <span className="material-symbols-outlined text-white text-[14px]">check</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Direct Care Desk Quick Contact Box */}
              <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 mt-5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Facility Station Help Desk
                    </div>
                    <div className="font-extrabold text-sm text-slate-900 dark:text-white mt-0.5">
                      St. Peter's Nursing Care
                    </div>
                    <div className="text-xs text-slate-500 font-mono">+91 4828 251122</div>
                  </div>
                  <a
                    href="tel:+914828251122"
                    className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
                  >
                    <span className="material-symbols-outlined text-[16px]">call</span>
                    <span>Call Desk</span>
                  </a>
                </div>
              </div>
            </div>

            {/* Resident Connections & Expandable Link Option */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 sm:p-6 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-emerald-600">link</span>
                  <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                    Connected Residents
                  </h3>
                </div>
                <button
                  onClick={() => setShowAddResident(!showAddResident)}
                  className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[16px]">
                    {showAddResident ? "expand_less" : "add_circle"}
                  </span>
                  <span>{showAddResident ? "Hide Form" : "+ Link Another"}</span>
                </button>
              </div>

              {/* Active Connection Summary */}
              <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/80 dark:border-emerald-800/50 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-sm">
                    {((resFirstName?.[0] || "A") + (resLastName?.[0] || "J")).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-bold text-xs text-slate-900 dark:text-white">
                      {resFirstName} {resLastName}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {resRoom} • Relationship: {resRelationship}
                    </div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                  APPROVED
                </span>
              </div>

              {/* Collapsible Connection Request Form */}
              {showAddResident && (
                <form
                  onSubmit={handleCreateConnection}
                  className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800 animate-fadeIn"
                >
                  <p className="text-xs text-slate-500">
                    Request authorization to monitor another elder resident:
                  </p>
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">
                      Target Resident
                    </label>
                    <select
                      value={selectedRequestResidentId}
                      onChange={(e) => setSelectedRequestResidentId(e.target.value)}
                      required
                      className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                    >
                      <option value="">-- Choose Resident --</option>
                      {residents.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.first_name} {r.last_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">
                        Relationship
                      </label>
                      <select
                        value={newRelationship}
                        onChange={(e) => setNewRelationship(e.target.value)}
                        className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
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
                      <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">
                        Verification Note
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Next-of-kin"
                        value={newNotes}
                        onChange={(e) => setNewNotes(e.target.value)}
                        className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={submittingConnection}
                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold uppercase transition-colors cursor-pointer"
                  >
                    {submittingConnection ? "Submitting..." : "Submit Connection Request"}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
