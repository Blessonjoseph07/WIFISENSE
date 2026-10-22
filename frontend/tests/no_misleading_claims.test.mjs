// Guards truthfulness: the UI must not claim live / real-time sensing it does not have, and must not invent values.
// Demo, dataset-replay and live data are shown with their own labels (see src/components/DetectionBadges.jsx).
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const walk = (dir) =>
  readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
const files = walk(SRC).filter((f) => /\.(jsx?|mjs)$/.test(f));

// phrase -> why it is forbidden
const FORBIDDEN = [
  [/real-?\s?time/i, "claims real-time sensing"],
  [/Live (Feed|CSI|Telemetry|Occupied|Incident|platform|Sensing|portal)/, "claims live data where the source is demo, replay or unknown"],
  [/System Live/, "claims the system is live"],
  [/Corporate Facility Engine Live/, "claims the engine is live"],
  [/Nominal \(No Falls\)/, "invented fall-safety statement"],
  [/RF Doppler Watch/, "invented monitoring claim"],
  [/99\.4% Stability|98\.9% conf|Gait: Stable/, "hard-coded measurements"],
  [/nominal_resting|Nominal Resting in Room|Gentle Room Ambulation/, "invented activity shown as if sensed"],
  [/\|\|\s*0\.9\d?\b/, "invents a confidence value when none was measured"],
  [/\b56 SC\b|-47 dBm\s*•|94% SQ/, "hard-coded signal figures"],
  [/RF Engine: ONLINE|Wi-Fi 6 Continuous|Dual-Band CSI Modem|Spherical Doppler/, "hard-coded status or hardware claims (the target ESP32-S3 is single-band 2.4 GHz)"],
  [/251122|RF Sensing:|Elder Care Station Hotline/, "invented care-desk phone number or sensing status"],
];

// Comments are not shown to users, so only the code and the text on screen are checked.
const stripComments = (text) => text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`])\/\/.*$/gm, "$1");

test("no source file contains a misleading live / real-time claim or an invented value", () => {
  const offenders = [];
  for (const f of files) {
    const text = stripComments(readFileSync(f, "utf8"));
    for (const [re, why] of FORBIDDEN) {
      const m = text.match(re);
      if (m) offenders.push(`${relative(SRC, f)}: "${m[0]}" (${why})`);
    }
  }
  assert.deepEqual(offenders, [], `\n${offenders.join("\n")}`);
});

test("the three data modes have their own labels", () => {
  const badges = readFileSync(join(SRC, "components", "DetectionBadges.jsx"), "utf8");
  for (const label of ["DEMO", "DATASET REPLAY", "LIVE HARDWARE"]) {
    assert.ok(badges.includes(`label: "${label}"`), `missing label ${label}`);
  }
});

test("model scores are never presented as High / Medium / Low confidence or as Reliable", () => {
  const badges = readFileSync(join(SRC, "components", "DetectionBadges.jsx"), "utf8");
  assert.match(badges, /uncalibrated/, "model scores must be shown as uncalibrated");
  assert.match(badges, /if \(model\) return \{ label: "Uncertain"/, "model output must map to Uncertain, never Reliable");
});
