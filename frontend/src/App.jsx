import React, { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

// Live Canvas CSI Waveform Visualizer
function CSIWaveform({ activity }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animationId;
    let offset = 0;

    let speed = 0.05;
    let amplitude = 20;
    let noiseLevel = 3;
    let color = "#86f2e4"; 

    if (activity === "Walking") {
      speed = 0.18;
      amplitude = 35;
      noiseLevel = 8;
      color = "#3B82F6"; 
    } else if (activity === "Sitting") {
      speed = 0.03;
      amplitude = 12;
      noiseLevel = 1.5;
      color = "#10B981"; 
    } else if (activity === "Fall_Detected") {
      speed = 0.25;
      amplitude = 65;
      noiseLevel = 12;
      color = "#ba1a1a"; 
    } else if (activity === "Empty") {
      speed = 0.01;
      amplitude = 4;
      noiseLevel = 0.5;
      color = "#9CA3AF"; 
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2;
      ctx.strokeStyle = color;
      
      // Draw Grid Lines
      ctx.strokeStyle = "rgba(118, 119, 125, 0.08)";
      ctx.lineWidth = 1;
      for (let i = 20; i < canvas.width; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
      }
      for (let j = 15; j < canvas.height; j += 30) {
        ctx.beginPath();
        ctx.moveTo(0, j);
        ctx.lineTo(canvas.width, j);
        ctx.stroke();
      }

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      const midY = canvas.height / 2;
      ctx.moveTo(0, midY);

      for (let x = 0; x < canvas.width; x++) {
        const sinVal = Math.sin(x * 0.04 + offset);
        const cosVal = Math.cos(x * 0.015 - offset * 0.5);
        const noise = (Math.random() - 0.5) * noiseLevel;
        let y = midY + sinVal * cosVal * amplitude + noise;
        
        if (activity === "Fall_Detected" && x > canvas.width * 0.6) {
          y = midY + (Math.sin(x * 0.1) * 8) + (Math.random() - 0.5) * 2;
        }
        ctx.lineTo(x, y);
      }
      ctx.stroke();
      
      offset += speed;
      animationId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animationId);
  }, [activity]);

  return (
    <div className="relative w-full bg-surface-container dark:bg-slate-900 border dark:border-slate-800 rounded-xl p-4 overflow-hidden shadow-inner">
      <div className="flex justify-between items-center mb-2 z-10 relative">
        <span className="text-[10px] text-outline font-bold uppercase tracking-wider">CSI Amplitude Matrix Subcarriers</span>
        <span className="flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-surface-bright dark:bg-slate-800 border dark:border-slate-700">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-ping"></span>
          Live Feed: {activity}
        </span>
      </div>
      <canvas ref={canvasRef} className="w-full h-28" width={500} height={112} />
    </div>
  );
}

