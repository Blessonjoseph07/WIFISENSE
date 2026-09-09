import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

/**
 * WifiModemVisualizer - Clean, Subtle Architectural Light Theme
 * Interactive 3D WebGL scene showcasing a modern pearl-white/metallic Wi-Fi modem
 * emitting delicate, ethereal concentric RF sensing domes on an architectural floor grid.
 */
export default function WifiModemVisualizer() {
  const mountRef = useRef(null);
  const [pulseRate, setPulseRate] = useState(1.0);
  const [activeFmt, setActiveFmt] = useState("5GHz");
  const [telemetry, setTelemetry] = useState({
    rssi: -52,
    packets: 1420,
    variance: 4.82,
    presence: "DETECTED"
  });

  const pulseRateRef = useRef(pulseRate);
  useEffect(() => {
    pulseRateRef.current = pulseRate;
  }, [pulseRate]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // --- SCENE & RENDERER SETUP (Light, Ethereal Atmosphere) ---
    const width = container.clientWidth || 500;
    const height = container.clientHeight || 600;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc); // Clean off-white
    scene.fog = new THREE.FogExp2(0xf8fafc, 0.022);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(13, 10.5, 15);
    camera.lookAt(0, 1.6, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    container.appendChild(renderer.domElement);

    // --- LIGHTING (Soft, Natural Studio Lighting) ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xf0f9ff, 2.4);
    keyLight.position.set(12, 22, 14);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xe0f2fe, 1.2);
    fillLight.position.set(-10, 12, -10);
    scene.add(fillLight);

    // Soft sky-blue glow near modem
    const modemGlow = new THREE.PointLight(0x0ea5e9, 2.8, 16);
    modemGlow.position.set(0, 1.2, 0);
    scene.add(modemGlow);

    // --- ARCHITECTURAL 3D FLOOR (Subtle Slate/Cyan Matrix Grid) ---
    const floorGroup = new THREE.Group();

    // Soft porcelain floor plane
    const planeGeo = new THREE.PlaneGeometry(24, 24);
    const planeMat = new THREE.MeshStandardMaterial({
      color: 0xf1f5f9,
      roughness: 0.95,
      metalness: 0.05
    });
    const floorPlane = new THREE.Mesh(planeGeo, planeMat);
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = -0.01;
    floorGroup.add(floorPlane);

    // Delicate grid lines
    const gridHelper = new THREE.GridHelper(24, 24, 0x38bdf8, 0xcfdbe8);
    gridHelper.position.y = 0.005;
    gridHelper.material.opacity = 0.55;
    gridHelper.material.transparent = true;
    floorGroup.add(gridHelper);

    // Subtle cyan/emerald intersection dots
    const dotsCount = 25 * 25;
    const dotPositions = new Float32Array(dotsCount * 3);
    let dotIdx = 0;
    const step = 24 / 24;
    for (let x = -12; x <= 12; x += step) {
      for (let z = -12; z <= 12; z += step) {
        dotPositions[dotIdx * 3] = x;
        dotPositions[dotIdx * 3 + 1] = 0.015;
        dotPositions[dotIdx * 3 + 2] = z;
        dotIdx++;
      }
    }
    const dotsGeo = new THREE.BufferGeometry();
    dotsGeo.setAttribute("position", new THREE.BufferAttribute(dotPositions, 3));
    const dotsMat = new THREE.PointsMaterial({
      color: 0x0284c7, // Refined sky blue
      size: 0.09,
      transparent: true,
      opacity: 0.55
    });
    const floorDots = new THREE.Points(dotsGeo, dotsMat);
    floorGroup.add(floorDots);

    // Subtle perimeter frame
    const boxFrameGeo = new THREE.BoxGeometry(24, 8, 24);
    const boxFrameEdges = new THREE.EdgesGeometry(boxFrameGeo);
    const boxFrameMat = new THREE.LineBasicMaterial({
      color: 0x94a3b8,
      transparent: true,
      opacity: 0.22
    });
    const boxFrame = new THREE.LineSegments(boxFrameEdges, boxFrameMat);
    boxFrame.position.y = 4;
    floorGroup.add(boxFrame);

    scene.add(floorGroup);

    // --- SLEEK PEARL-WHITE / METALLIC ROUTER MODEM ---
    const routerGroup = new THREE.Group();

    // Main router body (matte pearl-white/silver finish)
    const routerBodyGeo = new THREE.BoxGeometry(2.4, 0.5, 1.8);
    const routerBodyMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.28,
      metalness: 0.2
    });
    const routerBody = new THREE.Mesh(routerBodyGeo, routerBodyMat);
    routerBody.position.y = 0.25;
    routerGroup.add(routerBody);

    // Top brushed aluminum accent plate
    const topPlateGeo = new THREE.BoxGeometry(2.1, 0.08, 1.5);
    const topPlateMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      roughness: 0.2,
      metalness: 0.8
    });
    const topPlate = new THREE.Mesh(topPlateGeo, topPlateMat);
    topPlate.position.y = 0.52;
    routerGroup.add(topPlate);

    // Router base shadow plate
    const basePlateGeo = new THREE.BoxGeometry(2.5, 0.04, 1.9);
    const basePlateMat = new THREE.MeshBasicMaterial({ color: 0xcfdbe8 });
    const basePlate = new THREE.Mesh(basePlateGeo, basePlateMat);
    basePlate.position.y = 0.02;
    routerGroup.add(basePlate);

    // Subtle front status LEDs (Soft cyan, teal, blue)
    const leds = [];
    const ledColors = [0x0284c7, 0x10b981, 0x06b6d4, 0x10b981];
    for (let i = 0; i < 4; i++) {
      const ledGeo = new THREE.SphereGeometry(0.035, 8, 8);
      const ledMat = new THREE.MeshBasicMaterial({ color: ledColors[i] });
      const led = new THREE.Mesh(ledGeo, ledMat);
      led.position.set(-0.55 + i * 0.36, 0.26, 0.91);
      routerGroup.add(led);
      leds.push(led);
    }

    // 4 Metallic Brushed Antennas
    const antGeo = new THREE.CylinderGeometry(0.038, 0.038, 1.7, 12);
    const antMat = new THREE.MeshStandardMaterial({
      color: 0x94a3b8,
      metalness: 0.85,
      roughness: 0.25
    });
    const antPositions = [
      { x: -0.95, z: -0.75, rotZ: 0.22, rotX: -0.18 },
      { x: -0.32, z: -0.85, rotZ: 0.07, rotX: -0.25 },
      { x: 0.32, z: -0.85, rotZ: -0.07, rotX: -0.25 },
      { x: 0.95, z: -0.75, rotZ: -0.22, rotX: -0.18 }
    ];

    antPositions.forEach((pos) => {
      const antenna = new THREE.Mesh(antGeo, antMat);
      antenna.position.set(pos.x, 1.15, pos.z);
      antenna.rotation.z = pos.rotZ;
      antenna.rotation.x = pos.rotX;
      routerGroup.add(antenna);
    });

    scene.add(routerGroup);

    // --- SUBTLE CONCENTRIC WIREFRAME SIGNAL DOMES (Refined & Elegant) ---
    // Multiple concentric hemispheres with fine sky-blue wireframe lines and gentle opacity
    const DOME_COUNT = 4;
    const domes = [];
    const maxRadius = 10.2;
    const minRadius = 1.3;

    for (let i = 0; i < DOME_COUNT; i++) {
      // Hemisphere (phiLength = 2PI, thetaLength = PI/2)
      const domeGeo = new THREE.SphereGeometry(1, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2);
      
      // Delicate sky-blue wireframe material
      const domeMat = new THREE.MeshBasicMaterial({
        color: 0x0284c7, // Refined sky/cyan blue
        wireframe: true,
        transparent: true,
        opacity: 0.45,
        depthWrite: false,
        blending: THREE.NormalBlending
      });
      const domeMesh = new THREE.Mesh(domeGeo, domeMat);
      domeMesh.position.set(0, 0.01, 0);

      // Very soft translucent inner shell for delicate glass/RF aura
      const glowGeo = new THREE.SphereGeometry(0.995, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
      const glowMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.035,
        side: THREE.BackSide,
        depthWrite: false
      });
      const glowMesh = new THREE.Mesh(glowGeo, glowMat);
      domeMesh.add(glowMesh);

      scene.add(domeMesh);
      domes.push({
        mesh: domeMesh,
        glowMesh,
        phase: i / DOME_COUNT
      });
    }

    // --- FLOATING CSI MICRO-PACKETS ---
    const packetCount = 75;
    const packetPositions = new Float32Array(packetCount * 3);
    const packetVelocities = [];

    for (let i = 0; i < packetCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = 1.4 + Math.random() * 8.0;
      packetPositions[i * 3] = Math.cos(angle) * dist;
      packetPositions[i * 3 + 1] = 0.2 + Math.random() * 6.0;
      packetPositions[i * 3 + 2] = Math.sin(angle) * dist;

      packetVelocities.push({
        y: 0.007 + Math.random() * 0.012,
        speed: 0.02 + Math.random() * 0.02,
        angle: angle
      });
    }

    const packetGeo = new THREE.BufferGeometry();
    packetGeo.setAttribute("position", new THREE.BufferAttribute(packetPositions, 3));
    const packetMat = new THREE.PointsMaterial({
      color: 0x0284c7,
      size: 0.12,
      transparent: true,
      opacity: 0.6
    });
    const packetCloud = new THREE.Points(packetGeo, packetMat);
    scene.add(packetCloud);

    // --- MOUSE PARALLAX & SMOOTH ORBIT ---
    let mouseX = 0;
    let mouseY = 0;
    let targetCameraX = 13;
    let targetCameraY = 10.5;
    let targetCameraZ = 15;

    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseX = x;
      mouseY = y;
    };

    container.addEventListener("mousemove", handleMouseMove);

    // --- RESIZE LISTENER ---
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };
    window.addEventListener("resize", handleResize);

    // --- ANIMATION LOOP ---
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const time = clock.getElapsedTime() * pulseRateRef.current;

      // 1. Subtle, smooth dome propagation
      domes.forEach((dome) => {
        dome.phase = (dome.phase + delta * 0.28 * pulseRateRef.current) % 1.0;
        const currentScale = minRadius + dome.phase * (maxRadius - minRadius);
        dome.mesh.scale.set(currentScale, currentScale, currentScale);

        // Smooth sinusoidal fade-in and graceful fade-out
        const fade = Math.sin(dome.phase * Math.PI);
        dome.mesh.material.opacity = fade * 0.48;
        dome.glowMesh.material.opacity = fade * 0.045;

        // Soft sky blue with delicate tinting
        const lightness = 0.42 + (1.0 - dome.phase) * 0.12;
        dome.mesh.material.color.setHSL(0.57, 0.85, lightness);
      });

      // 2. Soft status LED blinking
      leds.forEach((led, idx) => {
        const blink = Math.sin(time * 7 + idx * 2.2) > 0.15;
        led.material.opacity = blink ? 1.0 : 0.3;
      });

      // 3. Gentle packet drift
      const positions = packetCloud.geometry.attributes.position.array;
      for (let i = 0; i < packetCount; i++) {
        positions[i * 3 + 1] += packetVelocities[i].y * pulseRateRef.current;
        if (positions[i * 3 + 1] > 7.5) {
          positions[i * 3 + 1] = 0.2;
        }
      }
      packetCloud.geometry.attributes.position.needsUpdate = true;

      // 4. Autonomous gentle orbit with responsive mouse parallax
      const autoAngle = time * 0.09;
      const baseRadius = 17.5;
      targetCameraX = Math.cos(autoAngle) * baseRadius + mouseX * 3.5;
      targetCameraZ = Math.sin(autoAngle) * baseRadius + mouseX * 2.0;
      targetCameraY = 9.5 + mouseY * 2.5;

      camera.position.x += (targetCameraX - camera.position.x) * 0.035;
      camera.position.y += (targetCameraY - camera.position.y) * 0.035;
      camera.position.z += (targetCameraZ - camera.position.z) * 0.035;
      camera.lookAt(0, 1.6, 0);

      renderer.render(scene, camera);
    };

    animate();

    // Telemetry ticker
    const telemetryInterval = setInterval(() => {
      setTelemetry((prev) => ({
        rssi: -48 - Math.floor(Math.random() * 5),
        packets: prev.packets + Math.floor(75 + Math.random() * 35),
        variance: +(4.2 + Math.random() * 0.7).toFixed(2),
        presence: "ACTIVE STANCE"
      }));
    }, 1400);

    // CLEANUP
    return () => {
      clearInterval(telemetryInterval);
      window.removeEventListener("resize", handleResize);
      container.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);

      renderer.dispose();
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="relative w-full h-full min-h-[480px] overflow-hidden rounded-2xl bg-slate-50/80 border border-slate-200/90 shadow-sm flex flex-col justify-between">
      {/* 3D WebGL Canvas Mount */}
      <div ref={mountRef} className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* TOP HUD BAR: Clean Light Glassmorphic Overlay */}
      <div className="relative z-10 p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        <div className="flex items-center gap-2.5 bg-white/85 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-200/80 shadow-xs pointer-events-auto">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-sky-500"></span>
          </span>
          <div className="flex flex-col text-left">
            <span className="text-[10px] font-mono tracking-wider text-sky-600 font-bold uppercase">
              CSI Signal Propagation
            </span>
            <span className="text-xs font-semibold text-slate-800">
              Wi-Fi 6 Continuous Sensing
            </span>
          </div>
        </div>

        {/* Freq & Bandwidth Selector */}
        <div className="flex items-center gap-1 bg-white/85 backdrop-blur-md p-1 rounded-xl border border-slate-200/80 shadow-xs pointer-events-auto text-[11px]">
          <button
            type="button"
            onClick={() => setActiveFmt("5GHz")}
            className={`px-2.5 py-1 rounded-lg font-mono font-medium transition-all ${
              activeFmt === "5GHz"
                ? "bg-sky-50 text-sky-700 border border-sky-200 font-semibold shadow-2xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            5.18 GHz (Ch 36)
          </button>
          <button
            type="button"
            onClick={() => setActiveFmt("2.4GHz")}
            className={`px-2.5 py-1 rounded-lg font-mono font-medium transition-all ${
              activeFmt === "2.4GHz"
                ? "bg-sky-50 text-sky-700 border border-sky-200 font-semibold shadow-2xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            2.4 GHz (Ch 6)
          </button>
        </div>
      </div>

      {/* FLOATING RF TELEMETRY CARDS (Light, Delicate Theme) */}
      <div className="relative z-10 px-4 sm:p-5 pointer-events-none flex justify-between items-end">
        {/* Live CSI metrics box */}
        <div className="bg-white/90 backdrop-blur-md p-3.5 rounded-xl border border-slate-200/80 max-w-[210px] text-left shadow-sm pointer-events-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
              Channel State
            </span>
            <span className="text-[10px] font-mono text-emerald-700 font-semibold px-1.5 py-0.5 bg-emerald-50 rounded border border-emerald-200">
              64 OFDM
            </span>
          </div>
          <div className="space-y-1 font-mono text-xs">
            <div className="flex justify-between text-slate-700">
              <span className="text-slate-400">Signal RSSI:</span>
              <span className="text-sky-600 font-semibold">{telemetry.rssi} dBm</span>
            </div>
            <div className="flex justify-between text-slate-700">
              <span className="text-slate-400">Variance:</span>
              <span className="text-sky-600 font-semibold">{telemetry.variance}</span>
            </div>
            <div className="flex justify-between text-slate-700">
              <span className="text-slate-400">CSI Frames:</span>
              <span className="text-emerald-600 font-semibold">{telemetry.packets}</span>
            </div>
          </div>
        </div>

        {/* Real-time Subcarrier Waveform simulation bars */}
        <div className="hidden sm:flex flex-col bg-white/90 backdrop-blur-md p-3 rounded-xl border border-slate-200/80 shadow-sm pointer-events-auto">
          <div className="flex items-center justify-between gap-4 mb-2">
            <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Subcarriers</span>
            <span className="text-[10px] font-mono text-sky-600 font-medium">80 MHz</span>
          </div>
          <div className="flex items-end gap-1 h-11 w-32 px-1">
            {[45, 65, 80, 50, 90, 70, 40, 85, 95, 60, 75, 55, 88, 72].map((h, i) => (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-sky-400 via-sky-500 to-teal-400 rounded-t-xs transition-all duration-300"
                style={{
                  height: `${Math.max(15, (h + ((telemetry.packets + i * 7) % 35)) % 100)}%`,
                  opacity: 0.75
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* BOTTOM CONTROLS & CAPTION (Clean Light Theme) */}
      <div className="relative z-10 p-4 sm:p-5 pt-3 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-t from-slate-50/95 via-slate-50/80 to-transparent">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-500 font-medium">Emission Rate:</span>
          {[0.5, 1.0, 1.8].map((rate) => (
            <button
              key={rate}
              type="button"
              onClick={() => setPulseRate(rate)}
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-mono font-medium transition-all ${
                pulseRate === rate
                  ? "bg-sky-500 text-white shadow-xs font-semibold"
                  : "bg-white text-slate-600 hover:text-slate-900 border border-slate-200 shadow-2xs"
              }`}
            >
              {rate}x
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-slate-500 text-xs">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-sky-500"></span>
          <span className="font-mono text-[11px] text-slate-500">Interactive 3D • Drag to Orbit</span>
        </div>
      </div>
    </div>
  );
}
