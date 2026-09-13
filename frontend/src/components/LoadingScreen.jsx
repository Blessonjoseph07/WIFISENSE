import React, { useEffect, useRef, useState } from "react";

// Digital glyphs and characters matching the visual reference storyboard
const GLYPHS = [
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
  "X", "Y", "Z", "0", "1", "░", "▒", "▓",
  ".", ":", "+", "*", "/", "\\", "|", "_"
];

function getRandomGlyph() {
  return GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
}

export default function LoadingScreen({ onComplete }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);

  // Stable ref for onComplete to prevent re-triggering animation on parent re-renders
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    // Accessibility check: prefers-reduced-motion
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (motionQuery.matches) {
      setIsReducedMotion(true);
      const timer = setTimeout(() => {
        setIsFadingOut(true);
        setTimeout(() => {
          if (onCompleteRef.current) onCompleteRef.current();
        }, 350);
      }, 950);
      return () => clearTimeout(timer);
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId;
    let startTime = null;
    let fadeTriggered = false;
    let completed = false;

    // Timeline duration: 3.85s (within requested 3.5s - 4.0s window)
    const TOTAL_DURATION = 3850;

    // Hard safety timer
    const safetyTimer = setTimeout(() => {
      if (!completed) {
        completed = true;
        if (onCompleteRef.current) onCompleteRef.current();
      }
    }, TOTAL_DURATION + 400);

    // Dynamic dimensions & DPI setup
    let width = window.innerWidth;
    let height = window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resizeCanvas = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const isMobile = width < 768;
    const particleCount = isMobile ? 65 : 135;

    // Background floating glyph particles
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 1.6,
        vy: (Math.random() - 0.5) * 0.4,
        char: getRandomGlyph(),
        baseAlpha: 0.12 + Math.random() * 0.45,
        colorType: Math.random() > 0.65 ? "cyan" : Math.random() > 0.45 ? "purple" : "dim",
        size: isMobile ? 11 : 13
      });
    }

    // Pre-calculate Wi-Fi symbol target positions
    const cx = width / 2;
    const cy = height / 2 - (isMobile ? 22 : 32);
    const wifiTargets = [];

    // Wi-Fi 3 arcs configuration
    const arcConfigs = [
      { r: isMobile ? 72 : 110, span: 92, count: isMobile ? 24 : 36 },
      { r: isMobile ? 48 : 74,  span: 96, count: isMobile ? 18 : 28 },
      { r: isMobile ? 26 : 42,  span: 100, count: isMobile ? 12 : 20 }
    ];

    arcConfigs.forEach((cfg) => {
      const startRad = (-90 - cfg.span / 2) * (Math.PI / 180);
      const endRad = (-90 + cfg.span / 2) * (Math.PI / 180);
      for (let j = 0; j < cfg.count; j++) {
        const theta = startRad + (j / (cfg.count - 1)) * (endRad - startRad);
        wifiTargets.push({
          x: cx + cfg.r * Math.cos(theta),
          y: cy + cfg.r * Math.sin(theta),
          char: getRandomGlyph(),
          radius: cfg.r
        });
      }
    });

    // Center dot cluster
    wifiTargets.push({ x: cx, y: cy, char: "●", radius: 0 });
    wifiTargets.push({ x: cx - 6, y: cy, char: "0", radius: 0 });
    wifiTargets.push({ x: cx + 6, y: cy, char: "1", radius: 0 });
    wifiTargets.push({ x: cx, y: cy - 6, char: "░", radius: 0 });

    // Link target points to particles
    for (let i = 0; i < wifiTargets.length && i < particles.length; i++) {
      particles[i].targetX = wifiTargets[i].x;
      particles[i].targetY = wifiTargets[i].y;
      particles[i].wifiChar = wifiTargets[i].char;
    }

    // Warp light streaks for finale (3.6s - 4.0s)
    const streakCount = isMobile ? 65 : 140;
    const streaks = [];
    for (let i = 0; i < streakCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      streaks.push({
        angle,
        speed: 18 + Math.random() * 30,
        length: 24 + Math.random() * 80,
        dist: 20 + Math.random() * (Math.max(width, height) * 0.6),
        color: Math.random() > 0.6 ? "#00f0ff" : Math.random() > 0.3 ? "#3b82f6" : "#a855f7"
      });
    }

    // Animation Loop
    const render = (timestamp) => {
      try {
        if (!startTime) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const t = elapsed / 1000; // time in seconds

        // Trigger container fade-out at 3.65s for seamless reveal of landing page
        if (t >= 3.65 && !fadeTriggered) {
          fadeTriggered = true;
          setIsFadingOut(true);
        }

        ctx.clearRect(0, 0, width, height);

        // Near-black CRT Background
        ctx.fillStyle = "#030509";
        ctx.fillRect(0, 0, width, height);

        // Subtle CRT scanlines
        ctx.fillStyle = "rgba(0, 240, 255, 0.015)";
        const step = isMobile ? 6 : 4;
        for (let y = 0; y < height; y += step) {
          ctx.fillRect(0, y, width, 1);
        }

        // ====================================================================
        // PHASE 1: 0.0s – 0.7s: INITIALIZATION
        // Starts almost completely black. Faint characters flicker. Center WIFISENSE micro-glitches.
        // ====================================================================
        if (t < 0.7) {
          const p1Ratio = Math.min(1, t / 0.7);

          // Very small number of extremely faint characters
          ctx.font = `${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
          particles.slice(0, Math.floor(particleCount * 0.35)).forEach((p, idx) => {
            if (Math.random() < 0.05) p.char = getRandomGlyph();
            const alpha = p.baseAlpha * Math.abs(Math.sin(t * 8 + idx)) * p1Ratio;
            if (alpha > 0.02) {
              ctx.fillStyle = `rgba(147, 197, 253, ${alpha * 0.75})`;
              ctx.fillText(p.char, p.x, p.y);
            }
          });

          // Center WIFISENSE with brief micro-glitches resolving quickly
          const titleChars = ["W", "I", "F", "I", "S", "E", "N", "S", "E"];
          if (t > 0.15 && t < 0.65 && Math.random() > 0.6) {
            const randIdx = Math.floor(Math.random() * titleChars.length);
            titleChars[randIdx] = Math.random() > 0.5 ? "░" : "1";
          }
          const titleText = titleChars.join("");

          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = `800 ${isMobile ? 28 : 42}px 'Inter', sans-serif`;

          // Subtle chromatic offsets
          const jitter = (Math.random() - 0.5) * 3;
          ctx.fillStyle = "rgba(239, 68, 68, 0.35)";
          ctx.fillText(titleText, cx - jitter, cy - 8);

          ctx.fillStyle = "rgba(0, 240, 255, 0.45)";
          ctx.fillText(titleText, cx + jitter, cy - 8);

          ctx.fillStyle = `rgba(255, 255, 255, ${0.45 + p1Ratio * 0.5})`;
          ctx.fillText(titleText, cx, cy - 8);

          // Below: INITIALIZING...
          ctx.font = `500 ${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = `rgba(148, 163, 184, ${0.35 + p1Ratio * 0.5})`;
          ctx.fillText("INITIALIZING...", cx, cy + (isMobile ? 32 : 40));
        }

        // ====================================================================
        // PHASE 2: 0.7s – 1.4s: GLITCH FIELD
        // Increased digital character noise throughout viewport. Horizontal movement.
        // Status: SCANNING ENVIRONMENT...
        // ====================================================================
        else if (t >= 0.7 && t < 1.4) {
          const p2Ratio = (t - 0.7) / 0.7;

          // Digital noise characters drifting horizontally
          ctx.font = `${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
          particles.forEach((p, idx) => {
            p.x += p.vx * 1.5;
            p.y += p.vy;
            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;
            if (Math.random() < 0.08) p.char = getRandomGlyph();

            const flicker = Math.abs(Math.sin(t * 16 + idx));
            const alpha = (0.15 + flicker * 0.6) * Math.min(1, 0.5 + p2Ratio * 0.5);

            if (p.colorType === "cyan") {
              ctx.fillStyle = `rgba(0, 240, 255, ${alpha})`;
            } else if (p.colorType === "purple") {
              ctx.fillStyle = `rgba(192, 132, 252, ${alpha})`;
            } else {
              ctx.fillStyle = `rgba(226, 232, 240, ${alpha * 0.75})`;
            }
            ctx.fillText(p.char, p.x, p.y);
          });

          // Horizontal glitch bands
          if (Math.random() > 0.35) {
            const barY = Math.random() * height;
            const barH = 2 + Math.random() * 6;
            ctx.fillStyle = Math.random() > 0.5 ? "rgba(0, 240, 255, 0.15)" : "rgba(239, 68, 68, 0.1)";
            ctx.fillRect(0, barY, width, barH);
          }

          // Subtitle: SCANNING ENVIRONMENT...
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = `600 ${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = "rgba(0, 240, 255, 0.45)";
          ctx.fillText("SCANNING ENVIRONMENT...", cx + 1, cy + (isMobile ? 38 : 48));
          ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
          ctx.fillText("SCANNING ENVIRONMENT...", cx, cy + (isMobile ? 38 : 48));
        }

        // ====================================================================
        // PHASE 3: 1.4s – 2.2s: SIGNAL FORMATION
        // Characters converge toward center. Progressively form recognizable Wi-Fi symbol.
        // Status: DETECTING SPACES...
        // ====================================================================
        else if (t >= 1.4 && t < 2.2) {
          const p3Ratio = (t - 1.4) / 0.8;
          const ease = 1 - Math.pow(1 - p3Ratio, 3); // smooth cubic ease

          // Ambient scattered characters continue slow drift
          ctx.font = `${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          particles.slice(wifiTargets.length).forEach((p) => {
            p.x += p.vx * 0.6;
            p.y += p.vy * 0.6;
            if (Math.random() < 0.05) p.char = getRandomGlyph();
            ctx.fillStyle = "rgba(148, 163, 184, 0.22)";
            ctx.fillText(p.char, p.x, p.y);
          });

          // Subtle guiding Wi-Fi arc aura
          ctx.save();
          ctx.strokeStyle = `rgba(0, 240, 255, ${0.12 * ease})`;
          ctx.lineWidth = 1;
          arcConfigs.forEach((cfg) => {
            ctx.beginPath();
            ctx.arc(cx, cy, cfg.r, (-90 - cfg.span / 2) * (Math.PI / 180), (-90 + cfg.span / 2) * (Math.PI / 180));
            ctx.stroke();
          });
          ctx.restore();

          // Converging Wi-Fi glyphs forming the symbol
          ctx.font = `600 ${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
          for (let i = 0; i < wifiTargets.length && i < particles.length; i++) {
            const p = particles[i];
            const target = wifiTargets[i];

            // Smooth migration towards arc position
            p.x += (target.x - p.x) * (0.14 + ease * 0.6);
            p.y += (target.y - p.y) * (0.14 + ease * 0.6);

            if (Math.random() < 0.08) p.wifiChar = getRandomGlyph();

            const glow = 0.5 + Math.sin(t * 18 + i) * 0.4;
            ctx.save();
            ctx.shadowColor = "#00f0ff";
            ctx.shadowBlur = isMobile ? 8 : 14;
            ctx.fillStyle = i % 2 === 0 
              ? `rgba(0, 240, 255, ${Math.min(1, glow + 0.3)})` 
              : `rgba(96, 165, 250, ${Math.min(1, glow + 0.3)})`;
            ctx.fillText(p.wifiChar, p.x, p.y);
            ctx.restore();
          }

          // Subtitle: DETECTING SPACES...
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = `600 ${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = "#38bdf8";
          ctx.fillText("DETECTING SPACES...", cx, cy + (isMobile ? 88 : 118));
        }

        // ====================================================================
        // PHASE 4: 2.2s – 2.8s: SIGNAL PULSE
        // Wi-Fi symbol stabilizes. Emits concentric waves of tiny characters/particles.
        // Status: ANALYZING...
        // ====================================================================
        else if (t >= 2.2 && t < 2.8) {
          const p4Ratio = (t - 2.2) / 0.6;

          // Render stabilized Wi-Fi symbol
          ctx.font = `600 ${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
          for (let i = 0; i < wifiTargets.length; i++) {
            const target = wifiTargets[i];
            ctx.save();
            ctx.shadowColor = "#00f0ff";
            ctx.shadowBlur = 12;
            ctx.fillStyle = i % 3 === 0 ? "#00f0ff" : i % 3 === 1 ? "#60a5fa" : "#c084fc";
            ctx.fillText(target.char, target.x, target.y);
            ctx.restore();
          }

          // Concentric signal pulse wave rings expanding outward
          const maxWaveRadius = isMobile ? 210 : 340;
          const wave1Radius = (isMobile ? 20 : 30) + p4Ratio * maxWaveRadius;
          const wave1Alpha = Math.max(0, (1 - p4Ratio) * 0.85);

          ctx.save();
          ctx.beginPath();
          ctx.arc(cx, cy, wave1Radius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(0, 240, 255, ${wave1Alpha})`;
          ctx.lineWidth = isMobile ? 1.5 : 2;
          ctx.setLineDash([4, 8]);
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 10;
          ctx.stroke();
          ctx.restore();

          // Second secondary wave
          if (p4Ratio > 0.25) {
            const p4SecRatio = (p4Ratio - 0.25) / 0.75;
            const wave2Radius = (isMobile ? 15 : 25) + p4SecRatio * (maxWaveRadius * 0.85);
            const wave2Alpha = Math.max(0, (1 - p4SecRatio) * 0.6);

            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, wave2Radius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(168, 85, 247, ${wave2Alpha})`;
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 6]);
            ctx.stroke();
            ctx.restore();
          }

          // Ambient characters reacting to pulse wave
          ctx.font = `${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          particles.slice(wifiTargets.length).forEach((p) => {
            const dx = p.x - cx;
            const dy = p.y - cy;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (Math.abs(dist - wave1Radius) < 25) {
              p.char = getRandomGlyph();
              ctx.fillStyle = "rgba(0, 240, 255, 0.8)";
            } else {
              ctx.fillStyle = "rgba(148, 163, 184, 0.22)";
            }
            ctx.fillText(p.char, p.x, p.y);
          });

          // Subtitle: ANALYZING...
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = `600 ${isMobile ? 10 : 12}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = "#38bdf8";
          ctx.fillText("ANALYZING...", cx, cy + (isMobile ? 88 : 118));
        }

        // ====================================================================
        // PHASE 5: 2.8s – 3.3s: WIFISENSE RECONSTRUCTION (CHAOS → ORDER)
        // Wi-Fi breaks apart with controlled glitch burst -> snaps to clean WIFISENSE + READY
        // ====================================================================
        else if (t >= 2.8 && t < 3.3) {
          const p5Ratio = (t - 2.8) / 0.5;

          // 2.8s - 2.95s: Controlled glitch burst & horizontal slice displacement
          if (p5Ratio < 0.3) {
            ctx.font = `${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
            particles.forEach((p) => {
              p.x += (Math.random() - 0.5) * 18;
              p.char = getRandomGlyph();
              ctx.fillStyle = Math.random() > 0.5 ? "rgba(0, 240, 255, 0.7)" : "rgba(239, 68, 68, 0.6)";
              ctx.fillText(p.char, p.x, p.y);
            });

            // Fractured logo
            const glitchTitle = "WIFISENSE";
            ctx.font = `800 ${isMobile ? 40 : 60}px 'Inter', sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            const shift = (Math.random() - 0.5) * 16;
            ctx.fillStyle = "rgba(239, 68, 68, 0.7)";
            ctx.fillText(glitchTitle, cx - shift, cy - 10);
            ctx.fillStyle = "rgba(0, 240, 255, 0.8)";
            ctx.fillText(glitchTitle, cx + shift, cy - 10);
            ctx.fillStyle = "#ffffff";
            ctx.fillText(glitchTitle, cx, cy - 10);
          }
          // 2.95s - 3.3s: Snaps into clean, pristine WIFISENSE + READY!
          else {
            const snapRatio = Math.min(1, (p5Ratio - 0.3) / 0.7);

            // Clean WIFISENSE wordmark with luminous electric blue glow
            const fontSize = isMobile ? 42 : 64;
            ctx.font = `800 ${fontSize}px 'Inter', sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            ctx.save();
            ctx.shadowColor = "rgba(0, 240, 255, 0.95)";
            ctx.shadowBlur = isMobile ? 20 : 34;
            ctx.fillStyle = "#ffffff";
            ctx.fillText("WIFISENSE", cx, cy - 12);
            ctx.restore();

            // Horizontal glowing laser line
            const lineY = cy + (isMobile ? 22 : 30);
            const lineHalfW = (isMobile ? 65 : 110) * snapRatio;
            const grad = ctx.createLinearGradient(cx - lineHalfW, lineY, cx + lineHalfW, lineY);
            grad.addColorStop(0, "rgba(0, 240, 255, 0)");
            grad.addColorStop(0.5, "rgba(0, 240, 255, 0.95)");
            grad.addColorStop(1, "rgba(0, 240, 255, 0)");

            ctx.save();
            ctx.strokeStyle = grad;
            ctx.lineWidth = 2;
            ctx.shadowColor = "#00f0ff";
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.moveTo(cx - lineHalfW, lineY);
            ctx.lineTo(cx + lineHalfW, lineY);
            ctx.stroke();
            ctx.restore();

            // Subtitle: READY
            ctx.font = `600 ${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
            ctx.fillStyle = `rgba(0, 240, 255, ${0.9 * snapRatio})`;
            ctx.fillText("READY", cx, lineY + (isMobile ? 20 : 26));
          }
        }

        // ====================================================================
        // PHASE 6: 3.3s – 3.6s: HOLD
        // Hold the clean Wifisense mark and READY for ~300ms. Stable, complete.
        // ====================================================================
        else if (t >= 3.3 && t < 3.6) {
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";

          // Pristine glowing wordmark
          const fontSize = isMobile ? 42 : 64;
          ctx.font = `800 ${fontSize}px 'Inter', sans-serif`;

          ctx.save();
          ctx.shadowColor = "rgba(0, 240, 255, 0.95)";
          ctx.shadowBlur = isMobile ? 20 : 34;
          ctx.fillStyle = "#ffffff";
          ctx.fillText("WIFISENSE", cx, cy - 12);
          ctx.restore();

          // Laser line
          const lineY = cy + (isMobile ? 22 : 30);
          const lineHalfW = isMobile ? 65 : 110;
          const grad = ctx.createLinearGradient(cx - lineHalfW, lineY, cx + lineHalfW, lineY);
          grad.addColorStop(0, "rgba(0, 240, 255, 0)");
          grad.addColorStop(0.5, "rgba(0, 240, 255, 0.95)");
          grad.addColorStop(1, "rgba(0, 240, 255, 0)");

          ctx.save();
          ctx.strokeStyle = grad;
          ctx.lineWidth = 2;
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 10;
          ctx.beginPath();
          ctx.moveTo(cx - lineHalfW, lineY);
          ctx.lineTo(cx + lineHalfW, lineY);
          ctx.stroke();
          ctx.restore();

          // Subtitle: READY
          ctx.font = `600 ${isMobile ? 11 : 13}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = "rgba(0, 240, 255, 0.95)";
          ctx.fillText("READY", cx, lineY + (isMobile ? 20 : 26));
        }

        // ====================================================================
        // PHASE 7: 3.6s – 4.0s: ENTERING WIFISENSE
        // Radial signal warp streaks bursting outward + ENTERING WIFISENSE
        // Transitions directly into existing landing page
        // ====================================================================
        else if (t >= 3.6) {
          const p7Ratio = Math.min(1, (t - 3.6) / 0.4);

          // Radial warp light streaks
          streaks.forEach((st) => {
            st.dist += st.speed * (1 + p7Ratio * 3.2);
            const x1 = cx + Math.cos(st.angle) * st.dist;
            const y1 = cy + Math.sin(st.angle) * st.dist;
            const curLen = st.length * (1 + p7Ratio * 2.4);
            const x2 = cx + Math.cos(st.angle) * (st.dist + curLen);
            const y2 = cy + Math.sin(st.angle) * (st.dist + curLen);

            ctx.save();
            ctx.strokeStyle = st.color;
            ctx.lineWidth = isMobile ? 1.5 : 2.5;
            ctx.shadowColor = st.color;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
            ctx.restore();
          });

          // Center Text: ENTERING WIFISENSE
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";

          ctx.save();
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = 20;

          ctx.font = `600 ${isMobile ? 12 : 16}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
          ctx.fillText("ENTERING", cx, cy - (isMobile ? 14 : 18));

          ctx.font = `800 ${isMobile ? 24 : 34}px 'Inter', sans-serif`;
          ctx.fillStyle = "#ffffff";
          ctx.fillText("WIFISENSE", cx, cy + (isMobile ? 16 : 20));
          ctx.restore();
        }

        // Check for sequence completion
        if (elapsed >= TOTAL_DURATION) {
          if (!completed) {
            completed = true;
            if (onCompleteRef.current) onCompleteRef.current();
          }
          return;
        }

        animationFrameId = requestAnimationFrame(render);
      } catch (err) {
        console.error("[LoadingScreen] Error in animation frame:", err);
        if (!completed) {
          completed = true;
          if (onCompleteRef.current) onCompleteRef.current();
        }
      }
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      clearTimeout(safetyTimer);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []); // Run ONCE on mount

  // Reduced motion accessible fallback
  if (isReducedMotion) {
    return (
      <div 
        ref={containerRef}
        className={`fixed inset-0 z-50 bg-[#030509] flex flex-col items-center justify-center text-white transition-opacity duration-300 ${
          isFadingOut ? "opacity-0 pointer-events-none" : "opacity-100"
        }`}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-white flex items-center justify-center rounded-sm">
            <span className="material-symbols-outlined text-[#030509] text-2xl font-black">sensors</span>
          </div>
          <span className="text-3xl font-bold tracking-tight">Wifisense</span>
        </div>
        <p className="text-xs font-mono text-cyan-400 tracking-widest uppercase">ENTERING WIFISENSE...</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      role="status"
      aria-label="Loading Wi-Fi Sense"
      className={`fixed inset-0 z-50 overflow-hidden bg-[#030509] pointer-events-auto transition-opacity duration-350 ease-out ${
        isFadingOut ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      style={{ willChange: "opacity" }}
    >
      <canvas
        ref={canvasRef}
        className="block w-full h-full"
      />
    </div>
  );
}
