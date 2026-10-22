// Session guard: keeps an expired login from leaving a broken, half-empty screen.
//
// It wraps fetch. For a request to our API that carried a bearer token and came back 401 it:
//   1. tries ONE token refresh (all concurrent 401s share the same refresh call),
//   2. on success stores the new tokens and retries the original request once with the new token,
//   3. otherwise clears the stored login and tells the app once, so it can show the sign-in screen with a message.
// Login, registration, refresh and logout requests are never intercepted. Requests without a token are never
// intercepted. Nothing here handles passwords, and tokens only ever move between this code and localStorage.
//
// Dependencies are injected so the logic can be tested without a browser (see tests/session.test.mjs).

export const SESSION_KEYS = ["token", "refresh_token", "user", "role", "application_context", "is_system_admin"];
const SKIP_PATHS = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"];

function headerValue(headers, name) {
  if (!headers) return null;
  if (typeof headers.get === "function") return headers.get(name);
  if (Array.isArray(headers)) {
    const pair = headers.find(([k]) => String(k).toLowerCase() === name.toLowerCase());
    return pair ? pair[1] : null;
  }
  const key = Object.keys(headers).find((k) => k.toLowerCase() === name.toLowerCase());
  return key ? headers[key] : null;
}

function withAuthorization(init, token) {
  const headers = {};
  const src = init && init.headers;
  if (src && typeof src.forEach === "function" && !Array.isArray(src)) {
    src.forEach((value, key) => {
      headers[key] = value;
    });
  } else if (Array.isArray(src)) {
    src.forEach(([k, v]) => {
      headers[k] = v;
    });
  } else if (src) {
    Object.assign(headers, src);
  }
  for (const k of Object.keys(headers)) {
    if (k.toLowerCase() === "authorization") delete headers[k];
  }
  headers.Authorization = `Bearer ${token}`;
  return { ...(init || {}), headers };
}

export function createSessionGuard({ apiBase, storage, fetchImpl, onExpired = () => {}, onRefreshed = () => {} }) {
  let handlers = { onExpired, onRefreshed };
  const base = apiBase.replace(/\/+$/, "");
  let refreshing = null;
  let expiredNotified = false;

  const isApi = (url) => url === base || url.startsWith(`${base}/`);
  const isSkipped = (url) => SKIP_PATHS.some((p) => url.startsWith(`${base}${p}`));

  function expire() {
    SESSION_KEYS.forEach((k) => storage.removeItem(k));
    if (!expiredNotified) {
      expiredNotified = true;
      handlers.onExpired();
    }
  }

  async function refreshOnce() {
    if (!refreshing) {
      refreshing = (async () => {
        const refreshToken = storage.getItem("refresh_token");
        if (!refreshToken) return null;
        try {
          const res = await fetchImpl(`${base}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (!res.ok) return null;
          const data = await res.json();
          if (!data || !data.access_token) return null;
          storage.setItem("token", data.access_token);
          if (data.refresh_token) storage.setItem("refresh_token", data.refresh_token);
          handlers.onRefreshed(data.access_token);
          return data.access_token;
        } catch (_) {
          return null;
        }
      })().finally(() => {
        refreshing = null;
      });
    }
    return refreshing;
  }

  async function guardedFetch(input, init) {
    const url = typeof input === "string" ? input : input && input.url ? input.url : String(input);
    if (!isApi(url) || isSkipped(url)) return fetchImpl(input, init);

    const sentAuth = headerValue(init && init.headers, "authorization") || (input && input.headers && headerValue(input.headers, "authorization"));
    const response = await fetchImpl(input, init);
    if (response.status !== 401 || !sentAuth) return response;

    // A slow request sent with an OLD token can come back 401 after a refresh or a new sign-in already replaced it.
    // That is not an expired session: just retry once with the token that is current now.
    const sentToken = String(sentAuth).replace(/^Bearer\s+/i, "");
    const currentToken = storage.getItem("token");
    if (currentToken && currentToken !== sentToken) {
      const again = await fetchImpl(url, withAuthorization(init, currentToken));
      if (again.status === 401) expire();
      return again;
    }

    const newToken = await refreshOnce();
    if (!newToken) {
      expire();
      return response;
    }
    // Only plain string/undefined bodies can be replayed safely; the app sends JSON strings or FormData.
    const retry = await fetchImpl(url, withAuthorization(init, newToken));
    if (retry.status === 401) {
      expire();
    }
    return retry;
  }

  return {
    fetch: guardedFetch,
    /** Call after a successful sign-in so a later expiry is reported again. */
    markSignedIn() {
      expiredNotified = false;
    },
    /** Lets the app point the guard at its latest handlers (for example after a hot reload). */
    setHandlers(next) {
      handlers = { ...handlers, ...next };
    },
  };
}

/** Browser wiring: replaces window.fetch once. Returns the guard so the app can call markSignedIn(). */
export function installSessionGuard({ apiBase, onExpired, onRefreshed }) {
  if (window.__wifisenseSessionGuard) {          // already installed (React dev mode runs effects twice): just update handlers
    window.__wifisenseSessionGuard.setHandlers({ onExpired, onRefreshed });
    return window.__wifisenseSessionGuard;
  }
  const original = window.fetch.bind(window);
  const guard = createSessionGuard({ apiBase, storage: window.localStorage, fetchImpl: original, onExpired, onRefreshed });
  window.fetch = guard.fetch;
  window.__wifisenseSessionGuard = guard;
  return guard;
}
