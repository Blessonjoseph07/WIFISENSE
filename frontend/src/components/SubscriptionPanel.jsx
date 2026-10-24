import React, { useState, useEffect, useCallback } from "react";
import { API_BASE } from "../config";

const STATUS_STYLE = {
  ACTIVE: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  PAST_DUE: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  PENDING: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  CANCELLED: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  EXPIRED: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
  SUSPENDED: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300",
};

const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" }) : "-");
const fmtPrice = (p) => (p ? `${(p.amount_minor / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })} ${p.currency}` : "-");

/**
 * Family subscription (CARE_MONTHLY) with the SANDBOX payment provider.
 * Nothing here is a real payment: the sandbox "checkout" is two buttons that pick an outcome, and the result still
 * arrives through the same signed-webhook path a real provider would use. No card details are entered or stored.
 */
export default function SubscriptionPanel({ token, setToastMessage = () => {}, onChanged = () => {} }) {
  const [data, setData] = useState(null);
  const [checkout, setCheckout] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/payments/subscription`, { headers });
      if (res.ok) {
        setData(await res.json());
        setError("");
      } else {
        setError("Subscription details could not be loaded.");
      }
    } catch {
      setError("Subscription details could not be loaded (network).");
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (path, body, okText) => {
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: body ? JSON.stringify(body) : undefined });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (res.status === 404) {
          setCheckout(null);
        }
        setToastMessage({ type: "error", text: json.detail || "That did not work." });
        return null;
      }
      setData((d) => ({ ...(d || {}), ...json, connection_approved: true }));
      if (okText) setToastMessage({ type: "success", text: okText });
      onChanged();
      return json;
    } catch {
      setToastMessage({ type: "error", text: "Network error." });
      return null;
    } finally {
      setBusy(false);
    }
  };

  const loadRazorpayScript = () =>
    new Promise((resolve, reject) => {
      if (window.Razorpay) return resolve();
      const el = document.createElement("script");
      el.src = "https://checkout.razorpay.com/v1/checkout.js";
      el.onload = resolve;
      el.onerror = () => reject(new Error("Could not load Razorpay Checkout. Check the internet connection."));
      document.body.appendChild(el);
    });

  // Razorpay Checkout is Razorpay's own page: card, UPI and bank details are typed there and never reach this app. When it finishes, the
  // browser sends only the order id, payment id and signature; the server checks the signature AND asks Razorpay about the payment.
  const openRazorpay = async (c) => {
    try {
      await loadRazorpayScript();
    } catch (e) {
      setToastMessage({ type: "error", text: e.message });
      return;
    }
    const rzp = new window.Razorpay({
      key: c.key_id,
      amount: c.amount_minor,
      currency: c.currency,
      order_id: c.order_id,
      name: c.name,
      description: c.description,
      prefill: c.prefill,
      theme: { color: "#0d9488" },
      handler: async (resp) => {
        const json = await act("/payments/razorpay/verify", {
          razorpay_order_id: resp.razorpay_order_id,
          razorpay_payment_id: resp.razorpay_payment_id,
          razorpay_signature: resp.razorpay_signature,
        }, null);
        if (json) setToastMessage({ type: "success", text: "Payment confirmed. Your Care Plan is active." });
      },
      modal: { ondismiss: () => setToastMessage({ type: "info", text: "Checkout closed. You have not been charged." }) },
    });
    rzp.on("payment.failed", (r) => setToastMessage({ type: "error", text: `Payment failed: ${r?.error?.description || "the bank declined it"}. You can try again.` }));
    rzp.open();
  };

  const startCheckout = async () => {
    const json = await act("/payments/checkout", null, null);
    if (!json?.checkout) return;
    if (json.checkout.provider === "razorpay") openRazorpay(json.checkout);
    else setCheckout(json.checkout);
  };

  const completeCheckout = async (outcome) => {
    const json = await act(`/payments/sandbox/checkout/${checkout.id}/complete`, { outcome }, null);
    if (json) {
      setCheckout(null);
      setToastMessage(
        outcome === "success"
          ? { type: "success", text: "Payment successful. Your subscription is active." }
          : { type: "error", text: "Payment failed. You can try again." }
      );
    }
  };

  const cancel = async () => {
    const end = fmtDate(data?.subscription?.current_period_end);
    if (!window.confirm(`Cancel at the end of the paid period?\n\nYou keep the optional features until ${end}. Emergency alerts are never affected. You can resume before then.`)) return;
    await act("/payments/cancel", null, "Cancellation scheduled for the end of the paid period.");
  };

  const resume = () => act("/payments/resume", null, "Subscription resumed.");

  if (error && !data) return <div className="text-xs text-slate-500">{error}</div>;
  if (!data) return null;

  const sub = data.subscription;
  const status = sub?.status || "NONE";
  const actions = sub?.actions;
  const canSubscribe = data.connection_approved && (!sub || actions?.can_subscribe);
  const isRazorpay = data.provider === "razorpay";

  return (
    <div className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xs" data-testid="subscription-panel">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-base font-black text-slate-900 dark:text-white">Care Plan subscription</h2>
            <span className="inline-flex items-center" title={data.mode === "RAZORPAY_LIVE" ? "Payments are processed by Razorpay" : "Payments run in test mode"} data-testid="payment-mode-dot">
              <span className="w-2.5 h-2.5 rounded-full inline-block shadow-[0_0_0_3px_rgba(148,163,184,0.18)]"
                    style={{ background: data.mode === "RAZORPAY_LIVE" ? "#10b981" : "#f59e0b" }} aria-hidden="true" />
              <span className="sr-only">{data.mode}</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {data.plan?.plan} - {fmtPrice(data.plan)} for {data.plan?.period_days} days.
          </p>
        </div>
        <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold uppercase ${STATUS_STYLE[status] || STATUS_STYLE.PENDING}`}>
          {status === "NONE" ? "NOT SUBSCRIBED" : status.replace("_", " ")}
        </span>
      </div>

      {sub && (
        <dl className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-xs">
          <div><dt className="text-slate-400">Paid until</dt><dd className="font-bold text-slate-800 dark:text-slate-200">{fmtDate(sub.current_period_end)}</dd></div>
          <div><dt className="text-slate-400">Next renewal</dt><dd className="font-bold text-slate-800 dark:text-slate-200">{sub.cancel_at_period_end ? "None (cancelling)" : fmtDate(sub.renewal_date)}</dd></div>
          <div><dt className="text-slate-400">Last payment</dt><dd className="font-bold text-slate-800 dark:text-slate-200">{sub.last_payment_status || "-"}</dd></div>
          {sub.grace_until && <div><dt className="text-slate-400">Grace period ends</dt><dd className="font-bold text-amber-700 dark:text-amber-300">{fmtDate(sub.grace_until)}</dd></div>}
        </dl>
      )}

      {sub?.cancel_at_period_end && (
        <p className="mt-3 text-xs rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 px-3 py-2">
          Set to end on {fmtDate(sub.current_period_end)}. Optional features continue until then.
        </p>
      )}
      {status === "PAST_DUE" && (
        <p className="mt-3 text-xs rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300 px-3 py-2">
          The last renewal did not go through. Features continue during a short grace period; after that the subscription expires.
        </p>
      )}
      {status === "SUSPENDED" && (
        <p className="mt-3 text-xs rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 px-3 py-2">
          This subscription is on hold by the care facility. Payments do not lift a hold - please contact the facility.
        </p>
      )}
      {sub?.access_note && status !== "SUSPENDED" && !sub.cancel_at_period_end && <p className="mt-3 text-xs text-slate-500">{sub.access_note}</p>}

      <p className="mt-3 text-[11px] text-slate-500 dark:text-slate-400">
        A subscription only controls optional portal features. It never gives access to a resident - the facility approves that - and
        emergency alerts for your approved resident never depend on it.
      </p>

      {!data.connection_approved && (
        <p className="mt-3 text-xs text-slate-600 dark:text-slate-300">You can subscribe once the facility has approved your connection to a resident.</p>
      )}

      <div className="flex flex-wrap gap-2 mt-4">
        {isRazorpay ? (
          canSubscribe && (
            <button disabled={busy} onClick={startCheckout} className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer" data-testid="pay-with-razorpay">
              {`Pay ${fmtPrice(data.plan)} with Razorpay`}
            </button>
          )
        ) : data.simulator_enabled === false ? (
          <div className="w-full text-xs rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 px-3 py-2">
            Online payment is not available right now.
          </div>
        ) : (
          canSubscribe && !checkout && (
            <button disabled={busy} onClick={startCheckout} className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer">
              {sub ? "Subscribe again" : "Subscribe"}
            </button>
          )
        )}
        {actions?.can_cancel && (
          <button disabled={busy} onClick={cancel} className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 cursor-pointer">
            Cancel at period end
          </button>
        )}
        {actions?.can_resume && (
          <button disabled={busy} onClick={resume} className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer">
            Resume subscription
          </button>
        )}
      </div>

      {isRazorpay && data.mode === "RAZORPAY_TEST" && canSubscribe && (
        <details className="mt-3 text-[11px] text-slate-400" data-testid="razorpay-test-hint">
          <summary className="cursor-pointer">Payment test details</summary>
          <p className="mt-1">Test card 4111 1111 1111 1111, any future expiry date and any 3-digit CVV, or the UPI id success@razorpay.</p>
        </details>
      )}

      {checkout && !isRazorpay && data.simulator_enabled !== false && (
        <div className="mt-4 rounded-xl border-2 border-dashed border-violet-300 dark:border-violet-800 bg-violet-50/60 dark:bg-violet-950/30 p-4">
          <p className="text-xs font-bold text-violet-900 dark:text-violet-200">Checkout - {fmtPrice(checkout)}</p>
          <div className="flex flex-wrap gap-2 mt-3">
            <button disabled={busy} onClick={() => completeCheckout("success")} className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer">Complete payment</button>
            <button disabled={busy} onClick={() => completeCheckout("failure")} className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer">Decline payment</button>
            <button disabled={busy} onClick={() => setCheckout(null)} className="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 cursor-pointer">Close</button>
          </div>
        </div>
      )}

      {data.simulator_enabled !== false && sub?.provider && status !== "SUSPENDED" && sub.current_period_end && (
        <details className="mt-4 text-xs">
          <summary className="cursor-pointer text-slate-500 font-semibold">Renewal tools</summary>
          <div className="flex flex-wrap gap-2 mt-2">
            <button disabled={busy} onClick={() => act("/payments/sandbox/simulate", { event: "renewal_succeeded" }, "Renewal received.")} className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 font-bold cursor-pointer">Renewal paid</button>
            <button disabled={busy} onClick={() => act("/payments/sandbox/simulate", { event: "renewal_failed" }, "Renewal failed.")} className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 font-bold cursor-pointer">Renewal failed</button>
            <button disabled={busy} onClick={() => act("/payments/sandbox/simulate", { event: "provider_cancelled" }, "Subscription cancelled by the provider.")} className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 font-bold cursor-pointer">Cancelled at provider</button>
          </div>
        </details>
      )}
    </div>
  );
}
