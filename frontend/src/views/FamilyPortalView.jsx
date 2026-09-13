import React from "react";

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
}) {
  return (
    <div className="space-y-6 text-left">
      {role !== "emergency_contact" ? (
        /* Admin Preview / Warning */
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
          <div className="w-16 h-16 bg-teal-50 dark:bg-teal-950/20 rounded-full flex items-center justify-center mb-6 mx-auto">
            <span className="material-symbols-outlined text-[36px] text-teal-600">verified_user</span>
          </div>
          <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">
            Administrative Preview Mode
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
            This Family Member Portal is customized exclusively for elder-care resident emergency
            contacts. Administrators can approve access link requests, but to view the live dashboard
            interface, please register a family member account and submit a link request.
          </p>
          <div className="bg-slate-50 dark:bg-slate-950 p-5 rounded-lg border border-slate-200 dark:border-slate-850 text-left text-xs space-y-3">
            <div className="font-bold text-slate-800 dark:text-white uppercase tracking-wider">
              Demo Credentials:
            </div>
            <div className="flex justify-between">
              <span>John Smith (Approved Link):</span>{" "}
              <code className="bg-slate-250 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">
                john@wifisense.com / johnpassword
              </code>
            </div>
            <div className="flex justify-between">
              <span>Susan Varghese (Pending Link):</span>{" "}
              <code className="bg-slate-255 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">
                susan@wifisense.com / susanpassword
              </code>
            </div>
          </div>
        </div>
      ) : !familyStatus ? (
        /* Loading */
        <div className="p-8 text-center text-slate-500 italic">Syncing family portal status...</div>
      ) : familyStatus.linked === false ? (
        /* Unlinked Statuses */
        <div className="space-y-6">
          {familyStatus.request_status === "pending" ? (
            /* Pending Request */
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
              <div className="w-16 h-16 bg-amber-50 dark:bg-amber-950/20 rounded-full flex items-center justify-center mb-6 mx-auto animate-pulse">
                <span className="material-symbols-outlined text-[36px] text-amber-500">pending</span>
              </div>
              <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">
                Access Link Request Pending
              </h2>
              <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
                Your request to view real-time safety status for{" "}
                <strong className="text-slate-850 dark:text-white">
                  {familyStatus.resident_name}
                </strong>{" "}
                is currently pending. The Organization Administrator will verify your credentials and
                approve link access.
              </p>
              {/* Stepper representation */}
              <div className="flex justify-between items-center max-w-md mx-auto mt-8 text-xs font-semibold text-slate-500">
                <div className="flex flex-col items-center gap-1 text-teal-650">
                  <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold">
                    1
                  </span>
                  <span>Registered</span>
                </div>
                <div className="h-0.5 bg-teal-500 flex-1 mx-2"></div>
                <div className="flex flex-col items-center gap-1 text-teal-655 relative">
                  <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold animate-ping absolute"></span>
                  <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold relative">
                    2
                  </span>
                  <span>Link Submitted</span>
                </div>
                <div className="h-0.5 bg-slate-250 dark:bg-slate-800 flex-1 mx-2"></div>
                <div className="flex flex-col items-center gap-1 text-slate-400">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center border border-slate-200 dark:border-slate-700 font-bold">
                    3
                  </span>
                  <span>Approved</span>
                </div>
              </div>
            </div>
          ) : familyStatus.request_status === "declined" ? (
            /* Declined Request */
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
              <div className="w-16 h-16 bg-red-50 dark:bg-red-950/20 rounded-full flex items-center justify-center mb-6 mx-auto">
                <span className="material-symbols-outlined text-[36px] text-red-500">cancel</span>
              </div>
              <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">
                Access Link Request Declined
              </h2>
              <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
                Your request to link with{" "}
                <strong className="text-slate-850 dark:text-white">
                  {familyStatus.resident_name}
                </strong>{" "}
                was declined by the administrator. Please ensure the registration details align with the
                resident records.
              </p>
              <button
                onClick={async () => {
                  setSelectedRequestResidentId("");
                  setFamilyStatus((prev) => ({ ...prev, request_status: null }));
                }}
                className="px-4 py-2 bg-teal-600 text-white rounded font-bold hover:bg-teal-700 cursor-pointer"
              >
                Resubmit New Link Request
              </button>
            </div>
          ) : (
            /* No request yet: Link Request Form */
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 max-w-xl mx-auto shadow-sm">
              <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2 text-center">
                Link Resident Profile
              </h2>
              <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6 text-center">
                Please select the resident profile at this elder-care facility that you are authorized
                to monitor.
              </p>
              <form onSubmit={submitLinkRequest} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">
                    MONITORED SUBJECT
                  </label>
                  <select
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2.5 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white font-semibold"
                    value={selectedRequestResidentId}
                    onChange={(e) => setSelectedRequestResidentId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Resident Profile --</option>
                    {residents.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.first_name} {r.last_name}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full py-2.5 bg-teal-600 text-white rounded-lg text-sm font-bold uppercase shadow hover:bg-teal-700 transition-colors cursor-pointer"
                >
                  Submit Link Request
                </button>
              </form>
            </div>
          )}
        </div>
      ) : (
        /* Approved Linked Family Member Portal Dashboard */
        <div className="space-y-6">
          {/* Page Header */}
          <div className="mb-stack-lg flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold mb-1">
                Access Control &amp; Privacy
              </h1>
              <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400">
                Configure family member visibility and monitor safety status.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  setToastMessage({ type: "success", text: "Saved visibility settings." })
                }
                className="px-4 py-2 bg-teal-650 text-white rounded-lg text-label-caps font-label-caps hover:opacity-90 font-bold cursor-pointer"
              >
                Save Settings
              </button>
            </div>
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-12 gap-gutter">
            {/* Privacy Guarantee Hero Card (Span 8) */}
            <div className="col-span-12 lg:col-span-8 bg-teal-50/40 dark:bg-teal-950/10 rounded-xl border border-slate-200 dark:border-slate-800 p-8 relative overflow-hidden flex flex-col justify-between shadow-sm">
              <div className="absolute -right-20 -top-20 w-64 h-64 border-[40px] border-teal-100/30 dark:border-teal-900/10 rounded-full opacity-50"></div>

              <div className="relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-800 mb-6">
                  <span className="material-symbols-outlined text-[16px] text-teal-600 dark:text-teal-400">
                    verified_user
                  </span>
                  <span className="text-label-caps font-label-caps text-slate-655 dark:text-slate-350">
                    Core Principle
                  </span>
                </div>
                <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-4 max-w-lg">
                  Invisible Security. Zero Cameras. Absolute Privacy.
                </h2>
                <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 max-w-xl mb-6">
                  Wi-Fi Sense monitors ambient signal shifts instead of cameras. Your loved one's
                  optical privacy is fully preserved.
                </p>
              </div>
              <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <span className="material-symbols-outlined text-teal-605 mb-2">videocam_off</span>
                  <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">
                    No Cameras
                  </div>
                  <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">
                    100% optical privacy
                  </div>
                </div>
                <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <span className="material-symbols-outlined text-teal-605 mb-2">mic_off</span>
                  <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">
                    No Microphones
                  </div>
                  <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">
                    No audio recorded
                  </div>
                </div>
                <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <span className="material-symbols-outlined text-teal-605 mb-2">lock</span>
                  <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">
                    Encrypted CSI
                  </div>
                  <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">
                    Data mathematically hashed
                  </div>
                </div>
              </div>
            </div>

            {/* Facility Contact Info Card (Span 4) */}
            <div className="col-span-12 lg:col-span-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                  Facility Contact Info
                </h3>
              </div>
              <div className="flex-1 flex flex-col justify-center p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950 space-y-4">
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase">CARE CENTRE</div>
                  <div className="text-sm font-bold text-slate-850 dark:text-white">
                    {familyStatus?.facility_contact?.name || "Care Facility"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase">
                    TELEPHONE LINE
                  </div>
                  <div className="text-sm font-mono text-slate-850 dark:text-white">
                    {familyStatus?.facility_contact?.phone || "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase">DIRECT EMAIL</div>
                  <div className="text-sm font-mono text-slate-850 dark:text-white">
                    {familyStatus?.facility_contact?.email || "N/A"}
                  </div>
                </div>
              </div>
            </div>

            {/* Resident Live Status Card (Span 6) */}
            <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-sm">
              <div className="bg-slate-50 dark:bg-slate-950 border-b border-slate-250 dark:border-slate-800 p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-teal-605">verified_user</span>
                  <h3 className="text-body-md font-body-md font-bold text-slate-950 dark:text-white">
                    Resident Status
                  </h3>
                </div>
                <span className="text-[10px] font-bold bg-teal-50 text-teal-650 px-2.5 py-1 rounded">
                  Linked profile
                </span>
              </div>
              <div className="p-6 flex-1 bg-slate-50 dark:bg-slate-950 flex flex-col justify-between">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 text-left space-y-4 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-headline-md font-headline-md font-bold text-slate-950 dark:text-white">
                        {familyStatus?.resident?.first_name} {familyStatus?.resident?.last_name}
                      </div>
                      <div className="text-body-md font-data-mono text-slate-500 mt-1">
                        Assigned: {familyStatus?.resident?.room_name || "Living Quarters"}
                      </div>
                    </div>
                    <div className="bg-teal-50 dark:bg-teal-950/20 text-teal-650 px-3 py-1 rounded-full text-label-caps font-label-caps border border-teal-200/20 flex items-center gap-1.5 font-bold">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span>
                      {(familyStatus?.presence_status || "Safe").toUpperCase()}
                    </div>
                  </div>

                  <div className="border-t border-slate-100 dark:border-slate-800 pt-4 flex justify-between items-center text-xs">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase">
                        RECENT ACTIVITY
                      </p>
                      <p className="font-semibold text-slate-850 dark:text-white mt-1 capitalize">
                        {familyStatus?.recent_activity?.activity?.replace("_", " ") || "Nominal"}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">
                        LAST DETECTED
                      </p>
                      <p className="font-data-mono text-data-mono text-slate-850 dark:text-white mt-1">
                        {familyStatus?.recent_activity?.timestamp
                          ? new Date(familyStatus.recent_activity.timestamp).toLocaleTimeString()
                          : "Live"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Read-Only Alert History List */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 mt-4 text-left shadow-sm flex-1">
                  <h4 className="text-xs font-bold uppercase text-slate-400 mb-3 tracking-wider">
                    Alert History (Read-only)
                  </h4>
                  <div className="space-y-3 max-h-[160px] overflow-y-auto">
                    {(familyStatus?.alerts || []).map((a) => (
                      <div
                        key={a.id}
                        className="flex justify-between items-center p-3 rounded bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-855 text-xs"
                      >
                        <div>
                          <div className="font-bold text-slate-850 dark:text-white">
                            {a.event_type?.replace("_", " ")}
                          </div>
                          <div className="text-[10px] text-slate-400 mt-0.5">
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
                      <p className="text-xs text-slate-400 italic text-center p-4">
                        No historic warnings logged.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Access Control Settings (Span 6) */}
            <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-sm">
              <div className="mb-6">
                <h3 className="text-headline-sm font-headline-sm text-slate-950 dark:text-white font-bold mb-1">
                  Privacy Controls
                </h3>
                <p className="text-body-md font-body-md text-slate-500">
                  Configure safety granularity settings.
                </p>
              </div>
              <div className="flex-1 space-y-4">
                {/* Toggle 1 */}
                <div
                  onClick={() => {
                    setStrictPrivacy(!strictPrivacy);
                    setToastMessage({
                      type: "success",
                      text: `Strict Privacy Mode toggled: ${!strictPrivacy ? "ON" : "OFF"}`,
                    });
                  }}
                  className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer bg-slate-50 dark:bg-slate-950 ${
                    strictPrivacy
                      ? "border-teal-500 bg-teal-50/10"
                      : "border-slate-200 dark:border-slate-800 hover:border-teal-500"
                  }`}
                >
                  <div className="flex gap-4">
                    <div className="mt-1">
                      <span className="material-symbols-outlined text-slate-550">
                        visibility_off
                      </span>
                    </div>
                    <div>
                      <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">
                        Strict Privacy Mode
                      </div>
                      <div className="text-body-md font-body-md text-slate-500 mt-1 max-w-sm">
                        Mask presence values to safe status indicators. Hide room location.
                      </div>
                    </div>
                  </div>
                  <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                    <input
                      checked={strictPrivacy}
                      type="checkbox"
                      readOnly
                      className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-slate-300 dark:border-slate-700 appearance-none cursor-pointer"
                    />
                    <label
                      className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${
                        strictPrivacy ? "bg-teal-500" : "bg-slate-300 dark:bg-slate-800"
                      }`}
                    ></label>
                  </div>
                </div>

                {/* Toggle 2 */}
                <div
                  onClick={() => {
                    setContextualVisibility(!contextualVisibility);
                    setToastMessage({
                      type: "success",
                      text: `Contextual Visibility toggled: ${!contextualVisibility ? "ON" : "OFF"}`,
                    });
                  }}
                  className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer bg-slate-50 dark:bg-slate-950 ${
                    contextualVisibility
                      ? "border-teal-500 bg-teal-50/10"
                      : "border-slate-200 dark:border-slate-800 hover:border-teal-500"
                  }`}
                >
                  <div className="flex gap-4">
                    <div className="mt-1">
                      <span className="material-symbols-outlined text-teal-605">visibility</span>
                    </div>
                    <div>
                      <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">
                        Contextual Visibility
                      </div>
                      <div className="text-body-md font-body-md text-slate-500 mt-1 max-w-sm">
                        View current room activity indicators and alerts logs.
                      </div>
                    </div>
                  </div>
                  <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                    <input
                      checked={contextualVisibility}
                      type="checkbox"
                      readOnly
                      className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-slate-300 dark:border-slate-700 appearance-none cursor-pointer"
                    />
                    <label
                      className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${
                        contextualVisibility ? "bg-teal-500" : "bg-slate-300 dark:bg-slate-800"
                      }`}
                    ></label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
