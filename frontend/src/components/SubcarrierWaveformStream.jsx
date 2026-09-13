import React, { useState, useEffect } from "react";

/**
 * SubcarrierWaveformStream
 * Self-contained diagnostic waveform visualizer that updates every 150ms
 * without triggering re-renders in the parent application tree.
 */
export default function SubcarrierWaveformStream({ activeActivity = "Empty" }) {
  const [subcarriers, setSubcarriers] = useState(() => Array.from({ length: 40 }, () => 20));

  useEffect(() => {
    const interval = setInterval(() => {
      setSubcarriers(prev => prev.map(() => {
        let noise = Math.random() * 15;
        if (activeActivity === "Walking") noise = Math.random() * 45;
        if (activeActivity === "Fall_Detected") noise = Math.random() * 75;
        if (activeActivity === "Empty") noise = Math.random() * 3;
        
        let base = 20;
        if (activeActivity === "Sitting") base = 12;
        if (activeActivity === "Fall_Detected") base = 10;
        
        return Math.min(100, Math.max(5, base + noise));
      }));
    }, 150);
    return () => clearInterval(interval);
  }, [activeActivity]);

  return (
    <div>
      <div className="text-label-caps font-label-caps text-slate-400 mb-2 flex justify-between">
        <span>Amplitude Stream</span>
        <span className="font-data-mono text-[10px] text-teal-600 dark:text-teal-400 font-bold">LIVE</span>
      </div>
      <div className="h-32 bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 relative overflow-hidden flex items-end p-1 gap-0.5">
        {subcarriers.map((h, i) => (
          <div 
            key={i} 
            className="flex-1 bg-teal-600 dark:bg-teal-400 opacity-60 rounded-t transition-all duration-150" 
            style={{ height: `${h}%` }}
          ></div>
        ))}
      </div>
    </div>
  );
}
