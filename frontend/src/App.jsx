import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function App() {
  // Authentication State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  
  // Navigation State
  const [currentView, setCurrentView] = useState("dashboard"); // 'dashboard' (Central Monitoring), 'corporate', 'family', 'assets', 'devices', 'residents', 'alerts', 'analytics'
  
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

  // Privacy toggles state for Family Portal view
  const [strictPrivacy, setStrictPrivacy] = useState(false);
  const [contextualVisibility, setContextualVisibility] = useState(true);

  // Analytics Aggregates
  const [occupancySummary, setOccupancySummary] = useState({
    total_rooms: 0,
    occupied_rooms: 0,
    vacant_rooms: 0,
    occupancy_rate: 0,
    occupied_room_details: []
  });

  // Live Simulated Subcarrier Bars array (diagnostics)
  const [subcarriers, setSubcarriers] = useState(Array.from({ length: 40 }, () => 20));

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

  // Animate diagnostics subcarrier stream bars based on current telemetry state
  useEffect(() => {
    const interval = setInterval(() => {
      setSubcarriers(prev => prev.map(val => {
        let noise = Math.random() * 15;
        if (activeTelemetryActivity === "Walking") noise = Math.random() * 45;
        if (activeTelemetryActivity === "Fall_Detected") noise = Math.random() * 75;
        if (activeTelemetryActivity === "Empty") noise = Math.random() * 3;
        
        let base = 20;
        if (activeTelemetryActivity === "Sitting") base = 12;
        if (activeTelemetryActivity === "Fall_Detected") base = 10;
        
        return Math.min(100, Math.max(5, base + noise));
      }));
    }, 150);
    return () => clearInterval(interval);
  }, [activeTelemetryActivity]);

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
              <span className="font-headline-md text-headline-md text-slate-900 dark:text-slate-100 font-bold">Wi-Fi Sense</span>
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
              className="bg-slate-100 dark:bg-slate-900 text-slate-850 dark:text-white text-xs font-bold focus:outline-none"
              value={orgScope}
              onChange={(e) => setOrgScope(e.target.value)}
            >
              <option value="all" className="bg-white dark:bg-slate-900 text-slate-850 dark:text-white">Blesson Byju (System Admin)</option>
              <option value="ajce" className="bg-white dark:bg-slate-900 text-slate-850 dark:text-white">Abhinand M A (AJCE Corporate)</option>
              <option value="lab" className="bg-white dark:bg-slate-900 text-slate-850 dark:text-white">Abhinanth S Pillai (Research Lab Caregiver)</option>
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
                  <button type="button" onClick={() => setIsRegistering(true)} className="text-teal-600 dark:text-teal-400 font-medium text-xs hover:underline font-semibold">
                    Create new registration
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-white bg-teal-600 hover:bg-teal-700 transition-colors font-semibold">
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
          toastMessage.type === "error" ? "bg-red-650 text-white" : "bg-teal-600 text-white"
        }`}>
          <span className="material-symbols-outlined">{toastMessage.type === "error" ? "error" : "check_circle"}</span>
          <span className="text-xs font-bold">{toastMessage.text}</span>
        </div>
      )}

      {/* SideNavbar */}
      <nav className="fixed left-0 top-0 bottom-0 w-sidebar-width flex flex-col z-45 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
        {/* Logo / Header */}
        <div className="p-gutter flex items-center gap-stack-sm border-b border-slate-200 dark:border-slate-800">
          <div className="w-10 h-10 rounded bg-teal-55 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900 flex items-center justify-center text-teal-600 dark:text-teal-400">
            <span className="material-symbols-outlined fill text-[20px]">sensors</span>
          </div>
          <div className="text-left">
            <h1 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold leading-tight">Wi-Fi Sense</h1>
            <p className="text-[10px] text-secondary font-bold uppercase tracking-wider block">AI Monitoring Active</p>
          </div>
        </div>

        {/* Navigation items */}
        <div className="flex-1 overflow-y-auto py-stack-lg px-3 flex flex-col gap-2">
          
          <button
            onClick={() => { setCurrentView("dashboard"); }}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "dashboard" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined fill">sensors</span>
            Live Monitoring
          </button>

          <button
            onClick={() => { setCurrentView("corporate"); }}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "corporate" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">dashboard</span>
            Corporate Staff
          </button>

          <button
            onClick={() => { setCurrentView("family"); }}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "family" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">lock</span>
            Family Portal
          </button>

          <button
            onClick={() => setCurrentView("assets")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "assets" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">business</span> Physical Config
          </button>

          <button
            onClick={() => setCurrentView("residents")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "residents" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">group</span> User Management
          </button>

          <button
            onClick={() => setCurrentView("devices")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "devices" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">router</span> Device Health
          </button>

          <button
            onClick={() => setCurrentView("alerts")}
            className={`flex items-center justify-between gap-stack-sm rounded-lg p-3 text-left w-full transition-all text-xs font-bold uppercase tracking-wider ${
              currentView === "alerts" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-655 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined">history</span> Alert History
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
              currentView === "analytics" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 shadow-sm" : "text-slate-650 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/40"
            }`}
          >
            <span className="material-symbols-outlined">analytics</span> Analytics
          </button>
        </div>

        {/* Sidebar Footer */}
        <div className="p-gutter border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 flex flex-col gap-4">
          <button
            onClick={triggerEmergencyProtocol}
            className="w-full bg-red-650 text-white py-2 px-4 rounded text-xs font-bold uppercase hover:bg-red-750 transition-colors flex items-center justify-center gap-2 shadow-sm font-semibold"
          >
            <span className="material-symbols-outlined text-[18px]">emergency</span>
            Emergency Protocol
          </button>

          <div className="text-left text-xs">
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
        <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 fixed top-0 right-0 left-sidebar-width h-header-height z-30 flex items-center justify-between px-gutter">
          {/* Navigation Links */}
          <div className="flex items-center gap-stack-md h-full text-xs font-bold uppercase tracking-wider">
            <button
              onClick={() => setCurrentView("dashboard")}
              className={`h-full flex items-center px-2 border-b-2 transition-all ${
                currentView === "dashboard" ? "text-teal-600 dark:text-teal-400 border-teal-600 dark:border-teal-400" : "text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-800"
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView("assets")}
              className={`h-full flex items-center px-2 border-b-2 transition-all ${
                currentView === "assets" ? "text-teal-600 dark:text-teal-400 border-teal-600 dark:border-teal-400" : "text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-800"
              }`}
            >
              Heatmaps & Config
            </button>
            <button
              onClick={() => setCurrentView("analytics")}
              className={`h-full flex items-center px-2 border-b-2 transition-all ${
                currentView === "analytics" ? "text-teal-600 dark:text-teal-400 border-teal-600 dark:border-teal-400" : "text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-800"
              }`}
            >
              Reports
            </button>
            <button
              onClick={() => setCurrentView("alerts")}
              className={`h-full flex items-center px-2 border-b-2 transition-all ${
                currentView === "alerts" ? "text-teal-600 dark:text-teal-400 border-teal-600 dark:border-teal-400" : "text-slate-500 dark:text-slate-400 border-transparent hover:text-slate-800"
              }`}
            >
              Alerts
            </button>
          </div>

          <div className="flex items-center gap-gutter">
            {/* Search Input */}
            <div className="relative hidden md:block">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[20px]">search</span>
              <input
                className="pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-body-md focus:outline-none focus:border-teal-500 w-64 text-slate-800 dark:text-white"
                placeholder="Search resources..."
                type="text"
              />
            </div>

            {/* Actions group */}
            <div className="flex items-center gap-stack-sm border-l border-slate-200 dark:border-slate-850 pl-gutter">
              <select
                className="bg-slate-50 dark:bg-slate-800 text-slate-850 dark:text-white text-xs font-bold border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-full focus:outline-none"
                value={orgScope}
                onChange={(e) => setOrgScope(e.target.value)}
              >
                <option value="all" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">Global scope view</option>
                <option value="ajce" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">Amal Jyothi (Corporate)</option>
                <option value="lab" className="bg-white dark:bg-slate-800 text-slate-850 dark:text-white">WiFi Sense Lab (Elder-Care)</option>
              </select>

              <button
                onClick={() => {
                  if (devices.length > 0) {
                    setSimDeviceId(devices[0].id);
                    setShowSimulateDrawer(true);
                  } else {
                    alert("Please register a sensing device first.");
                  }
                }}
                className="text-teal-600 dark:text-teal-400 border border-teal-600 dark:border-teal-450 px-4 py-2 rounded text-xs font-bold uppercase hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-colors"
              >
                Simulate Event
              </button>

              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                title="Toggle Dark Mode Theme"
              >
                <span className="material-symbols-outlined">{darkMode ? "light_mode" : "dark_mode"}</span>
              </button>

              <button
                onClick={() => setCurrentView("alerts")}
                className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors relative"
              >
                <span className="material-symbols-outlined">notifications</span>
                {alerts.filter(a => a.status === "new").length > 0 && (
                  <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
                )}
              </button>

              <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 ml-2 overflow-hidden border border-slate-200 dark:border-slate-800">
                <img alt="User avatar" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCu1RCn5_eg7EySwCBpXG2E5joCiEZy4lvWvSaDVhBHzvt0rhEMs_hZC9HeTPGvt-oJnrDUGlBL2Tb4tYqjlWOP_S4fxlpydOmtf5Y6hG1U2WQnQH1Nx13BotmVTUcmv7sOZtIjEegIXE6g4RZQ-r1PtXh6OM0WxPjorUBfwJig7xcbtg_lExE_t6bnvZfqHinuVSz8lXFPGqEOp_M4YwzZ5a-VISCIKS2DaDPlJ4rqTWUQEtcD5eAXMg"/>
              </div>
            </div>
          </div>
        </header>

        {/* Global Fall Alert Banner */}
        {activeFallAlert && (
          <div className="mt-header-height bg-red-50 border-b border-red-500 text-red-700 dark:bg-red-950/20 dark:text-red-400 p-4 flex items-center justify-between pulse-animation relative z-25">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500 text-2xl fill">warning</span>
              <div className="text-left font-sans">
                <h3 className="text-[10px] font-bold uppercase tracking-wider text-red-650">POTENTIAL FALL ALERT</h3>
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
        <main className={`p-container-padding flex-1 ${activeFallAlert ? "pt-2" : "pt-[64px]"}`}>
          
          {/* ============================================================================
            1. CENTRAL MONITORING VIEW (DEFAULT DASHBOARD)
          ============================================================================ */}
          {currentView === "dashboard" && (
            <div className="space-y-6">
              
              {/* Central Monitoring Dashboard Title Row */}
              <div className="mb-stack-lg flex items-end justify-between">
                <div className="text-left">
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white tracking-tight">Central Monitoring</h2>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">Real-time floor visibility and device telemetry.</p>
                </div>
                <div className="flex items-center gap-2 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded border border-slate-200 dark:border-slate-800">
                  <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
                  System Live
                </div>
              </div>

              {/* Central Monitoring Bento Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter items-start">
                
                {/* Live Feed Table (Spans 8 columns) */}
                <div className="xl:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-sm">
                  <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-between items-center text-left">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white">Live Feed</h3>
                    <span className="material-symbols-outlined text-slate-400">filter_list</span>
                  </div>
                  
                  <div className="overflow-x-auto text-left">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800">
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Location / Subject</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Status</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Activity</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Fall Risk</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Telemetry</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold text-right">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-body-md font-body-md">
                        {occupancySummary.occupied_room_details.map(rm => {
                          const isAlert = rm.is_occupied && rm.current_activity === "Fall_Detected";
                          const isWarning = rm.is_occupied && rm.current_activity === "Sitting"; 
                          return (
                            <tr 
                              key={rm.room_id} 
                              className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                                isAlert ? "bg-red-50/20 dark:bg-red-950/10 border-l-4 border-l-red-500" : isWarning ? "bg-amber-50/20 dark:bg-amber-950/10" : ""
                              }`}
                            >
                              <td className="p-4">
                                <div className="font-headline-sm text-slate-900 dark:text-white font-semibold">{rm.room_name}</div>
                                <div className="text-xs text-slate-500 dark:text-slate-400">
                                  {residents.filter(res => res.room_id === rm.room_id).map(r => `${r.first_name} ${r.last_name}`).join(", ") || "Unassigned"}
                                </div>
                              </td>
                              <td className="p-4">
                                {rm.is_occupied ? (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-50 dark:bg-teal-950/30 text-teal-650 dark:text-teal-400 text-xs font-bold uppercase tracking-wider">
                                    <span className="material-symbols-outlined text-[14px]">person</span>
                                    Occupied
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-bold uppercase tracking-wider">
                                    <span className="material-symbols-outlined text-[14px]">chair</span>
                                    Vacant
                                  </span>
                                )}
                              </td>
                              <td className="p-4 text-slate-800 dark:text-slate-350">
                                {rm.is_occupied ? (
                                  <span className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-slate-400">
                                      {rm.current_activity === "Walking" ? "directions_walk" : rm.current_activity === "Sitting" ? "bed" : "warning"}
                                    </span>
                                    {rm.current_activity.replace("_", " ")}
                                  </span>
                                ) : (
                                  <span className="text-slate-400 italic text-sm">No activity</span>
                                )}
                              </td>
                              <td className="p-4">
                                {rm.is_occupied ? (
                                  rm.current_activity === "Fall_Detected" ? (
                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-red-500 rounded bg-red-600 text-white font-medium text-xs animate-pulse">
                                      Detected
                                    </span>
                                  ) : rm.current_activity === "Sitting" ? (
                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-amber-300 dark:border-amber-700 rounded bg-amber-500 text-white font-medium text-xs">
                                      <span className="material-symbols-outlined text-[16px]">warning</span> Warning
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-slate-200 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 text-xs font-semibold">
                                      <span className="w-2 h-2 rounded-full bg-teal-500"></span> Safe
                                    </span>
                                  )
                                ) : (
                                  <span className="text-slate-400">-</span>
                                )}
                              </td>
                              <td className="p-4">
                                <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 font-medium">
                                  <span className="material-symbols-outlined text-[16px] text-teal-600 dark:text-teal-400">wifi</span> 
                                  {devices.find(d => d.room_id === rm.room_id)?.firmware_version || "ESP-Node"}
                                </div>
                              </td>
                              <td className="p-4 text-right font-data-mono text-data-mono text-slate-500 dark:text-slate-400">
                                {rm.is_occupied ? new Date().toLocaleTimeString() + ".112" : "-"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 text-right text-xs text-slate-500 dark:text-slate-400">
                    Active monitoring grid: {occupancySummary.occupied_rooms} of {occupancySummary.total_rooms} rooms occupied
                  </div>
                </div>

                {/* Side Diagnostics Panel (Spans 4 columns) */}
                <div className="xl:col-span-4 flex flex-col gap-gutter text-left">
                  
                  {/* Device Diagnostics Card */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
                        <span className="material-symbols-outlined text-teal-600 dark:text-teal-400">query_stats</span>
                        Device Diagnostics
                      </h3>
                      <span className="text-label-caps font-label-caps bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded text-slate-500 border border-slate-200 dark:border-slate-700">ESP32-S3</span>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 border-b border-slate-100 dark:border-slate-800 pb-4">
                      Real-time Channel State Information (CSI) variance monitoring for network stability.
                    </p>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850">
                        <div className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-1">Signal Var (σ²)</div>
                        <div className="font-data-mono text-[20px] font-bold text-slate-850 dark:text-white">
                          {activeTelemetryActivity === "Walking" ? "12.45" : activeTelemetryActivity === "Sitting" ? "1.12" : activeTelemetryActivity === "Fall_Detected" ? "89.45" : "0.08"}
                        </div>
                      </div>
                      <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850">
                        <div className="text-label-caps font-label-caps text-slate-400 dark:text-slate-500 mb-1">Packet Drop</div>
                        <div className="font-data-mono text-[20px] font-bold text-teal-650">0.02%</div>
                      </div>
                      <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded border border-slate-200 dark:border-slate-850 col-span-2">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-label-caps font-label-caps text-slate-400">SNR Quality</span>
                          <span className="font-data-mono text-sm text-slate-700 dark:text-slate-300">32 dB</span>
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                          <div className="bg-teal-500 h-1.5 rounded-full" style={{ width: "85%" }}></div>
                        </div>
                      </div>
                    </div>

                    {/* Subcarriers Waveform Bars visualization */}
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
                  </div>

                  {/* Environmental Context Card */}
                  <div className="bg-gradient-to-br from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs">
                    <h4 className="text-body-md font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px]">thermostat</span> Environmental Context
                    </h4>
                    <div className="space-y-3 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 dark:text-slate-400">Floor Interference</span>
                        <span className="font-data-mono bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-750 text-slate-700 dark:text-slate-300">Low</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 dark:text-slate-400">Active Anchors</span>
                        <span className="font-data-mono text-slate-700 dark:text-slate-350">{devices.filter(d => d.device_status === "ONLINE").length} / {devices.length}</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* ============================================================================
            1.1 CORPORATE FACILITY STAFF DASHBOARD
          ============================================================================ */}
          {currentView === "corporate" && (
            <div className="space-y-6 text-left">
              {/* Header Section */}
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Facility Overview</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400 mt-1">Real-time occupancy and environmental metrics for floor 4.</p>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1 font-bold"><span className="w-2 h-2 rounded-full bg-teal-500 block animate-pulse"></span> Live Feed Active</span>
                  <span className="text-slate-300 dark:text-slate-700">|</span>
                  <span>Last updated: Just now</span>
                </div>
              </div>

              {/* Metrics Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-teal-55 transition-colors duration-300 shadow-xs">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <span className="material-symbols-outlined text-6xl text-slate-400">show_chart</span>
                  </div>
                  <h3 className="text-label-caps font-label-caps text-slate-400 dark:text-slate-550 uppercase mb-2">Peak Utilization</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">88%</span>
                    <span className="text-body-md text-teal-600 font-semibold flex items-center">
                      <span className="material-symbols-outlined text-[16px]">arrow_upward</span> 4%
                    </span>
                  </div>
                  <p className="text-xs text-slate-450 mt-2">Between 10:00 AM - 2:00 PM</p>
                </div>

                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-teal-55 transition-colors duration-300 shadow-xs">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <span className="material-symbols-outlined text-6xl text-slate-400">meeting_room</span>
                  </div>
                  <h3 className="text-label-caps font-label-caps text-slate-400 dark:text-slate-550 uppercase mb-2">Underutilized Rooms</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
                      {rooms.filter(r => residents.filter(res => res.room_id === r.id).length === 0).length || 4}
                    </span>
                    <span className="text-body-md text-slate-500 dark:text-slate-400">/ {rooms.length || 42} total</span>
                  </div>
                  <p className="text-xs text-slate-455 mt-2">Rooms &lt;10% usage this week</p>
                </div>

                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 relative overflow-hidden group hover:border-teal-55 transition-colors duration-300 shadow-xs">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <span className="material-symbols-outlined text-6xl text-slate-400">eco</span>
                  </div>
                  <h3 className="text-label-caps font-label-caps text-slate-400 dark:text-slate-550 uppercase mb-2">Energy Savings Est.</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-headline-lg font-headline-lg text-teal-650 dark:text-teal-400 font-bold">15%</span>
                  </div>
                  <p className="text-xs text-slate-455 mt-2">Potential savings via HVAC optimization</p>
                </div>
              </div>

              {/* Complex Layout Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                
                {/* Real-time Meeting Room Status Table */}
                <div className="xl:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-xs">
                  <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-900">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Real-time Meeting Room Status</h3>
                    <button 
                      onClick={() => setCurrentView("assets")}
                      className="text-teal-650 dark:text-teal-450 hover:text-teal-700 transition-colors text-xs font-bold uppercase flex items-center gap-1"
                    >
                      View All <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800">
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Room Name</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Capacity</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold">Status</th>
                          <th className="p-4 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 font-semibold text-right">Duration</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-body-md">
                        {rooms.filter(r => r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT") || r.name.includes("Boardroom")).map((rm, i) => {
                          const isOccupied = i % 2 === 0;
                          return (
                            <tr key={rm.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                              <td className="p-4 font-semibold text-slate-900 dark:text-white">{rm.name}</td>
                              <td className="p-4 text-slate-500 dark:text-slate-400">{rm.capacity}</td>
                              <td className="p-4">
                                {isOccupied ? (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 text-xs font-semibold">
                                    <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span> Occupied
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 text-xs font-semibold">
                                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span> Vacant
                                  </span>
                                )}
                              </td>
                              <td className="p-4 text-right font-data-mono text-data-mono text-slate-500 dark:text-slate-400">
                                {isOccupied ? `${12 + i * 8}m 05s` : `${2 + i}h 15m`}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Side Underutilized Spaces Card */}
                <div className="flex flex-col gap-6">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex flex-col h-full shadow-xs">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Underutilized Spaces</h3>
                      <span className="material-symbols-outlined text-slate-400 cursor-pointer hover:text-slate-650 transition-colors">info</span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">&lt;10% usage over the last 7 days.</p>
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white text-sm">Training Room B</p>
                          <p className="text-xs text-slate-450">Capacity: 20</p>
                        </div>
                        <div className="text-right">
                          <p className="text-red-500 font-bold text-sm">4%</p>
                          <p className="text-[9px] text-slate-400 uppercase font-bold">Usage</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white text-sm">Huddle C</p>
                          <p className="text-xs text-slate-450">Capacity: 3</p>
                        </div>
                        <div className="text-right">
                          <p className="text-red-500 font-bold text-sm">7%</p>
                          <p className="text-[9px] text-slate-400 uppercase font-bold">Usage</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950">
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white text-sm">Exec Office 4A</p>
                          <p className="text-xs text-slate-455">Capacity: 1</p>
                        </div>
                        <div className="text-right">
                          <p className="text-red-500 font-bold text-sm">9%</p>
                          <p className="text-[9px] text-slate-400 uppercase font-bold">Usage</p>
                        </div>
                      </div>
                    </div>
                    <button 
                      onClick={() => setToastMessage({ type: "success", text: "Repurposing report compiled & downloaded." })}
                      className="mt-4 w-full py-2 border border-teal-600 text-teal-600 rounded-lg text-xs font-bold uppercase hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors shadow-2xs"
                    >
                      Generate Repurposing Report
                    </button>
                  </div>
                </div>

              </div>

              {/* Utilization Analytics Bar Chart */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-xs">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Utilization Analytics (24h)</h3>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 bg-slate-100 dark:bg-slate-800 border border-slate-250 dark:border-slate-700 rounded text-xs font-semibold text-slate-850 dark:text-white">Today</button>
                    <button className="px-3 py-1 border border-slate-200 dark:border-slate-850 rounded text-xs font-semibold text-slate-500 hover:bg-slate-50 transition-colors">Week</button>
                  </div>
                </div>

                <div className="w-full h-64 rounded-lg bg-slate-50 dark:bg-slate-950 flex items-end relative border-l border-b border-slate-200 dark:border-slate-800 px-2 pt-2">
                  {/* Y Axis Labels */}
                  <div className="absolute left-[-35px] top-0 bottom-0 flex flex-col justify-between text-[10px] py-2 font-data-mono text-slate-400">
                    <span>100%</span>
                    <span>75%</span>
                    <span>50%</span>
                    <span>25%</span>
                    <span>0%</span>
                  </div>

                  {/* Chart Bars */}
                  <div className="flex-1 flex items-end justify-between h-full px-4 gap-1 sm:gap-2">
                    {[5, 15, 40, 75, 88, 85, 82, 60, 70, 45, 20, 10].map((h, i) => {
                      const colorClass = h > 80 ? "bg-teal-700" : h > 40 ? "bg-teal-500" : "bg-teal-200 opacity-60";
                      const timeLabel = ["6am", "7am", "8am", "9am", "10am", "11am", "12pm", "1pm", "2pm", "3pm", "4pm", "5pm"][i];
                      return (
                        <div key={i} className={`w-full ${colorClass} rounded-t-xs relative group transition-all`} style={{ height: `${h}%` }}>
                          <div className="hidden group-hover:block absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white text-[10px] font-bold px-2 py-1 rounded whitespace-nowrap z-10">
                            {timeLabel}: {h}%
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* X Axis Labels */}
                  <div className="absolute -bottom-6 left-0 right-0 flex justify-between px-6 text-[10px] font-data-mono text-slate-450">
                    <span>6 AM</span>
                    <span>9 AM</span>
                    <span>12 PM</span>
                    <span>3 PM</span>
                    <span>6 PM</span>
                  </div>
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-6 mt-10 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-teal-700"></span>
                    <span className="text-slate-500 dark:text-slate-400">Peak (&gt;80%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-teal-500"></span>
                    <span className="text-slate-500 dark:text-slate-400">Moderate (40-80%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-teal-200"></span>
                    <span className="text-slate-500 dark:text-slate-400">Low (&lt;40%)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            1.2 FAMILY PORTAL / ACCESS CONTROL VIEW
          ============================================================================ */}
          {currentView === "family" && (
            <div className="space-y-6 text-left">
              {/* Page Header */}
              <div className="mb-stack-lg flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                  <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white mb-1">Access Control &amp; Privacy</h1>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400">Configure family member visibility and manage privacy settings for resident monitoring.</p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => setToastMessage({ type: "success", text: "Privacy audit log exported." })}
                    className="px-4 py-2 border border-slate-200 dark:border-slate-800 text-slate-750 dark:text-white rounded-lg text-xs font-bold uppercase hover:bg-slate-100 dark:hover:bg-slate-850 transition-colors shadow-2xs"
                  >
                    Export Logs
                  </button>
                  <button 
                    onClick={() => setToastMessage({ type: "success", text: "Privacy configurations saved." })}
                    className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-bold uppercase hover:opacity-90 transition-opacity"
                  >
                    Save Changes
                  </button>
                </div>
              </div>

              {/* Bento Grid Layout */}
              <div className="grid grid-cols-12 gap-gutter">
                
                {/* Privacy Guarantee Hero Card (Span 8) */}
                <div className="col-span-12 lg:col-span-8 bg-teal-50/40 dark:bg-teal-950/10 rounded-xl border border-slate-200 dark:border-slate-800 p-8 relative overflow-hidden flex flex-col justify-between shadow-xs">
                  {/* Decorative Wi-Fi wave background element */}
                  <div className="absolute -right-20 -top-20 w-64 h-64 border-[40px] border-teal-100 dark:border-teal-950/30 rounded-full opacity-40"></div>
                  <div className="absolute -right-10 -top-10 w-48 h-48 border-[30px] border-teal-100 dark:border-teal-950/20 rounded-full opacity-30"></div>
                  
                  <div className="relative z-10">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-800 mb-6 shadow-2xs">
                      <span className="material-symbols-outlined text-[16px] text-teal-600 dark:text-teal-400">verified_user</span>
                      <span className="text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">Core Principle</span>
                    </div>
                    <h2 className="text-headline-md font-headline-md text-slate-950 dark:text-white mb-4 max-w-lg font-bold leading-snug">
                      Invisible Security. Zero Cameras. Absolute Privacy.
                    </h2>
                    <p className="text-sm text-slate-600 dark:text-slate-350 max-w-xl mb-6">
                      Wi-Fi Sense relies entirely on Channel State Information (CSI) from ambient radio waves. 
                      It detects movement, breathing patterns, and falls mathematically, without capturing any optical images or audio.
                    </p>
                  </div>

                  <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200/50 dark:border-slate-800">
                      <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 mb-2">videocam_off</span>
                      <div className="text-sm font-bold text-slate-900 dark:text-white">No Cameras</div>
                      <div className="text-xs text-slate-450 dark:text-slate-500 mt-1">100% optical privacy</div>
                    </div>
                    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200/50 dark:border-slate-800">
                      <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 mb-2">mic_off</span>
                      <div className="text-sm font-bold text-slate-900 dark:text-white">No Microphones</div>
                      <div className="text-xs text-slate-450 dark:text-slate-500 mt-1">No audio recorded</div>
                    </div>
                    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200/50 dark:border-slate-800">
                      <span className="material-symbols-outlined text-teal-600 dark:text-teal-400 mb-2">lock</span>
                      <div className="text-sm font-bold text-slate-900 dark:text-white">Encrypted CSI</div>
                      <div className="text-xs text-slate-455 dark:text-slate-500 mt-1">Data mathematically hashed</div>
                    </div>
                  </div>
                </div>

                {/* Global Alert Status (Span 4) */}
                <div className="col-span-12 lg:col-span-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-xs">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Facility Status</h3>
                    <span className="material-symbols-outlined text-slate-400">more_vert</span>
                  </div>

                  <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950">
                    <div className="w-16 h-16 bg-teal-50 dark:bg-teal-950/20 rounded-full flex items-center justify-center mb-4 border border-teal-100 dark:border-teal-900">
                      <span className="material-symbols-outlined text-[32px] text-teal-600 dark:text-teal-400 fill">health_and_safety</span>
                    </div>
                    <div className="text-headline-sm font-headline-sm text-slate-950 dark:text-white mb-2">All Clear</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {activeFallAlert ? "Active warning alert on elder sector. Responders active." : "No active environmental or health alerts detected across monitored zones."}
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-xs">
                    <span className="text-slate-400">Last Scan:</span>
                    <span className="text-data-mono font-data-mono text-teal-650 dark:text-teal-400 font-semibold">LIVE • 10ms latency</span>
                  </div>
                </div>

                {/* Family Member Portal Preview (Span 6) */}
                <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-xs">
                  <div className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 p-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-slate-500">preview</span>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">Family Portal Preview</h3>
                    </div>
                    <span className="text-[10px] text-slate-400 bg-white dark:bg-slate-800 border dark:border-slate-700 px-2 py-0.5 rounded font-bold uppercase">Restricted View</span>
                  </div>

                  <div className="p-6 flex-1 bg-slate-50/50 dark:bg-slate-950/20 flex items-center justify-center">
                    {/* Simulated Mobile Device View */}
                    <div className="w-full max-w-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2rem] shadow-xl overflow-hidden flex flex-col h-[340px]">
                      <div className="h-10 bg-slate-50 dark:bg-slate-850 flex justify-center items-center border-b border-slate-200 dark:border-slate-800">
                        <div className="w-16 h-1 bg-slate-350 dark:bg-slate-750 rounded-full"></div>
                      </div>
                      <div className="p-5 flex-1 overflow-y-auto text-left flex flex-col justify-between">
                        <div>
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Resident Status</h4>
                          
                          {/* Resident Card */}
                          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg p-3">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <div className="text-sm font-bold text-slate-900 dark:text-white">
                                  {residents.length > 0 ? `${residents[0].first_name} ${residents[0].last_name}` : "Mary Smith"}
                                </div>
                                <div className="text-[10px] text-slate-500">
                                  {rooms.find(rm => rm.id === residents[0]?.room_id)?.name || "Room 102"}
                                </div>
                              </div>
                              <span className="bg-teal-50 dark:bg-teal-950/30 text-teal-650 dark:text-teal-400 px-2 py-0.5 rounded text-[10px] font-bold border border-teal-200/20 flex items-center gap-1">
                                <span className="material-symbols-outlined text-[12px]">bed</span> Resting
                              </span>
                            </div>
                            <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden mb-2">
                              <div className="bg-teal-500 h-full w-3/4 rounded-full opacity-60"></div>
                            </div>
                            <div className="text-[10px] font-mono text-slate-400">Respiration Normal • No erratic movement</div>
                          </div>
                        </div>

                        {/* Simplified Alert */}
                        <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg p-3 flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center text-teal-600 dark:text-teal-400">
                            <span className="material-symbols-outlined text-[16px] fill">check</span>
                          </div>
                          <div>
                            <div className="text-xs font-bold text-slate-900 dark:text-white">Safe Status</div>
                            <div className="text-[10px] text-slate-450">No active warnings.</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Access Control Settings (Span 6) */}
                <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-xs">
                  <div className="mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold mb-1">Visibility Settings</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Manage what external contacts can see via the portal.</p>
                  </div>

                  <div className="flex-1 space-y-4">
                    {/* Setting 1 */}
                    <div 
                      onClick={() => {
                        setStrictPrivacy(!strictPrivacy);
                        setToastMessage({ type: "success", text: `Strict Privacy Mode ${!strictPrivacy ? "Enabled" : "Disabled"}` });
                      }}
                      className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer ${
                        strictPrivacy ? "border-teal-600 bg-teal-50/10" : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950"
                      }`}
                    >
                      <div className="flex gap-4">
                        <span className="material-symbols-outlined text-slate-400 mt-1">visibility_off</span>
                        <div>
                          <div className="text-sm font-bold text-slate-950 dark:text-white">Strict Privacy Mode</div>
                          <div className="text-xs text-slate-500 dark:text-slate-450 mt-1 max-w-xs">
                            Family sees only generic "Safe" / "Requires Attention" states. No location or activity details.
                          </div>
                        </div>
                      </div>
                      <div className={`w-10 h-6 flex items-center rounded-full p-0.5 transition-colors ${strictPrivacy ? "bg-teal-600" : "bg-slate-350"}`}>
                        <div className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-transform ${strictPrivacy ? "translate-x-4" : "translate-x-0"}`}></div>
                      </div>
                    </div>

                    {/* Setting 2 (Active) */}
                    <div 
                      onClick={() => {
                        setContextualVisibility(!contextualVisibility);
                        setToastMessage({ type: "success", text: `Contextual Visibility ${!contextualVisibility ? "Enabled" : "Disabled"}` });
                      }}
                      className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer ${
                        contextualVisibility ? "border-teal-600 bg-teal-50/10" : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950"
                      }`}
                    >
                      <div className="flex gap-4">
                        <span className="material-symbols-outlined text-teal-650 dark:text-teal-400 mt-1">visibility</span>
                        <div>
                          <div className="text-sm font-bold text-slate-950 dark:text-white">Contextual Visibility</div>
                          <div className="text-xs text-slate-500 dark:text-slate-450 mt-1 max-w-xs">
                            Family sees current room location and basic activity state (Resting, Active, Away).
                          </div>
                        </div>
                      </div>
                      <div className={`w-10 h-6 flex items-center rounded-full p-0.5 transition-colors ${contextualVisibility ? "bg-teal-600" : "bg-slate-350"}`}>
                        <div className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-transform ${contextualVisibility ? "translate-x-4" : "translate-x-0"}`}></div>
                      </div>
                    </div>

                    {/* Authorization List Table */}
                    <div className="mt-8">
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Authorized Contacts</h4>
                      <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                        <table className="w-full text-left border-collapse">
                          <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-850 text-[10px] text-slate-400 font-bold uppercase">
                            <tr>
                              <th className="py-2 px-4">Name</th>
                              <th className="py-2 px-4">Relation</th>
                              <th className="py-2 px-4">Access Level</th>
                              <th className="py-2 px-4 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="text-xs text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-900 divide-y divide-slate-100 dark:divide-slate-800">
                            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                              <td className="py-3 px-4 font-semibold">John Smith</td>
                              <td className="py-3 px-4 text-slate-500 dark:text-slate-400">Son</td>
                              <td className="py-3 px-4">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 uppercase">Contextual</span>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button className="text-teal-600 dark:text-teal-400 hover:underline font-bold">Edit</button>
                              </td>
                            </tr>
                            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                              <td className="py-3 px-4 font-semibold">Blesson Joseph Byju</td>
                              <td className="py-3 px-4 text-slate-500 dark:text-slate-400">System Admin</td>
                              <td className="py-3 px-4">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 uppercase">Full Access</span>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button className="text-teal-600 dark:text-teal-400 hover:underline font-bold">Edit</button>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                  </div>
                </div>

              </div>
            </div>
          )}

          {/* ============================================================================
            2. PHYSICAL CONFIG VIEW
          ============================================================================ */}
          {currentView === "assets" && (
            <div className="space-y-6 text-left">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white mb-1 font-bold">Physical Configuration</h2>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400">Hierarchical database mappings of physical deployment structures.</p>
                </div>
              </div>

              {/* Grid of details */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                
                {/* Collapsible Facility Hierarchy accordion card */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg flex flex-col shadow-sm">
                  <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-between items-center rounded-t-lg">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
                      <span className="material-symbols-outlined text-slate-400">account_tree</span>
                      Facility Hierarchy
                    </h3>
                    <button
                      onClick={expandAllBuildings}
                      className="text-teal-600 dark:text-teal-400 text-label-caps font-label-caps uppercase border border-teal-600 dark:border-teal-400 px-3 py-1 rounded hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-colors font-semibold"
                    >
                      Expand All
                    </button>
                  </div>
                  
                  <div className="p-6 flex-1">
                    <ul className="flex flex-col gap-4">
                      {buildings.map(b => (
                        <li key={b.id} className="border border-slate-200 dark:border-slate-800 rounded p-4 bg-slate-50 dark:bg-slate-950">
                          <div
                            onClick={() => toggleBuildingExpand(b.id)}
                            className="flex items-center justify-between cursor-pointer"
                          >
                            <div className="flex items-center gap-2">
                              <span className="material-symbols-outlined text-slate-500 dark:text-slate-400">business</span>
                              <span className="text-body-lg font-body-lg font-semibold text-slate-955 dark:text-slate-200">{b.name}</span>
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
                                  <div className="flex items-center gap-2 text-body-md font-body-md text-slate-850 dark:text-slate-300">
                                    <span className="material-symbols-outlined text-sm text-slate-400">layers</span> Floor {f.floor_number}
                                  </div>
                                  <div className="flex flex-wrap gap-2 mt-1">
                                    {rooms.filter(r => r.floor_id === f.id).map(r => (
                                      <span key={r.id} className="text-label-caps font-label-caps bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-750 px-2.5 py-0.5 rounded text-slate-700 dark:text-slate-300 font-semibold">
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

                {/* Add Quick Asset Options */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-sm flex flex-col gap-4">
                  <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold border-b border-slate-100 dark:border-slate-800 pb-2">
                    Configuration Actions
                  </h3>
                  <button
                    onClick={() => setShowAddOrgModal(true)}
                    className="w-full text-xs font-bold uppercase border border-slate-250 dark:border-slate-700 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-855 transition-colors text-slate-800 dark:text-white flex items-center gap-2 justify-center"
                  >
                    <span className="material-symbols-outlined text-sm">corporate_fare</span>
                    Add Organization
                  </button>
                  <button
                    onClick={() => {
                      if (organizations.length > 0) {
                        setNewBldOrgId(organizations[0].id);
                        setShowAddBuildingModal(true);
                      }
                    }}
                    className="w-full text-xs font-bold uppercase border border-slate-250 dark:border-slate-700 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-855 transition-colors text-slate-800 dark:text-white flex items-center gap-2 justify-center"
                  >
                    <span className="material-symbols-outlined text-sm">business</span>
                    Add Building
                  </button>
                  <button
                    onClick={() => {
                      if (buildings.length > 0) {
                        setNewFlrBldId(buildings[0].id);
                        setShowAddFloorModal(true);
                      }
                    }}
                    className="w-full text-xs font-bold uppercase border border-slate-255 dark:border-slate-700 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-855 transition-colors text-slate-800 dark:text-white flex items-center gap-2 justify-center"
                  >
                    <span className="material-symbols-outlined text-sm">layers</span>
                    Add Floor
                  </button>
                  <button
                    onClick={() => {
                      if (floors.length > 0) {
                        setNewRmFlrId(floors[0].id);
                        setShowAddRoomModal(true);
                      }
                    }}
                    className="w-full text-xs font-bold uppercase border border-slate-255 dark:border-slate-700 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-855 transition-colors text-slate-800 dark:text-white flex items-center gap-2 justify-center"
                  >
                    <span className="material-symbols-outlined text-sm">meeting_room</span>
                    Add Room
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            3. DEVICE HEALTH VIEW
          ============================================================================ */}
          {currentView === "devices" && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm text-left">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">ESP32 Hardware Nodes</h3>
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
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">MAC Address</th>
                      <th className="p-3">Device Label</th>
                      <th className="p-3">Assigned Room</th>
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
                      <tr key={dev.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="p-3 font-semibold font-data-mono dark:text-white">{dev.mac_address}</td>
                        <td className="p-3 text-slate-700 dark:text-slate-350">{dev.firmware_version}</td>
                        <td className="p-3 font-semibold text-xs text-slate-650 dark:text-slate-400">
                          {rooms.find(r => r.id === dev.room_id)?.name || "Unassigned"}
                        </td>
                        <td className="p-3">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-label-caps font-label-caps ${
                            dev.device_status === "ONLINE" ? "bg-teal-50 dark:bg-teal-950/20 text-teal-650" : "bg-slate-105 dark:bg-slate-800 text-slate-500"
                          }`}>
                            <span className={`w-2 h-2 rounded-full ${dev.device_status === "ONLINE" ? "bg-teal-500 animate-pulse" : "bg-slate-400"}`}></span>
                            {dev.device_status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleToggleDevice(dev.id)}
                            className="text-xs font-bold uppercase px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-white shadow-xs"
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
            4. RESIDENTS / USER MANAGEMENT VIEW
          ============================================================================ */}
          {currentView === "residents" && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm text-left">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">User & Resident Profiles</h3>
                <button
                  onClick={() => {
                    if (rooms.length === 0) {
                      alert("Please create a room first.");
                    } else {
                      setNewResRmId(rooms[0].id);
                      setShowAddResidentModal(true);
                    }
                  }}
                  className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700 font-semibold"
                >
                  Add Record
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                      <th className="p-3">Full Name</th>
                      <th className="p-3">Assigned Room Location</th>
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
                      <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="p-3 font-semibold dark:text-white">{r.first_name} {r.last_name}</td>
                        <td className="p-3 font-semibold text-slate-600 dark:text-slate-400">
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
            5. ALERTS VIEW
          ============================================================================ */}
          {currentView === "alerts" && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm text-left">
              <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">Fall Alerts Incident Center</h3>
                <span className="text-[10px] text-slate-400 font-bold uppercase">Incident Status Log</span>
              </div>
              <div className="overflow-x-auto">
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
                            a.severity === "CRITICAL" ? "bg-red-650 text-white" : "bg-amber-500 text-white"
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="p-3 font-semibold dark:text-white">{rooms.find(rm => rm.id === a.room_id)?.name || "Unknown"}</td>
                        <td className="p-3 font-mono text-xs text-slate-500">{a.event_type}</td>
                        <td className="p-3 text-xs dark:text-slate-350">{a.message}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            a.status === "new"
                              ? "bg-red-100 text-red-700 border border-red-200"
                              : a.status === "acknowledged"
                              ? "bg-teal-50 dark:bg-teal-950/20 text-teal-700 border border-teal-200"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-605"
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
            6. ANALYTICS VIEW
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
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2 mb-4 font-semibold">Fall Warning Audit History</h3>
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
        <div className="fixed inset-0 z-50 flex justify-end animate-fade-in">
          <div onClick={() => setShowSimulateDrawer(false)} className="absolute inset-0 bg-slate-900/65 backdrop-blur-xs"></div>
          
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
                  <label className="block text-[10px] font-bold uppercase text-slate-400 mb-1">Target Device Node</label>
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
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase font-semibold">
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
                    className="w-full border border-slate-200 dark:border-slate-805 rounded p-2 text-sm bg-slate-55 dark:bg-slate-800 dark:text-white"
                    value={newResFirst}
                    onChange={(e) => setNewResFirst(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Last Name</label>
                  <input
                    type="text"
                    className="w-full border border-slate-200 dark:border-slate-805 rounded p-2 text-sm bg-slate-55 dark:bg-slate-800 dark:text-white"
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
                <button type="submit" className="px-4 py-2 bg-teal-600 text-white rounded-full text-xs font-bold uppercase font-semibold">
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
            <h3 className="font-bold text-headline-sm mb-2 text-red-650 font-semibold">Resolve Incident Alert</h3>
            <p className="text-xs text-slate-455 mb-4">
              Enter resolution notes to clear the warning banner.
            </p>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-400 mb-1">Resolution Actions / Notes</label>
                <textarea
                  className="w-full border border-slate-200 dark:border-slate-800 rounded p-2 text-sm bg-slate-55 dark:bg-slate-850 dark:text-white h-24"
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
            <h3 className="font-bold text-2xl text-red-650 mb-2 uppercase tracking-wide">Emergency Protocol Activated</h3>
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
                className="px-6 py-2 bg-red-650 text-white rounded-full text-sm font-bold uppercase hover:bg-red-750 transition-colors shadow-lg"
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
