// Run with: npm test   (uses Node's built-in test runner; no browser needed)
import assert from "node:assert/strict";
import { test } from "node:test";

import { SESSION_KEYS, createSessionGuard } from "../src/session.js";

const BASE = "http://api.test";

function makeStorage(initial = {}) {
  const data = { ...initial };
  return {
    data,
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => {
      data[k] = String(v);
    },
    removeItem: (k) => {
      delete data[k];
    },
  };
}

const json = (status, body) => ({ status, ok: status >= 200 && status < 300, json: async () => body });

function setup({ routes, storage }) {
  const calls = [];
  const fetchImpl = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const auth = init.headers && (init.headers.Authorization || init.headers.authorization);
    calls.push({ url, auth, method: init.method || "GET" });
    const handler = routes[url.replace(BASE, "")] || routes["*"];
    return handler({ url, auth, init, n: calls.filter((c) => c.url === url).length });
  };
  const events = { expired: 0, refreshed: [] };
  const guard = createSessionGuard({
    apiBase: BASE,
    storage,
    fetchImpl,
    onExpired: () => {
      events.expired += 1;
    },
    onRefreshed: (t) => events.refreshed.push(t),
  });
  return { guard, calls, events };
}

const loggedIn = () => makeStorage({ token: "old", refresh_token: "r1", user: "{}", role: "caregiver" });

test("requests to other hosts are passed through untouched", async () => {
  const storage = loggedIn();
  const { guard, calls, events } = setup({ routes: { "*": () => json(401, {}) }, storage });
  const res = await guard.fetch("https://fonts.example.com/x", { headers: { Authorization: "Bearer old" } });
  assert.equal(res.status, 401);
  assert.equal(calls.length, 1);
  assert.equal(events.expired, 0);
  assert.equal(storage.getItem("token"), "old");
});

test("a normal success or a non-401 error is returned as is", async () => {
  const storage = loggedIn();
  const { guard, calls, events } = setup({
    routes: { "/ok": () => json(200, { a: 1 }), "/forbidden": () => json(403, {}), "/boom": () => json(500, {}) },
    storage,
  });
  for (const [path, status] of [["/ok", 200], ["/forbidden", 403], ["/boom", 500]]) {
    const res = await guard.fetch(`${BASE}${path}`, { headers: { Authorization: "Bearer old" } });
    assert.equal(res.status, status);
  }
  assert.equal(calls.length, 3, "no refresh or retry for non-401 responses");
  assert.equal(events.expired, 0);
});

test("401 without a token is not treated as an expired session", async () => {
  const storage = loggedIn();
  const { guard, calls, events } = setup({ routes: { "*": () => json(401, {}) }, storage });
  const res = await guard.fetch(`${BASE}/public`, {});
  assert.equal(res.status, 401);
  assert.equal(calls.length, 1);
  assert.equal(events.expired, 0);
});

test("login, register, refresh and logout are never intercepted", async () => {
  for (const path of ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"]) {
    const storage = loggedIn();
    const { guard, calls, events } = setup({ routes: { "*": () => json(401, { detail: "Incorrect email or password." }) }, storage });
    const res = await guard.fetch(`${BASE}${path}`, { method: "POST", headers: { Authorization: "Bearer old" } });
    assert.equal(res.status, 401, path);
    assert.equal(calls.length, 1, path);
    assert.equal(events.expired, 0, path);
    assert.equal(storage.getItem("token"), "old", path);
  }
});

test("expired access token: refresh once, store new tokens, retry with the new token", async () => {
  const storage = loggedIn();
  const { guard, calls, events } = setup({
    routes: {
      "/residents": ({ auth }) => (auth === "Bearer new" ? json(200, [{ id: 1 }]) : json(401, { detail: "expired" })),
      "/auth/refresh": () => json(200, { access_token: "new", refresh_token: "r2" }),
    },
    storage,
  });
  const res = await guard.fetch(`${BASE}/residents`, { headers: { Authorization: "Bearer old" } });
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), [{ id: 1 }]);
  assert.equal(storage.getItem("token"), "new");
  assert.equal(storage.getItem("refresh_token"), "r2", "rotated refresh token is stored");
  assert.deepEqual(events.refreshed, ["new"]);
  assert.equal(events.expired, 0);
  assert.deepEqual(calls.map((c) => c.url.replace(BASE, "")), ["/residents", "/auth/refresh", "/residents"]);
});

test("refresh fails: the stored login is cleared and the app is told exactly once", async () => {
  const storage = loggedIn();
  const { guard, events } = setup({
    routes: { "/auth/refresh": () => json(401, { detail: "invalid" }), "*": () => json(401, { detail: "expired" }) },
    storage,
  });
  const results = await Promise.all(
    Array.from({ length: 6 }, (_, i) => guard.fetch(`${BASE}/alerts?i=${i}`, { headers: { Authorization: "Bearer old" } }))
  );
  assert.ok(results.every((r) => r.status === 401), "callers still see the 401");
  assert.equal(events.expired, 1, "six simultaneous 401s produce ONE sign-out");
  for (const k of SESSION_KEYS) assert.equal(storage.getItem(k), null, `${k} cleared`);
});

