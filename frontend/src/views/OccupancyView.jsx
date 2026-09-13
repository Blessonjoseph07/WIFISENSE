import React from "react";

export default function OccupancyView({
  appContext = "",
  role = "",
  isSystemAdmin = false,
  rooms = [],
  floors = [],
  buildings = [],
  organizations = [],
  residents = [],
  devices = [],
  alerts = [],
  occupancySummary = { occupied_room_details: [] },
  healthRecords = {},
  facilityFilter = "ALL",
  setFacilityFilter = () => {},
  occupancySearchQuery = "",
  setOccupancySearchQuery = () => {},
  occupancyStatusFilter = "ALL",
  setOccupancyStatusFilter = () => {},
  occupancyClassFilter = "ALL",
  setOccupancyClassFilter = () => {},
  selectedOccupancyRoomId = null,
  setSelectedOccupancyRoomId = () => {},
  handleAcknowledge = () => {},
  setShowResolveModal = () => {},
}) {
  const isCare = appContext === "ELDER_CARE" || appContext === "CARE";
  const isSpace = appContext === "CORPORATE" || appContext === "SPACE";

  // Strict context filtering: separate CARE vs SPACE rooms
  const contextRooms = rooms.filter((rm) => {
    const flr = floors.find((f) => f.id === rm.floor_id);
    const bld = buildings.find((b) => b.id === flr?.building_id);
    const org = organizations.find((o) => o.id === bld?.organization_id);

    if (isSystemAdmin && facilityFilter !== "ALL") {
      return org?.type === facilityFilter;
    }
    if (isCare) {
      return org?.type === "ELDER_CARE";
    }
    if (isSpace) {
      return org?.type === "CORPORATE";
    }
    return true;
  });

  // Extract available classifications for filter pills
  const availableClassifications = Array.from(
    new Set(contextRooms.map((rm) => rm.classification || rm.room_type).filter(Boolean))
  ).sort();

  // Filter rooms by search, classification, and status
  const filteredRooms = contextRooms.filter((rm) => {
    const detail =
      (occupancySummary.occupied_room_details || []).find((d) => d.room_id === rm.id) || {};
    const isOccupied = detail.is_occupied ?? false;
    const classification = rm.classification || detail.classification || rm.room_type;
    const assignedRes = residents.filter((res) => res.room_id === rm.id);
    const residentNames = assignedRes
      .map((r) => `${r.first_name} ${r.last_name}`)
      .join(" ")
      .toLowerCase();

    // Search query
    if (occupancySearchQuery.trim()) {
      const q = occupancySearchQuery.toLowerCase();
      const matchesName = rm.name.toLowerCase().includes(q);
      const matchesRes = residentNames.includes(q);
      const matchesClass = classification.toLowerCase().includes(q);
      if (!matchesName && !matchesRes && !matchesClass) return false;
    }

    // Classification filter
    if (occupancyClassFilter !== "ALL" && classification !== occupancyClassFilter) {
      return false;
    }

    // Status filter
    if (occupancyStatusFilter === "OCCUPIED" && !isOccupied) return false;
    if (occupancyStatusFilter === "VACANT" && isOccupied) return false;
    if (occupancyStatusFilter === "DISCREPANCY") {
      const hasDiscrepancy = detail.discrepancy && detail.discrepancy !== "NORMAL";
      const hasAlert = alerts.some((a) => a.room_id === rm.id && a.status !== "resolved");
      const hasEnergyAlert = detail.energy_state && detail.energy_state.alert_worthy;
      if (!hasDiscrepancy && !hasAlert && !hasEnergyAlert) return false;
    }

    return true;
  });

  // Active inspected room
  const safeRooms = filteredRooms.length > 0 ? filteredRooms : contextRooms;
  const currentSelectedId =
    selectedOccupancyRoomId || (safeRooms[0] ? safeRooms[0].id : null);
  const activeRm =
    safeRooms.find((r) => r.id === currentSelectedId) ||
    safeRooms[0] || {
      id: "none",
      name: "No rooms available",
      room_type: "N/A",
      classification: "N/A",
      capacity: 1,
    };

  const activeFlr = floors.find((f) => f.id === activeRm.floor_id) || { floor_number: 1 };
  const activeBld = buildings.find((b) => b.id === activeFlr.building_id) || {
    name: isCare ? "St. Peter's Care Wing" : "MCA Academic Block",
  };
  const activeDetail =
    (occupancySummary.occupied_room_details || []).find((d) => d.room_id === activeRm.id) || {};
  const activeIsOccupied = activeDetail.is_occupied ?? false;
  const activeActivity =
    activeDetail.current_activity || (activeIsOccupied ? "Presence" : "Empty");
  const activeConfidence = Math.round((activeDetail.model_confidence || 0.95) * 100);
  const activeClassification =
    activeRm.classification || activeDetail.classification || activeRm.room_type;
  const activeExpected =
    activeDetail.expected_state ||
    activeRm.dimensions_metadata?.expected_state ||
    (activeIsOccupied ? "Occupied" : "Vacant");
  const activeDiscrepancy = activeDetail.discrepancy || "NORMAL";
  const activeSchedule = activeDetail.schedule || activeRm.dimensions_metadata?.schedule || [];
  const activeEnergy = activeDetail.energy_state || activeRm.dimensions_metadata?.energy_state || {};

  // Assigned residents for active room (CARE context)
  const activeResidents = residents.filter((res) => res.room_id === activeRm.id);
  const activeDevice = devices.find((d) => d.room_id === activeRm.id) || {
    name: `NODE-CSI-${activeRm.name.replace(/\s+/g, "").substring(0, 8).toUpperCase()}`,
    mac_address: "B4:E6:2D:AA:1F:90",
    status: "ONLINE",
  };
  const activeRoomAlerts = alerts.filter(
    (a) => a.room_id === activeRm.id && a.status !== "resolved"
  );

  // Classification badge color helper
  const getClassificationBadgeStyle = (classification) => {
    switch (classification) {
      case "Resident Bedroom":
        return "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/30 dark:text-teal-300 dark:border-teal-800";
      case "Bathroom":
        return "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:border-rose-800";
      case "Physiotherapy":
      case "Nursing Area":
      case "Staff Area":
        return "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/30 dark:text-purple-300 dark:border-purple-800";
      case "Dining Area":
      case "Recreation":
      case "Seminar/Common Hall":
        return "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/30 dark:text-sky-300 dark:border-sky-800";
      case "Conference Room":
      case "Meeting Room":
        return "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/30 dark:text-indigo-300 dark:border-indigo-800";
      case "Computer Lab":
      case "Research Lab":
        return "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/30 dark:text-cyan-300 dark:border-cyan-800";
      case "Classroom":
      case "Seminar Hall":
        return "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-800";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700";
    }
  };

  const getActivityIcon = (act) => {
    switch (act) {
      case "Resting":
        return "bed";
      case "Sitting":
        return "airline_seat_recline_normal";
      case "Walking":
        return "directions_walk";
      case "Fall_Detected":
        return "warning";
      case "Presence":
        return "person";
      default:
        return "sensor_door";
    }
  };

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-250 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
              Room Occupancy & Spatial Intelligence
            </h2>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5 ${
                isCare
                  ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800"
                  : "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${isCare ? "bg-rose-500" : "bg-teal-500"} animate-pulse`}
              ></span>
              {isCare ? "CARE FACILITY MONITOR" : "SPACE INTELLIGENCE"}
            </span>
          </div>
          <p className="text-body-md text-slate-500 dark:text-slate-400 mt-1">
            {isCare
              ? "Real-time resident living quarters occupancy, posture telemetry, and fall-risk sensing."
              : "Real-time workplace room occupancy, schedule discrepancy tracking, and energy telemetry."}
          </p>
        </div>

        {/* Summary Metric Badges */}
        <div className="flex flex-wrap gap-2 text-xs">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 shadow-sm">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">
              Monitored Rooms
            </span>
            <span className="font-bold text-slate-900 dark:text-white font-mono text-sm">
              {contextRooms.length}
            </span>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 shadow-sm">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">
              Live Occupied
            </span>
            <span className="font-bold text-teal-600 dark:text-teal-400 font-mono text-sm">
              {
                contextRooms.filter((r) =>
                  (occupancySummary.occupied_room_details || []).some(
                    (d) => d.room_id === r.id && d.is_occupied
                  )
                ).length
              }
            </span>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 shadow-sm">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">
              Standby / Vacant
            </span>
            <span className="font-bold text-slate-500 font-mono text-sm">
              {
                contextRooms.filter(
                  (r) =>
                    !(occupancySummary.occupied_room_details || []).some(
                      (d) => d.room_id === r.id && d.is_occupied
                    )
                ).length
              }
            </span>
          </div>
          {isSystemAdmin && (
            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
              <button
                onClick={() => setFacilityFilter("ALL")}
                className={`px-2.5 py-1 text-xs font-bold rounded ${
                  facilityFilter === "ALL"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-500"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFacilityFilter("CORPORATE")}
                className={`px-2.5 py-1 text-xs font-bold rounded ${
                  facilityFilter === "CORPORATE"
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Corporate
              </button>
              <button
                onClick={() => setFacilityFilter("ELDER_CARE")}
                className={`px-2.5 py-1 text-xs font-bold rounded ${
                  facilityFilter === "ELDER_CARE"
                    ? "bg-rose-600 text-white shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Elder Care
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-[18px]">
              search
            </span>
            <input
              type="text"
              placeholder={
                isCare
                  ? "Search rooms, residents (e.g. Mary Joseph, Bathroom)..."
                  : "Search conference rooms, labs, classrooms..."
              }
              value={occupancySearchQuery}
              onChange={(e) => setOccupancySearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:border-teal-500"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-bold">
            {[
              { id: "ALL", label: "All Rooms" },
              { id: "OCCUPIED", label: "Occupied" },
              { id: "VACANT", label: "Vacant" },
              { id: "DISCREPANCY", label: "Attention Needed" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setOccupancyStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded transition-all ${
                  occupancyStatusFilter === tab.id
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Classification Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1 flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px] text-teal-600">tune</span>
            Categories:
          </span>
          <button
            onClick={() => setOccupancyClassFilter("ALL")}
            className={`px-2.5 py-1 rounded text-xs font-bold border transition-all ${
              occupancyClassFilter === "ALL"
                ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                : "bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800"
            }`}
          >
            All Categories ({contextRooms.length})
          </button>
          {availableClassifications.map((cls) => {
            const count = contextRooms.filter(
              (r) => (r.classification || r.room_type) === cls
            ).length;
            const isSelected = occupancyClassFilter === cls;
            return (
              <button
                key={cls}
                onClick={() => setOccupancyClassFilter(cls)}
                className={`px-2.5 py-1 rounded text-xs font-bold border transition-all ${
                  isSelected
                    ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                    : "bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-teal-500"
                }`}
              >
                {cls} <span className="opacity-70">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Master-Detail Layout: Rooms Directory (Left) & Deep Inspector (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (5 Cols): Interactive Room Directory Grid */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex justify-between items-center px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Select Room to Inspect ({filteredRooms.length})
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Active: <strong className="text-teal-605">{activeRm.name}</strong>
            </span>
          </div>

          <div className="space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
            {filteredRooms.map((rm) => {
              const detail =
                (occupancySummary.occupied_room_details || []).find((d) => d.room_id === rm.id) ||
                {};
              const isOcc = detail.is_occupied ?? false;
              const activity = detail.current_activity || (isOcc ? "Presence" : "Empty");
              const cls = rm.classification || detail.classification || rm.room_type;
              const isSelected = rm.id === activeRm.id;
              const assigned = residents.filter((r) => r.room_id === rm.id);
              const hasAlert = alerts.some((a) => a.room_id === rm.id && a.status !== "resolved");
              const hasDiscrepancy = detail.discrepancy && detail.discrepancy !== "NORMAL";
              const hasEnergyAlert = detail.energy_state && detail.energy_state.alert_worthy;

              return (
                <div
                  key={rm.id}
                  onClick={() => setSelectedOccupancyRoomId(rm.id)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer text-left ${
                    isSelected
                      ? "bg-teal-50/40 dark:bg-teal-950/30 border-teal-500 ring-2 ring-teal-500/20 shadow-sm"
                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-9 h-9 rounded-lg flex items-center justify-center border shadow-xs ${
                          isOcc
                            ? "bg-teal-50 text-teal-600 border-teal-200 dark:bg-teal-950/50 dark:text-teal-300 dark:border-teal-800"
                            : "bg-slate-100 text-slate-400 border-slate-200 dark:bg-slate-800 dark:border-slate-700"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[20px]">
                          {getActivityIcon(activity)}
                        </span>
                      </div>
                      <div>
                        <div className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
                          {rm.name}
                          {hasAlert && (
                            <span
                              className="w-2 h-2 rounded-full bg-rose-500 animate-ping"
                              title="Active Alert"
                            ></span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                          <span>Capacity: {rm.capacity}</span>
                          <span>•</span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${getClassificationBadgeStyle(
                              cls
                            )}`}
                          >
                            {cls}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Live Stance Badge */}
                    <div className="flex flex-col items-end">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                          isOcc
                            ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                            : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isOcc ? "bg-teal-500 animate-pulse" : "bg-slate-400"
                          }`}
                        ></span>
                        {isOcc ? "OCCUPIED" : "VACANT"}
                      </span>
                      <span
                        className={`text-[10px] font-semibold mt-1 ${
                          activity === "Fall_Detected"
                            ? "text-rose-600 font-bold"
                            : isOcc
                            ? "text-teal-605"
                            : "text-slate-400"
                        }`}
                      >
                        {activity.replace("_", " ")}
                      </span>
                    </div>
                  </div>

                  {/* Context-Specific Mini Information */}
                  <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                    {isCare ? (
                      <div className="text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[14px] text-slate-400">
                          person
                        </span>
                        {assigned.length > 0 ? (
                          <span>
                            Resident:{" "}
                            <strong>
                              {assigned.map((a) => `${a.first_name} ${a.last_name}`).join(", ")}
                            </strong>
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">
                            Communal / General Care Zone
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="text-slate-600 dark:text-slate-300 flex items-center gap-1.5 truncate max-w-[240px]">
                        <span className="material-symbols-outlined text-[14px] text-slate-400">
                          event
                        </span>
                        <span>
                          Schedule: <strong>{detail.expected_state || "Standard"}</strong>
                        </span>
                      </div>
                    )}

                    {hasDiscrepancy ? (
                      <span className="text-[10px] font-bold text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                        Unexpected
                      </span>
                    ) : hasEnergyAlert ? (
                      <span className="text-[10px] font-bold text-sky-600 bg-sky-50 dark:bg-sky-950/40 px-1.5 py-0.5 rounded border border-sky-200 dark:border-sky-800">
                        AC Idle
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400">Nominal</span>
                    )}
                  </div>
                </div>
              );
            })}

            {filteredRooms.length === 0 && (
              <div className="p-8 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-400 text-xs">
                No rooms matched the selected filter or search criteria.
              </div>
            )}
          </div>
        </div>

        {/* Right Column (7 Cols): Comprehensive Live Spatial Inspector */}
        <div className="lg:col-span-7 space-y-5">
          {/* Main Room Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getClassificationBadgeStyle(
                      activeClassification
                    )}`}
                  >
                    {activeClassification}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Floor {activeFlr.floor_number} • Capacity: {activeRm.capacity}
                  </span>
                </div>
                <h1 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
                  {activeRm.name}
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[14px]">apartment</span>
                  {activeBld.name}
                </p>
              </div>

              {/* Stance Banner */}
              <div className="flex flex-col items-end">
                <div
                  className={`px-4 py-1.5 rounded-full flex items-center gap-2 text-xs font-bold border ${
                    activeIsOccupied
                      ? "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800 shadow-sm"
                      : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      activeIsOccupied ? "bg-teal-500 animate-pulse" : "bg-slate-400"
                    }`}
                  ></span>
                  <span className="uppercase tracking-wider">
                    {activeIsOccupied ? "OCCUPIED" : "VACANT"}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-400 mt-1">
                  CSI Confidence: <strong className="text-teal-605">{activeConfidence}%</strong>
                </span>
              </div>
            </div>

            {/* Primary Telemetry Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
              {/* Detected Activity */}
              <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 dark:bg-teal-950/50 dark:text-teal-300 flex items-center justify-center border border-teal-200 dark:border-teal-800">
                  <span className="material-symbols-outlined text-[26px]">
                    {getActivityIcon(activeActivity)}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                    Current Posture / Stance
                  </span>
                  <span className="text-headline-sm font-headline-sm font-bold text-slate-900 dark:text-white block">
                    {activeActivity.replace("_", " ")}
                  </span>
                  <span className="text-[11px] text-teal-605 font-medium">
                    Wi-Fi Sensing Verified
                  </span>
                </div>
              </div>

              {/* Scheduled / Expected Comparison */}
              <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center gap-3.5">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
                    activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                      ? "bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800"
                      : "bg-sky-50 text-sky-600 border-sky-200 dark:bg-sky-950/50 dark:text-sky-300 dark:border-sky-800"
                  }`}
                >
                  <span className="material-symbols-outlined text-[26px]">
                    {activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                      ? "event_busy"
                      : "event_available"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                    Scheduled Expectation
                  </span>
                  <span className="text-headline-sm font-headline-sm font-bold text-slate-900 dark:text-white block">
                    {activeExpected}
                  </span>
                  <span
                    className={`text-[11px] font-bold ${
                      activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                        ? "text-amber-600"
                        : "text-slate-400"
                    }`}
                  >
                    {activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                      ? "Unexpected Occupancy"
                      : "Schedule Compliant"}
                  </span>
                </div>
              </div>
            </div>

            {/* Sensor Node & Privacy Guarantee */}
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-teal-605">
                  router
                </span>
                <span>
                  Sensor:{" "}
                  <strong className="text-slate-700 dark:text-slate-300 font-mono">
                    {activeDevice.name}
                  </strong>{" "}
                  ({activeDevice.mac_address})
                </span>
              </div>
              <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                <span className="material-symbols-outlined text-[15px]">verified_user</span>
                <span>100% Privacy Protected • Zero Optical Cameras</span>
              </div>
            </div>
          </div>

          {/* CONTEXT SPECIFIC DEEP CARD */}
          {isCare ? (
            /* CARE SPECIFIC: Resident Profile & Health Context */
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-rose-600">health_and_safety</span>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm uppercase tracking-wider">
                    Assigned Resident & Clinical Safety Information
                  </h3>
                </div>
                <span className="text-xs text-slate-400">
                  {activeResidents.length} Monitored Resident
                  {activeResidents.length === 1 ? "" : "s"}
                </span>
              </div>

              {activeResidents.length > 0 ? (
                <div className="space-y-4">
                  {activeResidents.map((res) => {
                    const health = healthRecords[res.id] || [];
                    return (
                      <div
                        key={res.id}
                        className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-3"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div>
                            <h4 className="text-headline-sm font-headline-sm font-bold text-slate-900 dark:text-white">
                              {res.first_name} {res.last_name}
                            </h4>
                            <p className="text-xs text-slate-500 font-mono">
                              DOB: {new Date(res.date_of_birth).toLocaleDateString()} • Living Unit:{" "}
                              {activeRm.name}
                            </p>
                          </div>
                          <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                            Active Monitored Profile
                          </span>
                        </div>

                        {/* Health Conditions */}
                        <div className="border-t border-slate-200/80 dark:border-slate-800/80 pt-3">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                            Diagnosed Health & Fall-Risk Profile
                          </span>
                          {health.length > 0 ? (
                            health.map((h) => (
                              <div
                                key={h.id}
                                className="text-xs bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800"
                              >
                                <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                                  {h.condition_name}
                                </div>
                                <p className="text-slate-600 dark:text-slate-300 text-[11px] mt-1">
                                  {h.notes}
                                </p>
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-slate-400 italic">
                              No chronic medical restrictions documented. Regular vital checkups.
                            </p>
                          )}
                        </div>

                        {/* Stance evaluation */}
                        <div className="flex items-center justify-between text-xs pt-1">
                          <span className="text-slate-500">Continuous Stance Tripwire:</span>
                          <span
                            className={`font-bold ${
                              activeActivity === "Fall_Detected"
                                ? "text-rose-600 animate-pulse"
                                : "text-emerald-605"
                            }`}
                          >
                            {activeActivity === "Fall_Detected"
                              ? "🚨 ABNORMAL COLLAPSE FLAGGED"
                              : "✓ Nominal Posture (No Sudden Drop)"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-400">
                  This room is currently a communal, nursing, or clinical care space without
                  dedicated resident residential assignments.
                </div>
              )}
            </div>
          ) : (
            /* SPACE SPECIFIC: Schedule Compliance & Smart Energy Efficiency */
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-teal-600">calendar_month</span>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm uppercase tracking-wider">
                    Corporate Schedule & Energy Automation
                  </h3>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Status:{" "}
                  <strong
                    className={
                      activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                        ? "text-amber-600"
                        : "text-teal-605"
                    }
                  >
                    {activeDiscrepancy === "UNEXPECTED_OCCUPANCY"
                      ? "Unexpected Occupancy Detected"
                      : "Schedule Matched"}
                  </strong>
                </span>
              </div>

              {/* Schedule Timeline Table */}
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  Today's Configured Schedule Blocks
                </span>
                {activeSchedule.length > 0 ? (
                  <div className="space-y-2">
                    {activeSchedule.map((s, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono font-bold text-teal-605 text-[11px] bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-800">
                            {s.time_range}
                          </span>
                          <span className="font-bold text-slate-900 dark:text-white">
                            {s.title}
                          </span>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            s.status === "Class" || s.status === "Occupied"
                              ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300"
                              : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {s.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">
                    No scheduled calendar bookings for this space today.
                  </p>
                )}
              </div>

              {/* Smart Energy Optimization Card */}
              <div className="mt-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-amber-500">
                      energy_savings_leaf
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white text-xs uppercase tracking-wider">
                      HVAC & Energy Automation Condition
                    </span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                      activeEnergy.ac_status === "ON"
                        ? "bg-sky-50 text-sky-700 border border-sky-200"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    AC: {activeEnergy.ac_status || "STANDBY"}
                  </span>
                </div>
                {activeEnergy.efficiency_recommendation ? (
                  <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-amber-200 dark:border-amber-800/60 text-xs">
                    <p className="text-amber-800 dark:text-amber-300 font-medium">
                      ⚠️ {activeEnergy.efficiency_recommendation}
                    </p>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Automation recommendation • Zero energy waste policy
                    </span>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Climate control setpoint:{" "}
                    {activeEnergy.hvac_setpoint_c ? `${activeEnergy.hvac_setpoint_c}°C` : "22.0°C"}{" "}
                    • Operational power load nominal.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Active Room Alerts & Quick Intervention */}
          {activeRoomAlerts.length > 0 && (
            <div className="bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400">
                  <span className="material-symbols-outlined">notification_important</span>
                  <h4 className="font-bold text-sm uppercase tracking-wider">
                    Active Alert for {activeRm.name}
                  </h4>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-600 text-white">
                  {activeRoomAlerts[0].severity}
                </span>
              </div>
              <p className="text-xs text-rose-900 dark:text-rose-200 font-medium">
                {activeRoomAlerts[0].message}
              </p>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => handleAcknowledge(activeRoomAlerts[0].id)}
                  className="px-3 py-1.5 bg-white dark:bg-slate-800 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-700 rounded-lg text-xs font-bold hover:bg-rose-50"
                >
                  Acknowledge Alert
                </button>
                <button
                  onClick={() => setShowResolveModal(activeRoomAlerts[0].id)}
                  className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-bold hover:bg-rose-700 shadow-sm"
                >
                  Resolve Alert
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