export default function App() {
  // Authentication State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  
  // Navigation State
  const [currentView, setCurrentView] = useState("dashboard");
  const [dashboardTab, setDashboardTab] = useState("assets"); // 'assets', 'telemetry'
  
  // Multi-tenant Org Scope Switcher
  const [orgScope, setOrgScope] = useState("all"); 

  // System Dark/Light Mode state
  const [darkMode, setDarkMode] = useState(false);

  // Asset Collections (Loaded from Real APIs)
  const [organizations, setOrganizations] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [floors, setFloors] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [devices, setDevices] = useState([]);
  const [residents, setResidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
  // Collapsible Buildings state inside Facility Hierarchy widget
  const [expandedBuildings, setExpandedBuildings] = useState({});

  // Selected visual active telemetry activity
  const [activeTelemetryActivity, setActiveTelemetryActivity] = useState("Empty");

  // Analytics Aggregates
  const [occupancySummary, setOccupancySummary] = useState({
    total_rooms: 0,
    occupied_rooms: 0,
    vacant_rooms: 0,
    occupancy_rate: 0,
    occupied_room_details: []
  });
  const [alertSummary, setAlertSummary] = useState({
    total_alerts: 0,
    status_counts: { new: 0, acknowledged: 0, resolved: 0 },
    severity_counts: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
  });

  // Modal Open States
  const [showSimulateDrawer, setShowSimulateDrawer] = useState(false);
  const [showAddOrgModal, setShowAddOrgModal] = useState(false);
  const [showAddBuildingModal, setShowAddBuildingModal] = useState(false);
  const [showAddFloorModal, setShowAddFloorModal] = useState(false);
  const [showAddRoomModal, setShowAddRoomModal] = useState(false);
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [showAddResidentModal, setShowAddResidentModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(null); 

  // Form Input States
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regFirst, setRegFirst] = useState("");
  const [regLast, setRegLast] = useState("");
  const [regRole, setRegRole] = useState("caregiver");
  const [isRegistering, setIsRegistering] = useState(false);

  // Asset Creation Inputs
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgType, setNewOrgType] = useState("ELDER_CARE");

  const [newBldOrgId, setNewBldOrgId] = useState("");
  const [newBldName, setNewBldName] = useState("");
  const [newBldAddress, setNewBldAddress] = useState("");

  const [newFlrBldId, setNewFlrBldId] = useState("");
  const [newFlrNum, setNewFlrNum] = useState(1);

  const [newRmFlrId, setNewRmFlrId] = useState("");
  const [newRmName, setNewRmName] = useState("");
  const [newRmType, setNewRmType] = useState("Resident Bedroom");
  const [newRmCapacity, setNewRmCapacity] = useState(1);

  const [newDevRmId, setNewDevRmId] = useState("");
  const [newDevMac, setNewDevMac] = useState("");
  const [newDevFirmware, setNewDevFirmware] = useState("v1.0.0");

  const [newResRmId, setNewResRmId] = useState("");
  const [newResFirst, setNewResFirst] = useState("");
  const [newResLast, setNewResLast] = useState("");

  // Simulation Inputs
  const [simDeviceId, setSimDeviceId] = useState("");
  const [simActivity, setSimActivity] = useState("Walking");

  // Alert Resolution Inputs
  const [resolutionNotes, setResolutionNotes] = useState("");

  // Global Notification Banner
  const [activeFallAlert, setActiveFallAlert] = useState(null);

  // Toast Notification Message
  const [toastMessage, setToastMessage] = useState(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  const getHeaders = () => {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
  };

  // ============================================================================
  // LOAD DATA & AUTO FILTERING
  // ============================================================================
  const fetchAllData = async () => {
    if (!token) return;
    try {
      const headers = getHeaders();

      // 1. Fetch Analytics Summary
      const occRes = await fetch(`${API_BASE}/analytics/occupancy-summary`, { headers });
      if (occRes.ok) {
        const data = await occRes.json();
        
        let filteredDetails = data.occupied_room_details;
        if (orgScope === "ajce") {
          filteredDetails = filteredDetails.filter(rm => rm.room_name === "MCA Lab" || rm.room_name === "Seminar Hall");
        } else if (orgScope === "lab") {
          filteredDetails = filteredDetails.filter(rm => rm.room_name !== "MCA Lab" && rm.room_name !== "Seminar Hall");
        }

        const totalFiltered = filteredDetails.length;
        const occupiedCount = filteredDetails.filter(rm => rm.is_occupied).length;
        const vacantCount = totalFiltered - occupiedCount;
        const rate = totalFiltered > 0 ? (occupiedCount / totalFiltered * 100) : 0;

        setOccupancySummary({
          total_rooms: totalFiltered,
          occupied_rooms: occupiedCount,
          vacant_rooms: vacantCount,
          occupancy_rate: Math.round(rate),
          occupied_room_details: filteredDetails
        });

        const criticalRoom = filteredDetails.find(rm => rm.current_activity === "Fall_Detected");
        const activeRoom = filteredDetails.find(rm => rm.is_occupied && rm.current_activity !== "Empty");
        
        if (criticalRoom) {
          setActiveTelemetryActivity("Fall_Detected");
        } else if (activeRoom) {
          setActiveTelemetryActivity(activeRoom.current_activity);
        } else {
          setActiveTelemetryActivity("Empty");
        }
      }

      // 2. Fetch Alerts List
      const alertRes = await fetch(`${API_BASE}/alerts`, { headers });
      if (alertRes.ok) {
        let alertData = await alertRes.json();
        if (orgScope === "ajce") {
          alertData = [];
        } else if (orgScope === "lab") {
          alertData = alertData.filter(a => {
            const rm = rooms.find(r => r.id === a.room_id);
            return rm && rm.name !== "MCA Lab" && rm.name !== "Seminar Hall";
          });
        }
        setAlerts(alertData);
        const activeFall = alertData.find(a => a.event_type === "Fall_Detected" && a.status !== "resolved");
        setActiveFallAlert(activeFall || null);
      }

      // 3. Fetch Asset Lists
      const orgRes = await fetch(`${API_BASE}/organizations`, { headers });
      if (orgRes.ok) {
        const orgData = await orgRes.json();
        setOrganizations(orgScope === "all" ? orgData : orgData.filter(o => {
          return orgScope === "ajce" ? o.name.includes("Amal Jyothi") : o.name.includes("Research Lab");
        }));
      }

      const bldRes = await fetch(`${API_BASE}/buildings`, { headers });
      if (bldRes.ok) {
        const bldData = await bldRes.json();
        setBuildings(orgScope === "all" ? bldData : bldData.filter(b => {
          return orgScope === "ajce" ? b.name.includes("MCA") : b.name.includes("Research");
        }));
      }

      const flrRes = await fetch(`${API_BASE}/floors`, { headers });
      if (flrRes.ok) setFloors(await flrRes.json());

      const rmRes = await fetch(`${API_BASE}/rooms`, { headers });
      if (rmRes.ok) setRooms(await rmRes.json());

      const devRes = await fetch(`${API_BASE}/devices`, { headers });
      if (devRes.ok) setDevices(await devRes.json());

      const resRes = await fetch(`${API_BASE}/residents`, { headers });
      if (resRes.ok) setResidents(await resRes.json());

    } catch (err) {
      console.error("Sync telemetry error: ", err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchAllData();
      const interval = setInterval(fetchAllData, 3000);
      return () => clearInterval(interval);
    }
  }, [token, orgScope]);

  useEffect(() => {
    if (orgScope === "ajce") {
      setLoginEmail("abhinand@wifisense.com");
      setLoginPassword("abhinandpassword");
    } else if (orgScope === "lab") {
      setLoginEmail("abhinanth@wifisense.com");
      setLoginPassword("abhinanthpassword");
    } else {
      setLoginEmail("blesson@wifisense.com");
      setLoginPassword("blessonpassword");
    }
  }, [orgScope]);

  // ============================================================================
  // AUTHENTICATION LOGIC
  // ============================================================================
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Authentication failed.");
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("role", data.role);
      
      setToken(data.access_token);
      setUser(data.user);
      setRole(data.role);
      setCurrentView("dashboard");
      setToastMessage({ type: "success", text: `Logged in successfully as ${data.user.first_name}` });
    } catch (err) {
      setLoginError(err.message);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: regEmail,
          password: regPassword,
          first_name: regFirst,
          last_name: regLast,
          role: regRole
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Registration failed.");
      }
      setIsRegistering(false);
      setLoginEmail(regEmail);
      setToastMessage({ type: "success", text: "Registered successfully! Please login." });
    } catch (err) {
      setLoginError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("role");
    setToken("");
    setUser(null);
    setRole("");
    setCurrentView("dashboard");
  };

  // ============================================================================
  // SIMULATION EVENTS INGESTION
  // ============================================================================
  const runSimulation = async (e) => {
    e.preventDefault();
    if (!simDeviceId) {
      alert("Please select a device node.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/sensing/simulate-event`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          device_id: simDeviceId,
          simulated_activity: simActivity
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Simulation pipeline failed.");
      }
      const data = await res.json();
      setShowSimulateDrawer(false);
      fetchAllData();
      
      setToastMessage({
        type: data.alert_triggered ? "error" : "success",
        text: `Simulation success! Status: ${data.activity_classified} (${data.presence_detected ? "Occupied" : "Empty"})`
      });
    } catch (err) {
      alert(err.message);
    }
  };

  // ============================================================================
  // ALERT ACK/RESOLVE LIFECYCLE ACTIONS
  // ============================================================================
  const handleAcknowledge = async (alertId) => {
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: "PATCH",
        headers: getHeaders()
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Acknowledgment failed.");
      }
      fetchAllData();
      setToastMessage({ type: "success", text: "Alert status updated: Acknowledged" });
    } catch (err) {
      alert(err.message);
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!showResolveModal) return;
    try {
      const res = await fetch(`${API_BASE}/alerts/${showResolveModal}/resolve`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify({ resolution_notes: resolutionNotes })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Resolution failed.");
      }
      setShowResolveModal(null);
      setResolutionNotes("");
      fetchAllData();
      setToastMessage({ type: "success", text: "Alert cleared and resolved" });
    } catch (err) {
      alert(err.message);
    }
  };

  // ============================================================================
  // INFRASTRUCTURE ADD HANDLERS
  // ============================================================================
  const addOrganization = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/organizations`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ name: newOrgName, type: newOrgType })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create organization.");
      }
      setNewOrgName("");
      setShowAddOrgModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "Organization registered successfully." });
    } catch (err) {
      alert(err.message);
    }
  };

  const addBuilding = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/buildings`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          organization_id: newBldOrgId,
          name: newBldName,
          address: newBldAddress
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create building.");
      }
      setNewBldName("");
      setNewBldAddress("");
      setShowAddBuildingModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "Building registered successfully." });
    } catch (err) {
      alert(err.message);
    }
  };

  const addFloor = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/floors`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          building_id: newFlrBldId,
          floor_number: parseInt(newFlrNum)
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create floor.");
      }
      setShowAddFloorModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "Floor added successfully." });
    } catch (err) {
      alert(err.message);
    }
  };

  const addRoom = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/rooms`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          floor_id: newRmFlrId,
          name: newRmName,
          room_type: newRmType,
          capacity: parseInt(newRmCapacity)
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create room.");
      }
      setNewRmName("");
      setShowAddRoomModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "Room added successfully." });
    } catch (err) {
      alert(err.message);
    }
  };

  const addDevice = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/devices`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          room_id: newDevRmId || null,
          mac_address: newDevMac,
          firmware_version: newDevFirmware
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to register device.");
      }
      setNewDevMac("");
      setShowAddDeviceModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "ESP32 Device Node registered." });
    } catch (err) {
      alert(err.message);
    }
  };

  const addResident = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/residents`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          room_id: newResRmId,
          first_name: newResFirst,
          last_name: newResLast
        })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create resident.");
      }
      setNewResFirst("");
      setNewResLast("");
      setShowAddResidentModal(false);
      fetchAllData();
      setToastMessage({ type: "success", text: "Resident record added." });
    } catch (err) {
      alert(err.message);
    }
  };

  // Facility Expand All / Collapse All Hierarchy toggle
  const toggleBuildingExpand = (bldId) => {
    setExpandedBuildings(prev => ({
      ...prev,
      [bldId]: !prev[bldId]
    }));
  };

  const expandAllBuildings = () => {
    const nextState = {};
    buildings.forEach(b => {
      nextState[b.id] = true;
    });
    setExpandedBuildings(nextState);
  };

  const triggerEmergencyProtocol = () => {
    setToastMessage({
      type: "error",
      text: "EMERGENCY PROTOCOL ACTIVATED: Dispatched local responders to research wings."
    });
  };

  // ============================================================================
  // OUT OF BOX VIEW (LOGIN)
  // ============================================================================
  if (!token) {
    return (
      <div className="bg-surface dark:bg-slate-950 text-on-surface font-body-md antialiased min-h-screen flex flex-col md:flex-row transition-all duration-300">
        {/* Banner Panel */}
        <div className="hidden md:flex flex-col w-[45%] bg-slate-100 dark:bg-slate-900 relative overflow-hidden p-container-padding justify-between border-r border-outline-variant dark:border-slate-800">
          <div className="absolute inset-0 bg-wave-pattern opacity-60 dark:opacity-40 z-0"></div>
          <div className="z-10 mt-8 ml-8">
            <div className="flex items-center gap-stack-sm mb-4">
              <span className="material-symbols-outlined text-secondary" style={{ fontSize: "36px" }}>sensors</span>
              <span className="font-headline-md text-headline-md text-primary dark:text-slate-100">Wi-Fi Sense</span>
            </div>
            <p className="font-headline-sm text-headline-sm text-on-surface-variant dark:text-slate-300 max-w-sm mt-4">
              AI-Powered Indoor Human Sensing and Fall Tracking via Wi-Fi CSI.
            </p>
          </div>
          <div className="z-10 mb-8 ml-8">
            <div className="inline-flex items-center gap-2 bg-surface-container-highest dark:bg-slate-800 px-4 py-2 rounded-full border border-outline-variant dark:border-slate-700">
              <span className="material-symbols-outlined text-secondary" style={{ fontSize: "16px" }}>check_circle</span>
              <span className="font-label-caps text-label-caps text-on-surface dark:text-slate-200">System: Seed Data Ready</span>
            </div>
          </div>
        </div>

        {/* Login Panel */}
        <div className="flex-1 flex flex-col justify-center p-gutter relative bg-surface-container-lowest dark:bg-slate-950">
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-surface-container dark:bg-slate-900 px-3 py-1.5 rounded-full border dark:border-slate-800">
            <span className="text-xs font-semibold text-outline">Org Scope:</span>
            <select
              className="bg-surface-container dark:bg-slate-800 text-on-surface dark:text-white text-xs font-bold focus:outline-none"
              value={orgScope}
              onChange={(e) => setOrgScope(e.target.value)}
            >
              <option value="all" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">Blesson Byju (All)</option>
              <option value="ajce" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">Abhinand M A (AJCE Corporate)</option>
              <option value="lab" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">Abhinanth Pillai (Elder Care)</option>
            </select>
          </div>

          <div className="w-full max-w-md mx-auto">
            <div className="mb-stack-lg text-center md:text-left">
              <h1 className="font-headline-lg text-headline-lg text-on-background dark:text-white mb-2">
                {isRegistering ? "Register Dev Account" : "WiFi Sense Login"}
              </h1>
              <p className="font-body-md text-body-md text-on-surface-variant dark:text-slate-400">
                {isRegistering 
                  ? "Create credentials to start testing the CSI data pipeline." 
                  : "Scope credentials automatically prefill based on the top-right Org Scope selector."}
              </p>
            </div>

            {loginError && (
              <div className="bg-error-container text-error rounded p-3 mb-4 text-xs font-semibold">
                {loginError}
              </div>
            )}

            {!isRegistering ? (
              <form onSubmit={handleLogin} className="space-y-stack-md">
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Email Address</label>
                  <input
                    type="email"
                    className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none font-body-md"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(true)} className="text-secondary font-medium text-xs hover:underline">
                    Create new registration
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-on-secondary bg-secondary hover:opacity-90">
                    Sign In <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>arrow_forward</span>
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-stack-md">
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Email Address</label>
                  <input
                    type="email"
                    className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">First Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                      value={regFirst}
                      onChange={(e) => setRegFirst(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Last Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                      value={regLast}
                      onChange={(e) => setRegLast(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Role Type</label>
                  <select
                    className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                  >
                    <option value="system_admin">System Admin</option>
                    <option value="facility_manager">Facility Manager</option>
                    <option value="caregiver">Caregiver</option>
                  </select>
                </div>
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3 py-2 border border-outline-variant dark:border-slate-800 rounded bg-surface dark:bg-slate-900 dark:text-white focus:outline-none"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(false)} className="text-on-surface-variant dark:text-slate-400 font-medium text-xs hover:underline">
                    Back to Sign In
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-on-secondary bg-secondary hover:opacity-90">
                    Register
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // WORKSPACE VIEW (AUTHENTICATED)
  // ============================================================================
  return (
    <div className="bg-background dark:bg-slate-950 text-on-background dark:text-slate-100 min-h-screen flex transition-all duration-300">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-all transform translate-y-0 ${
          toastMessage.type === "error" ? "bg-error text-on-error" : "bg-secondary text-on-secondary"
        }`}>
          <span className="material-symbols-outlined">{toastMessage.type === "error" ? "error" : "check_circle"}</span>
          <span className="text-xs font-bold">{toastMessage.text}</span>
        </div>
      )}

      {/* SideNavbar */}
      <nav className="fixed left-0 top-0 bottom-0 w-sidebar-width flex flex-col z-45 bg-surface-container-lowest dark:bg-slate-900 border-r border-outline-variant dark:border-slate-800">
        <div className="p-gutter flex flex-col gap-stack-sm border-b border-outline-variant dark:border-slate-800">
          <div className="flex items-center gap-stack-sm">
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: "32px" }}>sensors</span>
            <div>
              <h1 className="text-headline-sm font-headline-sm text-primary dark:text-white">Wi-Fi Sense</h1>
              <p className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400">AI Monitoring Active</p>
            </div>
          </div>
          <button
            onClick={triggerEmergencyProtocol}
            className="w-full mt-4 bg-error-container text-on-error-container py-2 rounded-DEFAULT text-body-md font-body-md font-semibold flex justify-center items-center gap-2 hover:bg-error hover:text-on-error transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
            Emergency Protocol
          </button>
        </div>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
          <button
            onClick={() => { setCurrentView("dashboard"); }}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "dashboard" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined" style={{ fontVariationSettings: currentView === "dashboard" ? "'FILL' 1" : "'FILL' 0" }}>dashboard</span>
            Dashboard
          </button>

          <button
            onClick={() => setCurrentView("buildings")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "buildings" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined">business</span> Buildings
          </button>

          <button
            onClick={() => setCurrentView("floors")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "floors" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined">layers</span> Floors
          </button>

          <button
            onClick={() => setCurrentView("rooms")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "rooms" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined">meeting_room</span> Rooms
          </button>

          <button
            onClick={() => setCurrentView("devices")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "devices" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined">router</span> Devices
          </button>

          <button
            onClick={() => setCurrentView("residents")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "residents" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
            }`}
          >
            <span className="material-symbols-outlined">group</span> Users & Access
          </button>

          <div className="mt-auto border-t border-outline-variant dark:border-slate-800 pt-4 flex flex-col gap-2">
            <button
              onClick={() => setCurrentView("alerts")}
              className={`flex items-center justify-between gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
                currentView === "alerts" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined">warning</span> Alert Incident
              </span>
              {alerts.filter(a => a.status === "new").length > 0 && (
                <span className="bg-error text-on-error rounded-full px-2 py-0.5 text-[9px] font-bold">
                  {alerts.filter(a => a.status === "new").length}
                </span>
              )}
            </button>

            <button
              onClick={() => setCurrentView("analytics")}
              className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
                currentView === "analytics" ? "bg-secondary-container text-on-secondary-container dark:bg-slate-800 dark:text-secondary" : "text-on-surface-variant hover:bg-surface-container dark:hover:bg-slate-800"
              }`}
            >
              <span className="material-symbols-outlined">analytics</span> Analytics
            </button>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-gutter border-t border-outline-variant dark:border-slate-800 bg-surface-container-low dark:bg-slate-900/50">
          <div className="text-left text-xs mb-3">
            <div className="font-bold text-on-background dark:text-white truncate">{user?.first_name} {user?.last_name}</div>
            <div className="text-[10px] text-on-surface-variant dark:text-slate-400 uppercase font-mono tracking-wider mt-0.5">{role}</div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full border border-error text-error py-2 rounded text-xs font-bold uppercase hover:bg-error-container hover:text-on-error-container transition-all flex items-center justify-center gap-1"
          >
            <span className="material-symbols-outlined text-sm">logout</span> Logout
          </button>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="ml-sidebar-width flex-1 flex flex-col min-h-screen">
        {/* TopAppBar */}
        <header className="fixed top-0 right-0 left-sidebar-width h-header-height z-30 flex items-center justify-between px-gutter bg-surface dark:bg-slate-900 border-b border-outline-variant dark:border-slate-800 transition-colors">
          <div className="flex items-center gap-2 text-on-surface-variant dark:text-slate-300 text-body-md font-body-md">
            <span className="material-symbols-outlined">corporate_fare</span>
            <span>Organization: <span className="font-semibold text-primary dark:text-white">
              {orgScope === "ajce" 
                ? "Amal Jyothi College of Engineering" 
                : orgScope === "lab"
                ? "WiFi Sense Research Lab" 
                : "St. Jude Retirement Home (Mock)"}
            </span></span>
          </div>

          <div className="flex items-center gap-4">
            <select
              className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white text-xs font-bold border border-outline-variant dark:border-slate-700 px-3 py-1.5 rounded-full focus:outline-none"
              value={orgScope}
              onChange={(e) => setOrgScope(e.target.value)}
            >
              <option value="all" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">Global view (All Orgs)</option>
              <option value="ajce" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">AJCE (Corporate)</option>
              <option value="lab" className="bg-surface-bright dark:bg-slate-800 text-on-surface dark:text-white">WiFi Sense Lab (Elder-Care)</option>
            </select>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="text-on-surface-variant hover:bg-surface-container-low p-2 rounded-full transition-colors opacity-80 hover:opacity-100"
            >
              <span className="material-symbols-outlined">{darkMode ? "light_mode" : "dark_mode"}</span>
            </button>
            
            <img alt="User avatar" className="w-8 h-8 rounded-full border border-outline-variant dark:border-slate-800" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCu1RCn5_eg7EySwCBpXG2E5joCiEZy4lvWvSaDVhBHzvt0rhEMs_hZC9HeTPGvt-oJnrDUGlBL2Tb4tYqjlWOP_S4fxlpydOmtf5Y6hG1U2WQnQH1Nx13BotmVTUcmv7sOZtIjEegIXE6g4RZQ-r1PtXh6OM0WxPjorUBfwJig7xcbtg_lExE_t6bnvZfqHinuVSz8lXFPGqEOp_M4YwzZ5a-VISCIKS2DaDPlJ4rqTWUQEtcD5eAXMg"/>
          </div>
        </header>

        {/* Global Fall Alert Banner */}
        {activeFallAlert && (
          <div className="mt-header-height bg-error-container border-b border-error text-on-error-container p-4 flex items-center justify-between pulse-animation relative z-20">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-error text-2xl fill">warning</span>
              <div className="text-left font-sans">
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-error">POTENTIAL FALL ALERT</h3>
                <p className="text-sm font-semibold">{activeFallAlert.message}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleAcknowledge(activeFallAlert.id)}
                className="px-3 py-1.5 border border-error text-error rounded text-xs font-bold uppercase hover:bg-error/10"
              >
                Acknowledge
              </button>
              <button
                onClick={() => setShowResolveModal(activeFallAlert.id)}
                className="px-3 py-1.5 bg-error text-on-error rounded text-xs font-bold uppercase hover:opacity-90 shadow"
              >
                Resolve
              </button>
            </div>
          </div>
        )}

        {/* Main Canvas */}
        <main className={`p-container-padding flex-1 ${activeFallAlert ? "pt-2" : "pt-header-height"}`}>
          {currentView === "dashboard" && (
            <div className="space-y-6">
              
              {/* Tab Selector for Dashboards */}
              <div className="flex justify-between items-center mb-4">
                <div className="text-left">
                  <h2 className="text-headline-lg font-headline-lg text-primary dark:text-white mb-1">Asset Management Dashboard</h2>
                  <p className="text-body-lg font-body-lg text-on-surface-variant dark:text-slate-400">Overview of physical infrastructure and monitoring devices.</p>
                </div>
                <div className="flex bg-surface-container dark:bg-slate-900 border dark:border-slate-800 rounded-full p-1">
                  <button
                    onClick={() => setDashboardTab("assets")}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase transition-all ${
                      dashboardTab === "assets" ? "bg-secondary text-on-secondary shadow" : "text-outline hover:text-on-surface"
                    }`}
                  >
                    Asset View
                  </button>
                  <button
                    onClick={() => setDashboardTab("telemetry")}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase transition-all ${
                      dashboardTab === "telemetry" ? "bg-secondary text-on-secondary shadow" : "text-outline hover:text-on-surface"
                    }`}
                  >
                    Telemetry Feed
                  </button>
                </div>
              </div>

              {dashboardTab === "assets" ? (
                <div className="space-y-8">
                  {/* Metrics Row */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-gutter">
                    <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-secondary transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-2 uppercase">Buildings</span>
                      <div className="flex items-end justify-between text-primary dark:text-slate-100">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{buildings.length}</span>
                        <span className="material-symbols-outlined text-outline">domain</span>
                      </div>
                    </div>
                    <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-secondary transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-2 uppercase">Total Rooms</span>
                      <div className="flex items-end justify-between text-primary dark:text-slate-100">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{rooms.length}</span>
                        <span className="material-symbols-outlined text-outline">door_front</span>
                      </div>
                    </div>
                    <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-secondary transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-2 uppercase">Registered Devices</span>
                      <div className="flex items-end justify-between text-primary dark:text-slate-100">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{devices.length}</span>
                        <span className="material-symbols-outlined text-secondary">sensors</span>
                      </div>
                    </div>
                    <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-secondary transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-2 uppercase">Staff / Residents</span>
                      <div className="flex items-end justify-between text-primary dark:text-slate-100">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{residents.length}</span>
                        <span className="material-symbols-outlined text-outline">badge</span>
                      </div>
                    </div>
                  </div>

                  {/* Collapsible Facility Hierarchy & Device Health Bento card */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                    
                    {/* Collapsible Facility Hierarchy */}
                    <div className="lg:col-span-2 bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                      <div className="p-6 border-b border-outline-variant dark:border-slate-800 bg-surface-bright dark:bg-slate-900 flex justify-between items-center rounded-t-lg">
                        <h3 className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 flex items-center gap-2">
                          <span className="material-symbols-outlined text-outline">account_tree</span>
                          Facility Hierarchy
                        </h3>
                        <button
                          onClick={expandAllBuildings}
                          className="text-secondary text-label-caps font-label-caps uppercase border border-secondary px-3 py-1 rounded hover:bg-surface-container-low transition-colors"
                        >
                          Expand All
                        </button>
                      </div>
                      
                      <div className="p-6 flex-1 text-left">
                        <ul className="flex flex-col gap-4">
                          {buildings.map(b => (
                            <li key={b.id} className="border border-outline-variant dark:border-slate-800 rounded p-4 bg-surface dark:bg-slate-950">
                              <div
                                onClick={() => toggleBuildingExpand(b.id)}
                                className="flex items-center justify-between cursor-pointer"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="material-symbols-outlined text-on-surface-variant dark:text-slate-400">business</span>
                                  <span className="text-body-lg font-body-lg font-semibold text-primary dark:text-slate-200">{b.name}</span>
                                </div>
                                <div className="flex items-center gap-4 text-body-md font-body-md text-on-surface-variant dark:text-slate-400">
                                  <span>{rooms.filter(r => floors.find(f => f.id === r.floor_id)?.building_id === b.id).length} Rooms</span>
                                  <span className="material-symbols-outlined">
                                    {expandedBuildings[b.id] ? "expand_less" : "chevron_right"}
                                  </span>
                                </div>
                              </div>

                              {/* Collapsible Floor list */}
                              {expandedBuildings[b.id] && (
                                <div className="ml-8 mt-2 pl-4 border-l-2 border-outline-variant dark:border-slate-800 flex flex-col gap-2">
                                  {floors.filter(f => f.building_id === b.id).map(f => (
                                    <div key={f.id} className="flex items-center justify-between py-1 border-b dark:border-slate-800 text-xs">
                                      <div className="flex items-center gap-2 text-body-md font-body-md text-on-surface dark:text-slate-300">
                                        <span className="material-symbols-outlined text-sm text-outline">layers</span> Floor {f.floor_number}
                                      </div>
                                      <span className="text-label-caps font-label-caps bg-surface-container dark:bg-slate-800 px-2 py-1 rounded text-on-surface-variant dark:text-slate-400">
                                        {rooms.filter(r => r.floor_id === f.id).map(r => r.name).join(", ") || "No rooms"}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </li>
                          ))}
                          {buildings.length === 0 && (
                            <div className="py-6 text-center text-xs text-outline border border-dashed rounded">
                              No buildings registered in the active organization.
                            </div>
                          )}
                        </ul>
                      </div>
                    </div>

                    {/* Device Health Status card */}
                    <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                      <div className="p-6 border-b border-outline-variant dark:border-slate-800 bg-surface-bright dark:bg-slate-900 rounded-t-lg text-left">
                        <h3 className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 flex items-center gap-2">
                          <span className="material-symbols-outlined text-secondary">memory</span>
                          Device Health
                        </h3>
                      </div>
                      
                      <div className="p-0 overflow-x-auto flex-1 text-left">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="bg-surface-container-low dark:bg-slate-800 border-b border-outline-variant dark:border-slate-800">
                              <th className="p-4 text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 uppercase">Device / MAC</th>
                              <th className="p-4 text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 uppercase">Location</th>
                              <th className="p-4 text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 uppercase">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {devices.filter(d => {
                              const r = rooms.find(rm => rm.id === d.room_id);
                              if (!r) return orgScope === "all";
                              if (orgScope === "ajce") return r.name === "MCA Lab" || r.name === "Seminar Hall";
                              if (orgScope === "lab") return r.name !== "MCA Lab" && r.name !== "Seminar Hall";
                              return true;
                            }).map(dev => (
                              <tr key={dev.id} className="border-b border-outline-variant dark:border-slate-800 hover:bg-surface-bright dark:hover:bg-slate-800/40 transition-colors">
                                <td className="p-4">
                                  <div className="flex flex-col">
                                    <span className="text-body-md font-body-md font-semibold text-primary dark:text-slate-200">{dev.firmware_version}</span>
                                    <span className="text-data-mono font-data-mono text-outline">{dev.mac_address}</span>
                                  </div>
                                </td>
                                <td className="p-4 text-body-md font-body-md text-on-surface dark:text-slate-300">
                                  {rooms.find(r => r.id === dev.room_id)?.name || "Unassigned"}
                                </td>
                                <td className="p-4">
                                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-label-caps font-label-caps ${
                                    dev.device_status === "ONLINE" ? "bg-secondary-container/20 text-on-secondary-container" : "bg-outline-variant/30 text-on-surface-variant"
                                  }`}>
                                    <span className={`w-2 h-2 rounded-full ${dev.device_status === "ONLINE" ? "bg-secondary animate-pulse" : "bg-outline"}`}></span>
                                    {dev.device_status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="p-4 bg-surface dark:bg-slate-900 border-t border-outline-variant dark:border-slate-800 rounded-b-lg flex justify-between items-center text-xs">
                        <span className="text-outline">Live hardware nodes refresh active</span>
                        <button
                          onClick={() => {
                            if (devices.length > 0) {
                              setSimDeviceId(devices[0].id);
                              setShowSimulateDrawer(true);
                            }
                          }}
                          className="text-secondary font-semibold hover:underline"
                        >
                          Trigger Simulation
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Access Summary: Staff Distribution */}
                  <div className="bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                    <div className="p-6 border-b border-outline-variant dark:border-slate-800 bg-surface-bright dark:bg-slate-900 text-left">
                      <h3 className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 flex items-center gap-2">
                        <span className="material-symbols-outlined text-outline">admin_panel_settings</span>
                        Access Summary: Inhabitant Distribution
                      </h3>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                      <div className="flex items-center gap-4 p-4 rounded border border-outline-variant dark:border-slate-800 bg-surface dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-surface-container-high dark:bg-slate-800 flex items-center justify-center text-primary dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Amal Jyothi - MCA Lab</div>
                          <div className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name === "MCA Lab").length} Active Users
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 rounded border border-outline-variant dark:border-slate-800 bg-surface dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-surface-container-high dark:bg-slate-800 flex items-center justify-center text-primary dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Research Lab Block</div>
                          <div className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name === "Research Lab").length} Active Residents
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 rounded border border-outline-variant dark:border-slate-800 bg-surface dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-surface-container-high dark:bg-slate-800 flex items-center justify-center text-primary dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-on-surface-variant dark:text-slate-400 mb-1">Research Lab - Project Room</div>
                          <div className="text-headline-sm font-headline-sm text-primary dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name === "Project Room").length} Active Residents
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Live Telemetry View */}
                  <CSIWaveform activity={activeTelemetryActivity} />
                  
                  <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                    <h3 className="text-xs font-bold uppercase tracking-wider border-b dark:border-slate-800 pb-2 mb-4 text-left dark:text-white">
                      Live Room Occupancy Grid
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {occupancySummary.occupied_room_details.map(rm => (
                        <div
                          key={rm.room_id}
                          className={`border dark:border-slate-800 rounded-xl p-3 text-left transition-all ${
                            rm.is_occupied
                              ? rm.current_activity === "Fall_Detected"
                                ? "border-error bg-error-container/10 dark:bg-error/5 animate-pulse"
                                : "border-blue-500 bg-blue-50/50 dark:bg-slate-950"
                              : "border-outline-variant bg-[#f1faf9] dark:bg-slate-900/30"
                          }`}
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-bold text-sm truncate dark:text-white">{rm.room_name}</span>
                            <span className={`w-2 h-2 rounded-full ${
                              rm.is_occupied 
                                ? rm.current_activity === "Fall_Detected"
                                  ? "bg-error animate-ping"
                                  : "bg-blue-500" 
                                : "bg-secondary"
                            }`}></span>
                          </div>
                          <p className="text-[9px] text-outline font-bold uppercase">{rm.room_type}</p>
                          <p className="text-xs font-bold mt-2 text-on-surface dark:text-slate-300 font-sans">
                            {rm.is_occupied ? `Activity Classified: ${rm.current_activity}` : "Vacant"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ============================================================================
            ORGANIZATIONS VIEW
          ============================================================================ */}
          {currentView === "organizations" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Registered Organizations</h3>
                <button
                  onClick={() => setShowAddOrgModal(true)}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Org
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Org ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Deployment Type</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {organizations.map(org => (
                      <tr key={org.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-data-mono text-xs">{org.id}</td>
                        <td className="p-3 font-semibold dark:text-white">{org.name}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-surface-container dark:bg-slate-800 text-on-surface">
                            {org.type}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            BUILDINGS VIEW
          ============================================================================ */}
          {currentView === "buildings" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Buildings Matrix</h3>
                <button
                  onClick={() => {
                    if (organizations.length === 0) {
                      alert("Please create an organization first.");
                    } else {
                      setNewBldOrgId(organizations[0].id);
                      setShowAddBuildingModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Building
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Building ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Address</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {buildings.map(bld => (
                      <tr key={bld.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-data-mono text-xs">{bld.id}</td>
                        <td className="p-3 font-semibold dark:text-white">{bld.name}</td>
                        <td className="p-3">{bld.address || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            FLOORS VIEW
          ============================================================================ */}
          {currentView === "floors" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Floor Layouts</h3>
                <button
                  onClick={() => {
                    if (buildings.length === 0) {
                      alert("Please create a building first.");
                    } else {
                      setNewFlrBldId(buildings[0].id);
                      setShowAddFloorModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Floor
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Floor ID</th>
                      <th className="p-3">Building Name</th>
                      <th className="p-3">Floor Number</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {floors.filter(f => {
                      const b = buildings.find(bld => bld.id === f.building_id);
                      return !!b;
                    }).map(flr => (
                      <tr key={flr.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-data-mono text-xs">{flr.id}</td>
                        <td className="p-3 font-semibold dark:text-white">{buildings.find(b => b.id === flr.building_id)?.name}</td>
                        <td className="p-3">Floor {flr.floor_number}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            ROOMS VIEW
          ============================================================================ */}
          {currentView === "rooms" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Rooms Configuration</h3>
                <button
                  onClick={() => {
                    if (floors.length === 0) {
                      alert("Please create a floor first.");
                    } else {
                      setNewRmFlrId(floors[0].id);
                      setShowAddRoomModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Room
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Room ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Capacity</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {rooms.filter(r => {
                      if (orgScope === "ajce") return r.name === "MCA Lab" || r.name === "Seminar Hall";
                      if (orgScope === "lab") return r.name !== "MCA Lab" && r.name !== "Seminar Hall";
                      return true;
                    }).map(rm => (
                      <tr key={rm.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-data-mono text-xs">{rm.id}</td>
                        <td className="p-3 font-semibold dark:text-white">{rm.name}</td>
                        <td className="p-3">{rm.room_type}</td>
                        <td className="p-3 font-data-mono">{rm.capacity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            DEVICES VIEW
          ============================================================================ */}
          {currentView === "devices" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">ESP32 Hardware Nodes</h3>
                <button
                  onClick={() => {
                    setNewDevRmId(rooms.length > 0 ? rooms[0].id : "");
                    setShowAddDeviceModal(true);
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Register Device
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">MAC Address</th>
                      <th className="p-3">Device Name</th>
                      <th className="p-3">Assigned Room</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {devices.filter(d => {
                      const r = rooms.find(rm => rm.id === d.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name === "MCA Lab" || r.name === "Seminar Hall";
                      if (orgScope === "lab") return r.name !== "MCA Lab" && r.name !== "Seminar Hall";
                      return true;
                    }).map(dev => (
                      <tr key={dev.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold font-data-mono dark:text-white">{dev.mac_address}</td>
                        <td className="p-3">{dev.firmware_version}</td>
                        <td className="p-3 font-semibold text-xs">{rooms.find(r => r.id === dev.room_id)?.name || "Unassigned"}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            dev.device_status === "ONLINE" ? "bg-secondary-container text-on-secondary-container" : "bg-outline-variant/30 text-on-surface-variant"
                          }`}>
                            {dev.device_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            RESIDENTS VIEW
          ============================================================================ */}
          {currentView === "residents" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Registered Residents</h3>
                <button
                  onClick={() => {
                    if (rooms.length === 0) {
                      alert("Please create a room first.");
                    } else {
                      setNewResRmId(rooms[0].id);
                      setShowAddResidentModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Resident
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Resident ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Room</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {residents.filter(res => {
                      const r = rooms.find(rm => rm.id === res.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name === "MCA Lab";
                      if (orgScope === "lab") return r.name !== "MCA Lab";
                      return true;
                    }).map(r => (
                      <tr key={r.id} className="hover:bg-surface-bright dark:hover:bg-slate-800/40">
                        <td className="p-3 font-data-mono text-xs">{r.id}</td>
                        <td className="p-3 font-semibold dark:text-white">{r.first_name} {r.last_name}</td>
                        <td className="p-3 font-mono text-xs">{rooms.find(rm => rm.id === r.room_id)?.name || "Unassigned"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            ALERTS VIEW
          ============================================================================ */}
          {currentView === "alerts" && (
            <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary dark:text-slate-100">Fall Alerts Incident Center</h3>
                <span className="text-[10px] text-outline font-bold uppercase">Incident Status Log</span>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low dark:bg-slate-800 text-[10px] text-outline font-bold uppercase border-b dark:border-slate-800">
                      <th className="p-3">Severity</th>
                      <th className="p-3">Room</th>
                      <th className="p-3">Trigger Type</th>
                      <th className="p-3">Details</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y dark:divide-slate-800">
                    {alerts.map(a => (
                      <tr key={a.id} className={`hover:bg-surface-bright dark:hover:bg-slate-800/40 ${a.status === "new" ? "bg-error-container/10 dark:bg-error/5" : ""}`}>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                            a.severity === "CRITICAL" ? "bg-error text-on-error" : "bg-tertiary-fixed text-on-tertiary-fixed-variant"
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="p-3 font-semibold dark:text-white">{rooms.find(rm => rm.id === a.room_id)?.name || "Unknown"}</td>
                        <td className="p-3 font-mono text-xs">{a.event_type}</td>
                        <td className="p-3 text-xs">{a.message}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            a.status === "new"
                              ? "bg-error-container text-error border border-error/20"
                              : a.status === "acknowledged"
                              ? "bg-secondary-container text-on-secondary-container border border-secondary"
                              : "bg-slate-100 dark:bg-slate-800 text-on-surface"
                          }`}>
                            {a.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex justify-end gap-2">
                            {a.status === "new" && (
                              <button
                                onClick={() => handleAcknowledge(a.id)}
                                className="px-2.5 py-1 border border-secondary text-secondary rounded-full text-xs font-bold uppercase hover:bg-secondary/10"
                              >
                                Ack
                              </button>
                            )}
                            {a.status !== "resolved" && (
                              <button
                                onClick={() => setShowResolveModal(a.id)}
                                className="px-2.5 py-1 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase hover:opacity-90"
                              >
                                Resolve
                              </button>
                            )}
                            {a.status === "resolved" && (
                              <span className="text-xs text-outline font-semibold">Audit Cleared</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {alerts.length === 0 && (
                      <tr>
                        <td colSpan="6" className="p-4 text-center text-outline">No incidents logged. Set organization to WiFi Sense Lab and simulate events to trigger alerts.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            ANALYTICS VIEW
          ============================================================================ */}
          {currentView === "analytics" && (
            <div className="space-y-6 text-left">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b dark:border-slate-800 pb-2 mb-4 dark:text-slate-100">Occupancy Efficiency</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-on-surface-variant dark:text-slate-400">Total Occupancy Rate</span>
                      <span className="font-bold text-secondary font-data-mono">{occupancySummary.occupancy_rate}%</span>
                    </div>
                    <div className="w-full bg-surface-container dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                      <div className="bg-secondary h-full rounded-full" style={{ width: `${occupancySummary.occupancy_rate}%` }}></div>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span>{occupancySummary.occupied_rooms} Occupied Rooms</span>
                      <span>{occupancySummary.vacant_rooms} Vacant Rooms</span>
                    </div>
                  </div>
                </div>

                <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b dark:border-slate-800 pb-2 mb-4 dark:text-slate-100">Fall Warnings Audit Trails</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="border dark:border-slate-800 rounded-xl p-3 bg-surface dark:bg-slate-800/40">
                      <span className="text-[9px] text-outline font-bold uppercase">Status: Awaiting Ack</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "new").length}</p>
                    </div>
                    <div className="border dark:border-slate-800 rounded-xl p-3 bg-surface dark:bg-slate-800/40">
                      <span className="text-[9px] text-outline font-bold uppercase">Status: In Progress</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "acknowledged").length}</p>
                    </div>
                    <div className="border dark:border-slate-800 rounded-xl p-3 bg-surface dark:bg-slate-800/40">
                      <span className="text-[9px] text-outline font-bold uppercase">Status: Resolved</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "resolved").length}</p>
                    </div>
                    <div className="border dark:border-slate-800 rounded-xl p-3 bg-surface dark:bg-slate-800/40">
                      <span className="text-[9px] text-outline font-bold uppercase">Total Warnings</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.length}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ============================================================================
        SLIDE OVER DRAWER FOR SIMULATION
      ============================================================================ */}
      {showSimulateDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div onClick={() => setShowSimulateDrawer(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs"></div>
          
          <div className="relative w-sidebar-width max-w-full h-full bg-surface-container-lowest dark:bg-slate-900 border-l dark:border-slate-800 p-6 flex flex-col justify-between shadow-2xl z-10 transition-all">
            <div className="text-left font-sans">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-lg dark:text-white">Simulate Telemetry</h3>
                <button onClick={() => setShowSimulateDrawer(false)} className="material-symbols-outlined text-outline">close</button>
              </div>

              <p className="text-xs text-on-surface-variant dark:text-slate-400 mb-6">
                Send simulated subcarrier amplitude signals. Note that critical fall options will automatically trigger warnings in elder-care scopes.
              </p>

              <form onSubmit={runSimulation} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-outline mb-1">Target Node (Device)</label>
                  <select
                    className="w-full border dark:border-slate-800 rounded p-2 text-xs bg-surface dark:bg-slate-800 dark:text-white"
                    value={simDeviceId}
                    onChange={(e) => setSimDeviceId(e.target.value)}
                  >
                    {devices.filter(d => {
                      const r = rooms.find(rm => rm.id === d.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name === "MCA Lab" || r.name === "Seminar Hall";
                      if (orgScope === "lab") return r.name !== "MCA Lab" && r.name !== "Seminar Hall";
                      return true;
                    }).map(dev => (
                      <option key={dev.id} value={dev.id}>
                        {dev.firmware_version} ({rooms.find(r => r.id === dev.room_id)?.name})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase text-outline mb-1">Subcarrier Pattern</label>
                  <select
                    className="w-full border dark:border-slate-800 rounded p-2 text-xs bg-surface dark:bg-slate-800 dark:text-white"
                    value={simActivity}
                    onChange={(e) => setSimActivity(e.target.value)}
                  >
                    {orgScope !== "ajce" && (
                      <option value="Fall_Detected">Fall Detected (CSI Spike Alert)</option>
                    )}
                    <option value="Walking">Walking (Presence)</option>
                    <option value="Sitting">Sitting (Presence)</option>
                    <option value="Empty">Empty (Vacant status)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full mt-6 py-2 bg-secondary text-on-secondary font-bold uppercase text-xs rounded-full shadow"
                >
                  Ingest Signal
                </button>
              </form>
            </div>
            
            <p className="text-[9px] text-outline text-left">
              Simulation output evaluates model accuracy vectors in the next project phase.
            </p>
          </div>
        </div>
      )}

      {/* ============================================================================
        INFRASTRUCTURE DIALOGS
      ============================================================================ */}

      {/* 1. Add Org Modal */}
      {showAddOrgModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Organization</h3>
            <form onSubmit={addOrganization} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Organization Name</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. Sunrise Elder Care"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Deployment Type</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newOrgType}
                  onChange={(e) => setNewOrgType(e.target.value)}
                >
                  <option value="ELDER_CARE">Elder-Care / Assisted Living</option>
                  <option value="CORPORATE">Corporate / Commercial Facility</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddOrgModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. Add Building Modal */}
      {showAddBuildingModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Building</h3>
            <form onSubmit={addBuilding} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Parent Organization</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newBldOrgId}
                  onChange={(e) => setNewBldOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <option key={org.id} value={org.id}>{org.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Building Name</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. North Wing"
                  value={newBldName}
                  onChange={(e) => setNewBldName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Address</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. AJCE Campus"
                  value={newBldAddress}
                  onChange={(e) => setNewBldAddress(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddBuildingModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Add Floor Modal */}
      {showAddFloorModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Floor</h3>
            <form onSubmit={addFloor} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Parent Building</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newFlrBldId}
                  onChange={(e) => setNewFlrBldId(e.target.value)}
                >
                  {buildings.map(bld => (
                    <option key={bld.id} value={bld.id}>{bld.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Floor Number</label>
                <input
                  type="number"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newFlrNum}
                  onChange={(e) => setNewFlrNum(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddFloorModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. Add Room Modal */}
      {showAddRoomModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Room Layout</h3>
            <form onSubmit={addRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Parent Floor</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newRmFlrId}
                  onChange={(e) => setNewRmFlrId(e.target.value)}
                >
                  {floors.map(flr => (
                    <option key={flr.id} value={flr.id}>
                      Floor {flr.floor_number} ({buildings.find(bld => bld.id === flr.building_id)?.name})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Room Name</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. Research Lab"
                  value={newRmName}
                  onChange={(e) => setNewRmName(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-outline mb-1">Room Type</label>
                  <select
                    className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                    value={newRmType}
                    onChange={(e) => setNewRmType(e.target.value)}
                  >
                    <option value="Resident Bedroom">Resident Bedroom</option>
                    <option value="Conference Room">Conference Room</option>
                    <option value="Restroom">Restroom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-outline mb-1">Capacity</label>
                  <input
                    type="number"
                    className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                    value={newRmCapacity}
                    onChange={(e) => setNewRmCapacity(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddRoomModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 5. Add Device Modal */}
      {showAddDeviceModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Register ESP32 CSI Node</h3>
            <form onSubmit={addDevice} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Room Assignment</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newDevRmId}
                  onChange={(e) => setNewDevRmId(e.target.value)}
                >
                  {rooms.map(rm => (
                    <option key={rm.id} value={rm.id}>{rm.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">MAC Address</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. 4C:75:25:AA:BB:CC"
                  value={newDevMac}
                  onChange={(e) => setNewDevMac(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Device Name / Version</label>
                <input
                  type="text"
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newDevFirmware}
                  onChange={(e) => setNewDevFirmware(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddDeviceModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Register Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. Add Resident Modal */}
      {showAddResidentModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Resident</h3>
            <form onSubmit={addResident} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Assigned Room</label>
                <select
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                  value={newResRmId}
                  onChange={(e) => setNewResRmId(e.target.value)}
                >
                  {rooms.map(rm => (
                    <option key={rm.id} value={rm.id}>{rm.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-outline mb-1">First Name</label>
                  <input
                    type="text"
                    className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                    value={newResFirst}
                    onChange={(e) => setNewResFirst(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-outline mb-1">Last Name</label>
                  <input
                    type="text"
                    className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white"
                    value={newResLast}
                    onChange={(e) => setNewResLast(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddResidentModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Add Resident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 7. Resolve Alert Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest dark:bg-slate-900 border dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-2 text-error">Resolve Incident Alert</h3>
            <p className="text-xs text-outline mb-4">
              Enter resolution notes to clear the warning banner.
            </p>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-outline mb-1">Resolution Actions / Notes</label>
                <textarea
                  className="w-full border dark:border-slate-800 rounded p-2 text-sm bg-surface dark:bg-slate-800 dark:text-white h-24"
                  placeholder="e.g. Caregiver dispatched. Resident verified safe."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowResolveModal(null);
                    setResolutionNotes("");
                  }}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-surface-container dark:text-white dark:border-slate-800"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded-full text-xs font-bold uppercase">
                  Resolve Alert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
