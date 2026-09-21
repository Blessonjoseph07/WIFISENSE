import React, { useState } from "react";
import SharingPolicyManager from "../components/SharingPolicyManager";

export default function OrgAdminView({
  setShowAddOrgModal = () => {},
  organizations = [],
  accessRequests = [],
  residents = [],
  handleReviewRequest = () => {},
  sharingPolicies = [],
  onUpdateSharingPolicy = async () => {},
  canEditPolicies = false,
  userRole = "",
  initialTab = "policies",
  isLoading = false
}) {
  const [activeTab, setActiveTab] = useState(initialTab);

  const pendingRequestsCount = accessRequests.filter((r) => r.status === "pending").length;

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
            Organization Management & Governance
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage organization tenants, family portal link requests, and elder-care data sharing policies.
          </p>
        </div>

        {/* Tab Navigation Controls */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl self-start sm:self-auto border border-slate-200 dark:border-slate-700/60 text-xs font-bold">
          <button
            type="button"
            onClick={() => setActiveTab("policies")}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === "policies"
                ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-xs font-extrabold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">verified_user</span>
            Sharing Policies
            {sharingPolicies.length > 0 && (
              <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                {sharingPolicies.length}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("organizations")}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === "organizations"
                ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-xs font-extrabold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">domain</span>
            Organizations
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("requests")}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === "requests"
                ? "bg-white dark:bg-slate-900 text-teal-600 dark:text-teal-400 shadow-xs font-extrabold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">group_add</span>
            Link Requests
            {pendingRequestsCount > 0 && (
              <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-bold">
                {pendingRequestsCount}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("all")}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === "all"
                ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs font-extrabold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            All
          </button>
        </div>
      </div>

      {/* 1. Sharing Policies Section */}
      {(activeTab === "policies" || activeTab === "all") && (
        <SharingPolicyManager
          policies={sharingPolicies}
          organizations={organizations}
          residents={residents}
          canEdit={canEditPolicies}
          userRole={userRole}
          onUpdatePolicy={onUpdateSharingPolicy}
          isLoading={isLoading}
        />
      )}

      {/* 2. Active Organizations Section */}
      {(activeTab === "organizations" || activeTab === "all") && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-teal-600 dark:text-teal-400">
                  domain
                </span>
                Active Organizations ({organizations.length})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Multi-tenant organizations and facilities registered under Wi-Fi Sense.
              </p>
            </div>
            <button
              onClick={() => setShowAddOrgModal(true)}
              className="bg-teal-600 text-white px-3 py-1.5 rounded-lg text-xs font-bold uppercase hover:bg-teal-700 cursor-pointer flex items-center gap-1 shadow-xs"
            >
              <span className="material-symbols-outlined text-[14px]">add</span>
              Add Organization
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                  <th className="p-3 text-left">Organization Name</th>
                  <th className="p-3 text-left">Deployment Scope Type</th>
                  <th className="p-3 text-left">Organization ID</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                {organizations.map((org) => (
                  <tr key={org.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-3 font-semibold dark:text-white">{org.name}</td>
                    <td className="p-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                          org.type === "ELDER_CARE"
                            ? "bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800"
                            : "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800"
                        }`}
                      >
                        {org.type}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs text-slate-400">{org.id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Family Portal Access Link Requests Section */}
      {(activeTab === "requests" || activeTab === "all") && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-teal-600 dark:text-teal-400">
                group_add
              </span>
              Family Portal Link Requests ({accessRequests.length})
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Review and authorize family member access requests to resident sensing telemetry.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                  <th className="p-3 text-left">Request ID</th>
                  <th className="p-3 text-left">Applicant ID</th>
                  <th className="p-3 text-left">Target Resident Name</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                {accessRequests.map((req) => {
                  const targetRes = residents.find((r) => r.id === req.resident_id);
                  const targetName = targetRes
                    ? `${targetRes.first_name} ${targetRes.last_name}`
                    : req.resident_id;
                  return (
                    <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-mono text-xs text-slate-500">{req.id}</td>
                      <td className="p-3 font-mono text-xs">{req.requesting_user_id}</td>
                      <td className="p-3 font-semibold dark:text-white">{targetName}</td>
                      <td className="p-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                            req.status === "pending"
                              ? "bg-amber-50 text-amber-600 border border-amber-200"
                              : req.status === "approved"
                              ? "bg-teal-50 text-teal-600 border border-teal-200"
                              : "bg-red-50 text-red-600 border border-red-200"
                          }`}
                        >
                          {req.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-3 text-right space-x-2">
                        {req.status === "pending" && (
                          <>
                            <button
                              onClick={() => handleReviewRequest(req.id, "approved")}
                              className="bg-teal-600 text-white px-2.5 py-1 rounded text-xs hover:bg-teal-700 font-bold cursor-pointer"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReviewRequest(req.id, "declined")}
                              className="bg-red-600 text-white px-2.5 py-1 rounded text-xs hover:bg-red-700 font-bold cursor-pointer"
                            >
                              Decline
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {accessRequests.length === 0 && (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-slate-400 italic">
                      No access link requests recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
