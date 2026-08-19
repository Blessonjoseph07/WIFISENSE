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
    let color = "#0D9488"; // Teal in light mode

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
      color = "#EF4444"; 
    } else if (activity === "Empty") {
      speed = 0.01;
      amplitude = 4;
      noiseLevel = 0.5;
      color = "#9CA3AF"; 
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw Grid Lines
      ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
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
    <div className="relative w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 overflow-hidden shadow-sm">
      <div className="flex justify-between items-center mb-2 z-10 relative">
        <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">CSI Amplitude Matrix Subcarriers</span>
        <span className="flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-100 dark:border-slate-700">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-ping"></span>
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
  const [darkMode, setDarkMode] = useState(localStorage.getItem("darkMode") === "true");

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

  // Modal Open States
  const [showSimulateDrawer, setShowSimulateDrawer] = useState(false);
  const [showAddOrgModal, setShowAddOrgModal] = useState(false);
  const [showAddBuildingModal, setShowAddBuildingModal] = useState(false);
  const [showAddFloorModal, setShowAddFloorModal] = useState(false);
  const [showAddRoomModal, setShowAddRoomModal] = useState(false);
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [showAddResidentModal, setShowAddResidentModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(null); 
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);

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
          filteredDetails = filteredDetails.filter(rm => rm.room_name.includes("MCA") || rm.room_name.includes("Staff") || rm.room_name.includes("IoT"));
        } else if (orgScope === "lab") {
          filteredDetails = filteredDetails.filter(rm => !rm.room_name.includes("MCA") && !rm.room_name.includes("Staff") && !rm.room_name.includes("IoT"));
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
            return rm && !rm.name.includes("MCA") && !rm.name.includes("Staff") && !rm.name.includes("IoT");
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
          return orgScope === "ajce" ? (b.name.includes("MCA") || b.name.includes("R&D")) : b.name.includes("Care Wing");
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
      console.error("Sync data error: ", err);
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
  // TOGGLE DEVICE STATUS (INTERACTIVE FEATURE)
  // ============================================================================
  const handleToggleDevice = async (deviceId) => {
    try {
      const res = await fetch(`${API_BASE}/devices/${deviceId}/toggle`, {
        method: "PATCH",
        headers: getHeaders()
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to toggle device status.");
      }
      fetchAllData();
      setToastMessage({ type: "success", text: "Device operational power toggled successfully." });
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
    setShowEmergencyModal(true);
  };

  // ============================================================================
  // OUT OF BOX VIEW (LOGIN)
  // ============================================================================
  if (!token) {
    return (
      <div className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-body-md antialiased min-h-screen flex flex-col md:flex-row transition-all duration-300">
        {/* Banner Panel */}
        <div className="hidden md:flex flex-col w-[45%] bg-slate-100 dark:bg-slate-900 relative overflow-hidden p-container-padding justify-between border-r border-slate-200 dark:border-slate-800">
          <div className="absolute inset-0 bg-wave-pattern opacity-60 dark:opacity-40 z-0"></div>
          <div className="z-10 mt-8 ml-8">
            <div className="flex items-center gap-stack-sm mb-4">
              <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 animate-pulse" style={{ fontSize: "36px" }}>sensors</span>
              <span className="font-headline-md text-headline-md text-slate-900 dark:text-slate-100">Wi-Fi Sense</span>
            </div>
            <p className="font-headline-sm text-headline-sm text-slate-500 dark:text-slate-300 max-w-sm mt-4">
              Indoor Human Sensing and Fall Tracking via Channel State Information.
            </p>
          </div>
          <div className="z-10 mb-8 ml-8">
            <div className="inline-flex items-center gap-2 bg-slate-200 dark:bg-slate-800 px-4 py-2 rounded-full border border-slate-300 dark:border-slate-700">
              <span className="material-symbols-outlined text-teal-600 dark:text-teal-400" style={{ fontSize: "16px" }}>check_circle</span>
              <span className="font-label-caps text-label-caps text-slate-700 dark:text-slate-200">System: Seed Data Ready</span>
            </div>
          </div>
        </div>

        {/* Login Panel */}
        <div className="flex-1 flex flex-col justify-center p-gutter relative bg-white dark:bg-slate-950">
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">Scope Selector:</span>
            <select
              className="bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-white text-xs font-bold focus:outline-none"
              value={orgScope}
              onChange={(e) => setOrgScope(e.target.value)}
            >
              <option value="all" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">Blesson Byju (System Admin)</option>
              <option value="ajce" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">Abhinand M A (AJCE Corporate)</option>
              <option value="lab" className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">Abhinanth S Pillai (Research Lab Caregiver)</option>
            </select>
          </div>

          <div className="w-full max-w-md mx-auto">
            <div className="mb-stack-lg text-center md:text-left">
              <h1 className="font-headline-lg text-headline-lg text-slate-900 dark:text-white mb-2">
                {isRegistering ? "Register Dev Account" : "WiFi Sense Login"}
              </h1>
              <p className="font-body-md text-body-md text-slate-500 dark:text-slate-400">
                {isRegistering 
                  ? "Create credentials to start testing the CSI data pipeline." 
                  : "Scope credentials automatically prefill based on the top-right Scope Selector."}
              </p>
            </div>

            {loginError && (
              <div className="bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 rounded p-3 mb-4 text-xs font-semibold border border-red-200 dark:border-red-900">
                {loginError}
              </div>
            )}

            {!isRegistering ? (
              <form onSubmit={handleLogin} className="space-y-stack-md">
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Email Address</label>
                  <input
                    type="email"
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none font-body-md"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(true)} className="text-teal-600 dark:text-teal-400 font-medium text-xs hover:underline">
                    Create new registration
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-white bg-teal-600 hover:bg-teal-700 transition-colors">
                    Sign In <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>arrow_forward</span>
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-stack-md">
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Email Address</label>
                  <input
                    type="email"
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4 text-left">
                  <div>
                    <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">First Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                      value={regFirst}
                      onChange={(e) => setRegFirst(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Last Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                      value={regLast}
                      onChange={(e) => setRegLast(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Role Type</label>
                  <select
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                  >
                    <option value="system_admin">System Admin</option>
                    <option value="facility_manager">Facility Manager</option>
                    <option value="caregiver">Caregiver</option>
                  </select>
                </div>
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(false)} className="text-slate-500 dark:text-slate-400 font-medium text-xs hover:underline">
                    Back to Sign In
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-white bg-teal-600 hover:bg-teal-700 transition-colors">
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
    <div className="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen flex transition-all duration-300">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-all transform translate-y-0 ${
          toastMessage.type === "error" ? "bg-red-600 text-white" : "bg-teal-600 text-white"
        }`}>
          <span className="material-symbols-outlined">{toastMessage.type === "error" ? "error" : "check_circle"}</span>
          <span className="text-xs font-bold">{toastMessage.text}</span>
        </div>
      )}

      {/* SideNavbar */}
      <nav className="fixed left-0 top-0 bottom-0 w-sidebar-width flex flex-col z-45 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
        <div className="p-gutter flex flex-col gap-stack-sm border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-stack-sm">
            <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 animate-pulse" style={{ fontSize: "32px" }}>sensors</span>
            <div className="text-left">
              <h1 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white">Wi-Fi Sense</h1>
              <p className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500">AI Monitoring Active</p>
            </div>
          </div>
          <button
            onClick={triggerEmergencyProtocol}
            className="w-full mt-4 bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900 py-2 rounded text-body-md font-body-md font-semibold flex justify-center items-center gap-2 hover:bg-red-600 hover:text-white transition-all"
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
              currentView === "dashboard" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined" style={{ fontVariationSettings: currentView === "dashboard" ? "'FILL' 1" : "'FILL' 0" }}>dashboard</span>
            Dashboard
          </button>

          <button
            onClick={() => setCurrentView("buildings")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "buildings" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">business</span> Buildings
          </button>

          <button
            onClick={() => setCurrentView("floors")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "floors" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">layers</span> Floors
          </button>

          <button
            onClick={() => setCurrentView("rooms")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "rooms" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">meeting_room</span> Rooms
          </button>

          <button
            onClick={() => setCurrentView("devices")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "devices" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">router</span> Devices
          </button>

          <button
            onClick={() => setCurrentView("residents")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "residents" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">group</span> Users & Access
          </button>

          <div className="mt-auto border-t border-slate-200 dark:border-slate-800 pt-4 flex flex-col gap-2">
            <button
              onClick={() => setCurrentView("alerts")}
              className={`flex items-center justify-between gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
                currentView === "alerts" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined">warning</span> Alert Incident
              </span>
              {alerts.filter(a => a.status === "new").length > 0 && (
                <span className="bg-red-500 text-white rounded-full px-2 py-0.5 text-[9px] font-bold animate-pulse">
                  {alerts.filter(a => a.status === "new").length}
                </span>
              )}
            </button>

            <button
              onClick={() => setCurrentView("analytics")}
              className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
                currentView === "analytics" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
              }`}
            >
              <span className="material-symbols-outlined">analytics</span> Analytics
            </button>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-gutter border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40">
          <div className="text-left text-xs mb-3">
            <div className="font-bold text-slate-800 dark:text-white truncate">{user?.first_name} {user?.last_name}</div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-mono tracking-wider mt-0.5">{role}</div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full border border-red-500 text-red-500 py-2 rounded text-xs font-bold uppercase hover:bg-red-50 dark:hover:bg-red-950/20 transition-all flex items-center justify-center gap-1"
          >
            <span className="material-symbols-outlined text-sm">logout</span> Logout
          </button>
        </div>
      </nav>

      {/* Main Content Wrapper */}
      <div className="ml-sidebar-width flex-1 flex flex-col min-h-screen">
        {/* TopAppBar */}
        <header className="fixed top-0 right-0 left-sidebar-width h-header-height z-30 flex items-center justify-between px-gutter bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 text-body-md font-body-md">
            <span className="material-symbols-outlined">corporate_fare</span>
            <span>Organization: <span className="font-semibold text-slate-950 dark:text-white">
              {orgScope === "ajce" 
                ? "Amal Jyothi College of Engineering" 
                : orgScope === "lab"
                ? "WiFi Sense Research Lab" 
                : "Department of Computer Applications"}
            </span></span>
          </div>

          <div className="flex items-center gap-4">
            <select
              className="bg-slate-50 dark:bg-slate-800 text-slate-850 dark:text-white text-xs font-bold border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full focus:outline-none"
              value={orgScope}
              onChange={(e) => setOrgScope(e.target.value)}
            >
              <option value="all" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">Global Organization view</option>
              <option value="ajce" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">Amal Jyothi (Corporate)</option>
              <option value="lab" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">WiFi Sense Lab (Elder-Care)</option>
            </select>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 p-2 rounded-full transition-colors"
              title="Toggle Dark Mode Theme"
            >
              <span className="material-symbols-outlined">{darkMode ? "light_mode" : "dark_mode"}</span>
            </button>
            
            <img alt="User avatar" className="w-8 h-8 rounded-full border border-slate-200 dark:border-slate-800" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCu1RCn5_eg7EySwCBpXG2E5joCiEZy4lvWvSaDVhBHzvt0rhEMs_hZC9HeTPGvt-oJnrDUGlBL2Tb4tYqjlWOP_S4fxlpydOmtf5Y6hG1U2WQnQH1Nx13BotmVTUcmv7sOZtIjEegIXE6g4RZQ-r1PtXh6OM0WxPjorUBfwJig7xcbtg_lExE_t6bnvZfqHinuVSz8lXFPGqEOp_M4YwzZ5a-VISCIKS2DaDPlJ4rqTWUQEtcD5eAXMg"/>
          </div>
        </header>

        {/* Global Fall Alert Banner */}
        {activeFallAlert && (
          <div className="mt-header-height bg-red-50 border-b border-red-500 text-red-700 dark:bg-red-950/20 dark:text-red-400 p-4 flex items-center justify-between pulse-animation relative z-25">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500 text-2xl fill">warning</span>
              <div className="text-left font-sans">
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-red-600">POTENTIAL FALL ALERT</h3>
                <p className="text-sm font-semibold">{activeFallAlert.message}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleAcknowledge(activeFallAlert.id)}
                className="px-3 py-1.5 border border-red-500 text-red-600 dark:text-red-400 rounded text-xs font-bold uppercase hover:bg-red-50 dark:hover:bg-red-950/40"
              >
                Acknowledge
              </button>
              <button
                onClick={() => setShowResolveModal(activeFallAlert.id)}
                className="px-3 py-1.5 bg-red-600 text-white rounded text-xs font-bold uppercase hover:opacity-90 shadow"
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
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white mb-1">Asset Management Dashboard</h2>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400">Overview of physical infrastructure and monitoring devices.</p>
                </div>
                <div className="flex bg-slate-200 dark:bg-slate-900 border dark:border-slate-800 rounded-full p-1 shadow-inner">
                  <button
                    onClick={() => setDashboardTab("assets")}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase transition-all ${
                      dashboardTab === "assets" ? "bg-teal-600 text-white shadow" : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    Asset View
                  </button>
                  <button
                    onClick={() => setDashboardTab("telemetry")}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase transition-all ${
                      dashboardTab === "telemetry" ? "bg-teal-600 text-white shadow" : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
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
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-teal-500 dark:hover:border-teal-400 transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-2 uppercase">Buildings</span>
                      <div className="flex items-end justify-between text-slate-950 dark:text-white">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{buildings.length}</span>
                        <span className="material-symbols-outlined text-slate-400">domain</span>
                      </div>
                    </div>
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-teal-500 dark:hover:border-teal-400 transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-2 uppercase">Total Rooms</span>
                      <div className="flex items-end justify-between text-slate-950 dark:text-white">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{rooms.length}</span>
                        <span className="material-symbols-outlined text-slate-400">door_front</span>
                      </div>
                    </div>
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-teal-500 dark:hover:border-teal-400 transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-2 uppercase">Registered Devices</span>
                      <div className="flex items-end justify-between text-slate-950 dark:text-white">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{devices.length}</span>
                        <span className="material-symbols-outlined text-teal-500">sensors</span>
                      </div>
                    </div>
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 flex flex-col hover:border-teal-500 dark:hover:border-teal-400 transition-colors text-left shadow-sm">
                      <span className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-2 uppercase">Registered Inhabitants</span>
                      <div className="flex items-end justify-between text-slate-950 dark:text-white">
                        <span className="text-headline-lg font-headline-lg font-data-mono">{residents.length}</span>
                        <span className="material-symbols-outlined text-slate-400">badge</span>
                      </div>
                    </div>
                  </div>

                  {/* Collapsible Facility Hierarchy & Device Health Bento card */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                    
                    {/* Collapsible Facility Hierarchy */}
                    <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                      <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-between items-center rounded-t-lg">
                        <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-slate-200 flex items-center gap-2">
                          <span className="material-symbols-outlined text-slate-400">account_tree</span>
                          Facility Hierarchy
                        </h3>
                        <button
                          onClick={expandAllBuildings}
                          className="text-teal-600 dark:text-teal-400 text-label-caps font-label-caps uppercase border border-teal-600 dark:border-teal-400 px-3 py-1 rounded hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-colors"
                        >
                          Expand All
                        </button>
                      </div>
                      
                      <div className="p-6 flex-1 text-left">
                        <ul className="flex flex-col gap-4">
                          {buildings.map(b => (
                            <li key={b.id} className="border border-slate-200 dark:border-slate-800 rounded p-4 bg-slate-50 dark:bg-slate-950">
                              <div
                                onClick={() => toggleBuildingExpand(b.id)}
                                className="flex items-center justify-between cursor-pointer"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="material-symbols-outlined text-slate-500 dark:text-slate-400">business</span>
                                  <span className="text-body-lg font-body-lg font-semibold text-slate-950 dark:text-slate-200">{b.name}</span>
                                </div>
                                <div className="flex items-center gap-4 text-body-md font-body-md text-slate-500 dark:text-slate-400">
                                  <span>{rooms.filter(r => floors.find(f => f.id === r.floor_id)?.building_id === b.id).length} Rooms</span>
                                  <span className="material-symbols-outlined">
                                    {expandedBuildings[b.id] ? "expand_less" : "chevron_right"}
                                  </span>
                                </div>
                              </div>

                              {/* Collapsible Floor list */}
                              {expandedBuildings[b.id] && (
                                <div className="ml-8 mt-2 pl-4 border-l-2 border-slate-200 dark:border-slate-850 flex flex-col gap-2">
                                  {floors.filter(f => f.building_id === b.id).map(f => (
                                    <div key={f.id} className="flex flex-col py-2 border-b border-slate-200/50 dark:border-slate-800 text-xs">
                                      <div className="flex items-center gap-2 text-body-md font-body-md text-slate-850 dark:text-slate-300 mb-1">
                                        <span className="material-symbols-outlined text-sm text-slate-400">layers</span> Floor {f.floor_number}
                                      </div>
                                      <div className="flex flex-wrap gap-2 mt-1">
                                        {rooms.filter(r => r.floor_id === f.id).map(r => (
                                          <span 
                                            key={r.id} 
                                            className="text-label-caps font-label-caps bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded text-slate-700 dark:text-slate-300"
                                            title={`Type: ${r.room_type}`}
                                          >
                                            {r.name}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Device Health Status card */}
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                      <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 rounded-t-lg text-left">
                        <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-slate-200 flex items-center gap-2">
                          <span className="material-symbols-outlined text-teal-500">memory</span>
                          Device Health
                        </h3>
                      </div>
                      
                      <div className="p-0 overflow-x-auto flex-1 text-left">
                        <table className="w-full text-left border-collapse">
                          <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800">
                              <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 uppercase">Device / MAC</th>
                              <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 uppercase">Location</th>
                              <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 uppercase">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {devices.filter(d => {
                              const r = rooms.find(rm => rm.id === d.room_id);
                              if (!r) return orgScope === "all";
                              if (orgScope === "ajce") return r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT");
                              if (orgScope === "lab") return !r.name.includes("MCA") && !r.name.includes("Staff") && !r.name.includes("IoT");
                              return true;
                            }).map(dev => (
                              <tr key={dev.id} className="border-b border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                                <td className="p-4">
                                  <div className="flex flex-col">
                                    <span className="text-body-md font-body-md font-semibold text-slate-950 dark:text-slate-200">{dev.firmware_version}</span>
                                    <span className="text-data-mono font-data-mono text-slate-400">{dev.mac_address}</span>
                                  </div>
                                </td>
                                <td className="p-4 text-body-md font-body-md text-slate-700 dark:text-slate-300">
                                  {rooms.find(r => r.id === dev.room_id)?.name || "Unassigned"}
                                </td>
                                <td className="p-4">
                                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-label-caps font-label-caps ${
                                    dev.device_status === "ONLINE" ? "bg-teal-50 dark:bg-teal-950/20 text-teal-600" : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                                  }`}>
                                    <span className={`w-2 h-2 rounded-full ${dev.device_status === "ONLINE" ? "bg-teal-500 animate-pulse" : "bg-slate-400"}`}></span>
                                    {dev.device_status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 rounded-b-lg flex justify-between items-center text-xs">
                        <span className="text-slate-400">Live hardware nodes active</span>
                        <button
                          onClick={() => {
                            if (devices.length > 0) {
                              setSimDeviceId(devices[0].id);
                              setShowSimulateDrawer(true);
                            }
                          }}
                          className="text-teal-600 dark:text-teal-400 font-semibold hover:underline"
                        >
                          Trigger Simulation
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Access Summary: Staff Distribution */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                    <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-left">
                      <h3 className="text-headline-sm font-headline-sm text-slate-950 dark:text-slate-200 flex items-center gap-2">
                        <span className="material-symbols-outlined text-slate-400">admin_panel_settings</span>
                        Inhabitant Distribution Summary
                      </h3>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                      <div className="flex items-center gap-4 p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-800 dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-slate-400 mb-1">Amal Jyothi MCA block</div>
                          <div className="text-headline-sm font-headline-sm text-slate-950 dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name.includes("MCA") || rooms.find(rm => rm.id === r.room_id)?.name.includes("Staff")).length} Registered
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-800 dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-slate-400 mb-1">Research Lab Care Wing</div>
                          <div className="text-headline-sm font-headline-sm text-slate-950 dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name.includes("Room")).length} Residents
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                        <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-800 dark:text-white">
                          <span className="material-symbols-outlined">layers</span>
                        </div>
                        <div>
                          <div className="text-label-caps font-label-caps text-slate-400 mb-1">Common Ward / Rec Centers</div>
                          <div className="text-headline-sm font-headline-sm text-slate-950 dark:text-slate-200 font-data-mono">
                            {residents.filter(r => rooms.find(rm => rm.id === r.room_id)?.name.includes("Recreation") || rooms.find(rm => rm.id === r.room_id)?.name.includes("Ward")).length} Residents
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
                  
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                    <h3 className="text-xs font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 pb-2 mb-4 text-left dark:text-white">
                      Live Room Occupancy Grid
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {occupancySummary.occupied_room_details.map(rm => (
                        <div
                          key={rm.room_id}
                          className={`border rounded-xl p-3 text-left transition-all ${
                            rm.is_occupied
                              ? rm.current_activity === "Fall_Detected"
                                ? "border-red-500 bg-red-50 dark:bg-red-950/20 animate-pulse"
                                : "border-teal-500 bg-teal-50/50 dark:bg-teal-950/10"
                              : "border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30"
                          }`}
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-bold text-sm truncate dark:text-white">{rm.room_name}</span>
                            <span className={`w-2 h-2 rounded-full ${
                              rm.is_occupied 
                                ? rm.current_activity === "Fall_Detected"
                                  ? "bg-red-500 animate-ping"
                                  : "bg-teal-500" 
                                : "bg-slate-400"
                            }`}></span>
                          </div>
                          <p className="text-[9px] text-slate-400 font-bold uppercase">{rm.room_type}</p>
                          <p className="text-xs font-bold mt-2 text-slate-700 dark:text-slate-300">
                            {rm.is_occupied ? `Activity Classified: ${rm.current_activity.replace("_", " ")}` : "Vacant"}
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
            BUILDINGS VIEW
          ============================================================================ */}
          {currentView === "buildings" && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Registered Buildings</h3>
                <button
                  onClick={() => {
                    if (organizations.length === 0) {
                      alert("Please create an organization first.");
                    } else {
                      setNewBldOrgId(organizations[0].id);
                      setShowAddBuildingModal(true);
                    }
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                >
                  Add Building
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Building Name</th>
                      <th className="p-3">Address</th>
                      <th className="p-3">Building ID</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {buildings.map(bld => (
                      <tr key={bld.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold dark:text-white">{bld.name}</td>
                        <td className="p-3 text-slate-600 dark:text-slate-300">{bld.address || "N/A"}</td>
                        <td className="p-3 font-data-mono text-xs text-slate-400">{bld.id}</td>
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
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Floor Layouts</h3>
                <button
                  onClick={() => {
                    if (buildings.length === 0) {
                      alert("Please create a building first.");
                    } else {
                      setNewFlrBldId(buildings[0].id);
                      setShowAddFloorModal(true);
                    }
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                >
                  Add Floor
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Building Name</th>
                      <th className="p-3">Floor Number</th>
                      <th className="p-3">Floor ID</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {floors.filter(f => {
                      const b = buildings.find(bld => bld.id === f.building_id);
                      return !!b;
                    }).map(flr => (
                      <tr key={flr.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold dark:text-white">{buildings.find(b => b.id === flr.building_id)?.name}</td>
                        <td className="p-3 text-slate-600 dark:text-slate-300">Floor {flr.floor_number}</td>
                        <td className="p-3 font-data-mono text-xs text-slate-400">{flr.id}</td>
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
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Rooms Configuration</h3>
                <button
                  onClick={() => {
                    if (floors.length === 0) {
                      alert("Please create a floor first.");
                    } else {
                      setNewRmFlrId(floors[0].id);
                      setShowAddRoomModal(true);
                    }
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                >
                  Add Room
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Name</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Capacity</th>
                      <th className="p-3">Active Inhabitants</th>
                      <th className="p-3">Room ID</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {rooms.filter(r => {
                      if (orgScope === "ajce") return r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT");
                      if (orgScope === "lab") return !r.name.includes("MCA") && !r.name.includes("Staff") && !r.name.includes("IoT");
                      return true;
                    }).map(rm => (
                      <tr key={rm.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold dark:text-white">{rm.name}</td>
                        <td className="p-3 text-slate-600 dark:text-slate-300">{rm.room_type}</td>
                        <td className="p-3 font-data-mono">{rm.capacity}</td>
                        <td className="p-3 text-xs font-semibold text-teal-600 dark:text-teal-400">
                          {residents.filter(res => res.room_id === rm.id).map(r => `${r.first_name} ${r.last_name}`).join(", ") || "No inhabitants assigned"}
                        </td>
                        <td className="p-3 font-data-mono text-xs text-slate-400">{rm.id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            DEVICES VIEW (INTERACTIVE ONLINE/OFFLINE TOGGLES)
          ============================================================================ */}
          {currentView === "devices" && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">ESP32 CSI Hardware Nodes</h3>
                <button
                  onClick={() => {
                    setNewDevRmId(rooms.length > 0 ? rooms[0].id : "");
                    setShowAddDeviceModal(true);
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                >
                  Register Device
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">MAC Address</th>
                      <th className="p-3">Device Label</th>
                      <th className="p-3">Assigned Location</th>
                      <th className="p-3">Sensing Node Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {devices.filter(d => {
                      const r = rooms.find(rm => rm.id === d.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT");
                      if (orgScope === "lab") return !r.name.includes("MCA") && !r.name.includes("Staff") && !r.name.includes("IoT");
                      return true;
                    }).map(dev => (
                      <tr key={dev.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold font-data-mono dark:text-white">{dev.mac_address}</td>
                        <td className="p-3 text-slate-700 dark:text-slate-350">{dev.firmware_version}</td>
                        <td className="p-3 font-semibold text-xs text-slate-600 dark:text-slate-400">
                          {rooms.find(r => r.id === dev.room_id)?.name || "Unassigned"}
                        </td>
                        <td className="p-3">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-label-caps font-label-caps ${
                            dev.device_status === "ONLINE" ? "bg-teal-50 dark:bg-teal-950/20 text-teal-600" : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                          }`}>
                            <span className={`w-2 h-2 rounded-full ${dev.device_status === "ONLINE" ? "bg-teal-500 animate-pulse" : "bg-slate-400"}`}></span>
                            {dev.device_status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleToggleDevice(dev.id)}
                            className="text-xs font-bold uppercase px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-white"
                          >
                            Toggle Power
                          </button>
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
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Registered Monitored Inhabitants</h3>
                <button
                  onClick={() => {
                    if (rooms.length === 0) {
                      alert("Please create a room first.");
                    } else {
                      setNewResRmId(rooms[0].id);
                      setShowAddResidentModal(true);
                    }
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                >
                  Add Record
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Inhabitant Name</th>
                      <th className="p-3">Assigned Sensing Room</th>
                      <th className="p-3">Record ID</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {residents.filter(res => {
                      const r = rooms.find(rm => rm.id === res.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT");
                      if (orgScope === "lab") return !r.name.includes("MCA") && !r.name.includes("Staff") && !r.name.includes("IoT");
                      return true;
                    }).map(r => (
                      <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-3 font-semibold dark:text-white">{r.first_name} {r.last_name}</td>
                        <td className="p-3 font-semibold text-slate-600 dark:text-slate-450">
                          {rooms.find(rm => rm.id === r.room_id)?.name || "Unassigned"}
                        </td>
                        <td className="p-3 font-data-mono text-xs text-slate-400">{r.id}</td>
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
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Fall Alerts Incident Center</h3>
                <span className="text-[10px] text-slate-400 font-bold uppercase">Incident Status Log</span>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Severity</th>
                      <th className="p-3">Room</th>
                      <th className="p-3">Trigger Type</th>
                      <th className="p-3">Details</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                    {alerts.map(a => (
                      <tr key={a.id} className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 ${a.status === "new" ? "bg-red-50/50 dark:bg-red-950/10" : ""}`}>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                            a.severity === "CRITICAL" ? "bg-red-600 text-white" : "bg-amber-500 text-white"
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="p-3 font-semibold dark:text-white">{rooms.find(rm => rm.id === a.room_id)?.name || "Unknown"}</td>
                        <td className="p-3 font-mono text-xs text-slate-500">{a.event_type}</td>
                        <td className="p-3 text-xs dark:text-slate-300">{a.message}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            a.status === "new"
                              ? "bg-red-100 text-red-700 border border-red-200"
                              : a.status === "acknowledged"
                              ? "bg-teal-50 dark:bg-teal-950/20 text-teal-700 border border-teal-200"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-600"
                          }`}>
                            {a.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex justify-end gap-2">
                            {a.status === "new" && (
                              <button
                                onClick={() => handleAcknowledge(a.id)}
                                className="px-2.5 py-1 border border-teal-600 text-teal-600 rounded-full text-xs font-bold uppercase hover:bg-teal-50 dark:hover:bg-teal-950/20"
                              >
                                Ack
                              </button>
                            )}
                            {a.status !== "resolved" && (
                              <button
                                onClick={() => setShowResolveModal(a.id)}
                                className="px-2.5 py-1 bg-teal-600 text-white rounded-full text-xs font-bold uppercase hover:opacity-90 shadow-sm"
                              >
                                Resolve
                              </button>
                            )}
                            {a.status === "resolved" && (
                              <span className="text-xs text-slate-400 font-semibold">Audit Cleared</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {alerts.length === 0 && (
                      <tr>
                        <td colSpan="6" className="p-4 text-center text-slate-400">No incidents logged. Set organization to WiFi Sense Lab and simulate events to trigger alerts.</td>
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
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">Occupancy Efficiency</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Total Occupancy Rate</span>
                      <span className="font-bold text-teal-600 font-data-mono">{occupancySummary.occupancy_rate}%</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                      <div className="bg-teal-600 h-full rounded-full" style={{ width: `${occupancySummary.occupancy_rate}%` }}></div>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span>{occupancySummary.occupied_rooms} Occupied Rooms</span>
                      <span>{occupancySummary.vacant_rooms} Vacant Rooms</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">Fall Warning Audit History</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-slate-50 dark:bg-slate-950">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Status: Awaiting Ack</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "new").length}</p>
                    </div>
                    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-slate-50 dark:bg-slate-950">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Status: In Progress</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "acknowledged").length}</p>
                    </div>
                    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-slate-50 dark:bg-slate-950">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Status: Resolved</span>
                      <p className="text-xl font-bold font-data-mono mt-1 dark:text-white">{alerts.filter(a => a.status === "resolved").length}</p>
                    </div>
                    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-slate-50 dark:bg-slate-950">
                      <span className="text-[9px] text-slate-400 font-bold uppercase">Total Warnings</span>
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
          
          <div className="relative w-sidebar-width max-w-full h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between shadow-2xl z-10 transition-all">
            <div className="text-left font-sans">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-lg dark:text-white">Simulate Telemetry</h3>
                <button onClick={() => setShowSimulateDrawer(false)} className="material-symbols-outlined text-slate-400">close</button>
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
                Send simulated subcarrier amplitude signals. Note that critical fall options will automatically trigger warnings in elder-care scopes.
              </p>

              <form onSubmit={runSimulation} className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Target Node (Device)</label>
                  <select
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                    value={simDeviceId}
                    onChange={(e) => setSimDeviceId(e.target.value)}
                  >
                    {devices.filter(d => {
                      const r = rooms.find(rm => rm.id === d.room_id);
                      if (!r) return orgScope === "all";
                      if (orgScope === "ajce") return r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT");
                      if (orgScope === "lab") return !r.name.includes("MCA") && !r.name.includes("Staff") && !r.name.includes("IoT");
                      return true;
                    }).map(dev => (
                      <option key={dev.id} value={dev.id}>
                        {dev.firmware_version} ({rooms.find(r => r.id === dev.room_id)?.name})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Subcarrier Pattern</label>
                  <select
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-xs bg-slate-50 dark:bg-slate-800 dark:text-white"
                    value={simActivity}
                    onChange={(e) => setSimActivity(e.target.value)}
                  >
                    {orgScope !== "ajce" && (
                      <option value="Fall_Detected">Fall Detected (CSI Phase Spike)</option>
                    )}
                    <option value="Walking">Walking stance (Active)</option>
                    <option value="Sitting">Sitting stance (Active)</option>
                    <option value="Empty">Empty Room (Vacant)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full mt-6 py-2 bg-teal-600 text-white font-bold uppercase text-xs rounded-full shadow hover:bg-teal-700 transition-colors"
                >
                  Ingest Signal
                </button>
              </form>
            </div>
            
            <p className="text-[9px] text-slate-400 text-left">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Organization</h3>
            <form onSubmit={addOrganization} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Organization Name</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. Sunrise Elder Care"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Deployment Type</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
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
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Building</h3>
            <form onSubmit={addBuilding} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Parent Organization</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newBldOrgId}
                  onChange={(e) => setNewBldOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <option key={org.id} value={org.id}>{org.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Building Name</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. North Wing"
                  value={newBldName}
                  onChange={(e) => setNewBldName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Address</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. AJCE Campus"
                  value={newBldAddress}
                  onChange={(e) => setNewBldAddress(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddBuildingModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Floor</h3>
            <form onSubmit={addFloor} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Parent Building</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newFlrBldId}
                  onChange={(e) => setNewFlrBldId(e.target.value)}
                >
                  {buildings.map(bld => (
                    <option key={bld.id} value={bld.id}>{bld.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Floor Number</label>
                <input
                  type="number"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newFlrNum}
                  onChange={(e) => setNewFlrNum(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddFloorModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Room Layout</h3>
            <form onSubmit={addRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Parent Floor</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
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
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Room Name</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. Research Lab"
                  value={newRmName}
                  onChange={(e) => setNewRmName(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Room Type</label>
                  <select
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                    value={newRmType}
                    onChange={(e) => setNewRmType(e.target.value)}
                  >
                    <option value="Resident Bedroom">Resident Bedroom</option>
                    <option value="Conference Room">Conference Room</option>
                    <option value="Restroom">Restroom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Capacity</label>
                  <input
                    type="number"
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
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
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Register ESP32 CSI Node</h3>
            <form onSubmit={addDevice} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Room Assignment</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newDevRmId}
                  onChange={(e) => setNewDevRmId(e.target.value)}
                >
                  {rooms.map(rm => (
                    <option key={rm.id} value={rm.id}>{rm.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">MAC Address</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  placeholder="e.g. 4C:75:25:AA:BB:CC"
                  value={newDevMac}
                  onChange={(e) => setNewDevMac(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Device Name / Version</label>
                <input
                  type="text"
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newDevFirmware}
                  onChange={(e) => setNewDevFirmware(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddDeviceModal(false)}
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
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
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-4 dark:text-white">Add Resident Record</h3>
            <form onSubmit={addResident} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Assigned Room</label>
                <select
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                  value={newResRmId}
                  onChange={(e) => setNewResRmId(e.target.value)}
                >
                  {rooms.map(rm => (
                    <option key={rm.id} value={rm.id}>{rm.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4 text-left">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">First Name</label>
                  <input
                    type="text"
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
                    value={newResFirst}
                    onChange={(e) => setNewResFirst(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Last Name</label>
                  <input
                    type="text"
                    className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white"
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
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
                  Add Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 7. Resolve Alert Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full text-left shadow-2xl">
            <h3 className="font-bold text-headline-sm mb-2 text-red-600">Resolve Incident Alert</h3>
            <p className="text-xs text-slate-450 mb-4">
              Enter resolution notes to clear the warning banner.
            </p>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Resolution Actions / Notes</label>
                <textarea
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-50 dark:bg-slate-850 dark:text-white h-24"
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
                  className="px-4 py-2 border rounded-full text-xs font-bold uppercase hover:bg-slate-100 dark:text-white dark:border-slate-700"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase">
                  Resolve Alert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. Emergency Protocol Animated Modal */}
      {showEmergencyModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border-2 border-red-500 rounded-2xl p-8 max-w-lg w-full text-center shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-2 bg-red-500 animate-pulse"></div>
            <span className="material-symbols-outlined text-red-500 text-6xl animate-bounce mb-4 block" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
            <h3 className="font-bold text-2xl text-red-600 mb-2 uppercase tracking-wide">Emergency Protocol Activated</h3>
            <p className="text-slate-600 dark:text-slate-350 text-sm mb-6 max-w-sm mx-auto">
              Warning vectors broadcasted to local auxiliary responders. Dispatching caregivers to monitored facilities.
            </p>
            <div className="flex justify-center gap-4">
              <button
                type="button"
                onClick={() => setShowEmergencyModal(false)}
                className="px-6 py-2 border-2 border-slate-300 dark:border-slate-700 rounded-full text-sm font-bold uppercase dark:text-white hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Stand Down
              </button>
              <button 
                onClick={() => {
                  setShowEmergencyModal(false);
                  setToastMessage({ type: "success", text: "Auxiliary backup broadcasted." });
                }}
                className="px-6 py-2 bg-red-600 text-white rounded-full text-sm font-bold uppercase hover:bg-red-700 transition-colors shadow-lg"
              >
                Confirm Dispatch
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
