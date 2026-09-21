import React, { useState, useEffect } from "react";

export default function SharingPolicyManager({
  policies = [],
  organizations = [],
  residents = [],
  canEdit = false,
  userRole = "",
  onUpdatePolicy = async () => {},
  isLoading = false
}) {
  const [editingStates, setEditingStates] = useState({});
  const [savingPolicyId, setSavingPolicyId] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  // Initialize or synchronize local form state from incoming policies
  useEffect(() => {
    if (policies && policies.length > 0) {
      const initial = {};
      policies.forEach((policy) => {
        initial[policy.id] = {
          share_presence: policy.share_presence ?? true,
          share_activity_detail: policy.share_activity_detail ?? true,
          share_room_name: policy.share_room_name ?? true,
          share_alert_history: policy.share_alert_history ?? true,
          share_alert_severity_threshold: policy.share_alert_severity_threshold || "MEDIUM"
        };
      });
      setEditingStates(initial);
    }
  }, [policies]);

  const handleToggle = (policyId, field) => {
    if (!canEdit) return;
    setEditingStates((prev) => ({
      ...prev,
      [policyId]: {
        ...prev[policyId],
        [field]: !prev[policyId]?.[field]
      }
    }));
  };

  const handleThresholdChange = (policyId, value) => {
    if (!canEdit) return;
    setEditingStates((prev) => ({
      ...prev,
      [policyId]: {
        ...prev[policyId],
        share_alert_severity_threshold: value
      }
    }));
  };

  const handleSave = async (policyId) => {
    if (!canEdit || savingPolicyId) return;
    const currentState = editingStates[policyId];
    if (!currentState) return;

    setSavingPolicyId(policyId);
    setStatusMessage(null);
    try {
      await onUpdatePolicy(policyId, currentState);
      setStatusMessage({
        policyId,
        type: "success",
        text: "Sharing policy successfully saved and active."
      });
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      setStatusMessage({
        policyId,
        type: "error",
        text: err.message || "Failed to update sharing policy."
      });
    } finally {
      setSavingPolicyId(null);
    }
  };

  // Group policies into Organization-level and Resident-specific overrides
  const orgPolicies = policies.filter((p) => !p.resident_id);
  const residentOverrides = policies.filter((p) => Boolean(p.resident_id));

  return (
    <div className="space-y-6 text-left">
      {/* Header & Role Badge Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-2xl">
              verified_user
            </span>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Family Data Sharing Policies
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Govern automated sensor telemetry, posture observations, and critical emergency fall disclosures shared with verified family members.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          {canEdit ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              EDITOR ACCESS • {userRole === "system_admin" ? "System Admin" : "Org Administrator"}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
              <span className="material-symbols-outlined text-[14px]">visibility</span>
              READ-ONLY • Facility Manager
            </span>
          )}
        </div>
      </div>

      {/* Facility Manager Read-Only Notice */}
      {!canEdit && (
        <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 flex items-start gap-3">
          <span className="material-symbols-outlined text-amber-600 dark:text-amber-400 text-lg shrink-0 mt-0.5">
            info
          </span>
          <div className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
            <strong>View-Only Mode:</strong> Facility Managers can audit and review data sharing policies, but cannot modify rules or thresholds. Modifying sharing policies requires an Organization Administrator or System Administrator account.
          </div>
        </div>
      )}

      {/* Organization Baseline Policy */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
          <span className="material-symbols-outlined text-base text-emerald-600 dark:text-emerald-400">
            domain
          </span>
          Facility Baseline Policy
        </h3>

        {orgPolicies.length === 0 && !isLoading && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 text-center text-slate-400">
            No organization baseline sharing policies found.
          </div>
        )}

        {orgPolicies.map((policy) => {
          const form = editingStates[policy.id] || policy;
          const org = organizations.find((o) => o.id === policy.organization_id);
          const isSaving = savingPolicyId === policy.id;
          const msg = statusMessage?.policyId === policy.id ? statusMessage : null;

          // Check if modified compared to original
          const isDirty =
            form.share_presence !== policy.share_presence ||
            form.share_activity_detail !== policy.share_activity_detail ||
            form.share_room_name !== policy.share_room_name ||
            form.share_alert_history !== policy.share_alert_history ||
            form.share_alert_severity_threshold !== policy.share_alert_severity_threshold;

          return (
            <div
              key={policy.id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xs hover:border-emerald-200 dark:hover:border-slate-700 transition-colors"
            >
              {/* Policy Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3 mb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-900 dark:text-white text-base">
                      {org?.name || "Elder Care Organization Baseline"}
                    </h4>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      ID: {policy.id.substring(0, 8)}...
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Universal baseline rule applying to all enrolled residents without individual overrides.
                  </p>
                </div>

                {isDirty && canEdit && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full self-start">
                    ● Unsaved Changes
                  </span>
                )}
              </div>

              {/* Five Controlled Scope Toggles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {/* 1. share_presence */}
                <div className="flex items-start justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <div className="pr-4">
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">
                        sensors
                      </span>
                      Room Presence Disclosure
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Share binary presence (safe in suite / outside suite) with family portal.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={!canEdit}
                    onClick={() => handleToggle(policy.id, "share_presence")}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      form.share_presence ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                    } ${!canEdit ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                        form.share_presence ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* 2. share_activity_detail */}
                <div className="flex items-start justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <div className="pr-4">
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">
                        directions_walk
                      </span>
                      Activity & Posture Detail
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Allow family to see classified motions (Walking, Sitting, Resting, Ambulation).
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={!canEdit}
                    onClick={() => handleToggle(policy.id, "share_activity_detail")}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      form.share_activity_detail ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                    } ${!canEdit ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                        form.share_activity_detail ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* 3. share_room_name */}
                <div className="flex items-start justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <div className="pr-4">
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">
                        meeting_room
                      </span>
                      Room / Suite Identifier
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Disclose exact suite number (e.g. "Room 102") on the family dashboard.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={!canEdit}
                    onClick={() => handleToggle(policy.id, "share_room_name")}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      form.share_room_name ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                    } ${!canEdit ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                        form.share_room_name ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>

                {/* 4. share_alert_history */}
                <div className="flex items-start justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <div className="pr-4">
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">
                        notifications_active
                      </span>
                      Safety & Fall Notifications
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Send external email notifications & show incident logs to authorized family.
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={!canEdit}
                    onClick={() => handleToggle(policy.id, "share_alert_history")}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      form.share_alert_history ? "bg-emerald-600" : "bg-slate-300 dark:bg-slate-700"
                    } ${!canEdit ? "opacity-60 cursor-not-allowed" : ""}`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                        form.share_alert_history ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* 5. share_alert_severity_threshold Dropdown */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/30 border border-slate-200/80 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">
                      tune
                    </span>
                    Minimum Alert Severity Threshold
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Only events meeting or exceeding this threshold trigger external family alerts.
                  </p>
                </div>

                <div className="sm:w-56">
                  <select
                    disabled={!canEdit}
                    value={form.share_alert_severity_threshold}
                    onChange={(e) => handleThresholdChange(policy.id, e.target.value)}
                    className={`w-full px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                      !canEdit ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
                    }`}
                  >
                    <option value="LOW">LOW (All Anomaly Events)</option>
                    <option value="MEDIUM">MEDIUM (Moderate Anomaly & Falls)</option>
                    <option value="HIGH">HIGH (High Risk Motion Anomaly)</option>
                    <option value="CRITICAL">CRITICAL (Emergency Falls Only)</option>
                  </select>
                </div>
              </div>

              {/* Action Bar & Status Feedback */}
              {canEdit && (
                <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="text-[11px] text-slate-400">
                    Last updated: {policy.updated_at ? new Date(policy.updated_at).toLocaleString() : "Recently"}
                  </div>

                  <div className="flex items-center gap-3">
                    {msg && (
                      <span
                        className={`text-xs font-bold ${
                          msg.type === "success"
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {msg.text}
                      </span>
                    )}
                    <button
                      type="button"
                      disabled={!isDirty || isSaving}
                      onClick={() => handleSave(policy.id)}
                      className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                        isDirty && !isSaving
                          ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                          : "bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed"
                      }`}
                    >
                      {isSaving ? (
                        <>
                          <span className="material-symbols-outlined text-[14px] animate-spin">
                            progress_activity
                          </span>
                          Saving...
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[14px]">
                            save
                          </span>
                          Save Policy Changes
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Resident Overrides Section (if present in multi-tenant data) */}
      {residentOverrides.length > 0 && (
        <div className="space-y-4 pt-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <span className="material-symbols-outlined text-base text-emerald-600 dark:text-emerald-400">
              person_pin
            </span>
            Resident-Specific Policy Overrides ({residentOverrides.length})
          </h3>

          <div className="grid grid-cols-1 gap-4">
            {residentOverrides.map((policy) => {
              const form = editingStates[policy.id] || policy;
              const res = residents.find((r) => r.id === policy.resident_id);
              const isSaving = savingPolicyId === policy.id;
              const isDirty =
                form.share_presence !== policy.share_presence ||
                form.share_activity_detail !== policy.share_activity_detail ||
                form.share_room_name !== policy.share_room_name ||
                form.share_alert_history !== policy.share_alert_history ||
                form.share_alert_severity_threshold !== policy.share_alert_severity_threshold;

              return (
                <div
                  key={policy.id}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xs"
                >
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2 mb-3">
                    <div className="font-bold text-sm text-slate-900 dark:text-white">
                      Override: {res ? `${res.first_name} ${res.last_name}` : `Resident ${policy.resident_id}`}
                    </div>
                    <span className="text-[10px] uppercase font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded">
                      Individual Override
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs mb-3">
                    <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Presence</div>
                      <div className="font-bold">{form.share_presence ? "Shared" : "Restricted"}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Activity Detail</div>
                      <div className="font-bold">{form.share_activity_detail ? "Shared" : "Restricted"}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Alerts</div>
                      <div className="font-bold">{form.share_alert_history ? "Shared" : "Restricted"}</div>
                    </div>
                    <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/40">
                      <div className="text-[10px] text-slate-400 font-bold uppercase">Min Severity</div>
                      <div className="font-bold">{form.share_alert_severity_threshold}</div>
                    </div>
                  </div>

                  {canEdit && isDirty && (
                    <div className="flex justify-end">
                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => handleSave(policy.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
                      >
                        {isSaving ? "Saving..." : "Save Override"}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
