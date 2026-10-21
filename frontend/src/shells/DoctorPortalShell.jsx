import React from "react";

/** Minimal shell for approved medical providers: no staff navigation, no emergency or simulation controls. */
export default function DoctorPortalShell({ user, handleLogout, darkMode, setDarkMode, children }) {
  return (
    <div className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen w-full flex flex-col">
      <header className="w-full bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-800 sticky top-0 z-40 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-200 dark:border-teal-800/50 flex items-center justify-center text-teal-600 dark:text-teal-400">
              <span className="material-symbols-outlined text-[24px]">stethoscope</span>
            </div>
            <div className="text-left">
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold text-slate-900 dark:text-white leading-tight">Wi-Fi Sense</h1>
                <span className="text-[10px] font-black uppercase tracking-wider bg-teal-600 text-white px-1.5 py-0.5 rounded">CARE</span>
              </div>
              <p className="text-xs text-teal-700 dark:text-teal-400 font-semibold">Medical Provider Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden sm:block text-sm font-semibold text-slate-700 dark:text-slate-200">
              {user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : ""}
            </span>
            <button
              type="button"
              onClick={() => setDarkMode(!darkMode)}
              className="w-9 h-9 rounded-full border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center cursor-pointer"
              aria-label="Toggle dark mode"
            >
              <span className="material-symbols-outlined text-[18px]">{darkMode ? "light_mode" : "dark_mode"}</span>
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="w-full max-w-7xl mx-auto px-6 py-8 flex-1">{children}</main>
    </div>
  );
}
