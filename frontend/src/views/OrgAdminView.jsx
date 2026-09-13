import React from "react";

export default function OrgAdminView({
  setShowAddOrgModal = () => {},
  organizations = [],
  accessRequests = [],
  residents = [],
  handleReviewRequest = () => {},
}) {
  return (
    <div className="space-y-6 text-left">
      <div className="mb-stack-lg">
        <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
          Organization Admin Dashboard
        </h2>
        <p className="text-body-md text-slate-500 dark:text-slate-400">
          Manage corporate and elder-care tenant organizations settings.
        </p>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center border-b pb-2 mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
            Active Organizations
          </h3>
          <button
            onClick={() => setShowAddOrgModal(true)}
            className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700 cursor-pointer"
          >
            Add Organization
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                <th className="p-3">Organization Name</th>
                <th className="p-3">Deployment Scope Type</th>
                <th className="p-3">Organization ID</th>
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
                          ? "bg-teal-50 dark:bg-teal-950/20 text-teal-650"
                          : "bg-blue-50 dark:bg-blue-950/20 text-blue-650"
                      }`}
                    >
                      {org.type}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-xs text-slate-450">{org.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Family Portal Access Link Requests Section */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm mt-6">
        <div className="border-b pb-2 mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
            Family Portal Link Requests
          </h3>
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
                            ? "bg-amber-50 text-amber-600"
                            : req.status === "approved"
                            ? "bg-teal-50 text-teal-600"
                            : "bg-red-50 text-red-600"
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
    </div>
  );
}
