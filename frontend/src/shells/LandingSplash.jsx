import React, { useEffect, useState } from "react";
import TheProblemSection from "../components/TheProblemSection";
import LandingFeatures from "../components/LandingFeatures";

export default function LandingSplash({ onGetStarted }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToProblem = () => {
    const el = document.getElementById("the-problem");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="bg-[#0b0c10] min-h-screen text-white font-sans relative overflow-x-hidden scroll-smooth">
      <style>{`
        @keyframes customFloat {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-15px) rotate(2deg); }
        }
        @keyframes customFloatReverse {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(15px) rotate(-2deg); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.2; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(1.1); }
        }
        @keyframes scrollMouse {
          0% { transform: translateY(0); opacity: 1; }
          50% { transform: translateY(6px); opacity: 0.4; }
          100% { transform: translateY(0); opacity: 1; }
        }
        .animate-float { animation: customFloat 6s ease-in-out infinite; }
        .animate-float-reverse { animation: customFloatReverse 7s ease-in-out infinite; }
        .animate-float-delayed { animation: customFloat 5s ease-in-out infinite 1s; }
        .animate-float-fast { animation: customFloatReverse 4s ease-in-out infinite 0.5s; }
        
        .fade-in-up {
          opacity: 0;
          animation: fadeInUp 1s ease-out forwards;
        }
        .delay-100 { animation-delay: 100ms; }
        .delay-300 { animation-delay: 300ms; }
        .delay-500 { animation-delay: 500ms; }
      `}</style>

      {/* Hero Section (Preserved Layout & Elements) */}
      <section className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden w-full">
        {/* Top Navbar / Logo Area */}
        <div className={`absolute top-0 w-full p-8 flex justify-between items-center z-20 transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-10'}`}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white flex items-center justify-center rounded-sm shadow-md shadow-white/10">
              <span className="material-symbols-outlined text-[#0b0c10] font-black" style={{ fontSize: "20px" }}>sensors</span>
            </div>
            <span className="text-xl font-bold tracking-tight">Wifisense</span>
          </div>
        </div>

        {/* Background ambient glows */}
        <div className="absolute top-[10%] left-[10%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" style={{ animation: 'pulseGlow 10s ease-in-out infinite' }}></div>
        <div className="absolute bottom-[10%] right-[10%] w-[500px] h-[500px] bg-fuchsia-600/20 rounded-full blur-[120px] pointer-events-none" style={{ animation: 'pulseGlow 8s ease-in-out infinite 1s' }}></div>

        {/* Main Content */}
        <div className="relative z-10 text-center max-w-4xl mx-auto px-4 flex flex-col items-center">
          
          {/* Floating Pills */}
          <div className="absolute -top-24 -left-16 bg-white/10 backdrop-blur-md border border-white/20 text-blue-200 text-xs px-5 py-2 rounded-full font-semibold shadow-xl animate-float fade-in-up delay-300 hover:border-cyan-400/50 hover:text-white transition-colors cursor-default">
            Caregiver
          </div>
          {/* Admin pill */}
          <div className="absolute -top-12 -right-32 bg-yellow-400 text-yellow-900 text-xs px-5 py-2 rounded-full font-bold shadow-xl shadow-yellow-500/20 animate-float-delayed fade-in-up delay-500 hover:brightness-105 transition-all cursor-default">
            Admin
          </div>
          <div className="absolute bottom-12 -left-28 bg-fuchsia-500 text-white text-xs px-5 py-2 rounded-full font-bold shadow-xl shadow-fuchsia-500/30 animate-float-reverse fade-in-up delay-500 hover:brightness-105 transition-all cursor-default">
            Staff
          </div>
          <div className="absolute -bottom-8 -right-20 bg-indigo-500 text-white text-xs px-5 py-2 rounded-full font-bold shadow-xl shadow-indigo-500/30 animate-float-fast fade-in-up delay-300 hover:brightness-105 transition-all cursor-default">
            Family
          </div>

          {/* Hero Text */}
          <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6 leading-[1.1] fade-in-up">
            Smart Solutions for <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">Smarter Spaces.</span>
          </h1>
          
          {/* Action Button */}
          <div className="fade-in-up delay-300">
            <button 
              onClick={onGetStarted}
              className="mt-12 bg-blue-600 hover:bg-blue-500 text-white px-10 py-4 rounded-full font-bold text-lg transition-all shadow-xl shadow-blue-600/40 hover:scale-105 hover:shadow-blue-500/50 active:scale-95 cursor-pointer relative overflow-hidden group"
            >
              <span className="relative z-10 flex items-center gap-2">
                Get Started
                <span className="material-symbols-outlined text-[20px] transition-transform group-hover:translate-x-1">arrow_forward</span>
              </span>
              <div className="absolute inset-0 h-full w-0 bg-white/20 transition-all duration-300 ease-out group-hover:w-full"></div>
            </button>
          </div>
        </div>

        {/* Animated Scroll Down Indicator */}
        <div 
          onClick={scrollToProblem}
          className={`absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 cursor-pointer z-20 transition-all duration-1000 ${mounted ? 'opacity-85 translate-y-0' : 'opacity-0 translate-y-4'} hover:opacity-100 group`}
          title="Scroll down to discover"
        >
          <span className="text-[11px] font-mono tracking-widest text-cyan-400/80 uppercase font-medium flex items-center gap-1.5 group-hover:text-cyan-300 transition-colors">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            Scroll to discover
          </span>
          <div className="w-5 h-8 rounded-full border border-cyan-500/35 flex items-start justify-center p-1 backdrop-blur-sm bg-cyan-950/20 shadow-md shadow-cyan-950/50 group-hover:border-cyan-400/70 transition-colors">
            <div className="w-1 h-2 rounded-full bg-cyan-400" style={{ animation: "scrollMouse 1.8s ease-in-out infinite" }} />
          </div>
        </div>
      </section>

      {/* The Problem Section (Fluid & Cleanly Proportioned) */}
      <TheProblemSection />

      {/* Extended Useful Sections: Technology Pillars, Workspaces, Demo CTA, and Footer */}
      <LandingFeatures onGetStarted={onGetStarted} />

    </div>
  );
}