test("concurrent 401s share one refresh call", async () => {
  const storage = loggedIn();
  let refreshCalls = 0;
  const { guard, events } = setup({
    routes: {
      "/auth/refresh": async () => {
        refreshCalls += 1;
        await new Promise((r) => setTimeout(r, 15));
        return json(200, { access_token: "new", refresh_token: "r2" });
      },
      "*": ({ auth }) => (auth === "Bearer new" ? json(200, {}) : json(401, {})),
    },
    storage,
  });
  const results = await Promise.all(
    Array.from({ length: 5 }, (_, i) => guard.fetch(`${BASE}/x${i}`, { headers: { Authorization: "Bearer old" } }))
  );
  assert.ok(results.every((r) => r.status === 200));
  assert.equal(refreshCalls, 1, "refresh tokens rotate, so a second parallel refresh would fail");
  assert.deepEqual(events.refreshed, ["new"]);
});

test("no refresh token stored: sign out straight away", async () => {
  const storage = makeStorage({ token: "old", user: "{}" });
  const { guard, calls, events } = setup({ routes: { "*": () => json(401, {}) }, storage });
  await guard.fetch(`${BASE}/alerts`, { headers: { Authorization: "Bearer old" } });
  assert.equal(events.expired, 1);
  assert.equal(calls.some((c) => c.url.endsWith("/auth/refresh")), false);
  assert.equal(storage.getItem("token"), null);
});

test("a late 401 after the user signed out is not reported as an expired session", async () => {
  const storage = makeStorage({});
  const { guard, calls, events } = setup({ routes: { "*": () => json(401, {}) }, storage });
  const res = await guard.fetch(`${BASE}/alerts`, { headers: { Authorization: "Bearer old" } });
  await guard.fetch(`${BASE}/rooms`, { headers: { Authorization: "Bearer " } });
  assert.equal(res.status, 401);
  assert.equal(events.expired, 0);
  assert.equal(calls.some((c) => c.url.endsWith("/auth/refresh")), false);
});

test("still 401 after a successful refresh: sign out (no endless retrying)", async () => {
  const storage = loggedIn();
  const { guard, calls, events } = setup({
    routes: { "/auth/refresh": () => json(200, { access_token: "new", refresh_token: "r2" }), "*": () => json(401, {}) },
    storage,
  });
  const res = await guard.fetch(`${BASE}/alerts`, { headers: { Authorization: "Bearer old" } });
  assert.equal(res.status, 401);
  assert.equal(events.expired, 1);
  assert.equal(calls.filter((c) => c.url.endsWith("/alerts")).length, 2, "exactly one retry");
});

test("a slow request that used an old token after a refresh is retried, not treated as expiry", async () => {
  const storage = makeStorage({ token: "newer", refresh_token: "r2" });
  const { guard, calls, events } = setup({
    routes: { "*": ({ auth }) => (auth === "Bearer newer" ? json(200, {}) : json(401, {})) },
    storage,
  });
  const res = await guard.fetch(`${BASE}/alerts`, { headers: { Authorization: "Bearer stale" } });
  assert.equal(res.status, 200);
  assert.equal(events.expired, 0);
  assert.equal(calls.some((c) => c.url.endsWith("/auth/refresh")), false, "no refresh needed");
});

test("after signing in again a later expiry is reported again", async () => {
  const storage = loggedIn();
  const { guard, events } = setup({ routes: { "/auth/refresh": () => json(401, {}), "*": () => json(401, {}) }, storage });
  await guard.fetch(`${BASE}/a`, { headers: { Authorization: "Bearer old" } });
  assert.equal(events.expired, 1);
  storage.setItem("token", "t2");
  storage.setItem("refresh_token", "r9");
  guard.markSignedIn();
  await guard.fetch(`${BASE}/b`, { headers: { Authorization: "Bearer t2" } });
  assert.equal(events.expired, 2);
});

test("headers given as a Headers-like object keep their other fields on retry", async () => {
  const storage = loggedIn();
  const seen = [];
  const { guard } = setup({
    routes: {
      "/auth/refresh": () => json(200, { access_token: "new", refresh_token: "r2" }),
      "/x": ({ auth, init }) => {
        seen.push({ auth, ct: init.headers["Content-Type"] || init.headers["content-type"] });
        return auth === "Bearer new" ? json(200, {}) : json(401, {});
      },
    },
    storage,
  });
  const h = new Map([["Authorization", "Bearer old"], ["Content-Type", "application/json"]]);
  await guard.fetch(`${BASE}/x`, { method: "POST", body: "{}", headers: {
      // like the real Headers class, lookups are case-insensitive
      get: (k) => [...h.entries()].find(([key]) => key.toLowerCase() === k.toLowerCase())?.[1] ?? null,
      forEach: (cb) => h.forEach((v, k) => cb(v, k)),
    },
  });
  assert.equal(seen.at(-1).auth, "Bearer new");
  assert.equal(seen.at(-1).ct, "application/json");
});
