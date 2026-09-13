import React from "react";

export default function FacilityAssetsView({
  expandAllBuildings = () => {},
  organizations = [],
  setNewBldOrgId = () => {},
  setShowAddBuildingModal = () => {},
  isSystemAdmin = false,
  facilityFilter = "ALL",
  setFacilityFilter = () => {},
  buildings = [],
  floors = [],
  rooms = [],
  expandedBuildings = {},
  toggleBuildingExpand = () => {},
  setNewRmFlrId = () => {},
  setShowAddRoomModal = () => {},
  setNewFlrBldId = () => {},
  setShowAddFloorModal = () => {},
}) {
  return (
    <div className="space-y-6 text-left">
      {/* Facility Hierarchy view title */}
      <div className="mb-stack-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-headline-lg font-headline-lg text-slate-900 dark:text-white font-bold">
            Facility Config Manager
          </h2>
          <p className="text-body-md text-slate-500 dark:text-slate-400">
            Establish corporate and elder-care buildings, floors, and rooms configurations.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={expandAllBuildings}
            className="px-4 py-2 border border-slate-200 dark:border-slate-800 rounded text-xs font-bold uppercase hover:bg-slate-50 dark:hover:bg-slate-850 cursor-pointer"
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
            className="px-4 py-2 bg-teal-600 text-white rounded text-xs font-bold uppercase hover:bg-teal-700 shadow cursor-pointer"
          >
            Add Building
          </button>
        </div>
      </div>

      {/* Organization Filter Tabs (for System Admin) */}
      {isSystemAdmin && (
        <div className="mb-4 flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg self-start inline-flex">
          <button
            onClick={() => setFacilityFilter("ALL")}
            className={`px-3 py-1.5 text-xs font-bold rounded-md transition-colors cursor-pointer ${
              facilityFilter === "ALL"
                ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            All Facilities
          </button>
          <button
            onClick={() => setFacilityFilter("CORPORATE")}
            className={`px-3 py-1.5 text-xs font-bold rounded-md transition-colors flex items-center gap-1 cursor-pointer ${
              facilityFilter === "CORPORATE"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">corporate_fare</span>
            Corporate Workplace (AJCE)
          </button>
          <button
            onClick={() => setFacilityFilter("ELDER_CARE")}
            className={`px-3 py-1.5 text-xs font-bold rounded-md transition-colors flex items-center gap-1 cursor-pointer ${
              facilityFilter === "ELDER_CARE"
                ? "bg-emerald-600 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">health_and_safety</span>
            Old Age Care Home (St. Peter's)
          </button>
        </div>
      )}

      {/* Physical layout hierarchy card list */}
      <div className="space-y-4">
        {buildings
          .filter((bld) => {
            if (facilityFilter === "ALL") return true;
            const org = organizations.find((o) => o.id === bld.organization_id);
            if (!org) return true;
            return org.organization_type === facilityFilter;
          })
          .map((bld) => {
            const bldFloors = floors.filter((f) => f.building_id === bld.id);
            const isExpanded = expandedBuildings[bld.id];
            return (
              <div
                key={bld.id}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm"
              >
                <div
                  onClick={() => toggleBuildingExpand(bld.id)}
                  className="p-4 bg-slate-50 dark:bg-slate-950 flex items-center justify-between cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-teal-600 dark:text-teal-400">
                      corporate_fare
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">{bld.name}</span>
                    <span className="text-xs text-slate-500">({bld.address})</span>
                  </div>
                  <span className="material-symbols-outlined text-slate-400">
                    {isExpanded ? "expand_less" : "expand_more"}
                  </span>
                </div>

                {isExpanded && (
                  <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4">
                    {bldFloors.map((flr) => {
                      const flrRooms = rooms.filter((r) => r.floor_id === flr.id);
                      return (
                        <div
                          key={flr.id}
                          className="pl-6 border-l-2 border-slate-200 dark:border-slate-800 py-2 text-xs"
                        >
                          <div className="font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px] text-teal-500">
                              layers
                            </span>
                            Floor {flr.floor_number}
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                            {flrRooms.map((rm) => (
                              <div
                                key={rm.id}
                                className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded"
                              >
                                <div className="font-semibold text-slate-850 dark:text-white">
                                  {rm.name}
                                </div>
                                <div className="text-[10px] text-slate-500 uppercase mt-0.5">
                                  {rm.room_type}
                                </div>
                              </div>
                            ))}
                            <button
                              onClick={() => {
                                setNewRmFlrId(flr.id);
                                setShowAddRoomModal(true);
                              }}
                              className="p-3 border border-dashed border-slate-300 dark:border-slate-700 hover:border-teal-500 hover:text-teal-600 rounded flex items-center justify-center gap-1 font-bold text-slate-400 cursor-pointer"
                            >
                              <span className="material-symbols-outlined text-[16px]">add</span>{" "}
                              Add Room
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
                      className="bg-slate-50 dark:bg-slate-950 text-slate-650 hover:bg-slate-100 dark:hover:bg-slate-900 px-4 py-2 border rounded font-semibold text-xs flex items-center gap-1 cursor-pointer"
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
  );
}
