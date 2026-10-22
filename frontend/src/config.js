// Single place that decides where the API lives, so the same build works locally and when hosted.
//
//   - VITE_API_BASE set at build time  -> that URL (for example https://api.example.com when the API is on another host)
//   - not set, `vite` dev server       -> http://localhost:8000
//   - not set, production build        -> the same origin as the page (an API served behind the same host/reverse proxy)
//
// No component should contain an API host: import API_BASE from here.
const configured = (import.meta.env.VITE_API_BASE || "").trim();

export const API_BASE = (
  configured || (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin)
).replace(/\/+$/, "");
