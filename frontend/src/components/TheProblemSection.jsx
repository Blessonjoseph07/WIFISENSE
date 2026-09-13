import React, { useEffect, useRef, useState } from "react";

export default function TheProblemSection() {
  const sectionRef = useRef(null);
  const [inView, setInView] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    // Intersection Observer for entering view
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
        }
      },
      { threshold: 0.2 }
    );
    observer.observe(el);

    // Scroll listener for subtle parallax and progression
    const handleScroll = () => {
      const rect = el.getBoundingClientRect();
      const windowH = window.innerHeight;
      
      // Calculate how far through the section the user has scrolled
      const progress = Math.min(1, Math.max(0, (windowH - rect.top) / (windowH + rect.height * 0.5)));
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <section
      id="the-problem"
      ref={sectionRef}
      className="relative bg-[#05070c] text-white min-h-screen py-24 sm:py-32 flex flex-col items-center justify-center px-4 overflow-hidden border-t border-white/[0.05]"
    >
      {/* Dynamic Ambient Cyan / Blue Glow behind content */}
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none transition-opacity duration-1000"
        style={{ opacity: inView ? 0.75 : 0.2 }}
      />

      {/* Subtle Radio Wave Circles */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <div 
          className="w-[480px] h-[480px] rounded-full border border-cyan-500/15 transition-all duration-1000"
          style={{ transform: `scale(${0.9 + scrollProgress * 0.15})` }}
        />
        <div 
          className="absolute w-[750px] h-[750px] rounded-full border border-blue-500/10 border-dashed transition-all duration-1000"
          style={{ transform: `scale(${0.88 + scrollProgress * 0.18})` }}
        />
        <div 
          className="absolute w-[1050px] h-[1050px] rounded-full border border-cyan-400/[0.06] transition-all duration-1000"
          style={{ transform: `scale(${0.85 + scrollProgress * 0.2})` }}
        />
      </div>

      {/* Top Telemetry Badges */}
      <div className="w-full max-w-5xl flex justify-between items-center px-4 mb-12 text-[11px] font-mono text-slate-500 uppercase tracking-widest pointer-events-none z-10">
        <span className="flex items-center gap-1.5 text-cyan-400/80">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          RF CSI Waveform Telemetry
        </span>
        <span className="hidden sm:inline-block text-slate-400/70">Zero Lenses · Zero Microphones</span>
      </div>

      {/* Content Container */}
      <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center text-center">
        
        {/* The Problem Pill */}
        <div 
          className={`inline-flex items-center gap-2 px-5 py-2 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-semibold tracking-wide mb-8 shadow-lg shadow-cyan-950/50 backdrop-blur-md transition-all duration-700 ${
            inView ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-6 blur-xs"
          }`}
        >
          <span className="material-symbols-outlined text-[17px] text-cyan-400">lightbulb</span>
          <span>The Problem</span>
        </div>

        {/* Headline */}
        <h2 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight leading-[1.12] mb-8">
          {/* "Cameras" */}
          <span 
            className={`inline-block text-white transition-all duration-700 mr-2.5 sm:mr-3.5 ${
              inView ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-8 blur-sm"
            }`}
            style={{ transitionDelay: "150ms" }}
          >
            Cameras
          </span>

          {/* "break" in Red */}
          <span 
            className={`inline-block text-[#ef4444] font-black transition-all duration-700 mr-2.5 sm:mr-3.5 drop-shadow-[0_0_25px_rgba(239,68,68,0.6)] ${
              inView ? "opacity-100 scale-100 filter-none" : "opacity-0 scale-125 blur-sm"
            }`}
            style={{ transitionDelay: "300ms" }}
          >
            break
          </span>

          {/* "privacy." */}
          <span 
            className={`inline-block text-white transition-all duration-700 ${
              inView ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-8 blur-sm"
            }`}
            style={{ transitionDelay: "450ms" }}
          >
            privacy.
          </span>

          <br />

          {/* "Sensors miss context." in Luminous Cyan */}
          <span 
            className={`inline-block text-[#00f0ff] mt-1 sm:mt-2 font-extrabold drop-shadow-[0_0_30px_rgba(0,240,255,0.5)] transition-all duration-700 ${
              inView ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-10 blur-sm"
            }`}
            style={{ transitionDelay: "600ms" }}
          >
            Sensors miss context.
          </span>
        </h2>

        {/* Paragraph Card */}
        <div 
          className={`backdrop-blur-md bg-white/[0.02] border border-white/[0.08] rounded-2xl p-6 sm:p-8 shadow-2xl max-w-3xl transition-all duration-700 ${
            inView ? "opacity-100 translate-y-0 filter-none" : "opacity-0 translate-y-8 blur-sm"
          }`}
          style={{ transitionDelay: "750ms" }}
        >
          <p className="text-slate-300 text-base sm:text-lg md:text-xl leading-relaxed">
            Most "smart spaces" either record you or guess at you. Wifisense does neither. It reads the radio signals that are{" "}
            <strong className="text-white font-semibold">already saturating every room</strong> and turns them into structured, on-device intelligence — no lenses, no microphones, no cloud.
          </p>
        </div>

      </div>

      {/* Bottom Pulse Accent */}
      <div className="mt-16 flex items-center gap-3 text-xs font-mono text-slate-500 z-10">
        <span className="w-2 h-0.5 bg-cyan-500/50" />
        <span className="text-cyan-400/80">RADIO-FREQUENCY CHANNEL STATE INFORMATION (RF CSI)</span>
        <span className="w-2 h-0.5 bg-cyan-500/50" />
      </div>
    </section>
  );
}
