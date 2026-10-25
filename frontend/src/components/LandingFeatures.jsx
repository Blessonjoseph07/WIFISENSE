import React from "react";

export default function LandingFeatures({ onGetStarted }) {
  const features = [
    {
      icon: "wifi_tethering",
      title: "RF CSI Subcarrier Analysis",
      tag: "2.4 GHz · ESP32-S3",
      description: "Reads how a person's movement disturbs the amplitude and phase of Wi-Fi subcarriers between two ESP32-S3 nodes, through drywall and in total darkness.",
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
      title: "Signal Cleaning + Activity Model",
      tag: "Cloud API",
      description: "Phase unwrapping, Hampel outlier filtering and an empty-room baseline turn raw CSI into features a model classifies as empty, presence, walking, sitting or a possible fall.",
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
      highlights: ["Zero Wearables Required", "Room Status at a Glance", "Caregiver Shift Logs"]
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

  // How one reading travels from the room to a caregiver's screen. Every figure here describes the real hardware.
  const pipeline = [
    { icon: "router", step: "01", title: "Transmit", detail: "An ESP32-S3 node sends 802.11n frames across the room on 2.4 GHz." },
    { icon: "graphic_eq", step: "02", title: "Capture CSI", detail: "A second ESP32-S3 records amplitude and phase for every OFDM subcarrier." },
    { icon: "cloud_sync", step: "03", title: "Clean & classify", detail: "The API unwraps phase, filters outliers, removes the empty-room baseline and runs the model." },
    { icon: "notifications_active", step: "04", title: "Notify", detail: "Room tiles update and a possible fall reaches staff for confirmation." }
  ];

  const facts = [
    { value: "64", label: "OFDM subcarriers per frame" },
    { value: "2.4 GHz", label: "802.11 b/g/n channel" },
    { value: "0", label: "cameras or microphones" },
    { value: "5", label: "activity states classified" }
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

      {/* SECTION 3: HOW A READING TRAVELS */}
      <section className="py-24 px-4 max-w-7xl mx-auto border-t border-white/[0.05]">
        <style>{`
          @keyframes wfs-travel { 0% { left: 0%; opacity: 0; } 8% { opacity: 1; } 92% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
          .wfs-pulse { animation: wfs-travel 4.5s cubic-bezier(.45,.05,.55,.95) infinite; }
          @media (prefers-reduced-motion: reduce) { .wfs-pulse { animation: none; opacity: 0; } }
        `}</style>
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-950/40 border border-indigo-500/30 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-4">
            <span className="material-symbols-outlined text-[15px] text-indigo-300">conversion_path</span>
            How It Works
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight mb-4 text-white">
            From a Radio Wave to a <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Caregiver&apos;s Screen.</span>
          </h2>
          <p className="text-slate-400 text-base sm:text-lg">
            Two low-cost ESP32-S3 boards, a serial bridge and a cloud API. No wearables to charge, nothing to point at a resident.
          </p>
        </div>

        <div className="relative">
          {/* Signal path linking the four stages (desktop) */}
          <div className="hidden md:block absolute top-8 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-cyan-500/0 via-cyan-500/40 to-indigo-500/0" aria-hidden="true">
            <span className="wfs-pulse absolute -top-[3px] w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-[0_0_12px_4px_rgba(34,211,238,0.55)]" />
          </div>

          <ol className="grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-6">
            {pipeline.map((st) => (
              <li key={st.step} className="relative flex flex-col items-center text-center group">
                <div className="relative z-10 w-16 h-16 rounded-2xl bg-[#0a0f1a] border border-white/[0.1] group-hover:border-cyan-400/50 flex items-center justify-center mb-6 shadow-lg shadow-black/40 transition-colors">
                  <span className="material-symbols-outlined text-cyan-300 text-[28px]">{st.icon}</span>
                  <span className="absolute -top-2 -right-2 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md bg-cyan-500/15 border border-cyan-500/30 text-cyan-300">
                    {st.step}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{st.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed max-w-[15rem]">{st.detail}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* SECTION 4: CALL TO ACTION */}
      <section className="py-24 px-4 relative overflow-hidden border-t border-white/[0.06]">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-blue-600/15 rounded-full blur-[140px] pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto text-center flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/25 mb-8">
            <span className="material-symbols-outlined text-white text-3xl font-black">sensors</span>
          </div>

          <h2 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
            Care That Sees <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-indigo-400">
              Without Watching.
            </span>
          </h2>

          <p className="text-slate-400 text-base sm:text-lg max-w-2xl mb-10 leading-relaxed">
            Explore the caregiver desk, family portal and workplace console. Demo, dataset replay and live hardware data are always labelled.
          </p>

          <button
            onClick={onGetStarted}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-10 py-4 rounded-full font-bold text-lg transition-all shadow-xl shadow-cyan-600/30 hover:shadow-cyan-500/40 hover:scale-105 active:scale-95 cursor-pointer flex items-center gap-2 mb-16"
          >
            Launch Wifisense Platform
            <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
          </button>

          {/* The system in four numbers */}
          <dl className="w-full grid grid-cols-2 sm:grid-cols-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm divide-x divide-y sm:divide-y-0 divide-white/[0.06] overflow-hidden">
            {facts.map((f) => (
              <div key={f.label} className="px-4 py-6 flex flex-col items-center gap-1.5">
                <dt className="order-2 text-[11px] font-mono uppercase tracking-wider text-slate-500 leading-snug">{f.label}</dt>
                <dd className="order-1 text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-b from-white to-slate-400">{f.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* SECTION 5: FOOTER */}
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
            <span className="w-2 h-2 rounded-full bg-cyan-500/70" />
            <span className="text-cyan-400/80">ESP32-S3 · 2.4 GHz CSI</span>
          </div>

          <div>
            &copy; {new Date().getFullYear()} Wifisense. All rights reserved.
          </div>
        </div>
      </footer>

    </div>
  );
}
