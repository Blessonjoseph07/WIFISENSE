import React, { useEffect, useState } from "react";

export default function CorporateSplash({ user, onContinue }) {
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    setMounted(true);
  }, []);

  const userName = user?.first_name || "John";

  return (
    <div className="bg-[#DCE7DC] min-h-screen text-[#1B2D21] font-sans flex flex-col relative overflow-x-hidden overflow-y-auto selection:bg-[#284B35] selection:text-white">
      
      {/* Background Radiating Rays / Sunburst Watermark */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-0">
        <svg
          className="absolute -top-[20%] -left-[15%] w-[1100px] h-[1100px] opacity-[0.14] text-[#1D3B28] animate-[spin_180s_linear_infinite]"
          viewBox="0 0 500 500"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {Array.from({ length: 24 }).map((_, i) => (
            <polygon
              key={i}
              points="250,250 242,0 258,0"
              fill="currentColor"
              transform={`rotate(${i * 15} 250 250)`}
            />
          ))}
        </svg>

        {/* Soft background ambient gradient glow */}
        <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] bg-[#EAF4E8] rounded-full blur-3xl opacity-60"></div>
        <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-[#C8DAC9] rounded-full blur-3xl opacity-50"></div>
      </div>

      {/* Top Navigation / Brand Bar */}
      <header className="w-full max-w-[1550px] mx-auto px-8 pt-8 pb-4 flex items-center justify-between relative z-20">
        <div className="flex items-center gap-3">
          {/* Logo symbol */}
          <div className="w-9 h-9 rounded-xl bg-[#1C3325] text-[#DCE7DC] flex items-center justify-center shadow-md shadow-[#1C3325]/20">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 11a9 9 0 0 1 16 0" />
              <path d="M7 14a5 5 0 0 1 10 0" />
              <circle cx="12" cy="18" r="1.5" fill="currentColor" />
            </svg>
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-[#16291E]">Wifisense</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="hidden sm:inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-[#CBDDCB] text-[#223B2B] border border-[#B8CEB8]">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping"></span>
            Corporate Facility Engine Live
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-[1550px] mx-auto px-6 md:px-8 py-6 flex flex-col xl:flex-row items-center justify-between gap-10 relative z-10">
        
        {/* Left Column: Heading, Subtitle & Action */}
        <div className={`xl:w-[38%] flex flex-col items-start text-left z-20 transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-12'}`}>
          
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#CBDDCB] text-[#253E2F] text-xs font-bold uppercase tracking-wider mb-6 border border-[#B9CFB9]">
            <span className="material-symbols-outlined text-sm text-[#253E2F]">domain</span>
            Space Management
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-[68px] font-black tracking-tight text-[#16291E] leading-[1.08] mb-6">
            Space Management <br />
            <span className="text-[#2B4E38]">Dashboard UI</span>
          </h1>

          <p className="text-base sm:text-lg text-[#324B3A] mb-8 max-w-lg leading-relaxed font-normal">
            Intelligent spatial analytics and real-time facility intelligence powered by Wi-Fi CSI sensing. Monitor occupancy, optimize workstation efficiency, and streamline property operations with zero wearable requirements.
          </p>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
            <button
              onClick={onContinue}
              className="group bg-[#193223] hover:bg-[#0E1E15] text-white px-9 py-4 rounded-full font-bold text-base transition-all duration-300 shadow-xl shadow-[#193223]/25 hover:shadow-2xl hover:shadow-[#193223]/35 hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-3 cursor-pointer"
            >
              <span>Enter Dashboard</span>
              <svg 
                className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1.5" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor" 
                strokeWidth="2.5"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>

            <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-[#D2E0D2]/70 border border-[#BED0BF]">
              <div className="flex -space-x-2">
                <div className="w-8 h-8 rounded-full bg-[#1F3D2C] text-white flex items-center justify-center text-[10px] font-bold border-2 border-[#DCE7DC]">CSI</div>
                <div className="w-8 h-8 rounded-full bg-[#D1A68D] text-white flex items-center justify-center text-[10px] font-bold border-2 border-[#DCE7DC]">RF</div>
                <div className="w-8 h-8 rounded-full bg-[#7C9982] text-white flex items-center justify-center text-[10px] font-bold border-2 border-[#DCE7DC]">AI</div>
              </div>
              <div className="text-left">
                <div className="text-xs font-bold text-[#193223]">Live Telemetry</div>
                <div className="text-[10px] text-[#476550]">Zero Privacy Invasion</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Floating Realistic Dashboard UI Preview Card */}
        <div className={`xl:w-[62%] w-full relative flex justify-center items-center transition-all duration-1000 delay-400 ${mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-10 scale-95'}`}>
          
          {/* Peeking background secondary card for depth effect */}
          <div className="absolute top-[-14px] right-[-10px] w-[95%] h-[95%] bg-[#CDE0CF]/80 rounded-[36px] border border-[#BACFBD] -z-10 transform rotate-1 hidden sm:block"></div>

          {/* Main Dashboard Preview Card */}
          <div className="w-full bg-[#FBFBFA] rounded-[32px] sm:rounded-[36px] border border-[#DFE5DC] shadow-[0_30px_70px_-15px_rgba(25,48,34,0.18)] p-5 sm:p-7 text-[#223628] relative z-10 overflow-hidden">
            
            {/* Inner Dashboard Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#ECEEEA]">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-full bg-[#E5F0E4] text-[#1E3B27] flex items-center justify-center">
                  <svg className="w-6 h-6 animate-[spin_30s_linear_infinite]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07L19.07 4.93" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[#162B1E]">
                    Hello, {userName}!
                  </h2>
                  <p className="text-xs text-[#5D7363]">
                    Explore information and activity about your property
                  </p>
                </div>
              </div>

              {/* Search and Notification Actions */}
              <div className="flex items-center gap-2.5">
                <div className="relative flex items-center bg-[#F2F4F0] rounded-full px-3.5 py-2 w-48 sm:w-56 border border-[#E0E6DD]">
                  <input
                    type="text"
                    readOnly
                    placeholder="Search Anything..."
                    className="bg-transparent text-xs text-[#354D3C] focus:outline-none w-full placeholder:text-[#8D9F91]"
                  />
                  <div className="w-6 h-6 rounded-full bg-[#182F21] text-white flex items-center justify-center shrink-0 shadow-sm cursor-pointer">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                  </div>
                </div>

                <div className="w-9 h-9 rounded-full bg-[#F2F4F0] border border-[#E0E6DD] flex items-center justify-center text-[#3D5644] hover:bg-[#E7EBE4] transition-colors relative cursor-pointer">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white"></span>
                </div>

                <div className="w-9 h-9 rounded-full bg-[#F2F4F0] border border-[#E0E6DD] flex items-center justify-center text-[#3D5644] hover:bg-[#E7EBE4] transition-colors cursor-pointer">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Dashboard Inner Body: Sidebar Rail + Grid */}
            <div className="flex gap-5 pt-5">
              
              {/* Left Mini Sidebar Rail */}
              <div className="hidden md:flex flex-col items-center justify-between py-3 px-1.5 bg-[#F2F4F0] rounded-2xl border border-[#E2E7DF] w-12 shrink-0">
                <div className="flex flex-col items-center gap-3">
                  <button 
                    onClick={() => setActiveTab("dashboard")}
                    className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all ${activeTab === 'dashboard' ? 'bg-[#183021] text-white shadow-md' : 'text-[#5C7262] hover:bg-[#E3E8DF]'}`}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="5" width="20" height="14" rx="2" />
                      <line x1="2" y1="10" x2="22" y2="10" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>

                <div className="flex flex-col items-center gap-2.5 pt-4">
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  </button>
                  <button className="w-8 h-8 rounded-xl flex items-center justify-center text-[#5C7262] hover:bg-[#E3E8DF]">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="9" />
                      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                  </button>
                  <div className="w-7 h-7 rounded-full bg-[#182F21] text-white flex items-center justify-center text-[10px] font-bold mt-1">
                    {userName[0]}
                  </div>
                </div>
              </div>

              {/* Central Multi-Metric Content */}
              <div className="flex-1 flex flex-col gap-4">
                
                {/* 3 Top Stat Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                  
                  {/* Card 1: Total Property */}
                  <div className="bg-white rounded-2xl p-3.5 border border-[#E6EAE3] shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#EBF3EA] text-[#294B34] flex items-center justify-center">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                        </div>
                        <span className="text-xs font-semibold text-[#4F6555]">Total Property</span>
                      </div>
                      <span className="text-[#A4B5A8] text-xs">•••</span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-2xl font-black text-[#152B1D]">1,500</span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                        ↗ 20%
                      </span>
                    </div>
                    <span className="text-[10px] text-[#7A8E80] mt-1">Last month total 1,050</span>
                  </div>

                  {/* Card 2: Number of Presences */}
                  <div className="bg-white rounded-2xl p-3.5 border border-[#E6EAE3] shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#EBF3EA] text-[#294B34] flex items-center justify-center">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <span className="text-xs font-semibold text-[#4F6555]">Active Presence</span>
                      </div>
                      <span className="text-[#A4B5A8] text-xs">•••</span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-2xl font-black text-[#152B1D]">320</span>
                      <span className="text-[10px] font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded">
                        ↘ 20%
                      </span>
                    </div>
                    <span className="text-[10px] text-[#7A8E80] mt-1">Last month total 950</span>
                  </div>

                  {/* Card 3: Total Efficiency */}
                  <div className="bg-white rounded-2xl p-3.5 border border-[#E6EAE3] shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#F8EFEA] text-[#935D39] flex items-center justify-center">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <span className="text-xs font-semibold text-[#4F6555]">Total Sales</span>
                      </div>
                      <span className="text-[#A4B5A8] text-xs">•••</span>
                    </div>
                    <div className="flex items-baseline gap-2 mt-1">
                      <span className="text-2xl font-black text-[#152B1D]">$150k</span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                        ↗ 20%
                      </span>
                    </div>
                    <span className="text-[10px] text-[#7A8E80] mt-1">Last month total 1,500</span>
                  </div>
                </div>

                {/* Middle Row: Bar Chart & Donut Chart */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-3.5">
                  
                  {/* Left: Report Sales / Bar Chart (3 cols) */}
                  <div className="lg:col-span-3 bg-white rounded-2xl p-4 border border-[#E6EAE3] shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-bold text-[#182F21]">Report Sales</h3>
                      </div>
                      <div className="flex items-center gap-1 text-[11px] font-medium text-[#465F4F] bg-[#F2F4F0] px-2.5 py-1 rounded-lg border border-[#E0E5DC] cursor-pointer">
                        <span>Weekday</span>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                      </div>
                    </div>

                    {/* Chart Graphic */}
                    <div className="relative pt-6 pb-2">
                      
                      {/* Floating Tooltip above Thursday */}
                      <div className="absolute top-0 left-[55%] -translate-x-1/2 bg-[#1B3525] text-white px-2.5 py-1 rounded-lg shadow-lg text-[9px] font-semibold flex flex-col items-center z-10">
                        <div className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          <span>$4,096.00</span>
                        </div>
                        <span className="text-[8px] text-[#A2BEA9]">Thu, 12 Jul</span>
                        <div className="w-1.5 h-1.5 bg-[#1B3525] transform rotate-45 -mb-1 mt-0.5"></div>
                      </div>

                      {/* Bars & Horizontal Gridlines */}
                      <div className="flex items-end justify-between h-28 gap-2 border-b border-[#E8EDE5] px-2">
                        {/* Mon */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[45%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Mon</span>
                        </div>
                        {/* Tue */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[60%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Tue</span>
                        </div>
                        {/* Wed */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[50%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Wed</span>
                        </div>
                        {/* Thu (Active) */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#294E37] rounded-md h-[88%] shadow-md transition-all"></div>
                          <span className="text-[10px] font-bold text-[#1E3927]">Thu</span>
                        </div>
                        {/* Fri */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[68%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Fri</span>
                        </div>
                        {/* Sat */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[38%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Sat</span>
                        </div>
                        {/* Sun */}
                        <div className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                          <div className="w-full max-w-[28px] bg-[#E3EBE1] hover:bg-[#D5E1D3] rounded-md h-[55%] transition-all"></div>
                          <span className="text-[10px] text-[#7A8E80]">Sun</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right: Cost Breakdown / Donut Chart (2 cols) */}
                  <div className="lg:col-span-2 bg-white rounded-2xl p-4 border border-[#E6EAE3] shadow-sm flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-bold text-[#182F21]">Cost Breakdown</h3>
                      <button className="text-[10px] font-semibold text-[#54705D] hover:underline">See Details</button>
                    </div>

                    <div className="flex items-center justify-between gap-3 py-1">
                      {/* SVG Donut Chart */}
                      <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                          {/* Segment 1: Green */}
                          <circle cx="18" cy="18" r="14" fill="none" stroke="#90BA9A" strokeWidth="4.5" strokeDasharray="40 60" strokeDashoffset="0" />
                          {/* Segment 2: Tan/Sand */}
                          <circle cx="18" cy="18" r="14" fill="none" stroke="#D1BE9E" strokeWidth="4.5" strokeDasharray="25 75" strokeDashoffset="-40" />
                          {/* Segment 3: Lavender/Slate */}
                          <circle cx="18" cy="18" r="14" fill="none" stroke="#B8C4D6" strokeWidth="4.5" strokeDasharray="20 80" strokeDashoffset="-65" />
                          {/* Segment 4: Sage/Beige */}
                          <circle cx="18" cy="18" r="14" fill="none" stroke="#E2DAC9" strokeWidth="4.5" strokeDasharray="15 85" strokeDashoffset="-85" />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className="text-xs font-bold text-[#16291E]">$ 4,750</span>
                        </div>
                      </div>

                      {/* Donut Legend */}
                      <div className="flex flex-col gap-1.5 text-[10px]">
                        <div className="flex items-center gap-1.5 text-[#42584A]">
                          <span className="w-2 h-2 rounded-full bg-[#90BA9A]"></span>
                          <span>Maintenance</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[#42584A]">
                          <span className="w-2 h-2 rounded-full bg-[#D1BE9E]"></span>
                          <span>Repair</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[#42584A]">
                          <span className="w-2 h-2 rounded-full bg-[#B8C4D6]"></span>
                          <span>Taxes</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[#42584A]">
                          <span className="w-2 h-2 rounded-full bg-[#E2DAC9]"></span>
                          <span>Saving</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bottom Row: Last Transactions & Maintenance Request */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
                  
                  {/* Card 1: Last Transactions */}
                  <div className="bg-white rounded-2xl p-3.5 border border-[#E6EAE3] shadow-sm">
                    <div className="flex items-center justify-between mb-2.5">
                      <h4 className="text-xs font-bold text-[#182F21]">Last Transactions</h4>
                      <button className="text-[10px] font-semibold text-[#54705D] hover:underline">See All</button>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-[#EBECE7] flex items-center justify-center text-xs">🏢</div>
                          <div>
                            <div className="text-[11px] font-semibold text-[#182F21] leading-tight">123 Maple Avenue Springfield</div>
                            <div className="text-[9px] text-[#7A8E80]">12 Sep 2026, 9:29</div>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-[#162C1E]">$30K</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-[#EBECE7] flex items-center justify-center text-xs">🏡</div>
                          <div>
                            <div className="text-[11px] font-semibold text-[#182F21] leading-tight">Booking 987 Villa Street</div>
                            <div className="text-[9px] text-[#7A8E80]">10 Sep 2026, 9:29</div>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-[#162C1E]">$10K</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-[#EBECE7] flex items-center justify-center text-xs">🏘️</div>
                          <div>
                            <div className="text-[11px] font-semibold text-[#182F21] leading-tight">Apartment Booking On Garden Street</div>
                            <div className="text-[9px] text-[#7A8E80]">08 Sep 2026, 9:29</div>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-[#162C1E]">$20K</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Maintenance Request */}
                  <div className="bg-white rounded-2xl p-3.5 border border-[#E6EAE3] shadow-sm">
                    <div className="flex items-center justify-between mb-2.5">
                      <h4 className="text-xs font-bold text-[#182F21]">Maintenance Request</h4>
                      <button className="text-[10px] font-semibold text-[#54705D] hover:underline">See All</button>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-[#EBF3EA] text-[#294B34] flex items-center justify-center text-xs">🔧</div>
                          <div>
                            <div className="font-semibold text-[#182F21] leading-tight">Plumbing | 721 Meadowview</div>
                            <div className="text-[9px] text-[#7A8E80]">Broken Garbage</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-[#B2927C] text-white flex items-center justify-center text-[8px] font-bold">JJ</div>
                          <span className="text-[9px] font-medium text-[#465E4E]">Jacob Jones</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-[#EBF3EA] text-[#294B34] flex items-center justify-center text-xs">⚡</div>
                          <div>
                            <div className="font-semibold text-[#182F21] leading-tight">Electrical | 721 Meadowview</div>
                            <div className="text-[9px] text-[#7A8E80]">No Heat Bathroom</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-[#6B8C9E] text-white flex items-center justify-center text-[8px] font-bold">AF</div>
                          <span className="text-[9px] font-medium text-[#465E4E]">Albert Flores</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-[#EBF3EA] text-[#294B34] flex items-center justify-center text-xs">❄️</div>
                          <div>
                            <div className="font-semibold text-[#182F21] leading-tight">HVAC | 721 Meadowview</div>
                            <div className="text-[9px] text-[#7A8E80]">Non Functional Fan</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-[#8E79A8] text-white flex items-center justify-center text-[8px] font-bold">RF</div>
                          <span className="text-[9px] font-medium text-[#465E4E]">Robert Fox</span>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

              </div>

            </div>

          </div>
        </div>

      </main>

      {/* Footer minimal info */}
      <footer className="w-full max-w-[1550px] mx-auto px-8 py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-[#5D7363] border-t border-[#CBDDCB]/60 relative z-20">
        <div>© 2026 Wifisense Inc. Next-Generation Space Management & Environmental Intelligence.</div>
        <div className="flex items-center gap-6 mt-2 sm:mt-0">
          <span className="hover:text-[#182F21] transition-colors cursor-pointer">Privacy Framework</span>
          <span className="hover:text-[#182F21] transition-colors cursor-pointer">Hardware Diagnostics</span>
          <span className="hover:text-[#182F21] transition-colors cursor-pointer">API Docs</span>
        </div>
      </footer>
    </div>
  );
}
