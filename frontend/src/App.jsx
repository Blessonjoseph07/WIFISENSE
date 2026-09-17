import React, { useState, useEffect, useRef, useCallback } from "react";
import WifiModemVisualizer from "./WifiModemVisualizer";
import {
  APP_CONTEXTS,
  isViewAllowed,
  getDefaultView,
  getNavItemsForUser
} from "./navigation/navConfig";
import CareAppShell from "./shells/CareAppShell";
import SpaceAppShell from "./shells/SpaceAppShell";
import SystemAdminShell from "./shells/SystemAdminShell";
import FamilyPortalShell from "./shells/FamilyPortalShell";
import LandingSplash from "./shells/LandingSplash";
import ElderCareSplash from "./shells/ElderCareSplash";
import CorporateSplash from "./shells/CorporateSplash";
import LoadingScreen from "./components/LoadingScreen";
import SubcarrierWaveformStream from "./components/SubcarrierWaveformStream";
import CentralMonitoringView from "./views/CentralMonitoringView";
import OccupancyView from "./views/OccupancyView";
import CaregiverView from "./views/CaregiverView";
import OrgAdminView from "./views/OrgAdminView";
import SysAdminView from "./views/SysAdminView";
import CorporateView from "./views/CorporateView";
import FamilyPortalView from "./views/FamilyPortalView";
import AnalyticsView from "./views/AnalyticsView";
import FacilityAssetsView from "./views/FacilityAssetsView";
import DevicesView from "./views/DevicesView";
import ResidentsView from "./views/ResidentsView";
import AlertsView from "./views/AlertsView";
import UserProfileView from "./views/UserProfileView";
import EmergencyFallModal from "./components/EmergencyFallModal";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  // Loading & Pre-Entry Screen State
  const [isLoading, setIsLoading] = useState(true);
  const handleLoadingComplete = useCallback(() => {
    setIsLoading(false);
  }, []);

  // Authentication State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [showSplash, setShowSplash] = useState(!localStorage.getItem("token"));
  const [hasSeenElderSplash, setHasSeenElderSplash] = useState(false);
  const [hasSeenCorporateSplash, setHasSeenCorporateSplash] = useState(false);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("user")) || null);
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  const [appContext, setAppContext] = useState(localStorage.getItem("application_context") || "");
  const [isSystemAdmin, setIsSystemAdmin] = useState(localStorage.getItem("is_system_admin") === "true");
  
  // Navigation State & Browser History Management
  const [currentView, _setCurrentView] = useState(() => {
    const savedRole = localStorage.getItem("role") || "";
    const savedCtx = localStorage.getItem("application_context") || "";
    const savedSys = localStorage.getItem("is_system_admin") === "true";
    return savedRole ? getDefaultView(savedCtx, savedRole, savedSys) : "dashboard";
  }); 
  const navHistoryRef = useRef([]);

  const setCurrentView = (newView, pushHistory = true) => {
    if (token && role && !isViewAllowed(newView, appContext, role, isSystemAdmin)) {
      console.warn(`[RouteGuard] Blocked unauthorized view "${newView}" for role "${role}" in context "${appContext}".`);
      const safeDefault = getDefaultView(appContext, role, isSystemAdmin);
      _setCurrentView(safeDefault);
      setToastMessage({
        type: "error",
        text: `Access Denied: "${newView}" is not available in ${appContext === "CORPORATE" ? "WIFISENSE SPACE" : "WIFISENSE CARE"}.`
      });
      return;
    }
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
  const [activePersonnel, setActivePersonnel] = useState([]);
  const [healthRecords, setHealthRecords] = useState({});
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

  // Node Classification & Hardware Token Tracer states
  const [nodeFilter, setNodeFilter] = useState("ALL"); // "ALL", "CORPORATE", "ELDER_CARE", "TRACER"
  const [facilityFilter, setFacilityFilter] = useState("ALL"); // "ALL", "CORPORATE", "ELDER_CARE"
  const [occupancyRoomIndex, setOccupancyRoomIndex] = useState(0);
  const [selectedOccupancyRoomId, setSelectedOccupancyRoomId] = useState(null);
  const [occupancyStatusFilter, setOccupancyStatusFilter] = useState("ALL");
  const [occupancyClassFilter, setOccupancyClassFilter] = useState("ALL");
  const [occupancySearchQuery, setOccupancySearchQuery] = useState("");

  // Analytics Classified View states
  const [analyticsClassificationFilter, setAnalyticsClassificationFilter] = useState("ALL");
  const [analyticsTimeRange, setAnalyticsTimeRange] = useState("30D");

  const [faultReports, setFaultReports] = useState([]);
  const [showReportFaultModal, setShowReportFaultModal] = useState(false);
  const [selectedFaultDevice, setSelectedFaultDevice] = useState(null);
  const [faultIssueType, setFaultIssueType] = useState("FAULTY_CSI_VALUES");
  const [faultDescription, setFaultDescription] = useState("");
  const [faultSeverity, setFaultSeverity] = useState("HIGH");
  const [selectedInspectTicket, setSelectedInspectTicket] = useState(null);
  const [serviceActionNotes, setServiceActionNotes] = useState("");
  const [serviceActionStatus, setServiceActionStatus] = useState("DISPATCHED_SERVICE");

  // Form Input States
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regFirst, setRegFirst] = useState("");
  const [regLast, setRegLast] = useState("");
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


  const getHeaders = () => {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
  };

  // Sync authoritative user profile & application context from /auth/me on mount
  useEffect(() => {
    if (token) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => (res.ok ? res.json() : null))
        .then(data => {
          if (data) {
            setUser(data.user);
            setRole(data.role);
            setAppContext(data.application_context);
            setIsSystemAdmin(Boolean(data.is_system_admin));
            localStorage.setItem("user", JSON.stringify(data.user));
            localStorage.setItem("role", data.role);
            localStorage.setItem("application_context", data.application_context);
            localStorage.setItem("is_system_admin", String(Boolean(data.is_system_admin)));
          }
        })
        .catch(err => console.error("Sync me error:", err));
    }
  }, [token]);

  // Keep view aligned with authorized bounds
  useEffect(() => {
    if (token && role && !isViewAllowed(currentView, appContext, role, isSystemAdmin)) {
      const safeDefault = getDefaultView(appContext, role, isSystemAdmin);
      _setCurrentView(safeDefault);
    }
  }, [currentView, appContext, role, isSystemAdmin, token]);

  // ============================================================================
  // LOAD DATA & AUTO FILTERING
  // ============================================================================
  const fetchAllData = async () => {
    if (!token) return;
    try {
      const headers = getHeaders();

      // If family member, fetch their resident's status
      if (role === "family_member") {
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

      // If elder-care admin or system admin, fetch pending access requests
      if ((isSystemAdmin || appContext === "ELDER_CARE") && (role === "system_admin" || role === "organization_admin")) {
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

      const faultRes = await fetch(`${API_BASE}/devices/fault-tracer`, { headers });
      if (faultRes.ok) setFaultReports(await faultRes.json());

      if (isSystemAdmin || appContext === "SYSTEM" || role === "system_admin") {
        const persRes = await fetch(`${API_BASE}/users/personnel`, { headers });
        if (persRes.ok) {
          setActivePersonnel(await persRes.json());
        }
      }


      // Only fetch residents for elder care or system admin (zero leak to corporate)
      if (appContext !== "CORPORATE" && role !== "corporate_staff") {
        const resRes = await fetch(`${API_BASE}/residents`, { headers });
        if (resRes.ok) {
          const fetchedResidents = await resRes.json();
          setResidents(fetchedResidents);
          
          // Fetch health records
          const records = {};
          for (const res of fetchedResidents) {
            try {
              const hRes = await fetch(`${API_BASE}/residents/${res.id}/health`, { headers });
              if (hRes.ok) {
                records[res.id] = await hRes.json();
              }
            } catch(e) {}
          }
          setHealthRecords(records);
        }
      }

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
  }, [token, appContext, role]);

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
      localStorage.setItem("application_context", data.application_context);
      localStorage.setItem("is_system_admin", String(Boolean(data.is_system_admin)));
      
      setToken(data.access_token);
      setUser(data.user);
      setRole(data.role);
      setAppContext(data.application_context);
      setIsSystemAdmin(Boolean(data.is_system_admin));
      setHasSeenElderSplash(false);
      setHasSeenCorporateSplash(false);
      
      const safeStart = getDefaultView(data.application_context, data.role, data.is_system_admin);
      _setCurrentView(safeStart);
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
          last_name: regLast
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
    localStorage.removeItem("application_context");
    localStorage.removeItem("is_system_admin");
    setToken("");
    setUser(null);
    setRole("");
    setAppContext("");
    setIsSystemAdmin(false);
    setHasSeenElderSplash(false);
    setHasSeenCorporateSplash(false);
    _setCurrentView("dashboard");
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
  // HARDWARE TOKEN & FAULT TRACER HANDLERS
  // ============================================================================
  const handleResetDeviceToken = async (deviceId) => {
    if (!confirm("Are you sure you want to regenerate and reset the hardware pairing token for this ESP node?")) return;
    try {
      const res = await fetch(`${API_BASE}/devices/${deviceId}/reset-token`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({})
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to reset token.");
      }
      const data = await res.json();
      fetchAllData();
      setToastMessage({ type: "success", text: `Token regenerated: ${data.hardware_token}` });
    } catch (err) {
      alert(err.message);
    }
  };

  const handleReportFault = async (e) => {
    e.preventDefault();
    if (!selectedFaultDevice) return;
    try {
      const res = await fetch(`${API_BASE}/devices/${selectedFaultDevice.id}/report-fault`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          issue_type: faultIssueType,
          description: faultDescription,
          severity: faultSeverity
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit fault report.");
      }
      const data = await res.json();
      setShowReportFaultModal(false);
      setFaultDescription("");
      setSelectedFaultDevice(null);
      fetchAllData();
      setToastMessage({ type: "success", text: `Token tracer query ${data.tracer_token} submitted to Global Admin Desk!` });
    } catch (err) {
      alert(err.message);
    }
  };

  const handleServiceTicket = async (ticketId, statusVal, notes) => {
    try {
      const res = await fetch(`${API_BASE}/devices/fault-tracer/${ticketId}/service`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify({
          status: statusVal,
          service_notes: notes || "Serviced by Global Super Admin Desk"
        })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to service ticket.");
      }
      setSelectedInspectTicket(null);
      setServiceActionNotes("");
      fetchAllData();
      setToastMessage({ type: "success", text: `Tracer ticket status updated to ${statusVal}!` });
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
    if (showSplash) {
      return (
        <div className="relative">
          <LandingSplash onGetStarted={() => setShowSplash(false)} />
          {isLoading && <LoadingScreen onComplete={handleLoadingComplete} />}
        </div>
      );
    }
    return (
      <div className="relative">
        {isLoading && <LoadingScreen onComplete={handleLoadingComplete} />}
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
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none font-medium"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                  >
                    <option value="caregiver">Caregiver (Elder-Care Home)</option>
                    <option value="family_member">Family Member (Elder-Care)</option>
                    <option value="facility_manager">Facility Manager</option>
                    <option value="corporate_staff">Corporate Staff (Smart Workplace)</option>
                    <option value="organization_admin">Organization Administrator</option>
                  </select>
                </div>
                <div className="text-left">
                  <label className="block font-label-caps text-label-caps text-slate-500 dark:text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    className="block w-full px-3 py-2 border border-slate-200 dark:border-slate-800 rounded bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-white focus:outline-none"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    minLength={8}
                    required
                  />
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Minimum 8 characters. New accounts start with family / emergency-contact access; an administrator assigns staff roles.
                  </p>
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
      </div>
    );
  }

  // ============================================================================
  // WORKSPACE VIEW (AUTHENTICATED SHELLS)
  // ============================================================================
  const renderAppShell = (content) => {
    const commonProps = {
      user,
      role,
      appContext,
      isSystemAdmin,
      currentView,
      setCurrentView,
      alerts,
      handleLogout,
      triggerEmergencyProtocol,
      organizations,
      devices,
      setSimDeviceId,
      setShowSimulateDrawer,
      darkMode,
      setDarkMode,
      showProfileMenu,
      setShowProfileMenu,
      fileInputRef,
      handlePhotoUpload,
      API_BASE
    };

    if (role === "family_member") {
      return (
        <FamilyPortalShell
          user={user}
          role={role}
          familyStatus={familyStatus}
          handleLogout={handleLogout}
          triggerEmergencyProtocol={triggerEmergencyProtocol}
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          showProfileMenu={showProfileMenu}
          setShowProfileMenu={setShowProfileMenu}
          fileInputRef={fileInputRef}
          handlePhotoUpload={handlePhotoUpload}
          API_BASE={API_BASE}
        >
          {content}
        </FamilyPortalShell>
      );
    }

    if (isSystemAdmin || appContext === APP_CONTEXTS.SYSTEM || role === "system_admin") {
      return (
        <SystemAdminShell {...commonProps}>
          {content}
        </SystemAdminShell>
      );
    }

    if (appContext === APP_CONTEXTS.SPACE) {
      return (
        <SpaceAppShell {...commonProps}>
          {content}
        </SpaceAppShell>
      );
    }

    return (
      <CareAppShell {...commonProps}>
        {content}
      </CareAppShell>
    );
  };

  const themeClass = appContext === "CORPORATE" ? "theme-corporate" : "theme-elder-care";

  if (appContext === "ELDER_CARE" && !hasSeenElderSplash) {
    return <ElderCareSplash onContinue={() => setHasSeenElderSplash(true)} />;
  }

  if (appContext === "CORPORATE" && !hasSeenCorporateSplash) {
    return (
      <CorporateSplash 
        user={user} 
        onContinue={() => setHasSeenCorporateSplash(true)} 
      />
    );
  }

  return (
    <div className={`bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 min-h-screen w-full flex flex-col transition-all duration-300 ${themeClass} relative`}>
      {isLoading && <LoadingScreen onComplete={handleLoadingComplete} />}
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 transition-all transform translate-y-0 ${
          toastMessage.type === "error" ? "bg-red-600 text-white" : "bg-teal-600 text-white"
        }`}>
          <span className="material-symbols-outlined">{toastMessage.type === "error" ? "error" : "check_circle"}</span>
          <span className="text-xs font-bold">{toastMessage.text}</span>
        </div>
      )}

      {renderAppShell(
        <div className="space-y-6 w-full">
          {/* Global Fall Alert Banner */}
          {activeFallAlert && role !== "family_member" && (
            <div className="bg-red-50 border border-red-500 text-red-700 dark:bg-red-950/20 dark:text-red-400 p-4 rounded-xl flex items-center justify-between pulse-animation relative z-25">
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
                  className="px-3 py-1.5 border border-red-500 text-red-600 dark:text-red-400 rounded text-xs font-bold uppercase hover:bg-red-50 dark:hover:bg-red-950/40 cursor-pointer"
                >
                  Acknowledge
                </button>
                <button
                  onClick={() => setShowResolveModal(activeFallAlert.id)}
                  className="px-3 py-1.5 bg-red-600 text-white rounded text-xs font-bold uppercase hover:opacity-90 shadow cursor-pointer"
                >
                  Resolve
                </button>
              </div>
            </div>
          )}

          {/* Access Denied Guard if currentView is unauthorized for user's context */}
          {!isViewAllowed(currentView, appContext, role, isSystemAdmin) && (
            <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-2xl p-8 text-center max-w-xl mx-auto shadow-sm my-12">
              <div className="w-16 h-16 bg-red-50 dark:bg-red-950/30 rounded-full flex items-center justify-center mb-4 mx-auto text-red-600">
                <span className="material-symbols-outlined text-3xl">lock</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">View Not Available</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                The requested view <code className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-red-600 dark:text-red-400">{currentView}</code> is not accessible in {appContext === APP_CONTEXTS.SPACE ? "WIFISENSE SPACE" : "WIFISENSE CARE"} for role <span className="font-semibold uppercase">{role}</span>.
              </p>
              <button
                onClick={() => setCurrentView(getDefaultView(appContext, role, isSystemAdmin))}
                className="bg-teal-600 hover:bg-teal-700 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase transition-colors cursor-pointer"
              >
                Return to Authorized Dashboard
              </button>
            </div>
          )}
          
          {/* ============================================================================
          {/* ============================================================================
            1. MONITORING DASHBOARD (CENTRAL MONITORING BENTO)
          ============================================================================ */}
          {currentView === "dashboard" && isViewAllowed("dashboard", appContext, role, isSystemAdmin) && (
            <CentralMonitoringView
              occupancySummary={occupancySummary}
              residents={residents}
              devices={devices}
              appContext={appContext}
              activeTelemetryActivity={activeTelemetryActivity}
            />
          )}

          {/* ============================================================================
            2. OCCUPANCY & ENVIRONMENTAL RADAR
          ============================================================================ */}
          {currentView === "occupancy" && isViewAllowed("occupancy", appContext, role, isSystemAdmin) && (
            <OccupancyView
              appContext={appContext}
              role={role}
              isSystemAdmin={isSystemAdmin}
              rooms={rooms}
              floors={floors}
              buildings={buildings}
              organizations={organizations}
              residents={residents}
              devices={devices}
              alerts={alerts}
              occupancySummary={occupancySummary}
              healthRecords={healthRecords}
              facilityFilter={facilityFilter}
              setFacilityFilter={setFacilityFilter}
              occupancySearchQuery={occupancySearchQuery}
              setOccupancySearchQuery={setOccupancySearchQuery}
              occupancyStatusFilter={occupancyStatusFilter}
              setOccupancyStatusFilter={setOccupancyStatusFilter}
              occupancyClassFilter={occupancyClassFilter}
              setOccupancyClassFilter={setOccupancyClassFilter}
              selectedOccupancyRoomId={selectedOccupancyRoomId}
              setSelectedOccupancyRoomId={setSelectedOccupancyRoomId}
              handleAcknowledge={handleAcknowledge}
              setShowResolveModal={setShowResolveModal}
            />
          )}

          {/* ============================================================================
            3. CAREGIVER DASHBOARD (ELDER-CARE ESCORT MATRIX)
          ============================================================================ */}
          {currentView === "caregiver" && isViewAllowed("caregiver", appContext, role, isSystemAdmin) && (
            <CaregiverView
              activeFallAlert={activeFallAlert}
              handleAcknowledge={handleAcknowledge}
              setShowResolveModal={setShowResolveModal}
              alerts={alerts}
              residents={residents}
              healthRecords={healthRecords}
              rooms={rooms}
              occupancySummary={occupancySummary}
              setCurrentView={setCurrentView}
            />
          )}

          {/* ============================================================================
            4. ORG ADMIN DASHBOARD
          ============================================================================ */}
          {currentView === "orgadmin" && isViewAllowed("orgadmin", appContext, role, isSystemAdmin) && (
            <OrgAdminView
              setShowAddOrgModal={setShowAddOrgModal}
              organizations={organizations}
              accessRequests={accessRequests}
              residents={residents}
              handleReviewRequest={handleReviewRequest}
            />
          )}

          {/* ============================================================================
            5. SYSTEM ADMIN DASHBOARD (USER & ROLES AUDITING)
          ============================================================================ */}
          {currentView === "sysadmin" && isViewAllowed("sysadmin", appContext, role, isSystemAdmin) && (
            <SysAdminView
              setIsRegistering={setIsRegistering}
              exportPersonnelCSV={exportPersonnelCSV}
              activePersonnel={activePersonnel}
              alerts={alerts}
              setCurrentView={setCurrentView}
              handleAcknowledge={handleAcknowledge}
              setShowResolveModal={setShowResolveModal}
            />
          )}

          {/* ============================================================================
            6. CORPORATE VIEW
          ============================================================================ */}
          {currentView === "corporate" && isViewAllowed("corporate", appContext, role, isSystemAdmin) && (
            <CorporateView
              exportCorporateAnalytics={exportCorporateAnalytics}
              occupancySummary={occupancySummary}
              generateRepurposingReport={generateRepurposingReport}
              authToken={token}
              setToastMessage={setToastMessage}
              fetchAllData={fetchAllData}
            />
          )}

          {/* ============================================================================
            7. FAMILY PORTAL VIEW
          ============================================================================ */}
          {currentView === "family" && isViewAllowed("family", appContext, role, isSystemAdmin) && (
            <FamilyPortalView
              role={role}
              familyStatus={familyStatus}
              setFamilyStatus={setFamilyStatus}
              selectedRequestResidentId={selectedRequestResidentId}
              setSelectedRequestResidentId={setSelectedRequestResidentId}
              residents={residents}
              submitLinkRequest={submitLinkRequest}
              setToastMessage={setToastMessage}
              strictPrivacy={strictPrivacy}
              setStrictPrivacy={setStrictPrivacy}
              contextualVisibility={contextualVisibility}
              setContextualVisibility={setContextualVisibility}
              authToken={token}
            />
          )}

          {/* ============================================================================
            8. ADVANCED ANALYTICS
          ============================================================================ */}
          {currentView === "analytics" && isViewAllowed("analytics", appContext, role, isSystemAdmin) && (
            <AnalyticsView
              appContext={appContext}
              role={role}
              isSystemAdmin={isSystemAdmin}
              occupancySummary={occupancySummary}
              analyticsClassificationFilter={analyticsClassificationFilter}
              setAnalyticsClassificationFilter={setAnalyticsClassificationFilter}
              analyticsTimeRange={analyticsTimeRange}
              setAnalyticsTimeRange={setAnalyticsTimeRange}
              exportOccupancyTimeData={exportOccupancyTimeData}
              setCurrentView={setCurrentView}
            />
          )}

          {/* ============================================================================
            9. PHYSICAL FACILITY HIERARCHY
          ============================================================================ */}
          {currentView === "assets" && isViewAllowed("assets", appContext, role, isSystemAdmin) && (
            <FacilityAssetsView
              expandAllBuildings={expandAllBuildings}
              organizations={organizations}
              setNewBldOrgId={setNewBldOrgId}
              setShowAddBuildingModal={setShowAddBuildingModal}
              isSystemAdmin={isSystemAdmin}
              facilityFilter={facilityFilter}
              setFacilityFilter={setFacilityFilter}
              buildings={buildings}
              floors={floors}
              rooms={rooms}
              expandedBuildings={expandedBuildings}
              toggleBuildingExpand={toggleBuildingExpand}
              setNewRmFlrId={setNewRmFlrId}
              setShowAddRoomModal={setShowAddRoomModal}
              setNewFlrBldId={setNewFlrBldId}
              setShowAddFloorModal={setShowAddFloorModal}
            />
          )}

          {/* ============================================================================
            10. HARDWARE TELEMETRY & SENSING NODES
          ============================================================================ */}
          {currentView === "devices" && isViewAllowed("devices", appContext, role, isSystemAdmin) && (
            <DevicesView
              devices={devices}
              rooms={rooms}
              faultReports={faultReports}
              nodeFilter={nodeFilter}
              setNodeFilter={setNodeFilter}
              setNewDevRmId={setNewDevRmId}
              setShowAddDeviceModal={setShowAddDeviceModal}
              setSelectedFaultDevice={setSelectedFaultDevice}
              setShowReportFaultModal={setShowReportFaultModal}
              handleServiceTicket={handleServiceTicket}
              appContext={appContext}
              isSystemAdmin={isSystemAdmin}
              role={role}
            />

          )}

          {/* ============================================================================
            11. RESIDENTS / CARE-RECIPENT PROFILES
          ============================================================================ */}
          {currentView === "residents" && isViewAllowed("residents", appContext, role, isSystemAdmin) && (
            <ResidentsView
              residents={residents}
              rooms={rooms}
              accessRequests={accessRequests}
              setNewResRmId={setNewResRmId}
              setShowAddResidentModal={setShowAddResidentModal}
              triggerEmergencyProtocol={triggerEmergencyProtocol}
              setCurrentView={setCurrentView}
            />
          )}

          {/* ============================================================================
            12. ALERTS & INCIDENT ESCALATIONS
          ============================================================================ */}
          {currentView === "alerts" && isViewAllowed("alerts", appContext, role, isSystemAdmin) && (
            <AlertsView
              alerts={alerts}
              rooms={rooms}
              handleAcknowledge={handleAcknowledge}
              setShowResolveModal={setShowResolveModal}
              authToken={token}
              API_BASE={API_BASE}
              role={role}
              isSystemAdmin={isSystemAdmin}
              appContext={appContext}
            />
          )}

          {/* ============================================================================
            13. USER PROFILE
          ============================================================================ */}
          {currentView === "profile" && isViewAllowed("profile", appContext, role, isSystemAdmin) && (
            <UserProfileView
              user={user}
              role={role}
              API_BASE={API_BASE}
              fileInputRef={fileInputRef}
            />
          )}
        </div>
      )}

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
            <h3 className="font-bold text-headline-sm mb-2 text-red-600 font-semibold">Resolve Incident Alert</h3>
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

      {/* Real-time CSI Emergency Fall Protocol Modal (Auto-pops for Global Admin, Elder Caregiver, Org Admin & Facility Manager) */}
      {token &&
        (isSystemAdmin ||
          role === "system_admin" ||
          (appContext === "ELDER_CARE" &&
            (role === "caregiver" || role === "organization_admin" || role === "facility_manager"))) && (
          <EmergencyFallModal
            authToken={token}
            role={role}
            appContext={appContext}
            isSystemAdmin={isSystemAdmin}
            onActionComplete={fetchAllData}
          />
        )}

      {/* 8. Emergency Protocol Animated Modal */}
      {showEmergencyModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border-2 border-red-500 rounded-2xl p-6 sm:p-8 max-w-lg w-full text-center shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-2 bg-red-600 animate-pulse"></div>
            <span className="material-symbols-outlined text-red-600 text-6xl animate-bounce mb-3 block" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
            <h3 className="font-bold text-2xl text-red-600 dark:text-red-400 mb-2 uppercase tracking-wide">Emergency Protocol Activated</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm mb-5 max-w-sm mx-auto">
              Warning vectors broadcasted to local auxiliary responders. Dispatching caregivers to monitored facilities.
            </p>

            {/* Registered Family Emergency Contacts Section */}
            <div className="bg-red-50/60 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-xl p-4 mb-6 text-left">
              <div className="flex items-center justify-between mb-2.5">
                <span className="font-bold text-red-900 dark:text-red-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px] text-red-600">contact_phone</span>
                  Family Emergency Contacts on Call
                </span>
                <span className="bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full animate-pulse">
                  SMS / Call Queued
                </span>
              </div>
              <div className="space-y-2 text-xs divide-y divide-red-200/60 dark:divide-red-900/40">
                <div className="flex justify-between items-center pt-1.5">
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">John Smith <span className="text-slate-500 font-normal">(Son of Annamma Joseph)</span></div>
                    <div className="text-slate-600 dark:text-slate-400 font-mono text-[11px]">+1 (555) 234-5678 • john@wifisense.com</div>
                  </div>
                  <a href="tel:5552345678" className="px-2.5 py-1 bg-white dark:bg-slate-800 text-red-600 dark:text-red-400 border border-red-300 dark:border-red-800 rounded-lg font-bold text-[11px] hover:bg-red-50 flex items-center gap-1 shadow-xs">
                    <span className="material-symbols-outlined text-[13px]">call</span>
                    Call
                  </a>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">Susan Varghese <span className="text-slate-500 font-normal">(Daughter of Devassy Varghese)</span></div>
                    <div className="text-slate-600 dark:text-slate-400 font-mono text-[11px]">+1 (555) 876-5432 • susan@wifisense.com</div>
                  </div>
                  <a href="tel:5558765432" className="px-2.5 py-1 bg-white dark:bg-slate-800 text-red-600 dark:text-red-400 border border-red-300 dark:border-red-800 rounded-lg font-bold text-[11px] hover:bg-red-50 flex items-center gap-1 shadow-xs">
                    <span className="material-symbols-outlined text-[13px]">call</span>
                    Call
                  </a>
                </div>
              </div>
            </div>

            {/* Action Buttons with high-contrast text */}
            <div className="flex justify-center gap-4">
              <button
                type="button"
                onClick={() => setShowEmergencyModal(false)}
                className="px-6 py-2.5 border-2 border-slate-300 dark:border-slate-700 rounded-full text-sm font-bold uppercase text-slate-700 dark:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                Stand Down
              </button>
              <button 
                type="button"
                onClick={() => {
                  setShowEmergencyModal(false);
                  setToastMessage({ type: "success", text: "Auxiliary backup & family contacts dispatched." });
                }}
                className="px-6 py-2.5 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white rounded-full text-sm font-bold uppercase transition-all shadow-lg cursor-pointer flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">emergency</span>
                Confirm Dispatch
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 9. Report ESP Node Fault / Token Tracer Modal */}
      {showReportFaultModal && selectedFaultDevice && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl text-left">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="p-2 bg-amber-50 dark:bg-amber-950/50 text-amber-600 rounded-lg material-symbols-outlined text-[20px]">
                  report_problem
                </span>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">Report ESP Node Fault</h3>
                  <p className="text-[11px] text-slate-500">Submit hardware tracer query to Global Admin Desk</p>
                </div>
              </div>
              <button 
                onClick={() => {
                  setShowReportFaultModal(false);
                  setSelectedFaultDevice(null);
                }}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl mb-4 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Node MAC:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">{selectedFaultDevice.mac_address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Hardware Token:</span>
                <span className="font-mono font-bold text-teal-600 dark:text-teal-400">{selectedFaultDevice.hardware_token || "TK-ESP32-GEN01"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Domain:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {selectedFaultDevice.organization_name || (selectedFaultDevice.organization_type === "CORPORATE" ? "Amal Jyothi College of Engineering" : "St. Peter's Elder Care Home")}
                </span>
              </div>
            </div>

            <form onSubmit={handleReportFault} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1.5">Issue Category</label>
                <select
                  value={faultIssueType}
                  onChange={(e) => setFaultIssueType(e.target.value)}
                  className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 bg-slate-50 dark:bg-slate-800 dark:text-white font-medium focus:ring-2 focus:ring-amber-500 outline-hidden"
                >
                  <option value="FAULTY_CSI_VALUES">Faulty CSI Values (Erratic Amplitude/Phase Noise)</option>
                  <option value="PHYSICAL_DAMAGE">Physical Damage (Antenna Broken / Enclosure Damaged)</option>
                  <option value="ELECTRONIC_FAILURE">Electronic / Circuit Problem (Power Surge / Desync)</option>
                  <option value="CONNECTIVITY_DROP">Connectivity Drop (Wi-Fi CSI Telemetry Disconnected)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1.5">Impact Severity</label>
                <div className="grid grid-cols-4 gap-2">
                  {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(lvl => (
                    <button
                      type="button"
                      key={lvl}
                      onClick={() => setFaultSeverity(lvl)}
                      className={`py-1.5 px-2 rounded-lg font-bold text-center text-[10px] cursor-pointer transition-all ${
                        faultSeverity === lvl
                          ? lvl === "CRITICAL" ? "bg-red-600 text-white shadow-xs" :
                            lvl === "HIGH" ? "bg-amber-600 text-white shadow-xs" :
                            lvl === "MEDIUM" ? "bg-blue-600 text-white shadow-xs" : "bg-slate-700 text-white shadow-xs"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1.5">Fault Description &amp; Electronic Diagnostics</label>
                <textarea
                  value={faultDescription}
                  onChange={(e) => setFaultDescription(e.target.value)}
                  placeholder="Describe the faulty values, hardware symptoms, or electronic issues observed..."
                  required
                  rows={3}
                  className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 bg-slate-50 dark:bg-slate-800 dark:text-white font-medium focus:ring-2 focus:ring-amber-500 outline-hidden resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setShowReportFaultModal(false);
                    setSelectedFaultDevice(null);
                  }}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-bold transition-colors cursor-pointer shadow-sm flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">send</span>
                  Dispatch Tracer Query
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 10. Global Super Admin Service & Inspection Modal */}
      {selectedInspectTicket && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl text-left">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="p-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-lg material-symbols-outlined text-[20px]">
                  handyman
                </span>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">Global Admin Service Desk</h3>
                  <p className="text-[11px] text-slate-500">Inspect ticket &amp; dispatch service to ESP sensor</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedInspectTicket(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl mb-4 text-xs space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-semibold">Tracer Ticket Token:</span>
                <span className="font-mono font-bold text-amber-600 dark:text-amber-400 text-sm">{selectedInspectTicket.tracer_token}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Target Node MAC:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">{selectedInspectTicket.mac_address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Classification Domain:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  {selectedInspectTicket.organization_type === "CORPORATE" ? "🏢 Corporate (AJCE)" : "🏥 Old Age Care (St. Peter's)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-semibold">Location / Room:</span>
                <span className="font-bold text-slate-900 dark:text-white">{selectedInspectTicket.room_name}</span>
              </div>
              <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 font-semibold block mb-0.5">Reported Issue:</span>
                <p className="text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-900 p-2 rounded border border-slate-200 dark:border-slate-700">
                  {selectedInspectTicket.description}
                </p>
              </div>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1.5">Action Status</label>
                <select
                  value={serviceActionStatus}
                  onChange={(e) => setServiceActionStatus(e.target.value)}
                  className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 bg-slate-50 dark:bg-slate-800 dark:text-white font-medium focus:ring-2 focus:ring-teal-500 outline-hidden"
                >
                  <option value="UNDER_INSPECTION">Under Inspection (Reviewing CSI Waveform Logs)</option>
                  <option value="DISPATCHED_SERVICE">Dispatched Service (Technician En Route to Facility)</option>
                  <option value="REPLACED_RESOLVED">Replaced &amp; Resolved (Node Restored ONLINE with New Token)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1.5">Service Notes &amp; Dispatch Resolution</label>
                <textarea
                  value={serviceActionNotes}
                  onChange={(e) => setServiceActionNotes(e.target.value)}
                  placeholder="e.g. Technician dispatched with new ESP32-S3 receiver module. Repaired antenna and verified CSI subcarrier signals."
                  rows={3}
                  className="w-full border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 bg-slate-50 dark:bg-slate-800 dark:text-white font-medium focus:ring-2 focus:ring-teal-500 outline-hidden resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedInspectTicket(null)}
                  className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleServiceTicket(selectedInspectTicket.id, serviceActionStatus, serviceActionNotes)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 dark:text-slate-900 text-white rounded-lg font-bold transition-colors cursor-pointer shadow-sm flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">verified</span>
                  Confirm Service Action
                </button>
              </div>
            </div>
          </div>


        </div>
      )}
    </div>
  );
}

