import React, { useCallback, useEffect, useMemo, useState } from "react";

const card = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm";
const input = "w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500";

const pad = (n) => String(n).padStart(2, "0");
const toDateInput = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const toTimeInput = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const fmtTime = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const fmtDay = (iso) => new Date(iso).toLocaleDateString([], { weekday: "long", day: "numeric", month: "short" });

function defaultSlot() {
  const d = new Date();
  d.setMinutes(Math.ceil((d.getMinutes() + 10) / 5) * 5, 0, 0);
  const end = new Date(d.getTime() + 60 * 60 * 1000);
  return { date: toDateInput(d), start: toTimeInput(d), end: toTimeInput(end) };
}

export default function RoomBookingsView({ authToken, API_BASE, rooms = [], canManage = false }) {
  const [bookings, setBookings] = useState(null);
  const [now, setNow] = useState(0);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showCancelled, setShowCancelled] = useState(false);
  const [roomFilter, setRoomFilter] = useState("");
  const [cancelling, setCancelling] = useState(null); // { id, reason }
  const [form, setForm] = useState(() => ({ room_id: "", purpose: "", ...defaultSlot() }));

  const headers = useMemo(() => ({ Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" }), [authToken]);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/bookings`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setBookings(await res.json());
      setNow(Date.now());
      setError(null);
    } catch (e) {
      setError(`Could not load bookings (${e.message}).`);
    }
  }, [API_BASE, headers]);

  useEffect(() => {
    const first = setTimeout(load, 0);
    const t = setInterval(load, 30000);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [load]);

  const roomId = form.room_id || rooms[0]?.id || "";

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    const start = new Date(`${form.date}T${form.start}`);
    const end = new Date(`${form.date}T${form.end}`);
    if (!(end > start)) {
      setError("The end time must be after the start time.");
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/bookings`, {
        method: "POST",
        headers,
        body: JSON.stringify({ room_id: roomId, purpose: form.purpose.trim(), start_at: start.toISOString(), end_at: end.toISOString() }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join(", ") : body.detail;
        throw new Error(detail || `HTTP ${res.status}`);
      }
      setNotice(`Booked ${body.room_name} ${fmtTime(body.start_at)}–${fmtTime(body.end_at)}. Corporate staff will be reminded 5 minutes before it starts.`);
      setForm((f) => ({ ...f, purpose: "" }));
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const confirmCancel = async () => {
    if (!cancelling) return;
    try {
      const res = await fetch(`${API_BASE}/bookings/${cancelling.id}/cancel`, {
        method: "POST",
        headers,
        body: JSON.stringify({ reason: cancelling.reason || null }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setNotice("Booking cancelled. The room is free for that time again.");
      setCancelling(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const visible = (bookings || [])
    .filter((b) => (showCancelled ? true : b.status === "BOOKED"))
    .filter((b) => (roomFilter ? b.room_id === roomFilter : true));
  const byDay = visible.reduce((acc, b) => {
    const k = fmtDay(b.start_at);
    (acc[k] = acc[k] || []).push(b);
    return acc;
  }, {});

  return (
    <div className="space-y-6 text-left" data-testid="room-bookings">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Room Scheduling</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {canManage
            ? "Reserve a room for a time and purpose. Cancel a booking if the meeting is called off. Corporate staff are reminded 5 minutes before a booking starts."
            : "Upcoming room bookings. You will see a reminder 5 minutes before a booking starts in the room you are using."}
        </p>
      </div>

      {error && <div className="p-3 rounded-xl bg-red-50 text-red-700 border border-red-200 text-sm font-medium" role="alert">{error}</div>}
      {notice && <div className="p-3 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-sm font-medium" role="status">{notice}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {canManage && (
          <form onSubmit={submit} className={`${card} p-5 space-y-4 xl:col-span-1 self-start`}>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">New booking</h3>
            <div>
              <label htmlFor="bk-room" className="text-xs font-semibold text-slate-600 dark:text-slate-300">Room</label>
              <select id="bk-room" className={input} value={roomId} onChange={(e) => setForm({ ...form, room_id: e.target.value })} required>
                {rooms.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="bk-purpose" className="text-xs font-semibold text-slate-600 dark:text-slate-300">Purpose</label>
              <input id="bk-purpose" className={input} value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                placeholder="e.g. Department review meeting" minLength={3} maxLength={200} required />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-3 sm:col-span-1">
                <label htmlFor="bk-date" className="text-xs font-semibold text-slate-600 dark:text-slate-300">Date</label>
                <input id="bk-date" type="date" className={input} value={form.date} min={toDateInput(new Date())} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
              </div>
              <div className="col-span-3 sm:col-span-1">
                <label htmlFor="bk-start" className="text-xs font-semibold text-slate-600 dark:text-slate-300">From</label>
                <input id="bk-start" type="time" className={input} value={form.start} onChange={(e) => setForm({ ...form, start: e.target.value })} required />
              </div>
              <div className="col-span-3 sm:col-span-1">
                <label htmlFor="bk-end" className="text-xs font-semibold text-slate-600 dark:text-slate-300">To</label>
                <input id="bk-end" type="time" className={input} value={form.end} onChange={(e) => setForm({ ...form, end: e.target.value })} required />
              </div>
            </div>
            <button type="submit" disabled={saving || !roomId}
              className="w-full px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-bold cursor-pointer transition-colors">
              {saving ? "Booking…" : "Book room"}
            </button>
            <p className="text-[11px] text-slate-400">Times are in your local time zone. A room cannot be double-booked.</p>
          </form>
        )}

        <div className={`${canManage ? "xl:col-span-2" : "xl:col-span-3"} space-y-4 min-w-0`}>
          <div className="flex flex-wrap items-center gap-3">
            <select aria-label="Filter by room" className={`${input} max-w-xs`} value={roomFilter} onChange={(e) => setRoomFilter(e.target.value)}>
              <option value="">All rooms</option>
              {rooms.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-600 dark:text-slate-300 cursor-pointer">
              <input type="checkbox" checked={showCancelled} onChange={(e) => setShowCancelled(e.target.checked)} />
              Show cancelled
            </label>
          </div>

          {bookings === null ? (
            <div className={`${card} p-8`}><div className="h-24 rounded-xl bg-slate-100 dark:bg-slate-800/50 animate-pulse" /></div>
          ) : visible.length === 0 ? (
            <div className={`${card} p-10 text-center text-sm text-slate-500`}>
              <span className="material-symbols-outlined text-4xl text-slate-300 block mb-2">event_available</span>
              No upcoming bookings{roomFilter ? " for this room" : ""}.{canManage ? " Use the form to reserve one." : ""}
            </div>
          ) : (
            Object.entries(byDay).map(([day, list]) => (
              <section key={day} className={`${card} overflow-hidden`}>
                <h3 className="px-5 py-3 text-xs font-bold uppercase tracking-wide text-slate-500 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800">{day}</h3>
                <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                  {list.map((b) => {
                    const startMs = new Date(b.start_at).getTime();
                    const endMs = new Date(b.end_at).getTime();
                    const cancelled = b.status === "CANCELLED";
                    const live = !cancelled && startMs <= now && now < endMs;
                    const soon = !cancelled && startMs > now && startMs - now <= 5 * 60 * 1000;
                    const ended = !cancelled && endMs <= now;
                    return (
                      <li key={b.id} className={`px-5 py-4 flex flex-wrap items-start justify-between gap-3 ${cancelled || ended ? "opacity-60" : ""}`}>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-sm font-semibold text-slate-900 dark:text-white">{fmtTime(b.start_at)}–{fmtTime(b.end_at)}</span>
                            <span className="font-semibold text-slate-800 dark:text-slate-200">{b.room_name}</span>
                            {live && <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">IN PROGRESS</span>}
                            {soon && <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold">STARTS SOON</span>}
                            {ended && <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold">ENDED</span>}
                            {cancelled && <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold">CANCELLED</span>}
                          </div>
                          <div className="text-sm text-slate-700 dark:text-slate-300 mt-0.5 break-words">{b.purpose}</div>
                          <div className="text-xs text-slate-500 mt-0.5">Booked by {b.organizer_name}{cancelled && b.cancel_reason ? ` · cancelled: ${b.cancel_reason}` : ""}</div>
                        </div>
                        {canManage && !cancelled && !ended && (
                          cancelling?.id === b.id ? (
                            <div className="flex flex-wrap items-center gap-2">
                              <input aria-label="Cancellation reason" className={`${input} w-48`} placeholder="Reason (optional)" maxLength={200}
                                value={cancelling.reason} onChange={(e) => setCancelling({ ...cancelling, reason: e.target.value })} />
                              <button type="button" onClick={confirmCancel} className="px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold cursor-pointer">Confirm cancel</button>
                              <button type="button" onClick={() => setCancelling(null)} className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 cursor-pointer">Keep</button>
                            </div>
                          ) : (
                            <button type="button" onClick={() => setCancelling({ id: b.id, reason: "" })}
                              className="px-3 py-1.5 rounded-lg border border-rose-200 text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/30 text-xs font-bold cursor-pointer">
                              Cancel booking
                            </button>
                          )
                        )}
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
