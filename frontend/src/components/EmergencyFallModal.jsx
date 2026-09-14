import React, { useState, useEffect } from "react";

export default function EmergencyFallModal({
  authToken = "",
  role = "",
  appContext = "",
  isSystemAdmin = false,
  onActionComplete = () => {},
  onClose = () => {},
}) {
  const [emergencyData, setEmergencyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dismissedAlertId, setDismissedAlertId] = useState(null);

  const isCareOps =
    appContext === "ELDER_CARE" &&
    !isSystemAdmin &&
    (role === "caregiver" || role === "organization_admin" || role === "facility_manager");

  const fetchActiveEmergency = async () => {
    if (!authToken) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/alerts/emergency-active", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        const isSessionDismissed =
          data.has_emergency &&
          sessionStorage.getItem(`dismissed_emergency_${data.alert_id}`) === "true";

        if (
          data.has_emergency &&
          data.alert_id !== dismissedAlertId &&
          !isSessionDismissed &&
          data.status !== "resolved"
        ) {
          setEmergencyData(data);
        } else if (!data.has_emergency || data.status === "resolved" || isSessionDismissed) {
          setEmergencyData(null);
        }
      }
    } catch (e) {
      console.warn("Emergency poll error:", e);
    }
  };

  useEffect(() => {
    fetchActiveEmergency();
    const timer = setInterval(fetchActiveEmergency, 4000);
    return () => clearInterval(timer);
  }, [authToken, dismissedAlertId]);

  const handleDismiss = () => {
    if (emergencyData && emergencyData.alert_id) {
      sessionStorage.setItem(`dismissed_emergency_${emergencyData.alert_id}`, "true");
      setDismissedAlertId(emergencyData.alert_id);
    }
    setEmergencyData(null);
    onClose();
  };

  const handleAction = async (actionType) => {
    if (!emergencyData || !emergencyData.alert_id) return;
    setLoading(true);
    try {
      if (actionType === "acknowledge") {
        await fetch(`http://127.0.0.1:8000/alerts/${emergencyData.alert_id}/acknowledge`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        });
        setEmergencyData((prev) => ({ ...prev, status: "acknowledged" }));
      } else if (actionType === "responding") {
        await fetch(`http://127.0.0.1:8000/alerts/${emergencyData.alert_id}/responding`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
        });
        setEmergencyData((prev) => ({ ...prev, status: "responding" }));
      } else if (actionType === "resolve") {
        await fetch(`http://127.0.0.1:8000/alerts/${emergencyData.alert_id}/resolve`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
          body: JSON.stringify({
            resolution_notes:
              "Emergency fall protocol executed by on-duty care personnel. Subject stabilized.",
          }),
        });
        if (emergencyData && emergencyData.alert_id) {
          sessionStorage.setItem(`dismissed_emergency_${emergencyData.alert_id}`, "true");
        }
        setDismissedAlertId(emergencyData.alert_id);
        setEmergencyData(null);
      }
      onActionComplete();
    } catch (err) {
      console.error("Action error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!emergencyData) return null;

  const contact = emergencyData.emergency_contact || {
    name: "Care Desk Officer",
    relationship: "Primary Response",
    phone: "+91 4828 251122",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border-2 border-red-600 rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border-t-8 border-t-red-600 animate-scale-up">
        {/* Header with Close [x] Button */}
        <div className="bg-red-50 dark:bg-red-950/40 p-5 flex items-center justify-between border-b border-red-200 dark:border-red-900/50">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-full bg-red-600 text-white flex items-center justify-center animate-pulse shrink-0">
              <span className="material-symbols-outlined text-2xl">emergency</span>
            </span>
            <div>
              <h2 className="text-xl font-black text-red-600 uppercase tracking-wide">
                EMERGENCY — FALL DETECTED
              </h2>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Wi-Fi CSI Sensing Event • Immediate Protocol Required
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-mono px-2.5 py-1 rounded bg-red-600 text-white font-bold tracking-wider">
              {emergencyData.status}
            </span>
            <button
              onClick={handleDismiss}
              className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-red-100 hover:text-red-700 dark:hover:bg-red-950/60 dark:hover:text-red-300 flex items-center justify-center transition-colors cursor-pointer"
              title="Close / Dismiss Alert Modal"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        {/* Role Responsibility Notice for System Admin */}
        {isSystemAdmin && (
          <div className="bg-amber-50 dark:bg-amber-950/40 border-b border-amber-200 dark:border-amber-900/40 px-5 py-2.5 flex items-center gap-2 text-xs text-amber-900 dark:text-amber-200 font-medium">
            <span className="material-symbols-outlined text-amber-600 text-[18px]">info</span>
            <span>
              <strong>Supervisory Monitor View:</strong> On-duty Caregiver &amp; Elder Care Facility
              Manager have active operational responsibility to dispatch assistance and resolve this
              incident.
            </span>
          </div>
        )}

        {/* Body Content */}
        <div className="p-6 space-y-5 text-left">
          {/* Main Resident & Room info */}
          <div className="grid grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
            <div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                RESIDENT
              </p>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                {emergencyData.resident_name}
              </h3>
            </div>
            <div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                ROOM LOCATION
              </p>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5 font-mono">
                {emergencyData.room_name}
              </h3>
            </div>
            <div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                DETECTED TIME
              </p>
              <p className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300 mt-0.5">
                {emergencyData.created_at
                  ? new Date(emergencyData.created_at).toLocaleString()
                  : "Live Active"}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                DETECTED ACTIVITY
              </p>
              <p className="text-xs font-bold text-red-600 flex items-center gap-1 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
                Fall Detected
              </p>
            </div>
          </div>

          {/* CSI Telemetry Fingerprint (RuView Integration) */}
          <div className="grid grid-cols-4 gap-2 bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-center">
            <div>
              <span className="text-[9px] font-bold uppercase text-slate-400 block">
                SIGNAL QUALITY
              </span>
              <span className="text-xs font-mono font-bold text-teal-600 dark:text-teal-400">
                {emergencyData.csi_telemetry?.signal_quality || "94%"}
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold uppercase text-slate-400 block">
                SUBCARRIERS
              </span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                {emergencyData.csi_telemetry?.subcarriers || "56"}
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold uppercase text-slate-400 block">RSSI</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                {emergencyData.csi_telemetry?.rssi || "-42 dBm"}
              </span>
            </div>
            <div>
              <span className="text-[9px] font-bold uppercase text-slate-400 block">CONFIDENCE</span>
              <span className="text-xs font-mono font-bold text-teal-600 dark:text-teal-400">
                {emergencyData.csi_telemetry?.confidence || "97.5%"}
              </span>
            </div>
          </div>

          {/* Primary Emergency Contact Card */}
          <div className="border-2 border-red-200 dark:border-red-900/60 rounded-xl p-4 bg-red-50/30 dark:bg-red-950/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-red-600 uppercase flex items-center gap-1">
                <span className="material-symbols-outlined text-sm">contact_emergency</span>
                PRIMARY EMERGENCY CONTACT
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-300">
                Priority 1
              </span>
            </div>
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-bold text-slate-900 dark:text-white text-base">
                  {contact.name}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Relationship:{" "}
                  <strong className="text-slate-700 dark:text-slate-200">
                    {contact.relationship}
                  </strong>
                </p>
                <p className="text-xs font-mono font-semibold text-slate-800 dark:text-slate-300 mt-1">
                  {contact.phone}
                </p>
              </div>
              <a
                href={`tel:${contact.phone.replace(/[^0-9+]/g, "")}`}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all"
                title="Initiate phone call via device dialer"
              >
                <span className="material-symbols-outlined text-sm">call</span>
                Call Contact
              </a>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-slate-50 dark:bg-slate-800/80 p-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center gap-3">
          <button
            type="button"
            onClick={handleDismiss}
            className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
          >
            Dismiss / Stand Down
          </button>

          <div className="flex items-center gap-2">
            {emergencyData.status === "new" && isCareOps && (
              <button
                disabled={loading}
                onClick={() => handleAction("acknowledge")}
                className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-100 dark:hover:bg-slate-700 transition cursor-pointer"
              >
                Acknowledge
              </button>
            )}
            {emergencyData.status !== "responding" && isCareOps && (
              <button
                disabled={loading}
                onClick={() => handleAction("responding")}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-bold shadow-sm transition cursor-pointer"
              >
                Mark Responding
              </button>
            )}
            {isCareOps ? (
              <button
                disabled={loading}
                onClick={() => handleAction("resolve")}
                className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-bold shadow-sm transition flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-base">check_circle</span>
                Resolve Emergency
              </button>
            ) : (
              <button
                type="button"
                onClick={handleDismiss}
                className="px-5 py-2 bg-slate-800 hover:bg-slate-900 dark:bg-white dark:hover:bg-slate-100 dark:text-slate-900 text-white rounded-lg text-sm font-bold shadow-sm transition cursor-pointer"
              >
                Close Monitoring View
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
