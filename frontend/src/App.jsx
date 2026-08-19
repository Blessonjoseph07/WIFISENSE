import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function App() {
  // Authentication State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  
  // Navigation State
  const [currentView, setCurrentView] = useState("dashboard"); // 'dashboard', 'organizations', 'buildings', 'floors', 'rooms', 'devices', 'residents', 'live', 'alerts', 'analytics'
  
  // Asset Collections (Loaded from Real APIs)
  const [organizations, setOrganizations] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [floors, setFloors] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [devices, setDevices] = useState([]);
  const [residents, setResidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
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
  const [showSimulateModal, setShowSimulateModal] = useState(false);
  const [showAddOrgModal, setShowAddOrgModal] = useState(false);
  const [showAddBuildingModal, setShowAddBuildingModal] = useState(false);
  const [showAddFloorModal, setShowAddFloorModal] = useState(false);
  const [showAddRoomModal, setShowAddRoomModal] = useState(false);
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false);
  const [showAddResidentModal, setShowAddResidentModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(null); // stores alert ID

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

  // Global Notification Banner (For real-time visual alerts like Falls)
  const [activeFallAlert, setActiveFallAlert] = useState(null);

  // Standard API Headers
  const getHeaders = () => {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
  };

  // ============================================================================
  // LOAD DATA FROM BACKEND
  // ============================================================================
  const fetchAllData = async () => {
    if (!token) return;
    try {
      const headers = getHeaders();

      // Fetch Analytics Summary (Real Occupancy & Alert Stats)
      const occRes = await fetch(`${API_BASE}/analytics/occupancy-summary`, { headers });
      if (occRes.ok) {
        const data = await occRes.json();
        setOccupancySummary(data);
      }

      const alertSumRes = await fetch(`${API_BASE}/analytics/alert-summary`, { headers });
      if (alertSumRes.ok) {
        const data = await alertSumRes.json();
        setAlertSummary(data);
      }

      // Fetch Alerts List
      const alertRes = await fetch(`${API_BASE}/alerts`, { headers });
      if (alertRes.ok) {
        const data = await alertRes.json();
        setAlerts(data);
        // Set active fall alert if there's any unresolved critical fall alert
        const activeFall = data.find(a => a.event_type === "Fall_Detected" && a.status !== "resolved");
        setActiveFallAlert(activeFall || null);
      }

      // Fetch Asset collections based on navigation view
      const orgRes = await fetch(`${API_BASE}/organizations`, { headers });
      if (orgRes.ok) setOrganizations(await orgRes.json());

      const bldRes = await fetch(`${API_BASE}/buildings`, { headers });
      if (bldRes.ok) setBuildings(await bldRes.json());

      const flrRes = await fetch(`${API_BASE}/floors`, { headers });
      if (flrRes.ok) setFloors(await flrRes.json());

      const rmRes = await fetch(`${API_BASE}/rooms`, { headers });
      if (rmRes.ok) setRooms(await rmRes.json());

      const devRes = await fetch(`${API_BASE}/devices`, { headers });
      if (devRes.ok) setDevices(await devRes.json());

      const resRes = await fetch(`${API_BASE}/residents`, { headers });
      if (resRes.ok) setResidents(await resRes.json());

    } catch (err) {
      console.error("Error loading backend records: ", err);
    }
  };

  // Poll for live alerts & telemetry updates every 4 seconds
  useEffect(() => {
    if (token) {
      fetchAllData();
      const interval = setInterval(fetchAllData, 4000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // ============================================================================
  // AUTH ROUTINES
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
      // Automatically prefill email for login
      setLoginEmail(regEmail);
      alert("Registration successful! Please login with your password.");
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
  // SIMULATION PIPELINE API
  // ============================================================================
  const runSimulation = async (e) => {
    e.preventDefault();
    if (!simDeviceId) {
      alert("Please select or register a device first.");
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
      setShowSimulateModal(false);
      fetchAllData();
      alert(`Simulation completed!\nActivity: ${data.activity_classified}\nPresence Check: ${data.presence_detected ? "Detected" : "Vacant"}\nAlert Triggered: ${data.alert_triggered ? "Yes (CRITICAL)" : "No"}`);
    } catch (err) {
      alert(err.message);
    }
  };

  // ============================================================================
  // ALERT ACTION HANDLERS
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
    } catch (err) {
      alert(err.message);
    }
  };

  // ============================================================================
  // ASSETS CREATION HANDLERS
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
        throw new Error(errData.detail || "Could not create Organization.");
      }
      setNewOrgName("");
      setShowAddOrgModal(false);
      fetchAllData();
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
        throw new Error(errData.detail || "Could not create Building.");
      }
      setNewBldName("");
      setNewBldAddress("");
      setShowAddBuildingModal(false);
      fetchAllData();
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
        throw new Error(errData.detail || "Could not create Floor.");
      }
      setShowAddFloorModal(false);
      fetchAllData();
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
        throw new Error(errData.detail || "Could not create Room.");
      }
      setNewRmName("");
      setShowAddRoomModal(false);
      fetchAllData();
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
        throw new Error(errData.detail || "Could not register Device.");
      }
      setNewDevMac("");
      setShowAddDeviceModal(false);
      fetchAllData();
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
        throw new Error(errData.detail || "Could not register Resident.");
      }
      setNewResFirst("");
      setNewResLast("");
      setShowAddResidentModal(false);
      fetchAllData();
    } catch (err) {
      alert(err.message);
    }
  };

  // ============================================================================
  // VIEW RENDER LAYOUT MAP
  // ============================================================================

  // Render Login Layout if not authenticated
  if (!token) {
    return (
      <div className="bg-surface text-on-surface font-body-md antialiased min-h-screen flex flex-col md:flex-row">
        {/* Left Panel: Brand */}
        <div className="hidden md:flex flex-col w-[45%] bg-surface-container relative overflow-hidden p-container-padding justify-between border-r border-outline-variant">
          <div className="absolute inset-0 bg-wave-pattern z-0"></div>
          <div className="z-10 mt-8 ml-8">
            <div className="flex items-center gap-stack-sm mb-4">
              <span className="material-symbols-outlined text-secondary" style={{ fontSize: "32px" }}>sensors</span>
              <span className="font-headline-md text-headline-md text-primary">Wi-Fi Sense</span>
            </div>
            <p className="font-headline-sm text-headline-sm text-on-surface-variant max-w-sm mt-4">
              Invisible security through mathematical precision.
            </p>
          </div>
          <div className="z-10 mb-8 ml-8">
            <div className="inline-flex items-center gap-2 bg-surface-container-highest px-4 py-2 rounded-full border border-outline-variant">
              <span className="material-symbols-outlined text-secondary" style={{ fontSize: "16px" }}>check_circle</span>
              <span className="font-label-caps text-label-caps text-on-surface">System Status: Optimal</span>
            </div>
          </div>
        </div>

        {/* Right Panel: Login / Register Form */}
        <div className="flex-1 flex flex-col justify-center bg-surface-container-lowest p-gutter relative">
          <div className="w-full max-w-md mx-auto">
            <div className="md:hidden flex items-center justify-center gap-stack-sm mb-8">
              <span className="material-symbols-outlined text-secondary" style={{ fontSize: "28px" }}>sensors</span>
              <span className="font-headline-md text-headline-md text-primary">Wi-Fi Sense</span>
            </div>

            <div className="mb-stack-lg text-center md:text-left">
              <h1 className="font-headline-lg text-headline-lg text-on-background mb-2">
                {isRegistering ? "Register Account" : "Sign In"}
              </h1>
              <p className="font-body-md text-body-md text-on-surface-variant">
                {isRegistering ? "Create your facility access credentials." : "Enter your credentials to access the monitoring dashboard."}
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
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1" htmlFor="email">Email Address</label>
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline" style={{ fontSize: "20px" }}>mail</span>
                    <input
                      type="email"
                      id="email"
                      className="block w-full pl-10 pr-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary font-body-md text-body-md text-on-surface"
                      placeholder="admin@organization.com"
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1" htmlFor="password">Password</label>
                  <div className="relative">
                    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline" style={{ fontSize: "20px" }}>lock</span>
                    <input
                      type="password"
                      id="password"
                      className="block w-full pl-10 pr-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary font-body-md text-body-md text-on-surface"
                      placeholder="••••••••"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(true)} className="text-secondary font-medium text-xs hover:underline">
                    Create a new account
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-on-secondary bg-secondary hover:opacity-90">
                    Sign In <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>arrow_forward</span>
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-stack-md">
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1" htmlFor="reg_email">Email Address</label>
                  <input
                    type="email"
                    id="reg_email"
                    className="block w-full px-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1"
                    placeholder="name@organization.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1">First Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1"
                      value={regFirst}
                      onChange={(e) => setRegFirst(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1">Last Name</label>
                    <input
                      type="text"
                      className="block w-full px-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1"
                      value={regLast}
                      onChange={(e) => setRegLast(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1">Role Type</label>
                  <select
                    className="block w-full px-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                  >
                    <option value="system_admin">System Admin</option>
                    <option value="organization_admin">Organization Admin</option>
                    <option value="facility_manager">Facility Manager</option>
                    <option value="caregiver">Caregiver</option>
                    <option value="corporate_staff">Corporate Staff</option>
                    <option value="emergency_contact">Emergency Contact</option>
                  </select>
                </div>
                <div>
                  <label className="block font-label-caps text-label-caps text-on-surface-variant mb-1" htmlFor="reg_password">Password</label>
                  <input
                    type="password"
                    id="reg_password"
                    className="block w-full px-3 py-2 border border-outline-variant rounded bg-surface focus:outline-none focus:ring-1"
                    placeholder="••••••••"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(false)} className="text-on-surface-variant font-medium text-xs hover:underline">
                    Back to Sign In
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2 px-6 border border-transparent rounded font-label-caps text-label-caps text-on-secondary bg-secondary hover:opacity-90">
                    Register Account
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
  // RENDER AUTHENTICATED SCREEN
  // ============================================================================
  return (
    <div className="bg-background text-on-background min-h-screen flex">
      {/* SideNavBar layout matching Stitch prototypes */}
      <nav className="hidden md:flex bg-surface-container-lowest dark:bg-on-background border-r border-outline-variant fixed left-0 top-0 bottom-0 w-sidebar-width flex-col z-40">
        <div className="p-gutter border-b border-outline-variant">
          <div className="flex items-center gap-stack-sm mb-stack-md">
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: "28px" }}>sensors</span>
            <div>
              <h1 className="text-headline-md font-headline-md font-bold text-primary">Wi-Fi Sense</h1>
              <p className="text-label-caps font-label-caps text-on-surface-variant">Focus Platform</p>
            </div>
          </div>
        </div>

        {/* View selection tabs */}
        <div className="flex-1 overflow-y-auto py-stack-md px-3 flex flex-col gap-1">
          <button
            onClick={() => setCurrentView("dashboard")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "dashboard" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">dashboard</span>
            <span className="text-xs font-bold uppercase tracking-wider">Dashboard</span>
          </button>

          {/* Render admin navigation fields */}
          <div className="mt-4 mb-2 px-3 text-left">
            <p className="text-[10px] text-outline font-bold uppercase tracking-wider">Infrastructure</p>
          </div>

          <button
            onClick={() => setCurrentView("organizations")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "organizations" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">domain</span>
            <span className="text-xs font-bold uppercase tracking-wider">Organizations</span>
          </button>

          <button
            onClick={() => setCurrentView("buildings")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "buildings" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">business</span>
            <span className="text-xs font-bold uppercase tracking-wider">Buildings</span>
          </button>

          <button
            onClick={() => setCurrentView("floors")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "floors" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">layers</span>
            <span className="text-xs font-bold uppercase tracking-wider">Floors</span>
          </button>

          <button
            onClick={() => setCurrentView("rooms")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "rooms" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">meeting_room</span>
            <span className="text-xs font-bold uppercase tracking-wider">Rooms</span>
          </button>

          <button
            onClick={() => setCurrentView("devices")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "devices" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">router</span>
            <span className="text-xs font-bold uppercase tracking-wider">Devices</span>
          </button>

          <button
            onClick={() => setCurrentView("residents")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "residents" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">badge</span>
            <span className="text-xs font-bold uppercase tracking-wider">Residents</span>
          </button>

          <div className="mt-4 mb-2 px-3 text-left">
            <p className="text-[10px] text-outline font-bold uppercase tracking-wider">Monitoring & Alerts</p>
          </div>

          <button
            onClick={() => setCurrentView("alerts")}
            className={`flex items-center justify-between gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "alerts" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <div className="flex items-center gap-stack-sm">
              <span className="material-symbols-outlined">warning</span>
              <span className="text-xs font-bold uppercase tracking-wider">Alert Center</span>
            </div>
            {alertSummary.status_counts.new > 0 && (
              <span className="bg-error text-on-error rounded-full px-2 py-0.5 text-[9px] font-bold">
                {alertSummary.status_counts.new}
              </span>
            )}
          </button>

          <button
            onClick={() => setCurrentView("analytics")}
            className={`flex items-center gap-stack-sm rounded-lg p-3 text-left w-full transition-all ${
              currentView === "analytics" ? "bg-secondary-container text-on-secondary-container font-semibold" : "text-on-surface-variant hover:bg-surface-container"
            }`}
          >
            <span className="material-symbols-outlined">analytics</span>
            <span className="text-xs font-bold uppercase tracking-wider">Analytics</span>
          </button>
        </div>

        {/* Sidebar Footer */}
        <div className="p-gutter border-t border-outline-variant flex flex-col gap-2">
          <div className="text-[10px] text-outline font-bold uppercase text-left mb-1">
            Active User Scope
          </div>
          <div className="bg-surface-container border rounded p-2 text-left text-xs mb-2">
            <div className="font-bold text-on-background">{user?.first_name} {user?.last_name}</div>
            <div className="text-[10px] text-on-surface-variant uppercase font-mono mt-0.5">{role}</div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full border border-error text-error py-2 rounded text-xs font-bold uppercase hover:bg-error-container hover:text-on-error-container transition-all flex items-center justify-center gap-1"
          >
            <span className="material-symbols-outlined text-sm">logout</span> Logout
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 md:ml-[260px] flex flex-col min-h-screen pb-12">
        {/* Top bar */}
        <header className="h-header-height bg-surface border-b border-outline-variant flex items-center justify-between px-gutter sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider">
              {currentView === "dashboard" ? `Welcome to WiFi Sense (${role})` : `Management / ${currentView}`}
            </h2>
          </div>
          <div className="flex items-center gap-stack-md">
            <button
              onClick={() => {
                if (devices.length === 0) {
                  alert("Please add a registered Sensing Device in the Devices tab first.");
                } else {
                  setSimDeviceId(devices[0].id);
                  setShowSimulateModal(true);
                }
              }}
              className="bg-secondary text-on-secondary px-4 py-1.5 rounded text-xs font-bold uppercase hover:opacity-90"
            >
              Simulate Event
            </button>
            <div className="h-8 w-8 rounded-full bg-surface-container border flex items-center justify-center font-bold text-primary select-none">
              {user?.first_name[0]}{user?.last_name[0]}
            </div>
          </div>
        </header>

        {/* Global Fall Alert Banner */}
        {activeFallAlert && (
          <div className="bg-error-container border-b border-error text-on-error-container p-4 flex items-center justify-between pulse-animation relative z-20">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-error text-2xl fill">warning</span>
              <div className="text-left">
                <h3 className="text-xs font-bold uppercase tracking-wider text-error">POTENTIAL RESIDENT FALL DETECTED</h3>
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
                className="px-3 py-1.5 bg-error text-on-error rounded text-xs font-bold uppercase hover:opacity-90"
              >
                Resolve
              </button>
            </div>
          </div>
        )}

        {/* Render Active View Canvas */}
        <div className="p-gutter max-w-[1200px] mx-auto w-full">
          {currentView === "dashboard" && (
            <div className="space-y-6">
              {/* Stats overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-gutter">
                <div className="bg-surface-container-lowest border rounded p-4 flex flex-col justify-between h-28">
                  <span className="text-[10px] text-outline font-bold uppercase text-left">Total Rooms</span>
                  <p className="text-3xl font-bold font-data-mono text-left">{occupancySummary.total_rooms}</p>
                </div>
                <div className="bg-surface-container-lowest border border-l-4 border-l-secondary rounded p-4 flex flex-col justify-between h-28">
                  <span className="text-[10px] text-outline font-bold uppercase text-left">Vacant Rooms</span>
                  <p className="text-3xl font-bold font-data-mono text-secondary text-left">{occupancySummary.vacant_rooms}</p>
                </div>
                <div className="bg-surface-container-lowest border border-l-4 border-l-[#3B82F6] rounded p-4 flex flex-col justify-between h-28">
                  <span className="text-[10px] text-outline font-bold uppercase text-left">Occupied Rooms</span>
                  <p className="text-3xl font-bold font-data-mono text-[#3B82F6] text-left">{occupancySummary.occupied_rooms}</p>
                </div>
                <div className="bg-surface-container-lowest border rounded p-4 flex flex-col justify-between h-28">
                  <span className="text-[10px] text-outline font-bold uppercase text-left">Pending Alerts</span>
                  <p className={`text-3xl font-bold font-data-mono text-left ${alertSummary.status_counts.new > 0 ? "text-error" : ""}`}>
                    {alertSummary.status_counts.new}
                  </p>
                </div>
              </div>

              {/* Bento panels depending on user roles */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                {/* Real-time Occupancy Overview */}
                <div className="lg:col-span-2 bg-surface-container-lowest border rounded-xl p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-2 mb-4 text-left">
                    Live Occupancy Status
                  </h3>
                  {occupancySummary.occupied_room_details.length === 0 ? (
                    <div className="py-12 border border-dashed rounded text-center text-on-surface-variant text-sm">
                      No rooms registered. Switch views below to register organization assets.
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {occupancySummary.occupied_room_details.map(rm => (
                        <div
                          key={rm.room_id}
                          className={`border rounded p-3 text-left transition-all ${
                            rm.is_occupied
                              ? rm.current_activity === "Fall_Detected"
                                ? "border-error bg-error-container/20"
                                : "border-[#3B82F6] bg-surface"
                              : "border-outline-variant bg-[#e6f4f1]"
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-semibold text-primary">{rm.room_name}</span>
                            <span
                              className={`w-2.5 h-2.5 rounded-full ${
                                rm.is_occupied
                                  ? rm.current_activity === "Fall_Detected"
                                    ? "bg-error animate-pulse"
                                    : "bg-[#3B82F6]"
                                  : "bg-secondary"
                              }`}
                            ></span>
                          </div>
                          <p className="text-[10px] text-on-surface-variant uppercase">{rm.room_type}</p>
                          <p className="text-xs font-bold text-on-surface mt-2">
                            {rm.is_occupied ? `Activity: ${rm.current_activity}` : "Vacant"}
                          </p>
                          {rm.is_occupied && (
                            <p className="text-[10px] text-outline font-data-mono mt-1">Conf: {(rm.model_confidence * 100).toFixed(0)}%</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Quick Diagnostics and Config Overview */}
                <div className="bg-surface-container-lowest border rounded-xl p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-2 mb-4 text-left">
                    Device Matrix Diagnostics
                  </h3>
                  <div className="space-y-4 text-left">
                    <div className="flex justify-between items-center text-sm border-b pb-2">
                      <span className="text-on-surface-variant">Registered Nodes</span>
                      <span className="font-bold font-data-mono">{devices.length}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-b pb-2">
                      <span className="text-on-surface-variant">Active Residents</span>
                      <span className="font-bold font-data-mono">{residents.length}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm border-b pb-2">
                      <span className="text-on-surface-variant">Network Status</span>
                      <span className="font-bold text-secondary font-mono">NOMINAL</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-on-surface-variant">Alert Resolutions</span>
                      <span className="font-bold font-data-mono">{alertSummary.status_counts.resolved}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            ORGANIZATIONS VIEW
          ============================================================================ */}
          {currentView === "organizations" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Registered Organizations</h3>
                <button
                  onClick={() => setShowAddOrgModal(true)}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Organization
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Org ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Created At</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {organizations.map(org => (
                      <tr key={org.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{org.id}</td>
                        <td className="p-3 font-semibold">{org.name}</td>
                        <td className="p-3">{org.type}</td>
                        <td className="p-3 font-data-mono text-xs">{new Date(org.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                    {organizations.length === 0 && (
                      <tr>
                        <td colSpan="4" className="p-4 text-center text-on-surface-variant">No organizations registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            BUILDINGS VIEW
          ============================================================================ */}
          {currentView === "buildings" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Registered Buildings</h3>
                <button
                  onClick={() => {
                    if (organizations.length === 0) {
                      alert("Please create an organization first.");
                    } else {
                      setNewBldOrgId(organizations[0].id);
                      setShowAddBuildingModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Building
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Building ID</th>
                      <th className="p-3">Org ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Address</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {buildings.map(bld => (
                      <tr key={bld.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{bld.id}</td>
                        <td className="p-3 font-data-mono text-xs">{bld.organization_id}</td>
                        <td className="p-3 font-semibold">{bld.name}</td>
                        <td className="p-3">{bld.address || "N/A"}</td>
                      </tr>
                    ))}
                    {buildings.length === 0 && (
                      <tr>
                        <td colSpan="4" className="p-4 text-center text-on-surface-variant">No buildings registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            FLOORS VIEW
          ============================================================================ */}
          {currentView === "floors" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Registered Floors</h3>
                <button
                  onClick={() => {
                    if (buildings.length === 0) {
                      alert("Please create a building first.");
                    } else {
                      setNewFlrBldId(buildings[0].id);
                      setShowAddFloorModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Floor
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Floor ID</th>
                      <th className="p-3">Building ID</th>
                      <th className="p-3">Floor Number</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {floors.map(flr => (
                      <tr key={flr.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{flr.id}</td>
                        <td className="p-3 font-data-mono text-xs">{flr.building_id}</td>
                        <td className="p-3 font-semibold">Floor {flr.floor_number}</td>
                      </tr>
                    ))}
                    {floors.length === 0 && (
                      <tr>
                        <td colSpan="3" className="p-4 text-center text-on-surface-variant">No floors registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            ROOMS VIEW
          ============================================================================ */}
          {currentView === "rooms" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Registered Rooms</h3>
                <button
                  onClick={() => {
                    if (floors.length === 0) {
                      alert("Please create a floor first.");
                    } else {
                      setNewRmFlrId(floors[0].id);
                      setShowAddRoomModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Room
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Room ID</th>
                      <th className="p-3">Floor ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Capacity</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {rooms.map(rm => (
                      <tr key={rm.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{rm.id}</td>
                        <td className="p-3 font-data-mono text-xs">{rm.floor_id}</td>
                        <td className="p-3 font-semibold">{rm.name}</td>
                        <td className="p-3">{rm.room_type}</td>
                        <td className="p-3 font-data-mono">{rm.capacity}</td>
                      </tr>
                    ))}
                    {rooms.length === 0 && (
                      <tr>
                        <td colSpan="5" className="p-4 text-center text-on-surface-variant">No rooms registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            DEVICES VIEW
          ============================================================================ */}
          {currentView === "devices" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Registered ESP32-S3 Nodes</h3>
                <button
                  onClick={() => {
                    setNewDevRmId(rooms.length > 0 ? rooms[0].id : "");
                    setShowAddDeviceModal(true);
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Register Device
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Device ID</th>
                      <th className="p-3">MAC Address</th>
                      <th className="p-3">Room ID</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Last Ping</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {devices.map(dev => (
                      <tr key={dev.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{dev.id}</td>
                        <td className="p-3 font-semibold font-data-mono">{dev.mac_address}</td>
                        <td className="p-3 font-data-mono text-xs">{dev.room_id || "Unassigned"}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            dev.device_status === "ONLINE" ? "bg-secondary-container text-on-secondary-container" : "bg-outline-variant/30 text-on-surface-variant"
                          }`}>
                            {dev.device_status}
                          </span>
                        </td>
                        <td className="p-3 font-data-mono text-xs">
                          {dev.last_seen_at ? new Date(dev.last_seen_at).toLocaleString() : "Never"}
                        </td>
                      </tr>
                    ))}
                    {devices.length === 0 && (
                      <tr>
                        <td colSpan="5" className="p-4 text-center text-on-surface-variant">No sensing devices registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            RESIDENTS VIEW
          ============================================================================ */}
          {currentView === "residents" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Assigned Residents</h3>
                <button
                  onClick={() => {
                    if (rooms.length === 0) {
                      alert("Please create a room first.");
                    } else {
                      setNewResRmId(rooms[0].id);
                      setShowAddResidentModal(true);
                    }
                  }}
                  className="bg-secondary text-on-secondary px-3 py-1 rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Add Resident
                </button>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Resident ID</th>
                      <th className="p-3">Room ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Created At</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {residents.map(res => (
                      <tr key={res.id} className="hover:bg-surface-bright">
                        <td className="p-3 font-data-mono text-xs">{res.id}</td>
                        <td className="p-3 font-data-mono text-xs">{res.room_id}</td>
                        <td className="p-3 font-semibold">{res.first_name} {res.last_name}</td>
                        <td className="p-3 font-data-mono text-xs">{new Date(res.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                    {residents.length === 0 && (
                      <tr>
                        <td colSpan="4" className="p-4 text-center text-on-surface-variant">No residents registered yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ============================================================================
            ALERTS VIEW
          ============================================================================ */}
          {currentView === "alerts" && (
            <div className="bg-surface-container-lowest border rounded-xl p-6">
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary">Alert Incident Center</h3>
                <span className="text-xs text-on-surface-variant">Active transitions flow: new &rarr; acknowledged &rarr; resolved</span>
              </div>
              <div className="overflow-x-auto text-left">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-[10px] text-outline font-bold uppercase tracking-wider border-b">
                      <th className="p-3">Severity</th>
                      <th className="p-3">Room</th>
                      <th className="p-3">Activity Trigger</th>
                      <th className="p-3">Message</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm divide-y">
                    {alerts.map(a => (
                      <tr key={a.id} className={`hover:bg-surface-bright ${a.status === "new" ? "bg-error-container/10" : ""}`}>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                            a.severity === "CRITICAL" ? "bg-error text-on-error" : "bg-tertiary-fixed text-on-tertiary-fixed-variant"
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="p-3 font-semibold">{rooms.find(rm => rm.id === a.room_id)?.name || "Unknown Room"}</td>
                        <td className="p-3 font-mono text-xs">{a.event_type}</td>
                        <td className="p-3">{a.message}</td>
                        <td className="p-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${
                            a.status === "new"
                              ? "bg-error-container text-error border border-error/20"
                              : a.status === "acknowledged"
                              ? "bg-secondary-container text-on-secondary-container border border-secondary"
                              : "bg-outline-variant/30 text-on-surface-variant"
                          }`}>
                            {a.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex justify-end gap-2">
                            {a.status === "new" && (
                              <button
                                onClick={() => handleAcknowledge(a.id)}
                                className="px-2 py-1 border border-secondary text-secondary rounded text-xs font-bold uppercase hover:bg-secondary/15"
                              >
                                Acknowledge
                              </button>
                            )}
                            {a.status !== "resolved" && (
                              <button
                                onClick={() => setShowResolveModal(a.id)}
                                className="px-2 py-1 bg-secondary text-on-secondary rounded text-xs font-bold uppercase hover:opacity-90"
                              >
                                Resolve
                              </button>
                            )}
                            {a.status === "resolved" && (
                              <span className="text-xs text-on-surface-variant font-mono">Resolved</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {alerts.length === 0 && (
                      <tr>
                        <td colSpan="6" className="p-4 text-center text-on-surface-variant">No alerts triggered yet. Run event simulations to generate alerts.</td>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
                {/* Occupancy aggregates */}
                <div className="bg-surface-container-lowest border rounded-xl p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-2 mb-4">Occupancy Rates</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-on-surface-variant">Occupancy Rate</span>
                      <span className="font-bold text-secondary font-data-mono">{occupancySummary.occupancy_rate}%</span>
                    </div>
                    <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden">
                      <div className="bg-secondary h-full rounded-full" style={{ width: `${occupancySummary.occupancy_rate}%` }}></div>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span>{occupancySummary.occupied_rooms} Occupied Rooms</span>
                      <span>{occupancySummary.vacant_rooms} Vacant Rooms</span>
                    </div>
                  </div>
                </div>

                {/* Alert summary metrics */}
                <div className="bg-surface-container-lowest border rounded-xl p-6">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-2 mb-4">Alert Distribution</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="border rounded p-3 bg-surface">
                      <span className="text-[10px] text-outline font-bold uppercase">Status: New</span>
                      <p className="text-2xl font-bold font-data-mono mt-1">{alertSummary.status_counts.new}</p>
                    </div>
                    <div className="border rounded p-3 bg-surface">
                      <span className="text-[10px] text-outline font-bold uppercase">Status: Acknowledged</span>
                      <p className="text-2xl font-bold font-data-mono mt-1">{alertSummary.status_counts.acknowledged}</p>
                    </div>
                    <div className="border rounded p-3 bg-surface">
                      <span className="text-[10px] text-outline font-bold uppercase">Status: Resolved</span>
                      <p className="text-2xl font-bold font-data-mono mt-1">{alertSummary.status_counts.resolved}</p>
                    </div>
                    <div className="border rounded p-3 bg-surface">
                      <span className="text-[10px] text-outline font-bold uppercase">Total Warnings</span>
                      <p className="text-2xl font-bold font-data-mono mt-1">{alertSummary.total_alerts}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ============================================================================
        MODAL REGISTRATION OVERLAYS
      ============================================================================ */}

      {/* 1. Simulate Event Modal */}
      {showSimulateModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-2">Simulate Wi-Fi CSI Event</h3>
            <p className="text-xs text-on-surface-variant mb-4">
              Select a registered device to send a simulated signal status to the presence pipeline.
            </p>
            <form onSubmit={runSimulation} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Target Device</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={simDeviceId}
                  onChange={(e) => setSimDeviceId(e.target.value)}
                >
                  {devices.map(dev => (
                    <option key={dev.id} value={dev.id}>
                      {dev.mac_address} (Room: {rooms.find(rm => rm.id === dev.room_id)?.name || "Unknown"})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Simulated Activity Type</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={simActivity}
                  onChange={(e) => setSimActivity(e.target.value)}
                >
                  <option value="Walking">Walking (Presence)</option>
                  <option value="Sitting">Sitting (Presence)</option>
                  <option value="Presence">Presence (Generic)</option>
                  <option value="Empty">Empty (Vacant)</option>
                  <option value="Fall_Detected">Fall_Detected (Critical Alert)</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowSimulateModal(false)}
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase hover:opacity-90"
                >
                  Simulate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. Add Organization Modal */}
      {showAddOrgModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Add Organization</h3>
            <form onSubmit={addOrganization} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Organization Name</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  placeholder="e.g. Sunrise Elder Care"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Deployment Type</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
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
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Add Building Modal */}
      {showAddBuildingModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Add Building</h3>
            <form onSubmit={addBuilding} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Parent Organization</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={newBldOrgId}
                  onChange={(e) => setNewBldOrgId(e.target.value)}
                >
                  {organizations.map(org => (
                    <option key={org.id} value={org.id}>{org.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Building Name</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  placeholder="e.g. North Wing"
                  value={newBldName}
                  onChange={(e) => setNewBldName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Address</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  placeholder="e.g. 123 Street Name"
                  value={newBldAddress}
                  onChange={(e) => setNewBldAddress(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddBuildingModal(false)}
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. Add Floor Modal */}
      {showAddFloorModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Add Floor</h3>
            <form onSubmit={addFloor} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Parent Building</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={newFlrBldId}
                  onChange={(e) => setNewFlrBldId(e.target.value)}
                >
                  {buildings.map(bld => (
                    <option key={bld.id} value={bld.id}>{bld.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Floor Number</label>
                <input
                  type="number"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={newFlrNum}
                  onChange={(e) => setNewFlrNum(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddFloorModal(false)}
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 5. Add Room Modal */}
      {showAddRoomModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Add Room</h3>
            <form onSubmit={addRoom} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Parent Floor</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
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
                <label className="block text-xs font-bold uppercase mb-1">Room Name / Number</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  placeholder="e.g. Room 204"
                  value={newRmName}
                  onChange={(e) => setNewRmName(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase mb-1">Room Type</label>
                  <select
                    className="w-full border rounded p-2 text-sm bg-surface"
                    value={newRmType}
                    onChange={(e) => setNewRmType(e.target.value)}
                  >
                    <option value="Resident Bedroom">Resident Bedroom</option>
                    <option value="Conference Room">Conference Room</option>
                    <option value="Common Area">Common Area</option>
                    <option value="Restroom">Restroom</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase mb-1">Capacity</label>
                  <input
                    type="number"
                    className="w-full border rounded p-2 text-sm bg-surface"
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
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. Add Device Modal */}
      {showAddDeviceModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Register ESP32-S3 Device</h3>
            <form onSubmit={addDevice} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Room Assignment</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={newDevRmId}
                  onChange={(e) => setNewDevRmId(e.target.value)}
                >
                  <option value="">Unassigned</option>
                  {rooms.map(rm => (
                    <option key={rm.id} value={rm.id}>{rm.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">MAC Address</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  placeholder="e.g. 4C:75:25:AA:BB:CC"
                  value={newDevMac}
                  onChange={(e) => setNewDevMac(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Firmware Version</label>
                <input
                  type="text"
                  className="w-full border rounded p-2 text-sm bg-surface"
                  value={newDevFirmware}
                  onChange={(e) => setNewDevFirmware(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddDeviceModal(false)}
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 7. Add Resident Modal */}
      {showAddResidentModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-4">Add Resident</h3>
            <form onSubmit={addResident} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Assigned Room</label>
                <select
                  className="w-full border rounded p-2 text-sm bg-surface"
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
                  <label className="block text-xs font-bold uppercase mb-1">First Name</label>
                  <input
                    type="text"
                    className="w-full border rounded p-2 text-sm bg-surface"
                    value={newResFirst}
                    onChange={(e) => setNewResFirst(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase mb-1">Last Name</label>
                  <input
                    type="text"
                    className="w-full border rounded p-2 text-sm bg-surface"
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
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. Resolve Alert Modal */}
      {showResolveModal && (
        <div className="fixed inset-0 bg-primary/45 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest border rounded-xl p-6 max-w-md w-full text-left shadow-lg">
            <h3 className="font-bold text-headline-sm mb-2 text-error">Resolve Incident Alert</h3>
            <p className="text-xs text-on-surface-variant mb-4">
              Enter resolution notes to audit the response time and clear the warning banner.
            </p>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase mb-1">Resolution Actions / Notes</label>
                <textarea
                  className="w-full border rounded p-2 text-sm bg-surface h-24"
                  placeholder="e.g. Caregiver dispatched. Resident found safe and guided back to resting position."
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
                  className="px-4 py-2 border rounded text-xs font-bold uppercase hover:bg-surface-container"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-secondary text-on-secondary rounded text-xs font-bold uppercase">
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
