import React, { useState, useEffect, useRef } from "react";
import WifiModemVisualizer from "./WifiModemVisualizer";

const API_BASE = "http://localhost:8000";

export default function App() {
  // Authentication State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  
  // Navigation State & Browser History Management
  // Views: 'family', 'analytics', 'devices', 'alerts', 'occupancy', 'dashboard', 'caregiver', 'corporate', 'facilitymanager', 'orgadmin', 'sysadmin'
  const [currentView, _setCurrentView] = useState("dashboard"); 
  const navHistoryRef = useRef([]);

  const setCurrentView = (newView, pushHistory = true) => {
    _setCurrentView((prev) => {
      if (prev !== newView && pushHistory) {
        navHistoryRef.current.push(prev);
        try {
          window.history.pushState({ app: "wifisense", view: newView }, "", window.location.pathname);
        } catch (_) {}
      }
      return newView;
    });
  };

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
  
  // Family Portal states
  const [familyStatus, setFamilyStatus] = useState(null);
  const [accessRequests, setAccessRequests] = useState([]);
  const [selectedRequestResidentId, setSelectedRequestResidentId] = useState("");
  
  // Collapsible Buildings state inside Facility Hierarchy widget
  const [expandedBuildings, setExpandedBuildings] = useState({});

  // Selected visual active telemetry activity
  const [activeTelemetryActivity, setActiveTelemetryActivity] = useState("Empty");

  // Privacy toggles state for Family Portal view
  const [strictPrivacy, setStrictPrivacy] = useState(false);
  const [contextualVisibility, setContextualVisibility] = useState(true);

  // Caregiver interactive shift notes log state
  const [caregiverLogs, setCaregiverLogs] = useState([
    { id: 1, caregiver: "Abhinanth S Pillai", shift: "Morning", notes: "Checked room 101, resident Devassy sleeping comfortably.", time: "09:15 AM" },
    { id: 2, caregiver: "Abhinand M A", shift: "Night", notes: "No anomaly signals detected in AJCE block.", time: "11:30 PM" }
  ]);
  const [newShiftNote, setNewShiftNote] = useState("");
  const [newShiftCaregiver, setNewShiftCaregiver] = useState("Blesson Joseph Byju");

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
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const fileInputRef = useRef(null);

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

  // Helper to step backward one step through user interactions
  const stepBack = () => {
    // 1. Close any active modal / popup drawer first
    if (showAddOrgModal) { setShowAddOrgModal(false); return true; }
    if (showAddBuildingModal) { setShowAddBuildingModal(false); return true; }
    if (showAddFloorModal) { setShowAddFloorModal(false); return true; }
    if (showAddRoomModal) { setShowAddRoomModal(false); return true; }
    if (showAddDeviceModal) { setShowAddDeviceModal(false); return true; }
    if (showAddResidentModal) { setShowAddResidentModal(false); return true; }
    if (showEmergencyModal) { setShowEmergencyModal(false); return true; }
    if (showResolveModal) { setShowResolveModal(null); return true; }
    if (showSimulateDrawer) { setShowSimulateDrawer(false); return true; }
    if (showProfileMenu) { setShowProfileMenu(false); return true; }

    // 2. If user is on the registration view of the landing page, step back to login
    if (!token && isRegistering) {
      setIsRegistering(false);
      return true;
    }

    // 3. Step back in view navigation history
    if (navHistoryRef.current.length > 0) {
      const prevView = navHistoryRef.current.pop();
      if (prevView && prevView !== currentView) {
        _setCurrentView(prevView);
        return true;
      }
    } else if (currentView !== "dashboard") {
      _setCurrentView("dashboard");
      return true;
    }

    return false;
  };

  // Push browser history state when registration form opens
  useEffect(() => {
    if (isRegistering) {
      try {
        window.history.pushState({ app: "wifisense", registering: true }, "", window.location.pathname);
      } catch (_) {}
    }
  }, [isRegistering]);

  // Push browser history state when any modal opens
  const anyModalActive = Boolean(
    showAddOrgModal ||
    showAddBuildingModal ||
    showAddFloorModal ||
    showAddRoomModal ||
    showAddDeviceModal ||
    showAddResidentModal ||
    showEmergencyModal ||
    showResolveModal ||
    showSimulateDrawer ||
    showProfileMenu
  );

  const prevModalStateRef = useRef(false);
  useEffect(() => {
    if (anyModalActive && !prevModalStateRef.current) {
      try {
        window.history.pushState({ app: "wifisense", modal: true }, "", window.location.pathname);
      } catch (_) {}
    }
    prevModalStateRef.current = anyModalActive;
  }, [anyModalActive]);

  // Handle Desktop Browser Back Arrow Button (popstate)
  useEffect(() => {
    try {
      window.history.replaceState({ app: "wifisense", view: currentView }, "", window.location.pathname);
      window.history.pushState({ app: "wifisense", view: currentView }, "", window.location.pathname);
    } catch (_) {}

    const handlePopState = () => {
      stepBack();
      try {
        window.history.pushState({ app: "wifisense", view: currentView }, "", window.location.pathname);
      } catch (_) {}
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [
    currentView,
    isRegistering,
    showAddOrgModal,
    showAddBuildingModal,
    showAddFloorModal,
    showAddRoomModal,
    showAddDeviceModal,
    showAddResidentModal,
    showEmergencyModal,
    showResolveModal,
    showSimulateDrawer,
    showProfileMenu,
    token
  ]);

  // Handle Desktop Backspace & Alt+ArrowLeft Keys
  useEffect(() => {
    const handleKeyDown = (e) => {
      const isBackNav = e.key === "Backspace" || (e.altKey && e.key === "ArrowLeft");
      if (!isBackNav) return;

      const target = e.target;
      const isEditable =
        target &&
        (target.tagName === "TEXTAREA" ||
          (target.tagName === "INPUT" &&
            !["button", "submit", "checkbox", "radio", "file", "image", "reset"].includes((target.type || "").toLowerCase()) &&
            !target.readOnly &&
            !target.disabled) ||
          target.isContentEditable);

      // If user is editing text in an input field, allow normal backspace deletion
      if (e.key === "Backspace" && isEditable) {
        return;
      }

      // Otherwise prevent browser from navigating back / closing tab, and step back in the app
      e.preventDefault();
      stepBack();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    currentView,
    isRegistering,
    showAddOrgModal,
    showAddBuildingModal,
    showAddFloorModal,
    showAddRoomModal,
    showAddDeviceModal,
    showAddResidentModal,
    showEmergencyModal,
    showResolveModal,
    showSimulateDrawer,
    showProfileMenu,
    token
  ]);

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

      // If family member, fetch their resident's status
      if (role === "emergency_contact") {
        const statusRes = await fetch(`${API_BASE}/family/resident-status`, { headers });
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setFamilyStatus(statusData);
          if (statusData.linked && statusData.recent_activity) {
            setActiveTelemetryActivity(statusData.recent_activity.activity);
          }
        }
        // Also fetch residents list so they can request link if not linked
        const resRes = await fetch(`${API_BASE}/residents`, { headers });
        if (resRes.ok) {
          setResidents(await resRes.json());
        }
        return;
      }

      // If admin, fetch pending access requests
      if (role === "system_admin" || role === "organization_admin") {
        const reqRes = await fetch(`${API_BASE}/family/requests`, { headers });
        if (reqRes.ok) {
          setAccessRequests(await reqRes.json());
        }
      }

      // 1. Fetch Analytics Summary
      const occRes = await fetch(`${API_BASE}/analytics/occupancy-summary`, { headers });
      if (occRes.ok) {
        const data = await occRes.json();
        const details = data.occupied_room_details || [];
        setOccupancySummary({
          total_rooms: data.total_rooms,
          occupied_rooms: data.occupied_rooms,
          vacant_rooms: data.vacant_rooms,
          occupancy_rate: data.occupancy_rate,
          occupied_room_details: details
        });

        const criticalRoom = details.find(rm => rm.current_activity === "Fall_Detected");
        const activeRoom = details.find(rm => rm.is_occupied && rm.current_activity !== "Empty");
        
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
        const alertData = await alertRes.json();
        setAlerts(alertData);
        const activeFall = alertData.find(a => a.event_type === "Fall_Detected" && a.status !== "resolved");
        setActiveFallAlert(activeFall || null);
      }

      // 3. Fetch Asset Lists
      const orgRes = await fetch(`${API_BASE}/organizations`, { headers });
      if (orgRes.ok) {
        setOrganizations(await orgRes.json());
      }

      const bldRes = await fetch(`${API_BASE}/buildings`, { headers });
      if (bldRes.ok) {
        setBuildings(await bldRes.json());
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
  }, [token]);

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
      if (data.role === "emergency_contact") {
        setCurrentView("family");
      } else {
        setCurrentView("dashboard");
      }
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

  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setToastMessage({ type: "error", text: "Please select an image file." });
      return;
    }
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/users/me/photo`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });
      if (res.ok) {
        const updatedUser = await res.json();
        setUser(updatedUser);
        localStorage.setItem("user", JSON.stringify(updatedUser));
        setToastMessage({ type: "success", text: "Profile photo updated successfully!" });
        setShowProfileMenu(false);
      } else {
        const err = await res.json().catch(() => ({}));
        setToastMessage({ type: "error", text: err.detail || "Failed to upload photo" });
      }
    } catch (err) {
      setToastMessage({ type: "error", text: "Network error uploading photo" });
    }
  };

  // Helper to trigger real browser file downloads
  const downloadFile = (filename, content, mimeType = "text/csv;charset=utf-8;") => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportPersonnelCSV = () => {
    const headers = ["Name", "Role", "Email", "Department/Scope", "Status"];
    const rows = [
      ["Dr. Evelyn Lin", "Staff Physician", "e.lin@healthcare.org", "Elder-Care Medical Director", "Active On-Shift"],
      ["Marcus Vance", "Facility Director", "m.vance@ajce.edu", "Campus Infrastructure Admin", "Active Off-Site"],
      ["Sarah Jenkins", "Lead Nurse / Caregiver", "s.jenkins@care.org", "Wing Alpha Senior Staff", "Active On-Shift"],
      ["Blesson Byju", "System Administrator", "blesson@wifisense.com", "Global Architecture", "Active Online"],
      ["Abhinand M A", "Facility Manager", "abhinand@wifisense.com", "AJCE MCA Block", "Active Online"]
    ];
    const csvContent = [headers.join(","), ...rows.map(r => r.map(c => `"${c}"`).join(","))].join("\n");
    downloadFile("active_personnel.csv", csvContent);
    setToastMessage({ type: "success", text: "Downloaded active_personnel.csv" });
  };

  const exportCorporateAnalytics = () => {
    const headers = ["Room Name", "Room Type", "Status", "Activity", "Confidence", "Last Updated"];
    const rows = (occupancySummary.occupied_room_details || []).map(rm => [
      rm.room_name,
      rm.room_type,
      rm.is_occupied ? "Occupied" : "Vacant",
      rm.current_activity,
      `${Math.round((rm.model_confidence || 0) * 100)}%`,
      rm.last_updated || "N/A"
    ]);
    const csvContent = [headers.join(","), ...rows.map(r => r.map(c => `"${c}"`).join(","))].join("\n");
    downloadFile("corporate_analytics.csv", csvContent);
    setToastMessage({ type: "success", text: "Downloaded corporate_analytics.csv" });
  };

  const generateRepurposingReport = () => {
    const content = [
      "Wi-Fi Sense - Underutilized Spaces & Repurposing Analysis Report",
      `Generated: ${new Date().toISOString()}`,
      "-------------------------------------------------------------",
      "Candidate Rooms for Repurposing:",
      "1. MCA Seminar Hall: Peak Utilization 14.2%, Average Utilization 8.5%. Recommendation: Subdivide or open for shared booking.",
      "2. Staff Room A: Peak Utilization 22.0%, Average Utilization 11.2%. Recommendation: Convert into collaborative workspace.",
      "",
      "Overall Campus Metrics:",
      `Total Monitored Rooms: ${occupancySummary.total_rooms}`,
      `Average Occupancy Rate: ${occupancySummary.occupancy_rate}%`,
      "Target Space Efficiency Gain: +35%"
    ].join("\n");
    downloadFile("space_repurposing_report.txt", content, "text/plain;charset=utf-8;");
    setToastMessage({ type: "success", text: "Downloaded space_repurposing_report.txt" });
  };

  const exportOccupancyTimeData = () => {
    const headers = ["Time", "Occupancy Rate (%)", "Occupied Rooms", "Total Rooms"];
    const tot = occupancySummary.total_rooms || 10;
    const rows = [
      ["08:00", "20", Math.round(tot * 0.2), tot],
      ["10:00", "55", Math.round(tot * 0.55), tot],
      ["12:00", "85", Math.round(tot * 0.85), tot],
      ["14:00", "70", Math.round(tot * 0.7), tot],
      ["16:00", "90", Math.round(tot * 0.9), tot],
      ["18:00", "30", Math.round(tot * 0.3), tot]
    ];
    const csvContent = [headers.join(","), ...rows.map(r => r.map(c => `"${c}"`).join(","))].join("\n");
    downloadFile("occupancy_over_time.csv", csvContent);
    setToastMessage({ type: "success", text: "Downloaded occupancy_over_time.csv" });
  };

  const submitLinkRequest = async (e) => {
    e.preventDefault();
    if (!selectedRequestResidentId) {
      alert("Please select a resident profile to link.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/family/requests`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ resident_id: selectedRequestResidentId })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Request failed.");
      }
      setToastMessage({ type: "success", text: "Access link request submitted. Awaiting admin approval." });
      setSelectedRequestResidentId("");
      fetchAllData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleReviewRequest = async (requestId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/family/requests/${requestId}`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify({ status: newStatus })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Review action failed.");
      }
      setToastMessage({ type: "success", text: `Access request ${newStatus} successfully.` });
      fetchAllData();
    } catch (err) {
      alert(err.message);
    }
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

  const addShiftNote = (e) => {
    e.preventDefault();
    if (!newShiftNote) return;
    const newLog = {
      id: Date.now(),
      caregiver: newShiftCaregiver,
      shift: "Regular",
      notes: newShiftNote,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setCaregiverLogs([newLog, ...caregiverLogs]);
    setNewShiftNote("");
    setToastMessage({ type: "success", text: "Caregiver shift note logged successfully." });
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
      <div className="bg-slate-50 text-slate-800 font-body-md antialiased min-h-screen flex flex-col lg:flex-row transition-all duration-300">
        {/* 3D Wi-Fi Modem Visualizer Showcase Panel (Subtle Light Theme) */}
        <div className="flex flex-col w-full lg:w-[55%] xl:w-[58%] bg-slate-50 relative p-3 sm:p-5 justify-between border-b lg:border-b-0 lg:border-r border-slate-200/90 min-h-[480px] lg:min-h-screen">
          {/* Header Title Bar */}
          <div className="flex items-center justify-between z-20 mb-3 px-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center shadow-md shadow-sky-500/20">
                <span className="material-symbols-outlined text-white" style={{ fontSize: "24px" }}>sensors</span>
              </div>
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-slate-900 tracking-tight">Wi-Fi Sense</span>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                    CSI 3D SENSING
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Contactless Fall & Activity Tracking via Subcarrier Distortion
                </p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-[11px] font-mono text-slate-700 font-medium">RF Engine: ONLINE</span>
            </div>
          </div>

          {/* 3D Modem & Signal Emitting Dome Canvas */}
          <div className="flex-1 w-full h-full relative min-h-[380px] lg:min-h-[520px]">
            <WifiModemVisualizer />
          </div>

          {/* Bottom Features Info Strip */}
          <div className="grid grid-cols-3 gap-2.5 mt-3 pt-3 border-t border-slate-200/70 z-20 text-left">
            <div className="p-2.5 rounded-xl bg-white/90 border border-slate-200/80 shadow-2xs">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-medium">Hardware</div>
              <div className="text-xs font-semibold text-slate-800 mt-0.5">Dual-Band CSI Modem</div>
            </div>
            <div className="p-2.5 rounded-xl bg-white/90 border border-slate-200/80 shadow-2xs">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-medium">Detection</div>
              <div className="text-xs font-semibold text-sky-600 mt-0.5">3D Spherical Doppler</div>
            </div>
            <div className="p-2.5 rounded-xl bg-white/90 border border-slate-200/80 shadow-2xs">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-medium">Privacy</div>
              <div className="text-xs font-semibold text-emerald-600 mt-0.5">100% Zero-Camera</div>
            </div>
          </div>
        </div>

        {/* Login Panel (Clean Light Theme) */}
        <div className="flex-1 flex flex-col justify-center p-6 sm:p-10 lg:p-14 relative bg-white overflow-y-auto">
          <div className="absolute top-5 right-5 flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-[11px]">
            <span className="text-slate-400 px-1 font-semibold">Demo:</span>
            <button
              type="button"
              onClick={() => { setLoginEmail("blesson@wifisense.com"); setLoginPassword("blessonpassword"); }}
              className="px-2.5 py-1 bg-white text-slate-700 rounded-lg shadow-2xs font-semibold hover:text-sky-600 border border-slate-200/60 cursor-pointer transition-colors"
            >
              SysAdmin
            </button>
            <button
              type="button"
              onClick={() => { setLoginEmail("abhinand@wifisense.com"); setLoginPassword("abhinandpassword"); }}
              className="px-2.5 py-1 bg-white text-slate-700 rounded-lg shadow-2xs font-semibold hover:text-sky-600 border border-slate-200/60 cursor-pointer transition-colors"
            >
              Corporate
            </button>
            <button
              type="button"
              onClick={() => { setLoginEmail("abhinanth@wifisense.com"); setLoginPassword("abhinanthpassword"); }}
              className="px-2.5 py-1 bg-white text-slate-700 rounded-lg shadow-2xs font-semibold hover:text-sky-600 border border-slate-200/60 cursor-pointer transition-colors"
            >
              Elder-Care
            </button>
          </div>

          <div className="w-full max-w-md mx-auto">
            <div className="mb-stack-lg text-center md:text-left">
              <h1 className="font-headline-lg text-headline-lg text-slate-900 mb-2 font-bold tracking-tight">Welcome to WiFi Sense</h1>
              <p className="font-body-md text-body-md text-slate-500">
                {isRegistering 
                  ? "Create credentials to start testing the CSI data pipeline." 
                  : "Sign in with your authorized credentials to access your deployment."}
              </p>
            </div>

            {loginError && (
              <div className="bg-red-50 text-red-600 rounded-xl p-3 mb-4 text-xs font-semibold border border-red-200 shadow-2xs">
                {loginError}
              </div>
            )}

            {!isRegistering ? (
              <form onSubmit={handleLogin} className="space-y-stack-md">
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 mb-1 font-medium">Email Address</label>
                  <input
                    type="email"
                    className="block w-full px-3.5 py-2.5 border border-slate-200 rounded-xl bg-slate-50/70 text-slate-900 focus:bg-white focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all font-body-md"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 mb-1 font-medium">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3.5 py-2.5 border border-slate-200 rounded-xl bg-slate-50/70 text-slate-900 focus:bg-white focus:border-sky-500 focus:ring-2 focus:ring-sky-100 transition-all font-body-md"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="flex items-center justify-between pt-4">
                  <button type="button" onClick={() => setIsRegistering(true)} className="text-sky-600 font-medium text-xs hover:underline font-semibold">
                    Create new registration
                  </button>
                  <button type="submit" className="flex items-center gap-2 justify-center py-2.5 px-6 border border-transparent rounded-xl font-label-caps text-label-caps text-white bg-sky-600 hover:bg-sky-700 transition-colors font-semibold shadow-sm shadow-sky-600/25">
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

      {/* SideNavbar (Styled strictly from layout list of dashboards) */}
      <nav className="fixed left-0 top-0 bottom-0 w-sidebar-width flex flex-col z-45 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
        {/* Logo / Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
          <div className="w-9 h-9 rounded bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900 flex items-center justify-center text-teal-600 dark:text-teal-400">
            <span className="material-symbols-outlined fill text-[20px]">sensors</span>
          </div>
          <div className="text-left">
            <h1 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold leading-tight">Wi-Fi Sense</h1>
            <p className="text-[10px] text-teal-600 font-bold uppercase tracking-wider block">AI Monitoring Active</p>
          </div>
        </div>

        {/* Navigation items (Strictly matches the layout in user screenshot) */}
        <div className="flex-1 overflow-y-auto py-3 px-3 flex flex-col gap-1 text-[11px] font-bold uppercase tracking-wider">
          
          <button
            onClick={() => setCurrentView("family")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "family" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">group</span>
            Family Member Portal
          </button>

          <button
            onClick={() => setCurrentView("analytics")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "analytics" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">analytics</span>
            Analytics Dashboard
          </button>

          <button
            onClick={() => setCurrentView("devices")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "devices" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">router</span>
            Sensing Device Management
          </button>

          <button
            onClick={() => setCurrentView("alerts")}
            className={`flex items-center justify-between gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "alerts" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">history</span>
              Alert Management Dashboard
            </span>
            {alerts.filter(a => a.status === "new").length > 0 && (
              <span className="bg-red-500 text-white rounded-full px-2 py-0.5 text-[9px] font-bold animate-pulse">
                {alerts.filter(a => a.status === "new").length}
              </span>
            )}
          </button>

          <button
            onClick={() => setCurrentView("occupancy")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "occupancy" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">meeting_room</span>
            Room Occupancy View
          </button>

          <button
            onClick={() => setCurrentView("dashboard")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "dashboard" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px] fill">sensors</span>
            Monitoring Dashboard
          </button>

          <button
            onClick={() => setCurrentView("caregiver")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "caregiver" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">medical_services</span>
            Caregiver Dashboard
          </button>

          <button
            onClick={() => setCurrentView("corporate")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "corporate" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">domain</span>
            Corporate Staff Dashboard
          </button>

          <button
            onClick={() => setCurrentView("assets")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "assets" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">account_tree</span>
            Facility Manager Dashboard
          </button>

          <button
            onClick={() => setCurrentView("orgadmin")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "orgadmin" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">settings_applications</span>
            Organization Admin Dashboard
          </button>

          <button
            onClick={() => setCurrentView("sysadmin")}
            className={`flex items-center gap-stack-sm rounded-lg p-2.5 text-left w-full transition-all ${
              currentView === "sysadmin" ? "bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200/20" : "text-slate-650 dark:text-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">admin_panel_settings</span>
            System Admin Dashboard
          </button>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 flex flex-col gap-4">
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
          {/* Top Scope Selector & Settings */}
          <div className="flex items-center gap-stack-md text-xs font-bold uppercase tracking-wider text-slate-550 dark:text-slate-400">
            <span className="material-symbols-outlined text-teal-600 dark:text-teal-400">corporate_fare</span>
            <span>Active Deployment: <span className="text-slate-950 dark:text-white">
              {organizations[0]?.name || "Wi-Fi Sense Enterprise"}
            </span></span>
          </div>

          <div className="flex items-center gap-gutter">
            {/* Search Input */}
            <div className="relative hidden md:block">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[20px]">search</span>
              <input
                className="pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-body-md focus:outline-none focus:border-teal-500 w-64 text-slate-800 dark:text-white"
                placeholder="Search rooms, telemetry..."
                type="text"
              />
            </div>

            {/* Actions group */}
            <div className="flex items-center gap-stack-sm border-l border-slate-200 dark:border-slate-850 pl-gutter">
              <button
                onClick={() => {
                  if (devices.length > 0) {
                    setSimDeviceId(devices[0].id);
                    setShowSimulateDrawer(true);
                  } else {
                    alert("Please register a sensing device first.");
                  }
                }}
                className="text-teal-600 dark:text-teal-400 border border-teal-600 dark:border-teal-450 px-4 py-2 rounded text-xs font-bold uppercase hover:bg-teal-50 dark:hover:bg-teal-950/20 transition-colors cursor-pointer"
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

              <div className="relative">
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 ml-2 overflow-hidden border border-slate-200 dark:border-slate-800 flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-teal-500 transition-all"
                  title="Profile Menu & Photo Upload"
                >
                  {user?.photo_url ? (
                    <img
                      alt="User avatar"
                      className="w-full h-full object-cover"
                      src={user.photo_url.startsWith("http") ? user.photo_url : `${API_BASE}${user.photo_url}`}
                    />
                  ) : (
                    <div className="w-full h-full bg-teal-50 dark:bg-teal-950/40 flex items-center justify-center text-teal-700 dark:text-teal-400 font-bold text-xs">
                      {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "WS"}
                    </div>
                  )}
                </button>

                {showProfileMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl p-4 z-50 text-left">
                    <div className="flex items-center gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
                      <div className="w-12 h-12 rounded-full overflow-hidden border border-slate-200 dark:border-slate-800 shrink-0 flex items-center justify-center bg-teal-50 dark:bg-teal-950/40">
                        {user?.photo_url ? (
                          <img
                            alt="User avatar"
                            className="w-full h-full object-cover"
                            src={user.photo_url.startsWith("http") ? user.photo_url : `${API_BASE}${user.photo_url}`}
                          />
                        ) : (
                          <span className="text-teal-700 dark:text-teal-400 font-bold text-sm">
                            {((user?.first_name?.[0] || "") + (user?.last_name?.[0] || "")).toUpperCase() || "WS"}
                          </span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-slate-900 dark:text-white truncate">
                          {user?.first_name} {user?.last_name}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {user?.email}
                        </div>
                        <div className="text-[10px] text-teal-600 dark:text-teal-400 font-mono uppercase mt-0.5 font-bold">
                          {role}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 space-y-2">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handlePhotoUpload}
                      />
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full py-1.5 px-3 bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 hover:bg-teal-100 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-sm">photo_camera</span>
                        Upload Profile Photo
                      </button>
                      <button
                        onClick={() => {
                          setShowProfileMenu(false);
                          handleLogout();
                        }}
                        className="w-full py-1.5 px-3 border border-red-200 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-sm">logout</span>
                        Logout
                      </button>
                    </div>
                  </div>
                )}
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
            1. MONITORING DASHBOARD (CENTRAL MONITORING BENTO)
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
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Live Feed</h3>
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
                              <td className="p-4 text-slate-800 dark:text-slate-355">
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
            2. ROOM OCCUPANCY VIEW (DEDICATED FULL GRID SCREEN / DETAILED ROOM 204 VIEW)
          ============================================================================ */}
          {currentView === "occupancy" && (
            <div className="space-y-6 text-left">
              {/* Breadcrumbs & Navigation */}
              <div className="flex items-center justify-between mb-4">
                <nav className="flex text-body-md font-body-md text-slate-500 dark:text-slate-400">
                  <ol className="inline-flex items-center space-x-1 md:space-x-3">
                    <li className="inline-flex items-center">
                      <a className="inline-flex items-center hover:text-teal-650 transition-colors cursor-pointer">
                        Building A
                      </a>
                    </li>
                    <li>
                      <div className="flex items-center">
                        <span className="material-symbols-outlined text-slate-400 mx-1" style={{ fontSize: "16px" }}>chevron_right</span>
                        <a className="hover:text-teal-650 transition-colors ml-1 md:ml-2 cursor-pointer">Floor 2</a>
                      </div>
                    </li>
                    <li aria-current="page">
                      <div className="flex items-center">
                        <span className="material-symbols-outlined text-slate-400 mx-1" style={{ fontSize: "16px" }}>chevron_right</span>
                        <span className="text-slate-800 dark:text-white font-semibold ml-1 md:ml-2">Room 204</span>
                      </div>
                    </li>
                  </ol>
                </nav>
                <div className="flex gap-2">
                  <button className="p-2 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 transition-colors flex items-center justify-center">
                    <span className="material-symbols-outlined">chevron_left</span>
                  </button>
                  <button className="p-2 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-850 transition-colors flex items-center justify-center">
                    <span className="material-symbols-outlined">chevron_right</span>
                  </button>
                </div>
              </div>

              {/* Bento Grid Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
                {/* Current Status Card (Large) */}
                <div className="lg:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 relative overflow-hidden shadow-sm">
                  <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: "repeating-linear-gradient(45deg, #0b1c30 0, #0b1c30 1px, transparent 1px, transparent 10px)" }}></div>
                  <div className="flex justify-between items-start mb-6 relative z-10">
                    <div>
                      <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold mb-1">Room 204</h1>
                      <p className="text-body-md font-body-md text-slate-500 dark:text-slate-400">Conference Room - East Wing</p>
                    </div>
                    <div className="bg-slate-950 dark:bg-slate-800 text-white px-4 py-2 rounded-full flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full bg-teal-400 ${activeTelemetryActivity !== "Empty" ? "animate-pulse" : ""}`}></span>
                      <span className="text-label-caps font-label-caps font-bold tracking-wider uppercase">
                        {activeTelemetryActivity !== "Empty" ? "OCCUPIED" : "VACANT"}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                    <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg p-5 flex flex-col justify-center">
                      <span className="text-label-caps font-label-caps text-slate-400 mb-2">DETECTED ACTIVITY</span>
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center text-teal-600 dark:text-teal-400">
                          <span className="material-symbols-outlined" style={{ fontSize: "28px" }}>
                            {activeTelemetryActivity === "Walking" ? "directions_walk" : activeTelemetryActivity === "Sitting" ? "bed" : "airline_seat_recline_normal"}
                          </span>
                        </div>
                        <div>
                          <span className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold block">{activeTelemetryActivity.replace("_", " ")}</span>
                          <span className="text-data-mono font-data-mono text-teal-650 dark:text-teal-400 font-bold">High Confidence (94%)</span>
                        </div>
                      </div>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-lg p-5 flex flex-col justify-center">
                      <span className="text-label-caps font-label-caps text-slate-400 mb-2">CURRENT DURATION</span>
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-amber-50 dark:bg-amber-950/20 flex items-center justify-center text-amber-600">
                          <span className="material-symbols-outlined" style={{ fontSize: "28px" }}>timer</span>
                        </div>
                        <div>
                          <span className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold block">
                            {activeTelemetryActivity !== "Empty" ? "15 mins" : "0 mins"}
                          </span>
                          <span className="text-data-mono font-data-mono text-slate-500">Started 10:42 AM</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 flex justify-between items-center text-body-sm font-body-md text-slate-500 border-t border-slate-200 dark:border-slate-800 pt-4">
                    <span>Signal Strength: Excellent (-45 dBm)</span>
                    <span>Last Updated: Just now</span>
                  </div>
                </div>

                {/* Occupancy Statistics (Side Panel) */}
                <div className="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 flex flex-col gap-6 shadow-sm">
                  <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white border-b border-slate-250 dark:border-slate-800 pb-2 font-bold">Occupancy Statistics</h3>
                  <div className="space-y-4 flex-1">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-550 dark:text-slate-400">Daily Average</span>
                      <span className="font-data-mono text-slate-905 dark:text-white font-semibold">4.2 hours</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-teal-650 h-full rounded-full" style={{ width: "35%" }}></div>
                    </div>
                    <div className="flex justify-between items-center mt-4 text-sm">
                      <span className="text-slate-550 dark:text-slate-400">Peak Time</span>
                      <span className="font-data-mono text-slate-905 dark:text-white font-semibold">14:00 - 15:30</span>
                    </div>
                    <div className="flex justify-between items-center mt-4 text-sm">
                      <span className="text-slate-550 dark:text-slate-400">Total Events (24h)</span>
                      <span className="font-data-mono text-slate-905 dark:text-white font-semibold">12</span>
                    </div>
                    <div className="mt-8 p-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg">
                      <span className="text-label-caps font-label-caps text-slate-405 block mb-1">LAST KNOWN VACANCY</span>
                      <span className="text-body-md font-body-md text-slate-800 dark:text-slate-205 block mb-1">Today, 09:15 AM - 10:42 AM</span>
                      <span className="text-data-mono font-data-mono text-teal-650 dark:text-teal-400 block font-bold">Duration: 1h 27m</span>
                    </div>
                  </div>
                </div>

                {/* Historical Occupancy Timeline (Full Width) */}
                <div className="lg:col-span-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Historical Occupancy (Last 24 Hours)</h3>
                    <div className="flex items-center gap-4 text-label-caps font-label-caps text-slate-455">
                      <div className="flex items-center gap-1"><span className="w-3 h-3 bg-teal-600 rounded-sm"></span> Occupied</div>
                      <div className="flex items-center gap-1"><span className="w-3 h-3 bg-slate-100 dark:bg-slate-800 rounded-sm border border-slate-200 dark:border-slate-700"></span> Vacant</div>
                    </div>
                  </div>
                  {/* Gantt Chart Container */}
                  <div className="relative pt-4 pb-8">
                    <div className="absolute top-0 left-0 w-full flex justify-between text-data-mono font-data-mono text-slate-400 text-xs px-2">
                      <span>12 PM</span>
                      <span>4 PM</span>
                      <span>8 PM</span>
                      <span>12 AM</span>
                      <span>4 AM</span>
                      <span>8 AM</span>
                      <span>Now</span>
                    </div>
                    <div className="h-8 bg-slate-100 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 mt-6 relative overflow-hidden flex">
                      <div className="h-full bg-teal-600 border-r border-slate-100 dark:border-slate-950 relative group" style={{ width: "15%" }}></div>
                      <div className="h-full bg-transparent border-r border-slate-200 dark:border-slate-800" style={{ width: "10%" }}></div>
                      <div className="h-full bg-teal-600 border-r border-slate-100 dark:border-slate-950 relative group" style={{ width: "8%" }}></div>
                      <div className="h-full bg-transparent border-r border-slate-200 dark:border-slate-800" style={{ width: "40%" }}></div>
                      <div className="h-full bg-teal-600 border-r border-slate-100 dark:border-slate-950 relative group" style={{ width: "12%" }}></div>
                      <div className="h-full bg-transparent border-r border-slate-200 dark:border-slate-800" style={{ width: "10%" }}></div>
                      <div className="h-full bg-teal-600 border-r border-slate-100 dark:border-slate-950 relative group" style={{ width: "5%" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            3. CAREGIVER DASHBOARD
          ============================================================================ */}
          {currentView === "caregiver" && (
            <div className="space-y-6 text-left">
              {/* Page Header */}
              <div className="mb-stack-lg flex justify-between items-end">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Caregiver Dashboard</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400">Shift handovers, caregiver logs, and patient safety tracking.</p>
                </div>
                <div className="text-xs font-bold text-slate-500 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
                  System Scan Status: Normal
                </div>
              </div>

              {/* Critical Alert Banner */}
              {activeFallAlert && (
                <div className="bg-red-50 border border-red-500 text-red-700 dark:bg-red-950/20 dark:text-red-400 rounded-lg p-4 mb-6 flex items-center justify-between shadow-sm pulse-animation">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined fill text-red-500 text-2xl">warning</span>
                    <div>
                      <h2 className="text-headline-sm font-headline-sm font-bold uppercase text-red-700">POTENTIAL FALL DETECTED - {activeFallAlert.message.split(" ")[0] || "Room"}</h2>
                      <p className="text-body-md font-body-md">{activeFallAlert.message}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleAcknowledge(activeFallAlert.id)}
                      className="px-4 py-2 bg-transparent border border-red-500 text-red-600 rounded font-body-md font-semibold hover:bg-red-500/10 transition-colors"
                    >
                      Acknowledge
                    </button>
                    <button 
                      onClick={() => setShowResolveModal(activeFallAlert.id)}
                      className="px-4 py-2 bg-red-650 text-white rounded font-body-md font-semibold hover:opacity-90 transition-opacity"
                    >
                      Dispatch Help
                    </button>
                  </div>
                </div>
              )}

              {/* Dashboard Layout: 12-column Grid */}
              <div className="grid grid-cols-12 gap-gutter">
                {/* Left Column: Active Incidents & Assigned Residents (8 cols on desktop) */}
                <div className="col-span-12 xl:col-span-8 flex flex-col gap-gutter">
                  {/* Active Incidents Table */}
                  <section className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                    <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
                      <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Active Incidents</h3>
                      <span className={`px-2 py-1 rounded text-label-caps font-label-caps ${alerts.filter(a => a.status !== "resolved").length > 0 ? "bg-red-50 text-red-650 font-bold" : "bg-teal-50 text-teal-650 font-bold"}`}>
                        {alerts.filter(a => a.status !== "resolved").length} Active
                      </span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left">
                        <thead className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-label-caps font-label-caps text-slate-500 dark:text-slate-400 uppercase">
                          <tr>
                            <th className="px-5 py-3">Severity</th>
                            <th className="px-5 py-3">Room</th>
                            <th className="px-5 py-3">Resident</th>
                            <th className="px-5 py-3">Type</th>
                            <th className="px-5 py-3">Time</th>
                            <th className="px-5 py-3 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-body-md font-body-md">
                          {alerts.filter(a => a.status !== "resolved").map(a => (
                            <tr key={a.id} className="bg-red-50/20 dark:bg-red-950/10">
                              <td className="px-5 py-4">
                                <div className="flex items-center gap-2">
                                  <span className="w-2 h-2 rounded-full bg-red-600"></span>
                                  <span className="text-red-600 font-semibold">{a.event_type === "Fall_Detected" ? "Critical" : "Warning"}</span>
                                </div>
                              </td>
                              <td className="px-5 py-4 font-data-mono text-data-mono">{rooms.find(r => r.id === a.room_id)?.name || "Room"}</td>
                              <td className="px-5 py-4 font-semibold text-slate-900 dark:text-white">
                                {residents.filter(r => r.room_id === a.room_id).map(r => `${r.first_name} ${r.last_name}`).join(", ") || "Mary Smith"}
                              </td>
                              <td className="px-5 py-4">{a.event_type.replace("_", " ")}</td>
                              <td className="px-5 py-4 text-slate-500 font-data-mono text-data-mono">{new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                              <td className="px-5 py-4 text-right">
                                {a.status === "new" && (
                                  <button onClick={() => handleAcknowledge(a.id)} className="text-teal-650 hover:underline mr-3 font-semibold">Acknowledge</button>
                                )}
                                <button onClick={() => setShowResolveModal(a.id)} className="px-3 py-1 bg-teal-600 text-white rounded hover:opacity-90 transition-opacity">Resolve</button>
                              </td>
                            </tr>
                          ))}
                          {alerts.filter(a => a.status !== "resolved").length === 0 && (
                            <tr>
                              <td colSpan="6" className="p-8 text-center text-slate-400 italic">No pending health incidents. All clear.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>

                  {/* Assigned Residents Grid */}
                  <section>
                    <div className="flex justify-between items-end mb-4">
                      <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Assigned Residents Overview</h3>
                      <div className="flex gap-2">
                        <span className="flex items-center gap-1 text-label-caps font-label-caps text-slate-550"><span className="w-2 h-2 bg-teal-500 rounded-full"></span> Monitored</span>
                        <span className="flex items-center gap-1 text-label-caps font-label-caps text-slate-550"><span className="w-2 h-2 bg-slate-300 rounded-full"></span> Vacant</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {residents.map((res, i) => {
                        const rm = rooms.find(r => r.id === res.room_id);
                        const isFall = rm && occupancySummary.occupied_room_details.find(d => d.room_id === rm.id)?.current_activity === "Fall_Detected";
                        return (
                          <div 
                            key={res.id} 
                            onClick={() => {
                              setCurrentView("occupancy");
                            }}
                            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col gap-3 hover:border-teal-500 transition-colors cursor-pointer group"
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center text-teal-700 dark:text-teal-400 font-headline-sm font-bold">
                                  {res.first_name[0]}{res.last_name[0]}
                                </div>
                                <div>
                                  <h4 className="font-bold text-slate-900 dark:text-white">{res.first_name} {res.last_name}</h4>
                                  <p className="text-body-md font-data-mono text-slate-500">{rm?.name || "Room"}</p>
                                </div>
                              </div>
                              <span className={`material-symbols-outlined ${isFall ? "text-red-500 fill animate-bounce" : "text-teal-650"}`} title="Assigned Subject">
                                {isFall ? "emergency_home" : "home"}
                              </span>
                            </div>
                            <div className="bg-slate-50 dark:bg-slate-950 rounded-lg p-3 mt-2 flex justify-between items-center text-xs">
                              <div>
                                <p className="text-[10px] font-bold text-slate-405 uppercase">ACTIVITY STATUS</p>
                                <p className="font-semibold text-slate-850 dark:text-white flex items-center gap-1">
                                  <span className="material-symbols-outlined text-[16px]">person</span> 
                                  {occupancySummary.occupied_room_details.find(d => d.room_id === res.room_id)?.current_activity.replace("_", " ") || "Resting"}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-[10px] font-bold text-slate-405 uppercase">LAST TIMEOUT</p>
                                <p className="font-data-mono text-data-mono text-slate-850 dark:text-white">Live</p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </section>
                </div>

                {/* Right Column: Alert History Sidebar (4 cols on desktop) */}
                <aside className="col-span-12 xl:col-span-4 flex flex-col gap-gutter">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm h-full flex flex-col">
                    <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
                      <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold flex items-center gap-2">
                        <span className="material-symbols-outlined text-slate-500">history</span>
                        Alert Timeline
                      </h3>
                      <button onClick={() => setCurrentView("alerts")} className="text-teal-605 text-label-caps font-label-caps font-semibold hover:underline">View All</button>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
                      {alerts.map((al, idx) => (
                        <div key={al.id} className="relative pl-6 pb-4 border-l-2 border-slate-200 dark:border-slate-800 last:border-0 last:pb-0">
                          <span className={`absolute left-[-9px] top-0 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 ${al.status === "resolved" ? "bg-slate-400" : "bg-red-500 animate-pulse"}`}></span>
                          <div className="flex justify-between items-start mb-1 text-xs">
                            <span className="text-slate-400 font-data-mono">{new Date(al.created_at).toLocaleTimeString()}</span>
                            <span className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded-full ${al.status === "resolved" ? "bg-slate-100 text-slate-650" : "bg-red-50 text-red-650"}`}>{al.status}</span>
                          </div>
                          <p className="font-bold text-slate-900 dark:text-white text-sm">{al.event_type.replace("_", " ")}</p>
                          <p className="text-xs text-slate-550">{rooms.find(r => r.id === al.room_id)?.name || "Room"}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </aside>
              </div>
            </div>
          )}

          {/* ============================================================================
            4. ORG ADMIN DASHBOARD
          ============================================================================ */}
          {currentView === "orgadmin" && (
            <div className="space-y-6 text-left">
              <div className="mb-stack-lg">
                <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Organization Admin Dashboard</h2>
                <p className="text-body-md text-slate-500 dark:text-slate-400">Manage corporate and elder-care tenant organizations settings.</p>
              </div>

              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-center border-b pb-2 mb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">Active Organizations</h3>
                  <button
                    onClick={() => setShowAddOrgModal(true)}
                    className="bg-teal-600 text-white px-3 py-1 rounded-full text-xs font-bold uppercase hover:bg-teal-700"
                  >
                    Add Organization
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                        <th className="p-3">Organization Name</th>
                        <th className="p-3">Deployment Scope Type</th>
                        <th className="p-3">Organization ID</th>
                      </tr>
                    </thead>
                    <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                      {organizations.map(org => (
                        <tr key={org.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                          <td className="p-3 font-semibold dark:text-white">{org.name}</td>
                          <td className="p-3">
                            <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                              org.type === "ELDER_CARE" ? "bg-teal-50 dark:bg-teal-950/20 text-teal-650" : "bg-blue-50 dark:bg-blue-950/20 text-blue-650"
                            }`}>
                              {org.type}
                            </span>
                          </td>
                          <td className="p-3 font-mono text-xs text-slate-450">{org.id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Family Portal Access Link Requests Section */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm mt-6">
                <div className="border-b pb-2 mb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                    Family Portal Link Requests
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800 text-[10px] text-slate-400 font-bold uppercase border-b border-slate-200 dark:border-slate-800">
                        <th className="p-3 text-left">Request ID</th>
                        <th className="p-3 text-left">Applicant ID</th>
                        <th className="p-3 text-left">Target Resident Name</th>
                        <th className="p-3 text-left">Status</th>
                        <th className="p-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="text-sm divide-y divide-slate-100 dark:divide-slate-800">
                      {accessRequests.map(req => {
                        const targetRes = residents.find(r => r.id === req.resident_id);
                        const targetName = targetRes ? `${targetRes.first_name} ${targetRes.last_name}` : req.resident_id;
                        return (
                          <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                            <td className="p-3 font-mono text-xs text-slate-500">{req.id}</td>
                            <td className="p-3 font-mono text-xs">{req.requesting_user_id}</td>
                            <td className="p-3 font-semibold dark:text-white">{targetName}</td>
                            <td className="p-3">
                              <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold ${
                                req.status === "pending" ? "bg-amber-50 text-amber-650" : req.status === "approved" ? "bg-teal-50 text-teal-650" : "bg-red-50 text-red-650"
                              }`}>
                                {req.status.toUpperCase()}
                              </span>
                            </td>
                            <td className="p-3 text-right space-x-2">
                              {req.status === "pending" && (
                                <>
                                  <button
                                    onClick={() => handleReviewRequest(req.id, "approved")}
                                    className="bg-teal-600 text-white px-2.5 py-1 rounded text-xs hover:bg-teal-700 font-bold"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    onClick={() => handleReviewRequest(req.id, "declined")}
                                    className="bg-red-600 text-white px-2.5 py-1 rounded text-xs hover:bg-red-700 font-bold"
                                  >
                                    Decline
                                  </button>
                                </>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                      {accessRequests.length === 0 && (
                        <tr>
                          <td colSpan="5" className="p-4 text-center text-slate-400 italic">No access link requests recorded.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            5. SYSTEM ADMIN DASHBOARD (USER & ROLES AUDITING)
          ============================================================================ */}
          {currentView === "sysadmin" && (
            <div className="flex flex-col gap-gutter text-left">
              {/* Page Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 font-label-caps text-label-caps mb-2">
                    <span>System Config</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                    <span className="text-teal-650 font-bold">User Management</span>
                  </div>
                  <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">User Administration</h1>
                  <p className="text-slate-500 dark:text-slate-400 font-body-md text-body-md mt-1">Manage institutional access, role scopes, and system permissions.</p>
                </div>
                <button 
                  onClick={() => setIsRegistering(true)}
                  className="bg-teal-600 text-white px-5 py-2.5 rounded-lg font-label-caps text-label-caps hover:bg-teal-700 transition-colors flex items-center gap-2 self-start md:self-auto shadow-sm font-semibold"
                >
                  <span className="material-symbols-outlined">person_add</span>
                  Add New User
                </button>
              </div>

              {/* Bento Grid Layout for Content */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-gutter">
                {/* Left/Main Column: Active Users Table */}
                <div className="xl:col-span-2 flex flex-col gap-4">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-sm">
                    <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900">
                      <h2 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Active Personnel</h2>
                      <button 
                        onClick={exportPersonnelCSV}
                        className="text-teal-600 dark:text-teal-400 font-label-caps text-label-caps hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        Export CSV <span className="material-symbols-outlined text-[16px]">download</span>
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800">
                            <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">User Details</th>
                            <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">Role & Scope</th>
                            <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold">Permissions Profile</th>
                            <th className="p-4 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 font-semibold text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {/* Dr. Evelyn Lin (Static/Seeded) */}
                          <tr className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-teal-650 dark:text-teal-450 font-bold text-sm">EL</div>
                                <div>
                                  <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">Dr. Evelyn Lin</div>
                                  <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">ID: 948-AX-01</div>
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-col gap-1">
                                <span className="inline-flex items-center gap-1 font-label-caps text-label-caps text-teal-650 border border-teal-200/50 dark:border-teal-900/50 rounded px-2 py-0.5 w-max">
                                  <span className="material-symbols-outlined text-[14px]">shield_person</span> Admin
                                </span>
                                <span className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs">St. Jude - Ward A, B, C</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-wrap gap-1">
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">SysConfig</span>
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">AlertRes</span>
                              </div>
                            </td>
                            <td className="p-4 text-right">
                              <span className="inline-flex items-center gap-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 px-2.5 py-1 rounded-full font-label-caps text-label-caps font-bold">
                                <span className="w-1.5 h-1.5 rounded-full bg-teal-600"></span> Active
                              </span>
                            </td>
                          </tr>

                          {/* Dynamic Active Registered Users */}
                          <tr className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-teal-650 dark:text-teal-450 font-bold text-sm">BJ</div>
                                <div>
                                  <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">Blesson Joseph Byju</div>
                                  <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">ID: System-Admin</div>
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-col gap-1">
                                <span className="inline-flex items-center gap-1 font-label-caps text-label-caps text-teal-650 border border-teal-200/50 dark:border-teal-900/50 rounded px-2 py-0.5 w-max">
                                  <span className="material-symbols-outlined text-[14px]">shield_person</span> system_admin
                                </span>
                                <span className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs">Global Deployment Scope</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-wrap gap-1">
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">SysConfig</span>
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">AlertRes</span>
                              </div>
                            </td>
                            <td className="p-4 text-right">
                              <span className="inline-flex items-center gap-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-450 px-2.5 py-1 rounded-full font-label-caps text-label-caps font-bold">
                                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span> Active
                              </span>
                            </td>
                          </tr>

                          {/* Abhinand M A */}
                          <tr className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-teal-650 dark:text-teal-450 font-bold text-sm">AM</div>
                                <div>
                                  <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">Abhinand M A</div>
                                  <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">ID: Facility-Manager</div>
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-col gap-1">
                                <span className="inline-flex items-center gap-1 font-label-caps text-label-caps text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-750 rounded px-2 py-0.5 w-max">
                                  <span className="material-symbols-outlined text-[14px]">supervisor_account</span> facility_manager
                                </span>
                                <span className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs">Amal Jyothi College</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-wrap gap-1">
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">AlertRes</span>
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">Analytics</span>
                              </div>
                            </td>
                            <td className="p-4 text-right">
                              <span className="inline-flex items-center gap-1.5 bg-teal-50 dark:bg-teal-950/20 text-teal-655 dark:text-teal-450 px-2.5 py-1 rounded-full font-label-caps text-label-caps font-bold">
                                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span> Active
                              </span>
                            </td>
                          </tr>

                          {/* Abhinanth S Pillai */}
                          <tr className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-teal-650 dark:text-teal-450 font-bold text-sm">AP</div>
                                <div>
                                  <div className="font-headline-sm text-[14px] leading-tight text-slate-900 dark:text-white font-semibold">Abhinanth S Pillai</div>
                                  <div className="font-data-mono text-data-mono text-slate-400 mt-0.5">ID: Caregiver-Lab</div>
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-col gap-1">
                                <span className="inline-flex items-center gap-1 font-label-caps text-label-caps text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-750 rounded px-2 py-0.5 w-max bg-slate-50 dark:bg-slate-800">
                                  <span className="material-symbols-outlined text-[14px]">badge</span> caregiver
                                </span>
                                <span className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs">WiFi Sense Research Lab</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex flex-wrap gap-1">
                                <span className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded text-xs font-data-mono">ViewOnly</span>
                              </div>
                            </td>
                            <td className="p-4 text-right">
                              <span className="inline-flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2.5 py-1 rounded-full font-label-caps text-label-caps">
                                <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span> Offline
                              </span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between text-xs">
                      <span className="text-slate-550 dark:text-slate-400">Showing 4 of 4 active accounts</span>
                    </div>
                  </div>
                </div>

                {/* Right Column: Role Permissions Grid */}
                <div className="xl:col-span-1 flex flex-col gap-4">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col h-full">
                    <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
                      <h2 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Role Matrix</h2>
                      <p className="font-body-md text-body-md text-slate-500 dark:text-slate-400 text-xs mt-1">System-wide access levels.</p>
                    </div>
                    <div className="p-0 flex-1">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 font-bold uppercase text-[10px] text-slate-450">
                            <th className="p-3 font-semibold">Capability</th>
                            <th className="p-3 text-center font-semibold">Admin</th>
                            <th className="p-3 text-center font-semibold">Manager</th>
                            <th className="p-3 text-center font-semibold">Caregiver</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          <tr>
                            <td className="p-3 font-body-md text-body-md text-slate-800 dark:text-slate-200">Live Monitoring</td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                          </tr>
                          <tr>
                            <td className="p-3 font-body-md text-body-md text-slate-800 dark:text-slate-200">Alert Resolution</td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-slate-300 dark:text-slate-700 text-[18px]">remove</span></td>
                          </tr>
                          <tr>
                            <td className="p-3 font-body-md text-body-md text-slate-800 dark:text-slate-200">Device Config</td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-teal-600 dark:text-teal-400 text-[18px]">check_circle</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-slate-300 dark:text-slate-700 text-[18px]">remove</span></td>
                            <td className="p-3 text-center"><span className="material-symbols-outlined text-slate-300 dark:text-slate-700 text-[18px]">remove</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex justify-center">
                      <button className="text-teal-600 dark:text-teal-400 font-label-caps text-label-caps hover:underline flex items-center gap-1">
                        Edit Policy <span className="material-symbols-outlined text-[16px]">edit</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================================
            OTHERS (CORPORATE, FAMILY, PHYSICAL CONFIG, DEVICE HEALTH, ALERTS, ANALYTICS)
          ============================================================================ */}
          {currentView === "corporate" && (
            <div className="space-y-6 text-left">
              {/* Corporate Facility View Title Row */}
              <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Corporate Overview</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400">Meeting Room Occupancy and Underutilized Spaces Management.</p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={exportCorporateAnalytics}
                    className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow cursor-pointer"
                  >
                    Export Analytics
                  </button>
                </div>
              </div>

              {/* Util Bento Widgets */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-gutter">
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                  <div className="text-label-caps font-label-caps text-slate-400 mb-1">Peak Utilization</div>
                  <div className="font-headline-lg text-slate-900 dark:text-white font-bold">88%</div>
                  <div className="w-full bg-slate-100 dark:bg-slate-850 h-2 rounded-full mt-3 overflow-hidden">
                    <div className="bg-teal-600 h-full rounded-full" style={{ width: "88%" }}></div>
                  </div>
                </div>
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                  <div className="text-label-caps font-label-caps text-slate-400 mb-1">Underutilized Spaces</div>
                  <div className="font-headline-lg text-slate-900 dark:text-white font-bold">
                    {occupancySummary.vacant_rooms} rooms
                  </div>
                  <p className="text-xs text-slate-500 mt-2">Space efficiency optimizations identified.</p>
                </div>
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                  <div className="text-label-caps font-label-caps text-slate-400 mb-1">Potential Savings</div>
                  <div className="font-headline-lg text-teal-600 dark:text-teal-400 font-bold">15%</div>
                  <p className="text-xs text-slate-500 mt-2">Idle HVAC and lighting energy recovery rate.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-12 gap-gutter items-start">
                {/* Meeting Rooms Table */}
                <div className="xl:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                  <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 font-bold text-slate-900 dark:text-white">
                    Real-time Meeting Room Status
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-850 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-450 uppercase font-semibold">
                          <th className="p-4">Room Name</th>
                          <th className="p-4">Capacity</th>
                          <th className="p-4">Status</th>
                          <th className="p-4">Current Stance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {rooms.filter(r => r.name.includes("MCA") || r.name.includes("Staff") || r.name.includes("IoT") || r.name.includes("Seminar")).map(r => {
                          const occ = occupancySummary.occupied_room_details.find(d => d.room_id === r.id);
                          return (
                            <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-850/40">
                              <td className="p-4 font-bold text-slate-900 dark:text-white">{r.name}</td>
                              <td className="p-4">{r.capacity} pax</td>
                              <td className="p-4">
                                {occ?.is_occupied ? (
                                  <span className="bg-teal-50 dark:bg-teal-950/20 text-teal-650 px-2 py-0.5 rounded text-[10px] font-bold">OCCUPIED</span>
                                ) : (
                                  <span className="bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded text-[10px] font-bold">VACANT</span>
                                )}
                              </td>
                              <td className="p-4 font-mono text-slate-500">
                                {occ?.is_occupied ? occ.current_activity : "No movement"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Underutilized spaces list */}
                <div className="xl:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
                  <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold mb-4">Underutilized Spaces</h3>
                  <div className="space-y-3">
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded">
                      <div className="font-bold text-xs text-slate-900 dark:text-white">MCA Seminar Hall</div>
                      <div className="text-[10px] text-slate-500 mt-1">Average Utilization: 8.5%</div>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded">
                      <div className="font-bold text-xs text-slate-900 dark:text-white">Staff Room A</div>
                      <div className="text-[10px] text-slate-500 mt-1">Average Utilization: 11.2%</div>
                    </div>
                  </div>
                  <button 
                    onClick={generateRepurposingReport}
                    className="w-full mt-4 bg-teal-600 text-white py-2 rounded text-xs font-bold uppercase hover:bg-teal-700 shadow cursor-pointer"
                  >
                    Generate Repurposing Report
                  </button>
                </div>
              </div>
            </div>
          )}          {currentView === "family" && (
            <div className="space-y-6 text-left">
              {role !== "emergency_contact" ? (
                /* Admin Preview / Warning */
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
                  <div className="w-16 h-16 bg-teal-50 dark:bg-teal-950/20 rounded-full flex items-center justify-center mb-6 mx-auto">
                    <span className="material-symbols-outlined text-[36px] text-teal-600">verified_user</span>
                  </div>
                  <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">Administrative Preview Mode</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
                    This Family Member Portal is customized exclusively for elder-care resident emergency contacts. 
                    Administrators can approve access link requests, but to view the live dashboard interface, please register a family member account and submit a link request.
                  </p>
                  <div className="bg-slate-50 dark:bg-slate-950 p-5 rounded-lg border border-slate-200 dark:border-slate-850 text-left text-xs space-y-3">
                    <div className="font-bold text-slate-800 dark:text-white uppercase tracking-wider">Demo Credentials:</div>
                    <div className="flex justify-between"><span>John Smith (Approved Link):</span> <code className="bg-slate-250 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">john@wifisense.com / johnpassword</code></div>
                    <div className="flex justify-between"><span>Susan Varghese (Pending Link):</span> <code className="bg-slate-255 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">susan@wifisense.com / susanpassword</code></div>
                  </div>
                </div>
              ) : !familyStatus ? (
                /* Loading */
                <div className="p-8 text-center text-slate-500 italic">Syncing family portal status...</div>
              ) : familyStatus.linked === false ? (
                /* Unlinked Statuses */
                <div className="space-y-6">
                  {familyStatus.request_status === "pending" ? (
                    /* Pending Request */
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
                      <div className="w-16 h-16 bg-amber-50 dark:bg-amber-950/20 rounded-full flex items-center justify-center mb-6 mx-auto animate-pulse">
                        <span className="material-symbols-outlined text-[36px] text-amber-500">pending</span>
                      </div>
                      <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">Access Link Request Pending</h2>
                      <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
                        Your request to view real-time safety status for <strong className="text-slate-850 dark:text-white">{familyStatus.resident_name}</strong> is currently pending.
                        The Organization Administrator will verify your credentials and approve link access.
                      </p>
                      {/* Stepper representation */}
                      <div className="flex justify-between items-center max-w-md mx-auto mt-8 text-xs font-semibold text-slate-500">
                        <div className="flex flex-col items-center gap-1 text-teal-650">
                          <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold">1</span>
                          <span>Registered</span>
                        </div>
                        <div className="h-0.5 bg-teal-500 flex-1 mx-2"></div>
                        <div className="flex flex-col items-center gap-1 text-teal-655 relative">
                          <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold animate-ping absolute"></span>
                          <span className="w-6 h-6 rounded-full bg-teal-50 dark:bg-teal-950/20 flex items-center justify-center border border-teal-500 font-bold relative">2</span>
                          <span>Link Submitted</span>
                        </div>
                        <div className="h-0.5 bg-slate-250 dark:bg-slate-800 flex-1 mx-2"></div>
                        <div className="flex flex-col items-center gap-1 text-slate-400">
                          <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center border border-slate-200 dark:border-slate-700 font-bold">3</span>
                          <span>Approved</span>
                        </div>
                      </div>
                    </div>
                  ) : familyStatus.request_status === "declined" ? (
                    /* Declined Request */
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm">
                      <div className="w-16 h-16 bg-red-50 dark:bg-red-950/20 rounded-full flex items-center justify-center mb-6 mx-auto">
                        <span className="material-symbols-outlined text-[36px] text-red-500">cancel</span>
                      </div>
                      <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2">Access Link Request Declined</h2>
                      <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6">
                        Your request to link with <strong className="text-slate-850 dark:text-white">{familyStatus.resident_name}</strong> was declined by the administrator.
                        Please ensure the registration details align with the resident records.
                      </p>
                      <button
                        onClick={async () => {
                          setSelectedRequestResidentId("");
                          setFamilyStatus(prev => ({ ...prev, request_status: null }));
                        }}
                        className="px-4 py-2 bg-teal-600 text-white rounded font-bold hover:bg-teal-700"
                      >
                        Resubmit New Link Request
                      </button>
                    </div>
                  ) : (
                    /* No request yet: Link Request Form */
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 max-w-xl mx-auto shadow-sm">
                      <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-2 text-center">Link Resident Profile</h2>
                      <p className="text-body-md text-slate-500 dark:text-slate-400 mb-6 text-center">
                        Please select the resident profile at this elder-care facility that you are authorized to monitor.
                      </p>
                      <form onSubmit={submitLinkRequest} className="space-y-4">
                        <div>
                          <label className="block text-xs font-bold uppercase text-slate-400 mb-1">MONITORED SUBJECT</label>
                          <select
                            className="w-full border border-slate-200 dark:border-slate-800 rounded p-2.5 text-sm bg-slate-50 dark:bg-slate-800 dark:text-white font-semibold"
                            value={selectedRequestResidentId}
                            onChange={(e) => setSelectedRequestResidentId(e.target.value)}
                            required
                          >
                            <option value="">-- Select Resident Profile --</option>
                            {residents.map(r => (
                              <option key={r.id} value={r.id}>{r.first_name} {r.last_name}</option>
                            ))}
                          </select>
                        </div>
                        <button
                          type="submit"
                          className="w-full py-2.5 bg-teal-600 text-white rounded-lg text-sm font-bold uppercase shadow hover:bg-teal-700 transition-colors"
                        >
                          Submit Link Request
                        </button>
                      </form>
                    </div>
                  )}
                </div>
              ) : (
                /* Approved Linked Family Member Portal Dashboard */
                <div className="space-y-6">
                  {/* Page Header */}
                  <div className="mb-stack-lg flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div>
                      <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold mb-1">Access Control &amp; Privacy</h1>
                      <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400">Configure family member visibility and monitor safety status.</p>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => setToastMessage({ type: "success", text: "Saved visibility settings." })}
                        className="px-4 py-2 bg-teal-650 text-white rounded-lg text-label-caps font-label-caps hover:opacity-90 font-bold"
                      >
                        Save Settings
                      </button>
                    </div>
                  </div>

                  {/* Bento Grid Layout */}
                  <div className="grid grid-cols-12 gap-gutter">
                    {/* Privacy Guarantee Hero Card (Span 8) */}
                    <div className="col-span-12 lg:col-span-8 bg-teal-50/40 dark:bg-teal-950/10 rounded-xl border border-slate-200 dark:border-slate-800 p-8 relative overflow-hidden flex flex-col justify-between shadow-sm">
                      <div className="absolute -right-20 -top-20 w-64 h-64 border-[40px] border-teal-100/30 dark:border-teal-900/10 rounded-full opacity-50"></div>
                      
                      <div className="relative z-10">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-800 mb-6">
                          <span className="material-symbols-outlined text-[16px] text-teal-600 dark:text-teal-400">verified_user</span>
                          <span className="text-label-caps font-label-caps text-slate-655 dark:text-slate-350">Core Principle</span>
                        </div>
                        <h2 className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold mb-4 max-w-lg">Invisible Security. Zero Cameras. Absolute Privacy.</h2>
                        <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 max-w-xl mb-6">
                          Wi-Fi Sense monitors ambient signal shifts instead of cameras. Your loved one's optical privacy is fully preserved.
                        </p>
                      </div>
                      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                          <span className="material-symbols-outlined text-teal-605 mb-2">videocam_off</span>
                          <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">No Cameras</div>
                          <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">100% optical privacy</div>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                          <span className="material-symbols-outlined text-teal-605 mb-2">mic_off</span>
                          <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">No Microphones</div>
                          <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">No audio recorded</div>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                          <span className="material-symbols-outlined text-teal-605 mb-2">lock</span>
                          <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">Encrypted CSI</div>
                          <div className="text-label-caps font-label-caps text-slate-500 dark:text-slate-450 mt-1">Data mathematically hashed</div>
                        </div>
                      </div>
                    </div>

                    {/* Facility Contact Info Card (Span 4) */}
                    <div className="col-span-12 lg:col-span-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-sm">
                      <div className="flex items-center justify-between mb-6">
                        <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Facility Contact Info</h3>
                      </div>
                      <div className="flex-1 flex flex-col justify-center p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950 space-y-4">
                        <div>
                          <div className="text-[10px] font-bold text-slate-400 uppercase">CARE CENTRE</div>
                          <div className="text-sm font-bold text-slate-850 dark:text-white">{familyStatus.facility_contact.name}</div>
                        </div>
                        <div>
                          <div className="text-[10px] font-bold text-slate-400 uppercase">TELEPHONE LINE</div>
                          <div className="text-sm font-mono text-slate-850 dark:text-white">{familyStatus.facility_contact.phone}</div>
                        </div>
                        <div>
                          <div className="text-[10px] font-bold text-slate-400 uppercase">DIRECT EMAIL</div>
                          <div className="text-sm font-mono text-slate-850 dark:text-white">{familyStatus.facility_contact.email}</div>
                        </div>
                      </div>
                    </div>

                    {/* Resident Live Status Card (Span 6) */}
                    <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-sm">
                      <div className="bg-slate-50 dark:bg-slate-950 border-b border-slate-250 dark:border-slate-800 p-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-teal-605">verified_user</span>
                          <h3 className="text-body-md font-body-md font-bold text-slate-950 dark:text-white">Resident Status</h3>
                        </div>
                        <span className="text-[10px] font-bold bg-teal-50 text-teal-650 px-2.5 py-1 rounded">Linked profile</span>
                      </div>
                      <div className="p-6 flex-1 bg-slate-50 dark:bg-slate-950 flex flex-col justify-between">
                        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 text-left space-y-4 shadow-sm">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="text-headline-md font-headline-md font-bold text-slate-950 dark:text-white">
                                {familyStatus.resident.first_name} {familyStatus.resident.last_name}
                              </div>
                              <div className="text-body-md font-data-mono text-slate-500 mt-1">Assigned: {familyStatus.resident.room_name}</div>
                            </div>
                            <div className="bg-teal-50 dark:bg-teal-950/20 text-teal-650 px-3 py-1 rounded-full text-label-caps font-label-caps border border-teal-200/20 flex items-center gap-1.5 font-bold">
                              <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span> 
                              {familyStatus.presence_status.toUpperCase()}
                            </div>
                          </div>
                          
                          <div className="border-t border-slate-100 dark:border-slate-800 pt-4 flex justify-between items-center text-xs">
                            <div>
                              <p className="text-[10px] font-bold text-slate-400 uppercase">RECENT ACTIVITY</p>
                              <p className="font-semibold text-slate-850 dark:text-white mt-1 capitalize">{familyStatus.recent_activity.activity.replace("_", " ")}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-[10px] font-bold text-slate-400 uppercase">LAST DETECTED</p>
                              <p className="font-data-mono text-data-mono text-slate-850 dark:text-white mt-1">
                                {familyStatus.recent_activity.timestamp ? new Date(familyStatus.recent_activity.timestamp).toLocaleTimeString() : "Live"}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Read-Only Alert History List */}
                        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 mt-4 text-left shadow-sm flex-1">
                          <h4 className="text-xs font-bold uppercase text-slate-400 mb-3 tracking-wider">Alert History (Read-only)</h4>
                          <div className="space-y-3 max-h-[160px] overflow-y-auto">
                            {familyStatus.alerts.map(a => (
                              <div key={a.id} className="flex justify-between items-center p-3 rounded bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 text-xs">
                                <div>
                                  <div className="font-bold text-slate-850 dark:text-white">{a.event_type.replace("_", " ")}</div>
                                  <div className="text-[10px] text-slate-400 mt-0.5">{new Date(a.created_at).toLocaleTimeString()}</div>
                                </div>
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  a.status === "resolved" ? "bg-slate-100 text-slate-655" : "bg-red-50 text-red-650"
                                }`}>
                                  {a.status.toUpperCase()}
                                </span>
                              </div>
                            ))}
                            {familyStatus.alerts.length === 0 && (
                              <p className="text-xs text-slate-400 italic text-center p-4">No historic warnings logged.</p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Access Control Settings (Span 6) */}
                    <div className="col-span-12 xl:col-span-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col shadow-sm">
                      <div className="mb-6">
                        <h3 className="text-headline-sm font-headline-sm text-slate-950 dark:text-white font-bold mb-1">Privacy Controls</h3>
                        <p className="text-body-md font-body-md text-slate-500">Configure safety granularity settings.</p>
                      </div>
                      <div className="flex-1 space-y-4">
                        {/* Toggle 1 */}
                        <div 
                          onClick={() => {
                            setStrictPrivacy(!strictPrivacy);
                            setToastMessage({ type: "success", text: `Strict Privacy Mode toggled: ${!strictPrivacy ? "ON" : "OFF"}` });
                          }}
                          className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer bg-slate-50 dark:bg-slate-950 ${strictPrivacy ? "border-teal-500 bg-teal-50/10" : "border-slate-200 dark:border-slate-800 hover:border-teal-500"}`}
                        >
                          <div className="flex gap-4">
                            <div className="mt-1">
                              <span className="material-symbols-outlined text-slate-550">visibility_off</span>
                            </div>
                            <div>
                              <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">Strict Privacy Mode</div>
                              <div className="text-body-md font-body-md text-slate-500 mt-1 max-w-sm">Mask presence values to safe status indicators. Hide room location.</div>
                            </div>
                          </div>
                          <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                            <input checked={strictPrivacy} type="checkbox" readOnly className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-slate-300 dark:border-slate-700 appearance-none cursor-pointer" />
                            <label className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${strictPrivacy ? "bg-teal-500" : "bg-slate-300 dark:bg-slate-800"}`}></label>
                          </div>
                        </div>

                        {/* Toggle 2 */}
                        <div 
                          onClick={() => {
                            setContextualVisibility(!contextualVisibility);
                            setToastMessage({ type: "success", text: `Contextual Visibility toggled: ${!contextualVisibility ? "ON" : "OFF"}` });
                          }}
                          className={`flex items-center justify-between p-4 border rounded-lg transition-colors cursor-pointer bg-slate-50 dark:bg-slate-950 ${contextualVisibility ? "border-teal-500 bg-teal-50/10" : "border-slate-200 dark:border-slate-800 hover:border-teal-500"}`}
                        >
                          <div className="flex gap-4">
                            <div className="mt-1">
                              <span className="material-symbols-outlined text-teal-605">visibility</span>
                            </div>
                            <div>
                              <div className="text-body-md font-body-md font-bold text-slate-900 dark:text-white">Contextual Visibility</div>
                              <div className="text-body-md font-body-md text-slate-500 mt-1 max-w-sm">View current room activity indicators and alerts logs.</div>
                            </div>
                          </div>
                          <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                            <input checked={contextualVisibility} type="checkbox" readOnly className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 border-slate-300 dark:border-slate-700 appearance-none cursor-pointer" />
                            <label className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer ${contextualVisibility ? "bg-teal-500" : "bg-slate-300 dark:bg-slate-800"}`}></label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {currentView === "analytics" && (
            <div className="space-y-6 text-left">
              {/* Page Header */}
              <div className="flex justify-between items-end mb-8">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Analytics Overview</h2>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">Deep dive into spatial utilization and response metrics.</p>
                </div>
                <div className="flex gap-stack-md text-label-caps font-label-caps text-slate-500 dark:text-slate-400">
                  <span className="bg-slate-100 dark:bg-slate-900 py-1.5 px-3 rounded-full flex items-center gap-1 border border-slate-200 dark:border-slate-800">
                    <span className="material-symbols-outlined text-[16px]">calendar_today</span>
                    Last 30 Days
                  </span>
                </div>
              </div>

              {/* Bento Grid Layout */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
                {/* Occupancy Over Time (Multi-line chart representation) */}
                <div className="col-span-1 md:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Occupancy Over Time</h3>
                    <button 
                      onClick={exportOccupancyTimeData}
                      className="text-teal-605 hover:underline text-label-caps font-label-caps font-bold cursor-pointer"
                    >
                      Export Data
                    </button>
                  </div>
                  {/* Chart representation */}
                  <div className="flex-1 w-full min-h-[300px] rounded-lg relative overflow-hidden flex items-end px-4 pb-4 gap-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850">
                    <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                      <path d="M0,80 Q10,70 20,60 T40,50 T60,30 T80,40 T100,20 L100,100 L0,100 Z" fill="rgba(13, 148, 136, 0.1)"></path>
                      <path d="M0,80 Q10,70 20,60 T40,50 T60,30 T80,40 T100,20" fill="none" stroke="#0d9488" strokeWidth="1.5"></path>
                    </svg>
                    <div className="absolute bottom-2 left-4 text-[10px] font-mono text-slate-400">08:00</div>
                    <div className="absolute bottom-2 right-4 text-[10px] font-mono text-slate-400">18:00</div>
                    <div className="absolute top-4 left-2 text-[10px] font-mono text-slate-400">100%</div>
                    <div className="absolute top-4 right-4 flex gap-4 bg-white dark:bg-slate-900 p-2 rounded text-[10px] font-bold uppercase tracking-wider border border-slate-200 dark:border-slate-800">
                      <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 bg-teal-600 rounded-full"></div>Zone A</div>
                      <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 bg-sky-500 rounded-full"></div>Zone B</div>
                    </div>
                  </div>
                </div>

                {/* Historical Activity Mix (Pie chart representation) */}
                <div className="col-span-1 md:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col">
                  <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold mb-6">Activity Mix</h3>
                  <div className="flex-1 flex flex-col items-center justify-center gap-6">
                    <div className="relative w-40 h-40 rounded-full border-[16px] border-slate-100 dark:border-slate-800 flex items-center justify-center" style={{ borderTopColor: "#0d9488", borderRightColor: "#0284c7" }}>
                      <div className="absolute flex flex-col items-center justify-center">
                        <span className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold">65%</span>
                        <span className="text-[10px] font-bold text-slate-450 uppercase">Sitting Stance</span>
                      </div>
                    </div>
                    <div className="w-full space-y-3 mt-4 text-xs font-semibold text-slate-650">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-teal-600 rounded-sm"></div>Sitting</div>
                        <span className="font-mono">65%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-sky-500 rounded-sm"></div>Walking</div>
                        <span className="font-mono">25%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-slate-350 rounded-sm"></div>Standing</div>
                        <span className="font-mono">10%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Underutilized Space Identification */}
                <div className="col-span-1 md:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm text-xs">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Underutilized Spaces (&lt;10%)</h3>
                    <span className="material-symbols-outlined text-slate-455">map</span>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded bg-white dark:bg-slate-900 flex items-center justify-center text-teal-650 dark:text-teal-400 border border-slate-100 dark:border-slate-850">
                          <span className="material-symbols-outlined">meeting_room</span>
                        </div>
                        <div>
                          <div className="font-bold text-slate-905 dark:text-white text-sm">Conference Rm 4B</div>
                          <div className="text-[10px] text-slate-455">North Wing</div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-red-500 font-mono font-bold text-sm">4.2%</span>
                        <span className="text-[9px] font-bold text-slate-455">Avg Util</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded bg-white dark:bg-slate-900 flex items-center justify-center text-teal-650 dark:text-teal-400 border border-slate-100 dark:border-slate-850">
                          <span className="material-symbols-outlined">chair</span>
                        </div>
                        <div>
                          <div className="font-bold text-slate-905 dark:text-white text-sm">Breakout Area C</div>
                          <div className="text-[10px] text-slate-455">East Corridor</div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-red-505 font-mono font-bold text-sm">7.8%</span>
                        <span className="text-[9px] font-bold text-slate-455">Avg Util</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Average Response Time */}
                <div className="col-span-1 md:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">Avg Alert Response Time</h3>
                    <div className="flex items-center gap-1 text-teal-650 dark:text-teal-400 text-xs font-bold uppercase">
                      <span className="material-symbols-outlined text-[16px]">trending_down</span>
                      -12% vs last month
                    </div>
                  </div>
                  <div className="flex items-end gap-4 h-[160px] w-full px-4 border-b border-slate-100 dark:border-slate-850 pb-4">
                    {/* Simulated bars */}
                    <div className="flex-1 flex flex-col justify-end items-center gap-2 group">
                      <div className="w-full bg-slate-100 dark:bg-slate-850 group-hover:bg-teal-200 transition-colors rounded-t h-[80%]"></div>
                      <span className="text-[9px] font-bold text-slate-400">Mon</span>
                    </div>
                    <div className="flex-1 flex flex-col justify-end items-center gap-2 group">
                      <div className="w-full bg-slate-100 dark:bg-slate-850 group-hover:bg-teal-200 transition-colors rounded-t h-[60%]"></div>
                      <span className="text-[9px] font-bold text-slate-400">Tue</span>
                    </div>
                    <div className="flex-1 flex flex-col justify-end items-center gap-2 group">
                      <div className="w-full bg-slate-100 dark:bg-slate-850 group-hover:bg-teal-200 transition-colors rounded-t h-[90%]"></div>
                      <span className="text-[9px] font-bold text-slate-400">Wed</span>
                    </div>
                    <div className="flex-1 flex flex-col justify-end items-center gap-2 group">
                      <div className="w-full bg-teal-600 rounded-t h-[40%]"></div>
                      <span className="text-[9px] font-bold text-teal-605">Thu</span>
                    </div>
                    <div className="flex-1 flex flex-col justify-end items-center gap-2 group">
                      <div className="w-full bg-slate-100 dark:bg-slate-850 group-hover:bg-teal-200 transition-colors rounded-t h-[50%]"></div>
                      <span className="text-[9px] font-bold text-slate-400">Fri</span>
                    </div>
                  </div>
                  <div className="mt-6 flex justify-between items-center text-xs">
                    <div>
                      <div className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold">3.4 min</div>
                      <div className="text-slate-455 text-[10px]">Weekly Average</div>
                    </div>
                    <button onClick={() => setCurrentView("alerts")} className="border border-teal-650 text-teal-650 px-4 py-2 rounded text-label-caps font-label-caps hover:bg-teal-50 font-bold uppercase transition-colors">
                      View Logs
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentView === "assets" && (
            <div className="space-y-6 text-left">
              {/* Facility Hierarchy view title */}
              <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Facility Config Manager</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400">Establish corporate and elder-care buildings, floors, and rooms configurations.</p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={expandAllBuildings}
                    className="px-4 py-2 border border-slate-200 dark:border-slate-800 rounded text-xs font-bold uppercase hover:bg-slate-50 dark:hover:bg-slate-850"
                  >
                    Expand All
                  </button>
                  <button 
                    onClick={() => {
                      if (organizations.length > 0) {
                        setNewBldOrgId(organizations[0].id);
                        setShowAddBuildingModal(true);
                      } else {
                        alert("Please create an organization first.");
                      }
                    }}
                    className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow"
                  >
                    Add Building
                  </button>
                </div>
              </div>

              {/* Physical layout hierarchy card list */}
              <div className="space-y-4">
                {buildings.map(bld => {
                  const bldFloors = floors.filter(f => f.building_id === bld.id);
                  const isExpanded = expandedBuildings[bld.id];
                  return (
                    <div key={bld.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                      <div 
                        onClick={() => toggleBuildingExpand(bld.id)}
                        className="p-4 bg-slate-50 dark:bg-slate-950 flex items-center justify-between cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-teal-600 dark:text-teal-400">corporate_fare</span>
                          <span className="font-bold text-slate-900 dark:text-white">{bld.name}</span>
                          <span className="text-xs text-slate-500">({bld.address})</span>
                        </div>
                        <span className="material-symbols-outlined text-slate-400">
                          {isExpanded ? "expand_less" : "expand_more"}
                        </span>
                      </div>
                      
                      {isExpanded && (
                        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4">
                          {bldFloors.map(flr => {
                            const flrRooms = rooms.filter(r => r.floor_id === flr.id);
                            return (
                              <div key={flr.id} className="pl-6 border-l-2 border-slate-200 dark:border-slate-800 py-2 text-xs">
                                <div className="font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                                  <span className="material-symbols-outlined text-[16px] text-teal-500">layers</span>
                                  Floor {flr.floor_number}
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                                  {flrRooms.map(rm => (
                                    <div key={rm.id} className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded">
                                      <div className="font-semibold text-slate-850 dark:text-white">{rm.name}</div>
                                      <div className="text-[10px] text-slate-500 uppercase mt-0.5">{rm.room_type}</div>
                                    </div>
                                  ))}
                                  <button 
                                    onClick={() => {
                                      setNewRmFlrId(flr.id);
                                      setShowAddRoomModal(true);
                                    }}
                                    className="p-3 border border-dashed border-slate-300 dark:border-slate-700 hover:border-teal-500 hover:text-teal-600 rounded flex items-center justify-center gap-1 font-bold text-slate-400"
                                  >
                                    <span className="material-symbols-outlined text-[16px]">add</span> Add Room
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                          <button 
                            onClick={() => {
                              setNewFlrBldId(bld.id);
                              setShowAddFloorModal(true);
                            }}
                            className="bg-slate-50 dark:bg-slate-950 text-slate-650 hover:bg-slate-100 dark:hover:bg-slate-900 px-4 py-2 border rounded font-semibold text-xs flex items-center gap-1"
                          >
                            <span className="material-symbols-outlined text-[16px]">add</span> Add Floor
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {currentView === "devices" && (
            <div className="space-y-6 text-left">
              {/* Header */}
              <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Sensing Device Management</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400">Manage hardware status, firmware revisions, and room bindings.</p>
                </div>
                <button 
                  onClick={() => {
                    if (rooms.length > 0) {
                      setNewDevRmId(rooms[0].id);
                      setShowAddDeviceModal(true);
                    } else {
                      alert("Please create a room layout first.");
                    }
                  }}
                  className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow"
                >
                  Register Node
                </button>
              </div>

              {/* Devices nodes list table */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 font-bold uppercase">
                        <th className="p-4">ESP Node MAC</th>
                        <th className="p-4">Assigned Room</th>
                        <th className="p-4">Firmware version</th>
                        <th className="p-4">Device status</th>
                        <th className="p-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {devices.map(dev => (
                        <tr key={dev.id} className="hover:bg-slate-50 dark:hover:bg-slate-850/40">
                          <td className="p-4 font-mono font-semibold text-slate-850 dark:text-white">{dev.mac_address}</td>
                          <td className="p-4 font-bold">{rooms.find(r => r.id === dev.room_id)?.name || "Unbound / Hub Node"}</td>
                          <td className="p-4 text-slate-500">{dev.firmware_version}</td>
                          <td className="p-4">
                            {dev.device_status === "ONLINE" ? (
                              <span className="bg-teal-50 dark:bg-teal-950/20 text-teal-650 px-2.5 py-0.5 rounded text-[10px] font-bold">ONLINE</span>
                            ) : (
                              <span className="bg-red-50 dark:bg-red-950/20 text-red-650 px-2.5 py-0.5 rounded text-[10px] font-bold">OFFLINE</span>
                            )}
                          </td>
                          <td className="p-4 text-right">
                            <button 
                              onClick={() => handleToggleDevice(dev.id)}
                              className="text-teal-650 hover:underline font-bold"
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
            </div>
          )}

          {currentView === "residents" && (
            <div className="space-y-6 text-left">
              {/* Header */}
              <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Resident Accounts</h2>
                  <p className="text-body-md text-slate-500 dark:text-slate-400">Auditing active monitored profiles and visibility logs.</p>
                </div>
                <button 
                  onClick={() => {
                    if (rooms.length > 0) {
                      setNewResRmId(rooms[0].id);
                      setShowAddResidentModal(true);
                    } else {
                      alert("Please create a room first.");
                    }
                  }}
                  className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow"
                >
                  Add Resident Record
                </button>
              </div>

              {/* Residents table list */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 font-bold uppercase">
                        <th className="p-4">Resident Subject</th>
                        <th className="p-4">Assigned Location</th>
                        <th className="p-4">Resident ID</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {residents.map(res => (
                        <tr key={res.id} className="hover:bg-slate-50 dark:hover:bg-slate-850/40">
                          <td className="p-4 font-bold text-slate-850 dark:text-white">{res.first_name} {res.last_name}</td>
                          <td className="p-4">{rooms.find(r => r.id === res.room_id)?.name || "No Bound Layout"}</td>
                          <td className="p-4 font-mono text-slate-450">{res.id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {currentView === "alerts" && (
            <div className="space-y-6 text-left">
              {/* Page Title */}
              <div className="flex justify-between items-end mb-4">
                <div>
                  <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">Alert Management</h2>
                  <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">Monitor, acknowledge, and resolve active environmental anomalies.</p>
                </div>
                <div className="text-body-md font-body-md text-slate-500 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
                  Live System Health: Nominal
                </div>
              </div>

              {/* Bento Grid Layout for Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                {/* Pending Alerts Table (Spans 2 columns) */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-sm">
                  <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-between items-center">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
                      <span className="material-symbols-outlined text-red-500">warning</span>
                      Pending Alerts
                    </h3>
                    <span className="bg-red-50 text-red-650 px-2.5 py-1 rounded text-label-caps font-label-caps font-bold">
                      {alerts.filter(a => a.status !== "resolved").length} Active
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead className="bg-slate-100 dark:bg-slate-850 text-slate-500 dark:text-slate-400 text-label-caps font-label-caps uppercase font-semibold">
                        <tr>
                          <th className="p-4">Location/Target</th>
                          <th className="p-4">Event Type</th>
                          <th className="p-4">Timestamp</th>
                          <th className="p-4">Severity</th>
                          <th className="p-4">Status</th>
                          <th className="p-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {alerts.filter(a => a.status !== "resolved").map(a => (
                          <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-850/50 transition-colors group">
                            <td className="p-4">
                              <div className="text-body-md font-body-md text-slate-900 dark:text-white font-bold">{rooms.find(r => r.id === a.room_id)?.name || "Room"}</div>
                              <div className="text-label-caps font-label-caps text-slate-500">
                                {residents.filter(r => r.room_id === a.room_id).map(r => `${r.first_name} ${r.last_name}`).join(", ") || "Subject"}
                              </div>
                            </td>
                            <td className="p-4 text-body-md font-body-md text-slate-805 dark:text-slate-200">{a.event_type.replace("_", " ")}</td>
                            <td className="p-4 text-data-mono font-data-mono text-slate-500">{new Date(a.created_at).toLocaleTimeString()}</td>
                            <td className="p-4">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                                a.event_type === "Fall_Detected" ? "bg-red-50 text-red-650" : "bg-amber-50 text-amber-650"
                              }`}>
                                {a.event_type === "Fall_Detected" ? "Critical" : "High"}
                              </span>
                            </td>
                            <td className="p-4">
                              <span className="inline-flex items-center gap-1 bg-slate-100 dark:bg-slate-800 text-slate-650 px-2 py-1 rounded text-[10px] font-bold border border-slate-200 dark:border-slate-700">
                                {a.status}
                              </span>
                            </td>
                            <td className="p-4 text-right">
                              <div className="flex justify-end gap-2">
                                {a.status === "new" && (
                                  <button onClick={() => handleAcknowledge(a.id)} className="text-label-caps font-label-caps font-bold px-3 py-1.5 rounded border border-teal-650 text-teal-650 hover:bg-teal-600 hover:text-white transition-colors">
                                    Acknowledge
                                  </button>
                                )}
                                <button onClick={() => setShowResolveModal(a.id)} className="text-label-caps font-label-caps font-bold px-3 py-1.5 rounded bg-teal-600 text-white hover:bg-teal-700 transition-colors">
                                  Resolve
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                        {alerts.filter(a => a.status !== "resolved").length === 0 && (
                          <tr>
                            <td colSpan="6" className="p-8 text-center text-slate-400 italic">No pending alerts. All clear.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Resolution History / Activity Stream */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-[500px] shadow-sm text-xs">
                  <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                    <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white flex items-center gap-2 font-bold">
                      <span className="material-symbols-outlined text-teal-605">check_circle</span>
                      Resolution History
                    </h3>
                  </div>
                  <div className="p-4 flex-1 overflow-y-auto space-y-4">
                    {alerts.filter(a => a.status === "resolved").map(a => (
                      <div key={a.id} className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 pb-4 text-left">
                        <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-800 border-2 border-white dark:border-slate-900"></div>
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                            {rooms.find(r => r.id === a.room_id)?.name || "Room"} Details
                          </h4>
                          <span className="text-data-mono font-data-mono text-slate-455">{new Date(a.created_at).toLocaleDateString()}</span>
                        </div>
                        <p className="text-slate-500 mb-2">Verified safe. Alert cleared.</p>
                      </div>
                    ))}
                    {alerts.filter(a => a.status === "resolved").length === 0 && (
                      <div className="p-8 text-center text-slate-400 italic">No resolved log database entries found.</div>
                    )}
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
                    {devices.map(dev => (
                      <option key={dev.id} value={dev.id}>
                        {dev.firmware_version} ({rooms.find(r => r.id === dev.room_id)?.name || "Room"})
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
                    <option value="Fall_Detected">Fall Detected (CSI Phase Spike)</option>
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
