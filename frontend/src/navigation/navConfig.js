// Nav configuration and authoritative role/context gating for WIFISENSE

export const BACKEND_ROLES = [
  "system_admin",
  "organization_admin",
  "facility_manager",
  "caregiver",
  "corporate_staff",
  "emergency_contact"
];

export const APP_CONTEXTS = {
  CARE: "ELDER_CARE",
  SPACE: "CORPORATE",
  SYSTEM: "SYSTEM"
};

export const VIEW_DEFINITIONS = {
  dashboard: {
    id: "dashboard",
    label: "Monitoring Dashboard",
    icon: "sensors",
    description: "Live sensor feeds and spatial telemetry"
  },
  caregiver: {
    id: "caregiver",
    label: "Caregiver Dashboard",
    icon: "medical_services",
    description: "Resident vitals, shift logs, and fall alerts"
  },
  residents: {
    id: "residents",
    label: "Resident Directory",
    icon: "person_alert",
    description: "Resident profiles, care plans, and room assignments"
  },
  corporate: {
    id: "corporate",
    label: "Corporate Workplace",
    icon: "domain",
    description: "Desk occupancy, meeting rooms, and office traffic"
  },
  occupancy: {
    id: "occupancy",
    label: "Room Occupancy View",
    icon: "meeting_room",
    description: "Real-time occupancy status across all rooms"
  },
  assets: {
    id: "assets",
    label: "Facility & Assets",
    icon: "account_tree",
    description: "Buildings, floors, and room infrastructure management"
  },
  devices: {
    id: "devices",
    label: "Sensing Devices",
    icon: "router",
    description: "Wi-Fi sensing node provisioning and status"
  },
  alerts: {
    id: "alerts",
    label: "Alerts & Incidents",
    icon: "history",
    hasBadge: true,
    description: "Active fall alarms and critical event queue"
  },
  analytics: {
    id: "analytics",
    label: "Analytics & Telemetry",
    icon: "analytics",
    description: "CSI telemetry trends and occupancy heatmaps"
  },
  orgadmin: {
    id: "orgadmin",
    label: "Organization Admin",
    icon: "settings_applications",
    description: "Organization policies, link requests, and user administration"
  },
  sysadmin: {
    id: "sysadmin",
    label: "System Admin Console",
    icon: "admin_panel_settings",
    description: "Multi-tenant oversight, global health, and system diagnostics"
  },
  family: {
    id: "family",
    label: "Family Member Portal",
    icon: "group",
    description: "Elder-care resident safety updates and privacy sharing"
  }
};

// Configuration per application context and role
const MATRIX = {
  [APP_CONTEXTS.CARE]: {
    caregiver: {
      allowedViews: ["dashboard", "caregiver", "alerts", "residents", "occupancy", "family"],
      defaultView: "dashboard",
      badgeText: "CARE • Caregiver",
      theme: "care"
    },
    facility_manager: {
      allowedViews: ["assets", "devices", "dashboard", "alerts", "occupancy", "analytics", "family"],
      defaultView: "assets",
      badgeText: "CARE • Facility Manager",
      theme: "care"
    },
    organization_admin: {
      allowedViews: ["orgadmin", "assets", "devices", "alerts", "analytics", "residents", "family"],
      defaultView: "orgadmin",
      badgeText: "CARE • Org Administrator",
      theme: "care"
    },
    emergency_contact: {
      allowedViews: ["family"],
      defaultView: "family",
      badgeText: "CARE • Family Portal",
      theme: "care"
    }
  },
  [APP_CONTEXTS.SPACE]: {
    corporate_staff: {
      allowedViews: ["corporate", "occupancy", "analytics"],
      defaultView: "corporate",
      badgeText: "SPACE • Staff",
      theme: "space"
    },
    facility_manager: {
      allowedViews: ["assets", "devices", "occupancy", "analytics", "alerts"],
      defaultView: "assets",
      badgeText: "SPACE • Facility Manager",
      theme: "space"
    },
    organization_admin: {
      allowedViews: ["orgadmin", "assets", "devices", "occupancy", "analytics", "alerts"],
      defaultView: "orgadmin",
      badgeText: "SPACE • Org Administrator",
      theme: "space"
    }
  },
  [APP_CONTEXTS.SYSTEM]: {
    system_admin: {
      allowedViews: ["sysadmin", "orgadmin", "assets", "devices", "alerts", "analytics", "occupancy", "dashboard"],
      defaultView: "sysadmin",
      badgeText: "SYSTEM CONSOLE",
      theme: "system"
    }
  }
};

// Development/runtime assertion to ensure all mapped roles are valid
Object.values(MATRIX).forEach((contextRoles) => {
  Object.keys(contextRoles).forEach((roleName) => {
    if (!BACKEND_ROLES.includes(roleName)) {
      console.warn(`[NavConfig] Warning: Unrecognized role key "${roleName}" mapped in navigation matrix.`);
    }
  });
});

export function getUserNavProfile(applicationContext, role, isSystemAdmin) {
  if (isSystemAdmin || role === "system_admin") {
    return MATRIX[APP_CONTEXTS.SYSTEM].system_admin;
  }

  const contextKey = applicationContext === APP_CONTEXTS.SPACE ? APP_CONTEXTS.SPACE : APP_CONTEXTS.CARE;
  const contextMap = MATRIX[contextKey];

  if (contextMap && contextMap[role]) {
    return contextMap[role];
  }

  // Fallbacks
  if (role === "emergency_contact") {
    return MATRIX[APP_CONTEXTS.CARE].emergency_contact;
  }

  if (contextKey === APP_CONTEXTS.SPACE) {
    return MATRIX[APP_CONTEXTS.SPACE].corporate_staff;
  }

  return MATRIX[APP_CONTEXTS.CARE].caregiver;
}

export function isViewAllowed(viewId, applicationContext, role, isSystemAdmin) {
  const profile = getUserNavProfile(applicationContext, role, isSystemAdmin);
  return profile.allowedViews.includes(viewId);
}

export function getDefaultView(applicationContext, role, isSystemAdmin) {
  const profile = getUserNavProfile(applicationContext, role, isSystemAdmin);
  return profile.defaultView;
}

export function getNavItemsForUser(applicationContext, role, isSystemAdmin) {
  const profile = getUserNavProfile(applicationContext, role, isSystemAdmin);
  return profile.allowedViews.map((viewId) => VIEW_DEFINITIONS[viewId]).filter(Boolean);
}
