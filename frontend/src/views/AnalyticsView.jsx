import React from "react";

export default function AnalyticsView({
  appContext = "",
  role = "",
  isSystemAdmin = false,
  occupancySummary = { occupied_room_details: [] },
  analyticsClassificationFilter = "ALL",
  setAnalyticsClassificationFilter = () => {},
  analyticsTimeRange = "30D",
  setAnalyticsTimeRange = () => {},
  exportOccupancyTimeData = () => {},
  setCurrentView = () => {},
}) {
  const isCareAnalytics = appContext === "ELDER_CARE" || appContext === "CARE";
  const allAnalyticsRooms = occupancySummary?.occupied_room_details || [];

  // Extract unique classifications from rooms scoped to current tenant
  const availableClassifications = Array.from(
    new Set(allAnalyticsRooms.map((rm) => rm.classification).filter(Boolean))
  ).sort();

  // Filter rooms based on active classification filter
  const filteredRooms =
    analyticsClassificationFilter === "ALL"
      ? allAnalyticsRooms
      : allAnalyticsRooms.filter((rm) => rm.classification === analyticsClassificationFilter);

  // Calculate Activity breakdown for the filtered rooms
  const activityCounts = {};
  filteredRooms.forEach((rm) => {
    const act = rm.is_occupied ? rm.current_activity || "Presence" : "Empty";
    activityCounts[act] = (activityCounts[act] || 0) + 1;
  });
  const totalFiltered = filteredRooms.length || 1;

  // Context-specific classifications grouping for KPI cards
  const careCategories = [
    {
      id: "Resident Bedroom",
      title: "Resident Bedrooms",
      icon: "bed",
      color: "teal",
      matcher: (c) => c === "Resident Bedroom" || c === "Resident Room",
      desc: "Assigned living quarters & rest zones",
    },
    {
      id: "Bathroom",
      title: "Bathrooms (Fall Risk)",
      icon: "bathtub",
      color: "rose",
      matcher: (c) => c === "Bathroom",
      desc: "High-risk slip & sudden collapse tripwires",
    },
    {
      id: "Communal",
      title: "Communal & Dining Halls",
      icon: "groups",
      color: "sky",
      matcher: (c) => ["Dining Area", "Recreation", "Seminar/Common Hall"].includes(c),
      desc: "Social engagement & dining halls",
    },
    {
      id: "Clinical",
      title: "Clinical & Rehab Stations",
      icon: "medical_services",
      color: "purple",
      matcher: (c) => ["Physiotherapy", "Nursing Area", "Staff Area"].includes(c),
      desc: "Rehabilitation, nursing desk & triage",
    },
  ];

  const spaceCategories = [
    {
      id: "Conference",
      title: "Conference & Meeting",
      icon: "meeting_room",
      color: "teal",
      matcher: (c) => ["Conference Room", "Meeting Room", "Seminar Hall"].includes(c),
      desc: "Executive collaboration & meeting suites",
    },
    {
      id: "Labs",
      title: "Computer & Research Labs",
      icon: "biotech",
      color: "sky",
      matcher: (c) => ["Computer Lab", "Research Lab"].includes(c),
      desc: "Workstations & high-performance clusters",
    },
    {
      id: "Classrooms",
      title: "Academic Classrooms",
      icon: "school",
      color: "indigo",
      matcher: (c) => c === "Classroom",
      desc: "Instructional halls & lecture theaters",
    },
    {
      id: "Offices",
      title: "Offices & Support Areas",
      icon: "work",
      color: "amber",
      matcher: (c) => ["Office", "Common Area", "Cafeteria", "Server Room"].includes(c),
      desc: "Staff cabins, server rooms & common areas",
    },
  ];

  const currentCategories = isCareAnalytics ? careCategories : spaceCategories;

  // Underutilized / attention spaces from actual rooms (vacant or discrepancy)
  const attentionRooms = allAnalyticsRooms
    .filter(
      (rm) =>
        !rm.is_occupied ||
        rm.discrepancy !== "NORMAL" ||
        (rm.energy_state && rm.energy_state.alert_worthy)
    )
    .slice(0, 3);

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

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-250 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
              Analytics Overview
            </h2>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5 ${
                isCareAnalytics
                  ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800"
                  : "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isCareAnalytics ? "bg-rose-500" : "bg-teal-500"
                }`}
              ></span>
              {isCareAnalytics ? "CARE CLASSIFICATION" : "SPACE CLASSIFICATION"}
            </span>
          </div>
          <p className="text-body-lg font-body-lg text-slate-500 dark:text-slate-400 mt-1">
            {isCareAnalytics
              ? "Classified spatial telemetry, resident stance distribution, and safety response metrics across elder-care zones."
              : "Classified spatial utilization, scheduled occupancy compliance, and energy optimization analytics across campus facilities."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-slate-100 dark:bg-slate-900 p-1 rounded-lg border border-slate-200 dark:border-slate-800 flex text-xs font-bold">
            {["TODAY", "7D", "30D"].map((range) => (
              <button
                key={range}
                onClick={() => setAnalyticsTimeRange(range)}
                className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                  analyticsTimeRange === range
                    ? "bg-white dark:bg-slate-800 text-teal-600 dark:text-teal-400 shadow-sm"
                    : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                {range === "TODAY" ? "Today" : range === "7D" ? "Last 7 Days" : "Last 30 Days"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Classification Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px] text-teal-600">category</span>
            Filter by Room Classification
          </span>
          <span className="text-xs text-slate-500 font-mono">
            Showing {filteredRooms.length} of {allAnalyticsRooms.length} rooms
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setAnalyticsClassificationFilter("ALL")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 border transition-all cursor-pointer ${
              analyticsClassificationFilter === "ALL"
                ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                : "bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-teal-500"
            }`}
          >
            <span className="material-symbols-outlined text-[15px]">apps</span>
            All Classifications
            <span
              className={`px-1.5 py-0.2 rounded text-[10px] ${
                analyticsClassificationFilter === "ALL"
                  ? "bg-teal-700 text-white"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
              }`}
            >
              {allAnalyticsRooms.length}
            </span>
          </button>
          {availableClassifications.map((cls) => {
            const count = allAnalyticsRooms.filter((r) => r.classification === cls).length;
            const occupiedCount = allAnalyticsRooms.filter(
              (r) => r.classification === cls && r.is_occupied
            ).length;
            const isSelected = analyticsClassificationFilter === cls;
            return (
              <button
                key={cls}
                onClick={() => setAnalyticsClassificationFilter(cls)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                    : "bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-800 hover:border-teal-500"
                }`}
              >
                <span>{cls}</span>
                <span
                  className={`px-1.5 py-0.2 rounded text-[10px] ${
                    isSelected
                      ? "bg-teal-700 text-white"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}
                >
                  {occupiedCount}/{count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Classification Category KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {currentCategories.map((cat) => {
          const catRooms = allAnalyticsRooms.filter((r) => cat.matcher(r.classification));
          const totalCat = catRooms.length;
          const occCat = catRooms.filter((r) => r.is_occupied).length;
          const pctCat = totalCat > 0 ? Math.round((occCat / totalCat) * 100) : 0;
          const hasAnomalies = catRooms.some(
            (r) => r.discrepancy !== "NORMAL" || r.current_activity === "Fall_Detected"
          );

          return (
            <div
              key={cat.id}
              onClick={() => {
                const matching = availableClassifications.find((c) => cat.matcher(c));
                if (matching) {
                  setAnalyticsClassificationFilter(
                    analyticsClassificationFilter === matching ? "ALL" : matching
                  );
                }
              }}
              className={`bg-white dark:bg-slate-900 border rounded-xl p-5 shadow-sm hover:shadow-md transition-all cursor-pointer text-left ${
                hasAnomalies && isCareAnalytics && cat.id === "Bathroom"
                  ? "border-rose-300 dark:border-rose-800/80 bg-rose-50/20"
                  : "border-slate-200 dark:border-slate-800"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                      cat.color === "teal"
                        ? "bg-teal-50 text-teal-600 dark:bg-teal-950/50 dark:text-teal-300"
                        : cat.color === "rose"
                        ? "bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300"
                        : cat.color === "sky"
                        ? "bg-sky-50 text-sky-600 dark:bg-sky-950/50 dark:text-sky-300"
                        : "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[20px]">{cat.icon}</span>
                  </div>
                  <h4 className="font-bold text-slate-900 dark:text-white text-sm">{cat.title}</h4>
                </div>
                <span className="text-xs font-mono font-bold text-slate-400">
                  {occCat}/{totalCat}
                </span>
              </div>
              <div className="flex items-baseline justify-between mt-2">
                <div className="text-headline-md font-headline-md font-bold text-slate-900 dark:text-white">
                  {pctCat}%<span className="text-xs font-normal text-slate-400 ml-1.5">utilization</span>
                </div>
                {hasAnomalies ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300">
                    Attention
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950/40 dark:text-teal-300">
                    Nominal
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2 line-clamp-1">
                {cat.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Bento Grid Layout: Multi-line Occupancy Chart + Classified Activity Mix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Occupancy Over Time Chart */}
        <div className="lg:col-span-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
            <div>
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                Classified Occupancy Over Time
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {isCareAnalytics
                  ? "Temporal distribution across resident living, communal, and care areas"
                  : "Scheduled vs actual utilization trends across labs, conference suites, and classrooms"}
              </p>
            </div>
            <button
              onClick={exportOccupancyTimeData}
              className="text-teal-605 hover:underline text-xs font-bold flex items-center gap-1.5 cursor-pointer self-start sm:self-auto"
            >
              <span className="material-symbols-outlined text-[16px]">download</span>
              Export Data
            </button>
          </div>

          {/* Chart visual representation */}
          <div className="flex-1 w-full min-h-[280px] rounded-lg relative overflow-hidden flex items-end px-4 pb-4 gap-4 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
            <svg
              className="absolute inset-0 w-full h-full"
              preserveAspectRatio="none"
              viewBox="0 0 100 100"
            >
              <defs>
                <linearGradient id="careGrad1" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#0d9488" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#0d9488" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="careGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#0284c7" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#0284c7" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              {/* Primary Series */}
              <path
                d="M0,75 Q15,65 30,50 T60,35 T85,45 T100,25 L100,100 L0,100 Z"
                fill="url(#careGrad1)"
              ></path>
              <path
                d="M0,75 Q15,65 30,50 T60,35 T85,45 T100,25"
                fill="none"
                stroke="#0d9488"
                strokeWidth="2"
              ></path>

              {/* Secondary Series */}
              <path
                d="M0,90 Q20,85 40,40 T70,30 T90,60 T100,50 L100,100 L0,100 Z"
                fill="url(#careGrad2)"
              ></path>
              <path
                d="M0,90 Q20,85 40,40 T70,30 T90,60 T100,50"
                fill="none"
                stroke="#0284c7"
                strokeWidth="1.5"
                strokeDasharray="3,3"
              ></path>

              {/* Tertiary Series */}
              <path
                d="M0,95 Q25,90 50,70 T75,65 T100,80"
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1.5"
              ></path>
            </svg>
            <div className="absolute bottom-2 left-4 text-[10px] font-mono text-slate-400">
              08:00 AM
            </div>
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-mono text-slate-400">
              01:00 PM
            </div>
            <div className="absolute bottom-2 right-4 text-[10px] font-mono text-slate-400">
              06:00 PM
            </div>
            <div className="absolute top-4 left-2 text-[10px] font-mono text-slate-400">100%</div>

            {/* Classification Legend */}
            <div className="absolute top-4 right-4 flex flex-wrap gap-3 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm p-2 rounded-lg text-[10px] font-bold tracking-wider border border-slate-200 dark:border-slate-800 shadow-sm">
              {isCareAnalytics ? (
                <>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-teal-600 rounded-full"></div>Resident Bedrooms
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-sky-500 rounded-full"></div>Communal & Dining
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-amber-500 rounded-full"></div>Bathrooms & Rehab
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-teal-600 rounded-full"></div>Labs & Workstations
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-sky-500 rounded-full"></div>Conference Suites
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 bg-amber-500 rounded-full"></div>Classrooms
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Classified Activity Mix */}
        <div className="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                {isCareAnalytics ? "Resident Stance Mix" : "Space Activity Mix"}
              </h3>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                {analyticsClassificationFilter === "ALL"
                  ? "All Zones"
                  : analyticsClassificationFilter}
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              {isCareAnalytics
                ? "Real-time posture classification derived from Wi-Fi CSI sensing"
                : "Classified telemetry activity across monitored facility spaces"}
            </p>

            {/* Donut Ring Visual */}
            <div className="flex flex-col items-center justify-center my-2">
              <div
                className="relative w-36 h-36 rounded-full border-[14px] border-slate-100 dark:border-slate-800 flex items-center justify-center shadow-inner"
                style={{
                  borderTopColor: "#0d9488",
                  borderRightColor: "#0284c7",
                  borderBottomColor: isCareAnalytics ? "#8b5cf6" : "#64748b",
                  borderLeftColor: isCareAnalytics ? "#f43f5e" : "#f59e0b",
                }}
              >
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold">
                    {Math.round(
                      (((activityCounts["Resting"] || 0) + (activityCounts["Sitting"] || 0)) /
                        totalFiltered) *
                        100
                    )}
                    %
                  </span>
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                    {isCareAnalytics ? "Rest / Sit" : "Seated"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown List */}
          <div className="space-y-2.5 mt-4 text-xs font-semibold">
            {isCareAnalytics ? (
              <>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-teal-600 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">Resting in Bed</span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Resting"] || 0} (
                    {Math.round(((activityCounts["Resting"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-sky-500 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">Seated Stance</span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Sitting"] || 0} (
                    {Math.round(((activityCounts["Sitting"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-purple-500 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">Active Walking</span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Walking"] || 0} (
                    {Math.round(((activityCounts["Walking"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-rose-500 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">
                      Fall / Anomaly Tripwire
                    </span>
                  </div>
                  <span className="font-mono font-bold text-rose-600">
                    {activityCounts["Fall_Detected"] || 0} (
                    {Math.round(((activityCounts["Fall_Detected"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
              </>
            ) : (
              <>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-teal-600 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">
                      Active Workstation Presence
                    </span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Presence"] || 0} (
                    {Math.round(((activityCounts["Presence"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-sky-500 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">Walking & Transit</span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Walking"] || 0} (
                    {Math.round(((activityCounts["Walking"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-indigo-500 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">
                      Seated Meeting / Session
                    </span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Sitting"] || 0} (
                    {Math.round(((activityCounts["Sitting"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
                <div className="flex justify-between items-center p-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-slate-400 rounded-sm"></div>
                    <span className="text-slate-700 dark:text-slate-300">Vacant / Standby</span>
                  </div>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {activityCounts["Empty"] || 0} (
                    {Math.round(((activityCounts["Empty"] || 0) / totalFiltered) * 100)}%)
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Underutilized / Attention Spaces + Average Alert Response Time */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Underutilized Spaces (STRICTLY CONTEXT SEPARATED) */}
        <div className="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                {isCareAnalytics
                  ? "Low Activity / Extended Quiet Spaces"
                  : "Underutilized Corporate Spaces (<15%)"}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {isCareAnalytics
                  ? "Communal and clinical rooms with extended absence of resident motion"
                  : "Facilities with low scheduled throughput or optimization potential"}
              </p>
            </div>
            <span className="material-symbols-outlined text-slate-400">map</span>
          </div>

          <div className="space-y-3">
            {attentionRooms.length > 0 ? (
              attentionRooms.map((rm) => (
                <div
                  key={rm.room_id}
                  className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:bg-white dark:hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white dark:bg-slate-900 flex items-center justify-center text-teal-600 dark:text-teal-400 border border-slate-200 dark:border-slate-800 shadow-sm">
                      <span className="material-symbols-outlined">
                        {rm.classification === "Bathroom"
                          ? "bathtub"
                          : rm.classification === "Resident Bedroom"
                          ? "bed"
                          : rm.classification === "Conference Room"
                          ? "meeting_room"
                          : rm.classification === "Computer Lab"
                          ? "computer"
                          : rm.classification === "Research Lab"
                          ? "biotech"
                          : rm.classification === "Classroom"
                          ? "school"
                          : "apartment"}
                      </span>
                    </div>
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
                        {rm.room_name}
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getClassificationBadgeStyle(
                            rm.classification
                          )}`}
                        >
                          {rm.classification}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Capacity: {rm.capacity} •{" "}
                        {rm.discrepancy !== "NORMAL"
                          ? rm.discrepancy.replace("_", " ")
                          : "Normal Standby"}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <span
                      className={`font-mono font-bold text-sm ${
                        rm.is_occupied ? "text-amber-500" : "text-slate-400"
                      }`}
                    >
                      {rm.is_occupied ? rm.current_activity : "Vacant"}
                    </span>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">
                      Status
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-slate-400 text-xs italic">
                All rooms operating at optimal capacity.
              </div>
            )}
          </div>
        </div>

        {/* Avg Alert Response Time */}
        <div className="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
                  Avg Alert Response Time
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {isCareAnalytics
                    ? "Caregiver acknowledgment & on-site arrival latency for fall/inactivity alerts"
                    : "Security and maintenance dispatch response latency"}
                </p>
              </div>
              <div className="flex items-center gap-1 text-teal-600 dark:text-teal-400 text-xs font-bold uppercase">
                <span className="material-symbols-outlined text-[16px]">trending_down</span>
                {isCareAnalytics ? "-28% vs baseline" : "-12% vs last month"}
              </div>
            </div>

            {/* Bar graph representation */}
            <div className="flex items-end gap-3 h-[140px] w-full px-2 border-b border-slate-100 dark:border-slate-800 pb-3">
              {[
                { day: "Mon", height: "70%", val: "2.1m" },
                { day: "Tue", height: "55%", val: "1.8m" },
                { day: "Wed", height: "85%", val: "2.5m" },
                { day: "Thu", height: "40%", val: "1.4m", active: true },
                { day: "Fri", height: "60%", val: "1.9m" },
                { day: "Sat", height: "45%", val: "1.5m" },
                { day: "Sun", height: "35%", val: "1.2m" },
              ].map((b) => (
                <div
                  key={b.day}
                  className="flex-1 flex flex-col justify-end items-center gap-1.5 group"
                >
                  <div
                    className={`w-full rounded-t transition-all ${
                      b.active
                        ? "bg-teal-600 shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 group-hover:bg-teal-200"
                    }`}
                    style={{ height: b.height }}
                  ></div>
                  <span
                    className={`text-[9px] font-bold ${
                      b.active ? "text-teal-600" : "text-slate-400"
                    }`}
                  >
                    {b.day}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 flex justify-between items-center text-xs">
            <div>
              <div className="text-headline-md font-headline-md text-slate-900 dark:text-white font-bold">
                {isCareAnalytics ? "1.4 min" : "3.4 min"}
              </div>
              <div className="text-slate-400 text-[10px]">
                {isCareAnalytics
                  ? "Caregiver Response Target: < 2 min"
                  : "Facility SLA Target: < 5 min"}
              </div>
            </div>
            <button
              onClick={() => setCurrentView("alerts")}
              className="border border-teal-600 text-teal-600 dark:text-teal-400 px-4 py-2 rounded-lg text-xs hover:bg-teal-50 dark:hover:bg-teal-950/30 font-bold uppercase transition-colors cursor-pointer"
            >
              {isCareAnalytics ? "View Care Alerts" : "View Alert Logs"}
            </button>
          </div>
        </div>
      </div>

      {/* Classified Room Spatial Telemetry Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 className="text-headline-sm font-headline-sm text-slate-900 dark:text-white font-bold">
              Spatial Telemetry Classified by Category
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Detailed sensor derivation and schedule comparison for {filteredRooms.length} rooms
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Category Filter: <strong className="text-teal-600">{analyticsClassificationFilter}</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-bold">
                <th className="py-3 px-3">Room Name</th>
                <th className="py-3 px-3">Classification</th>
                <th className="py-3 px-3">Expected State</th>
                <th className="py-3 px-3">Live CSI Sensing</th>
                <th className="py-3 px-3">Activity Stance</th>
                <th className="py-3 px-3">Operational Condition</th>
                <th className="py-3 px-3 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {filteredRooms.map((rm) => (
                <tr
                  key={rm.room_id}
                  className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">
                    {rm.room_name}
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getClassificationBadgeStyle(
                        rm.classification
                      )}`}
                    >
                      {rm.classification}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-500 dark:text-slate-400">
                    {rm.expected_state}
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold ${
                        rm.is_occupied
                          ? "bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300"
                          : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          rm.is_occupied ? "bg-teal-500 animate-pulse" : "bg-slate-400"
                        }`}
                      ></span>
                      {rm.is_occupied ? "OCCUPIED" : "VACANT"}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`font-semibold ${
                        rm.current_activity === "Fall_Detected"
                          ? "text-rose-600 font-bold"
                          : rm.current_activity === "Resting"
                          ? "text-teal-600"
                          : rm.current_activity === "Sitting"
                          ? "text-sky-600"
                          : rm.current_activity === "Walking"
                          ? "text-indigo-600"
                          : "text-slate-500"
                      }`}
                    >
                      {rm.current_activity?.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    {rm.discrepancy === "UNEXPECTED_OCCUPANCY" ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300">
                        Unexpected Occupancy
                      </span>
                    ) : rm.energy_state && rm.energy_state.alert_worthy ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200 dark:bg-sky-950/40 dark:text-sky-300">
                        AC ON (Idle)
                      </span>
                    ) : rm.current_activity === "Fall_Detected" ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/40 dark:text-rose-300">
                        Fall Risk Watch
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Nominal</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-slate-700 dark:text-slate-300">
                    {Math.round((rm.model_confidence || 0.95) * 100)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
