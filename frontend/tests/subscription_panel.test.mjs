// Guards the Family Subscription (SANDBOX) frontend integration:
// 1. A quiet payment-mode dot (no loud banners)
// 2. Staff control sending only SUSPENDED and ACTIVE (never PENDING)
// 3. Emergency alerts visible regardless of subscription status
// 4. SubscriptionPanel import & mount in FamilyPortalView
// 5. Configured API_BASE usage (no hardcoded hosts)
//
// NOTE ON VERIFICATION TYPE:
// All tests in this suite scan and verify the actual source code patterns (source text scans).
// They do NOT instantiate a virtual DOM or headless browser, and should be reported as source-level regression guards.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PANEL_SRC = join(ROOT, "src", "components", "SubscriptionPanel.jsx");
const PORTAL_SRC = join(ROOT, "src", "views", "FamilyPortalView.jsx");

test("[Source Scan] SubscriptionPanel marks the payment mode with a quiet dot, not loud wording", () => {
  const code = readFileSync(PANEL_SRC, "utf8");
  // The mode is still identified: a coloured dot with a tooltip and screen-reader text carrying the mode name.
  assert.ok(code.includes('data-testid="payment-mode-dot"'), "SubscriptionPanel must render the payment-mode dot");
  assert.ok(code.includes("{data.mode}"), "the mode name must stay available as screen-reader text");
  // ... and the loud banners are gone (the owner asked for a calm UI), while no false claim replaces them.
  for (const loud of ["SANDBOX - no real payment", "no real money", "SANDBOX checkout", "No card details are collected or stored"]) {
    assert.ok(!code.includes(loud), `the panel must not shout: ${loud}`);
  }
  assert.ok(!/real payments? (are|is) (on|enabled)/i.test(code), "must not claim real payments");
});

test("[Source Scan] Staff subscription controls send ONLY SUSPENDED and ACTIVE, never PENDING", () => {
  const code = readFileSync(PORTAL_SRC, "utf8");
  // Check the staff control handler
  assert.match(
    code,
    /handleHoldToggle/,
    "FamilyPortalView must define handleHoldToggle for administrative holds"
  );
  assert.match(
    code,
    /currentStatus === "SUSPENDED" \? "ACTIVE" : "SUSPENDED"/,
    "handleHoldToggle must toggle strictly between SUSPENDED and ACTIVE"
  );
  // Ensure staff control does not send PENDING
  const staffHandlerMatch = code.match(/handleHoldToggle[\s\S]*?fetch\([^)]*subscriptions\/[^)]*\)[\s\S]*?\}/);
  assert.ok(staffHandlerMatch, "Staff subscription PATCH handler must be present");
  assert.ok(
    !staffHandlerMatch[0].includes('"PENDING"'),
    "Staff control must never send PENDING to the subscription PATCH endpoint"
  );
});

test("[Source Scan] Emergency alerts are visible independent of subscription status and deduplicated", () => {
  const code = readFileSync(PORTAL_SRC, "utf8");
  // Check that open alerts merge familyStatus.emergency.open_alerts and directAlerts with deduplication
  assert.ok(
    code.includes("familyStatus?.emergency?.open_alerts"),
    "FamilyPortalView must inspect familyStatus.emergency.open_alerts to guarantee emergency visibility without subscription"
  );
  assert.ok(
    code.includes("combinedAlerts"),
    "FamilyPortalView must compute combinedAlerts to include emergency alerts when not subscribed"
  );
  assert.ok(
    code.includes("alertsById") || code.includes("alertsMap"),
    "FamilyPortalView must merge and deduplicate directAlerts and emergencyOpenAlerts by id"
  );
  assert.ok(
    code.includes("isFallAlert"),
    "FamilyPortalView must strictly filter open fall alerts so non-fall alerts are not displayed as fall alerts"
  );
  assert.ok(
    code.includes("Activity timeline is an optional Care Plan feature"),
    "FamilyPortalView must explain optional telemetry gating while reassuring that emergency fall alerts are not gated"
  );
});

test("[Source Scan] FamilyPortalView imports and mounts SubscriptionPanel", () => {
  const code = readFileSync(PORTAL_SRC, "utf8");
  assert.match(
    code,
    /import\s+SubscriptionPanel\s+from\s+["']\.\.\/components\/SubscriptionPanel["']/,
    "FamilyPortalView must import SubscriptionPanel"
  );
  assert.match(
    code,
    /<SubscriptionPanel[\s\S]*?token=\{token\}[\s\S]*?\/>/,
    "FamilyPortalView must mount SubscriptionPanel passing token"
  );
});

test("[Source Scan] SubscriptionPanel uses configured API_BASE and contains no hardcoded hosts", () => {
  const code = readFileSync(PANEL_SRC, "utf8");
  assert.match(
    code,
    /import\s*\{\s*API_BASE\s*\}\s*from\s*["']\.\.\/config["']/,
    "SubscriptionPanel must import API_BASE from ../config"
  );
  const hostPattern = /127\.0\.0\.1|localhost:\d+|\/\/localhost\b/;
  assert.ok(
    !hostPattern.test(code),
    "SubscriptionPanel must not contain hardcoded host strings"
  );
});
