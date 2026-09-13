import React from "react";

export default function UserProfileView({
  user = null,
  role = "",
  API_BASE = "http://localhost:8000",
  fileInputRef = { current: null },
}) {
  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
          My Profile
        </h2>
        <p className="text-body-md text-slate-500 dark:text-slate-400">
          Manage your personal settings and caregiver details.
        </p>
      </div>
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col md:flex-row gap-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-32 h-32 rounded-full border-4 border-slate-100 dark:border-slate-800 overflow-hidden bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
            {user?.photo_url ? (
              <img
                src={
                  user.photo_url.startsWith("http")
                    ? user.photo_url
                    : `${API_BASE}${user.photo_url}`
                }
                alt="Profile"
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-4xl text-slate-400 font-bold">
                {user?.first_name?.[0]}
                {user?.last_name?.[0]}
              </span>
            )}
          </div>
          <button
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            className="text-sm font-bold text-teal-600 hover:text-teal-700 bg-teal-50 hover:bg-teal-100 px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Upload Photo
          </button>
        </div>
        <div className="flex-1 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-label-caps text-slate-500 block mb-1">First Name</label>
              <div className="font-bold text-slate-900 dark:text-white text-lg">
                {user?.first_name}
              </div>
            </div>
            <div>
              <label className="text-label-caps text-slate-500 block mb-1">Last Name</label>
              <div className="font-bold text-slate-900 dark:text-white text-lg">
                {user?.last_name}
              </div>
            </div>
            <div className="col-span-2">
              <label className="text-label-caps text-slate-500 block mb-1">Email Address</label>
              <div className="font-bold text-slate-900 dark:text-white text-lg">
                {user?.email}
              </div>
            </div>
            <div className="col-span-2 mt-2 pt-4 border-t border-slate-100 dark:border-slate-800">
              <label className="text-label-caps text-slate-500 block mb-1">System Role</label>
              <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-3 py-1 rounded font-mono text-sm font-bold uppercase">
                {role}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
