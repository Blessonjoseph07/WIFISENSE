import React from "react";
import { getNavItemsForUser } from "../navigation/navConfig";

export default function CareAppShell({
  user,
  role,
  appContext,
  isSystemAdmin,
  currentView,
  setCurrentView,
  alerts,
  handleLogout,
  triggerEmergencyProtocol,
  organizations,
  devices,
  setSimDeviceId,
  setShowSimulateDrawer,
  darkMode,
  setDarkMode,
  showProfileMenu,
  setShowProfileMenu,
  fileInputRef,
  handlePhotoUpload,
  API_BASE,
  children
}) {
  const navItems = getNavItemsForUser(appContext, role, isSystemAdmin);
  const activeAlertsCount = alerts?.filter(a => a.status === "new").length || 0;

  return (
    <div className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen flex transition-all duration-300">
      {/* SideNavbar — WIFISENSE CARE Shell */}
      <nav className="fixed left-0 top-0 bottom-0 w-sidebar-width flex flex-col z-45 bg-white dark:bg-slate-900 border-r border-emerald-100 dark:border-slate-800 shadow-sm">
        {/* Logo / Header with CARE Branding */}
        <div className="p-4 border-b border-emerald-100 dark:border-slate-800 flex items-center gap-3 bg-gradient-to-r from-emerald-50/50 to-teal-50/30 dark:from-emerald-950/20 dark:to-transparent">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-200 dark:border-emerald-800/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-xs">
            <span className="material-symbols-outlined text-[22px]">health_and_safety</span>
          </div>
          <div className="text-left min-w-0">
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">Wi-Fi Sense</h1>
              <span className="text-[10px] font-black uppercase tracking-wider bg-emerald-600 text-white px-1.5 py-0.5 rounded">CARE</span>
            </div>
            <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold tracking-wide block truncate">Elder Care & Safety</p>
          </div>
        </div>

        {/* Filtered Navigation items for CARE */}
        <div className="flex-1 overflow-y-auto py-3 px-3 flex flex-col gap-1 text-[11px] font-bold uppercase tracking-wider">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 px-2 py-1 font-semibold">Care Navigation</div>
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`flex items-center justify-between gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all cursor-pointer ${
                  isActive
                    ? "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60 shadow-xs font-extrabold"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <span className={`material-symbols-outlined text-[19px] ${isActive ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400 dark:text-slate-500"}`}>
                    {item.icon}
                  </span>
                  <span className="truncate">{item.label}</span>
                </div>
                {item.hasBadge && activeAlertsCount > 0 && (
                  <span className="bg-red-500 text-white rounded-full px-2 py-0.5 text-[9px] font-bold animate-pulse shrink-0">
                    {activeAlertsCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-emerald-100 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/60 flex flex-col gap-3">
          <button
            onClick={triggerEmergencyProtocol}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-2.5 px-3 rounded-lg text-xs font-bold uppercase transition-colors flex items-center justify-center gap-2 shadow-sm cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">emergency</span>
            Fall Emergency Protocol
          </button>

          <div className="text-left text-xs bg-white dark:bg-slate-850 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
            <div className="font-bold text-slate-800 dark:text-white truncate">{user?.first_name} {user?.last_name}</div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded font-mono font-bold uppercase">{role}</span>
              <span className="text-[9px] text-slate-400 uppercase font-mono">CARE APP</span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 py-1.5 rounded-lg text-xs font-bold uppercase hover:bg-red-50 dark:hover:bg-red-950/20 transition-all flex items-center justify-center gap-1 cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">logout</span> Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="ml-sidebar-width flex-1 flex flex-col min-h-screen">
        {/* TopAppBar */}
        <header className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-b border-emerald-100 dark:border-slate-800 fixed top-0 right-0 left-sidebar-width h-header-height z-30 flex items-center justify-between px-gutter">
          <div className="flex items-center gap-stack-md text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
            <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400">healing</span>
            <span>Care Deployment: <span className="text-slate-950 dark:text-white font-extrabold">
              {organizations[0]?.name || "St. Peter's Elder Care Home"}
            </span></span>
            <span className="bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 text-[10px] px-2 py-0.5 rounded-full font-extrabold">CARE REPOSITORY</span>
          </div>

          <div className="flex items-center gap-gutter">
            <div className="flex items-center gap-stack-sm border-l border-slate-200 dark:border-slate-800 pl-gutter">
              <button
                onClick={() => {
                  if (devices.length > 0) {
                    setSimDeviceId(devices[0].id);
                    setShowSimulateDrawer(true);
                  } else {
                    alert("Please register a sensing device first.");
                  }
                }}
                className="text-emerald-600 dark:text-emerald-400 border border-emerald-500 dark:border-emerald-500/40 px-3 py-1.5 rounded-lg text-xs font-bold uppercase hover:bg-emerald-50 dark:hover:bg-emerald-950/20 transition-colors cursor-pointer flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[16px]">sensors</span>
                Simulate Fall / CSI
              </button>

              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors cursor-pointer"
                title="Toggle Theme"
              >
                <span className="material-symbols-outlined">{darkMode ? "light_mode" : "dark_mode"}</span>
              </button>

              <button
                onClick={() => setCurrentView("alerts")}
                className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors relative cursor-pointer"
              >
                <span className="material-symbols-outlined">notifications</span>
                {activeAlertsCount > 0 && (
                  <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>
                )}
              </button>

              <div className="relative">
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 ml-2 overflow-hidden border border-emerald-200 dark:border-emerald-800 flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-emerald-500 transition-all"
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
                      {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "WS"}
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
                            {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "WS"}
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
                          {role}
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

        {/* Content area */}
        <main className="mt-header-height p-gutter flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
