import React, { useCallback, useEffect, useState } from "react";
import { SourceBadge } from "./DetectionBadges";

const POLL_MS = 20000;
const KEY = "dismissedBookingReminders";

const readDismissed = () => {
  try {
    return JSON.parse(sessionStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
};

/**
 * Five-minute "please vacate" reminder for corporate users. It shows what the server reports for the caller's
 * organization; nothing is generated here. Each reminder can be dismissed for this browser session.
 */
export default function BookingReminders({ authToken, API_BASE, onOpenSchedule }) {
  const [reminders, setReminders] = useState([]);
  const [dismissed, setDismissed] = useState(readDismissed);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/bookings/reminders`, { headers: { Authorization: `Bearer ${authToken}` } });
      if (res.ok) setReminders(await res.json());
    } catch {
      /* a missed poll is retried on the next tick */
    }
  }, [API_BASE, authToken]);

  useEffect(() => {
    const first = setTimeout(load, 0);
    const t = setInterval(load, POLL_MS);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [load]);

  const dismiss = (id) => {
    const next = [...dismissed, id];
    setDismissed(next);
    try {
      sessionStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* storage can be blocked; the banner just returns on reload */
    }
  };

  const shown = reminders.filter((r) => !dismissed.includes(r.booking_id));
  if (!shown.length) return null;

  return (
    <div className="space-y-2" role="alert" data-testid="booking-reminders">
      {shown.map((r) => (
        <div key={r.booking_id} className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-800">
          <div className="flex items-start gap-3 min-w-0">
            <span className="material-symbols-outlined text-amber-600 text-2xl">event_busy</span>
            <div className="min-w-0">
              <div className="text-xs font-bold uppercase tracking-wide">
                {r.minutes_until_start === 0 ? "Booking starts now" : `Booking starts in ${r.minutes_until_start} min`}
              </div>
              <div className="text-sm font-semibold break-words">{r.message}</div>
              {r.occupied_now !== null && r.occupied_now !== undefined && (
                <div className="text-xs mt-1 flex items-center gap-2">
                  {r.occupied_now ? "The room currently appears occupied." : "The room currently appears empty."}
                  {r.occupancy_source && <SourceBadge source={r.occupancy_source} />}
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onOpenSchedule && (
              <button type="button" onClick={onOpenSchedule} className="px-3 py-1.5 rounded-lg border border-amber-400 text-xs font-bold hover:bg-amber-100 dark:hover:bg-amber-900/40 cursor-pointer">View schedule</button>
            )}
            <button type="button" onClick={() => dismiss(r.booking_id)} className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold cursor-pointer">Got it</button>
          </div>
        </div>
      ))}
    </div>
  );
}
