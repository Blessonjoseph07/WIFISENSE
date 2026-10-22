// Guards hosting: no component may hard-code where the API lives. Only src/config.js decides the API base.
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

test("no source file other than config.js contains a hard-coded API host", () => {
  const pattern = /127\.0\.0\.1|localhost:\d+|\/\/localhost\b/;
  const offenders = walk(SRC)
    .filter((f) => /\.(jsx?|mjs)$/.test(f) && !f.endsWith("config.js"))
    .filter((f) => pattern.test(readFileSync(f, "utf8")))
    .map((f) => relative(SRC, f));
  assert.deepEqual(offenders, [], `hard-coded hosts found in: ${offenders.join(", ")}`);
});

test("every file that calls the API imports API_BASE from the shared config or receives it as a prop", () => {
  const offenders = walk(SRC)
    .filter((f) => /\.(jsx?)$/.test(f) && !f.endsWith("config.js"))
    .filter((f) => {
      const text = readFileSync(f, "utf8");
      const usesBase = /\$\{API_BASE\}|API_BASE\s*\+/.test(text);
      const definesIt = /import\s*\{[^}]*API_BASE[^}]*\}\s*from\s*["'][./]*config["']/.test(text) || /\bAPI_BASE\b\s*[,=]/.test(text);
      return usesBase && !definesIt;
    })
    .map((f) => relative(SRC, f));
  assert.deepEqual(offenders, [], `API_BASE used without a source in: ${offenders.join(", ")}`);
});
