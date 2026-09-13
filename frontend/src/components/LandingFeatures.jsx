import React from "react";

export default function LandingFeatures({ onGetStarted }) {
  const features = [
    {
      icon: "wifi_tethering",
      title: "RF CSI Subcarrier Analysis",
      tag: "5.8 GHz Sensing",
      description: "Extracts subcarrier amplitude and phase distortion from existing Wi-Fi signals to map human movement, respiration, and micro-postures through walls.",
      color: "cyan"
    },
    {
      icon: "shield",
      title: "Zero Optical Surveillance",
      tag: "100% Privacy Preserved",
      description: "No cameras, no microphones, no video streams. Ensures total dignity in bedrooms, restrooms, and private quarters without risk of footage leaks.",
      color: "blue"
    },
    {
      icon: "bolt",
      title: "Edge Neural Inference",
      tag: "< 180ms Response",
      description: "Sub-second fall detection and anomaly classification run entirely on local gateway hardware. Zero cloud latency and immediate caregiver notification.",
      color: "purple"
    }
  ];

  const spaces = [
    {
      role: "Wifisense Care",
      subtitle: "Elder Care & Assisted Living",
      icon: "health_and_safety",
      badge: "ELDER CARE",
      badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      description: "Continuous contactless fall monitoring, bed-exit alerts, and nocturnal wander detection across resident wards.",
      highlights: ["Zero Wearables Required", "Real-Time Room Status", "Caregiver Shift Logs"]
    },
    {
      role: "Wifisense Space",
      subtitle: "Corporate & Enterprise Facilities",
      icon: "corporate_fare",
      badge: "CORPORATE",
      badgeColor: "bg-sky-500/10 text-sky-400 border-sky-500/20",
      description: "Spatial occupancy analytics, conference room utilization tracking, and automated HVAC/lighting energy policies.",
      highlights: ["Desk & Zone Heatmaps", "Automated Energy Modes", "RF Mesh Coverage"]
    },
    {
      role: "Family Portal",
      subtitle: "Family & Emergency Contacts",
      icon: "family_restroom",
      badge: "FAMILY ACCESS",
      badgeColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
      description: "Reassurance without intrusion. Family members check resident wellbeing and safety trends without disturbing their privacy.",
      highlights: ["Activity Verification", "Emergency SMS Hooks", "Privacy-Preserving Logs"]
    }
  ];

  const demoAccounts = [
    { role: "Admin", email: "blesson@wifisense.com", pill: "bg-amber-400/10 text-amber-400 border-amber-400/30" },
    { role: "Caregiver", email: "abhinanth@wifisense.com", pill: "bg-emerald-400/10 text-emerald-400 border-emerald-400/30" },
    { role: "Manager", email: "abhinand@wifisense.com", pill: "bg-sky-400/10 text-sky-400 border-sky-400/30" },
    { role: "Family", email: "john@wifisense.com", pill: "bg-indigo-400/10 text-indigo-400 border-indigo-400/30" }
  ];

  return (
    <div className="bg-[#05070c] text-white w-full border-t border-white/[0.06]">
      
      {/* SECTION 1: CORE TECHNOLOGY PILLARS */}
      <section className="py-24 px-4 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-950/40 border border-blue-500/30 text-blue-300 text-xs font-semibold uppercase tracking-wider mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            Core Technology
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-4 text-white">
            Invisible Signals. <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Concrete Intelligence.</span>
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            How Wi-Fi Channel State Information (CSI) turns everyday radio frequency waves into precision spatial awareness.
          </p>
        </div>

        {/* 3 Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feat) => (
            <div
              key={feat.title}
              className="relative rounded-2xl p-8 bg-white/[0.02] border border-white/[0.08] hover:border-cyan-500/30 transition-all duration-300 hover:-translate-y-1 shadow-xl hover:shadow-cyan-950/30 group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined text-[26px]">{feat.icon}</span>
                  </div>
                  <span className="text-[11px] font-mono font-medium px-2.5 py-1 rounded-full bg-white/[0.04] text-cyan-300 border border-white/[0.06]">
                    {feat.tag}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3 group-hover:text-cyan-300 transition-colors">
                  {feat.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {feat.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 2: APPLICATION WORKSPACES */}
      <section className="py-20 px-4 max-w-7xl mx-auto border-t border-white/[0.05]">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-4">
            <span className="material-symbols-outlined text-[15px] text-cyan-400">domain</span>
            Tailored Ecosystem
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-4 text-white">
            Specialized for <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">Every Facility Role.</span>
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Dedicated operational shells designed for caregivers, commercial facility administrators, and family members.
          </p>
        </div>

        {/* Workspaces Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {spaces.map((sp) => (
            <div
              key={sp.role}
              className="rounded-2xl p-8 bg-gradient-to-b from-white/[0.03] to-white/[0.01] border border-white/[0.08] hover:border-blue-500/40 transition-all duration-300 shadow-xl flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-full border ${sp.badgeColor}`}>
                    {sp.badge}
                  </span>
                  <span className="material-symbols-outlined text-slate-500 group-hover:text-cyan-400 transition-colors text-[22px]">
                    {sp.icon}
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">{sp.role}</h3>
                <p className="text-xs text-cyan-400/80 font-mono mb-4">{sp.subtitle}</p>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  {sp.description}
                </p>
                
                <ul className="space-y-2 mb-6 border-t border-white/[0.06] pt-4">
                  {sp.highlights.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-xs text-slate-300 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={onGetStarted}
                className="w-full py-2.5 rounded-xl bg-white/[0.04] hover:bg-cyan-500/10 border border-white/[0.1] hover:border-cyan-500/30 text-white hover:text-cyan-300 text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                Access Portal
                <span className="material-symbols-outlined text-[16px]">chevron_right</span>
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 3: CALL TO ACTION & DEMO ACCESS */}
      <section className="py-24 px-4 relative overflow-hidden border-t border-white/[0.06]">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-600/15 rounded-full blur-[140px] pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto text-center flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/25 mb-8">
            <span className="material-symbols-outlined text-white text-3xl font-black">sensors</span>
          </div>

          <h2 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
            Ready to Experience <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-indigo-400">
              Contactless Spatial Intelligence?
            </span>
          </h2>

          <p className="text-slate-400 text-base sm:text-lg max-w-2xl mb-10 leading-relaxed">
            Enter the live platform with our 3D Wi-Fi modem visualizer, real-time RF CSI telemetry streams, and pre-seeded multi-role facilities.
          </p>

          <button
            onClick={onGetStarted}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-10 py-4 rounded-full font-bold text-lg transition-all shadow-xl shadow-cyan-600/30 hover:shadow-cyan-500/40 hover:scale-105 active:scale-95 cursor-pointer flex items-center gap-2 mb-12"
          >
            Launch Wifisense Platform
            <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
          </button>

          {/* Quick Demo Access Pills */}
          <div className="flex flex-col items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-widest text-slate-500">
              Pre-Configured Demo Accounts (Password: [name]password)
            </span>
            <div className="flex flex-wrap justify-center gap-2.5 max-w-2xl">
              {demoAccounts.map((acc) => (
                <div
                  key={acc.email}
                  onClick={onGetStarted}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-mono flex items-center gap-2 cursor-pointer hover:brightness-125 transition-all ${acc.pill}`}
                  title="Click to sign in with this account"
                >
                  <span className="font-bold">{acc.role}:</span>
                  <span className="opacity-90">{acc.email}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: MINIMALIST FUTURISTIC FOOTER */}
      <footer className="py-12 px-4 border-t border-white/[0.06] bg-[#030508] text-slate-500 text-xs font-mono">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-white/10 rounded flex items-center justify-center">
              <span className="material-symbols-outlined text-white text-[15px]">sensors</span>
            </div>
            <span className="text-white font-bold tracking-tight text-sm font-sans">Wifisense</span>
            <span className="text-slate-600">|</span>
            <span>Contactless RF CSI Spatial Intelligence</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-400/90">RF ENGINE ONLINE · 5.8 GHz</span>
          </div>

          <div>
            &copy; {new Date().getFullYear()} Wifisense. All rights reserved.
          </div>
        </div>
      </footer>

    </div>
  );
}
