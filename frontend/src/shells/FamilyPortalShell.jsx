import React from "react";

export default function FamilyPortalShell({
  user,
  role,
  familyStatus,
  handleLogout,
  triggerEmergencyProtocol,
  darkMode,
  setDarkMode,
  showProfileMenu,
  setShowProfileMenu,
  fileInputRef,
  handlePhotoUpload,
  API_BASE,
  children
}) {
  return (
    <div className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen flex flex-col transition-all duration-300">
      {/* Streamlined Top Navigation Bar for Family Members (NO sidebar) */}
      <header className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-emerald-100 dark:border-slate-800 sticky top-0 z-40 px-6 py-3.5 shadow-xs">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Brand Header */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-200 dark:border-emerald-800/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
              <span className="material-symbols-outlined text-[24px]">group</span>
            </div>
            <div className="text-left">
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold text-slate-900 dark:text-white leading-tight">Wi-Fi Sense</h1>
                <span className="text-[10px] font-black uppercase tracking-wider bg-emerald-600 text-white px-1.5 py-0.5 rounded">CARE</span>
              </div>
              <p className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold">Family Member Portal</p>
            </div>
          </div>

          {/* Center Info Pill: Linked Resident status */}
          <div className="hidden md:flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 px-3.5 py-1.5 rounded-full text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-600 dark:text-slate-300 font-medium">Monitoring Link:</span>
            <span className="text-emerald-800 dark:text-emerald-300 font-bold">
              {familyStatus?.linked ? `${familyStatus.resident?.first_name} ${familyStatus.resident?.last_name} (${familyStatus.resident?.room?.name || "Room"})` : "Connecting..."}
            </span>
          </div>

          {/* Right Actions: Emergency Button, Theme, Profile */}
          <div className="flex items-center gap-3">
            <button
              onClick={triggerEmergencyProtocol}
              className="bg-red-600 hover:bg-red-700 text-white px-3.5 py-2 rounded-lg text-xs font-bold uppercase transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">emergency</span>
              <span className="hidden sm:inline">Emergency Help</span>
            </button>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors cursor-pointer"
              title="Toggle Theme"
            >
              <span className="material-symbols-outlined">{darkMode ? "light_mode" : "dark_mode"}</span>
            </button>

            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 ml-1 overflow-hidden border border-emerald-200 dark:border-emerald-800 flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-emerald-500 transition-all"
                title="Profile Menu"
              >
                {user?.photo_url ? (
                  <img
                    alt="User avatar"
                    className="w-full h-full object-cover"
                    src={user.photo_url.startsWith("http") ? user.photo_url : `${API_BASE}${user.photo_url}`}
                  />
                ) : (
                  <div className="w-full h-full bg-emerald-50 dark:bg-emerald-950/40 flex items-center justify-center text-emerald-700 dark:text-emerald-400 font-bold text-xs">
                    {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "FM"}
                  </div>
                )}
              </button>

              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl p-4 z-50 text-left">
                  <div className="flex items-center gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
                    <div className="w-10 h-10 rounded-full overflow-hidden border border-emerald-200 dark:border-emerald-800 shrink-0 flex items-center justify-center bg-emerald-50 dark:bg-emerald-950/40">
                      {user?.photo_url ? (
                        <img
                          alt="User avatar"
                          className="w-full h-full object-cover"
                          src={user.photo_url.startsWith("http") ? user.photo_url : `${API_BASE}${user.photo_url}`}
                        />
                      ) : (
                        <span className="text-emerald-700 dark:text-emerald-400 font-bold text-sm">
                          {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "FM"}
                        </span>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-bold text-slate-900 dark:text-white truncate">
                        {user?.first_name} {user?.last_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {user?.email}
                      </div>
                      <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono uppercase mt-0.5 font-bold">
                        Emergency Contact
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 space-y-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handlePhotoUpload}
                    />
                    <button
                      onClick={() => fileInputRef.current && fileInputRef.current.click()}
                      className="w-full text-xs font-bold text-slate-700 dark:text-slate-200 py-2 px-3 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg flex items-center gap-2 cursor-pointer transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px]">photo_camera</span>
                      Change Photo
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full text-xs font-bold text-red-650 dark:text-red-400 py-2 px-3 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg flex items-center gap-2 cursor-pointer transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px]">logout</span>
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Family Member Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {children}
      </main>
    </div>
  );
}
