import React, { useEffect, useState } from "react";
import elderImg from "../assets/elderly-care.png";

export default function ElderCareSplash({ onContinue }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="bg-[#FAF8F5] min-h-screen text-[#4A3C31] font-sans flex flex-col relative overflow-hidden transition-opacity duration-1000">
      
      {/* Main Content Area */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-8 flex flex-col lg:flex-row items-center justify-center relative z-10">
        
        {/* Left Side: Text and Button */}
        <div className={`lg:w-1/2 flex flex-col items-start text-left z-20 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`}>
          <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6 text-[#7E5B4B]">
            Elderly care
          </h1>
          <p className="text-lg md:text-xl text-[#8C6D58] mb-10 max-w-md leading-relaxed font-medium">
            Welcome to the Wifisense Elder Care monitoring portal. Connect with your residents, monitor real-time health data, and ensure a safer environment.
          </p>
          <button 
            onClick={onContinue}
            className="bg-[#D1A68D] hover:bg-[#8B5E43] text-white px-10 py-4 rounded-full font-bold text-lg transition-all shadow-xl shadow-[#D1A68D]/40 hover:scale-105 active:scale-95 cursor-pointer"
          >
            Enter Dashboard
          </button>
        </div>

        {/* Right Side: Illustration */}
        <div className={`lg:w-1/2 relative flex justify-center items-center mt-12 lg:mt-0 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10'}`}>
          {/* Subtle background blob */}
          <div className="absolute w-[120%] h-[120%] bg-[#F2ECE4] rounded-[40%_60%_70%_30%/40%_50%_60%_50%] -z-10 animate-[blob_10s_ease-in-out_infinite]"></div>
          
          <img 
            src={elderImg} 
            alt="Elderly care illustration" 
            className="w-full max-w-lg object-contain drop-shadow-md"
          />
        </div>
      </div>
      
      {/* Add custom blob animation */}
      <style>{`
        @keyframes blob {
          0%, 100% { border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; transform: scale(1); }
          34% { border-radius: 70% 30% 50% 50% / 30% 30% 70% 70%; transform: scale(1.05); }
          67% { border-radius: 100% 60% 60% 100% / 100% 100% 60% 60%; transform: scale(0.95); }
        }
      `}</style>
    </div>
  );
}
