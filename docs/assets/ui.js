/** Shared UI helpers for Atlas. */

export function $(id) {
  return document.getElementById(id);
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

export function hasCoordinates(row) {
  if (row.latitude === null || row.latitude === undefined || row.latitude === "") return false;
  if (row.longitude === null || row.longitude === undefined || row.longitude === "") return false;
  const lat = Number(row.latitude);
  const lon = Number(row.longitude);
  return Number.isFinite(lat) && Number.isFinite(lon);
}

export function uniqueSorted(items, key) {
  return [...new Set(items.map((row) => row[key]).filter(Boolean))].sort((a, b) =>
    String(a).localeCompare(String(b))
  );
}

export function highlightText(text, query) {
  const safe = escapeHtml(text || "");
  const q = (query || "").trim();
  if (!q) return safe;
  const pattern = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
  return safe.replace(pattern, '<mark class="mark">$1</mark>');
}

export function categoryLabel(category) {
  const map = {
    see: "See",
    do: "Do",
    eat: "Eat",
    drink: "Drink",
    sleep: "Stay",
    buy: "Buy",
  };
  return map[category] || category || "Place";
}

export function categoryColor(category) {
  const map = {
    see: "#1d4ed8",
    do: "#059669",
    eat: "#e11d48",
    drink: "#d97706",
    sleep: "#4338ca",
    buy: "#a21caf",
  };
  return map[category] || "#0f766e";
}

export function truncate(text, max = 140) {
  const value = String(text || "").trim();
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
}

export function readQueryState() {
  const params = new URLSearchParams(window.location.search);
  return {
    q: params.get("q") || "",
    country: params.getAll("country"),
    destination: params.getAll("destination"),
    category: params.getAll("category"),
    website: params.get("website") === "1",
    coords: params.get("coords") === "1",
    sort: params.get("sort") || "name",
  };
}

export function writeQueryState(state) {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  state.country.forEach((v) => params.append("country", v));
  state.destination.forEach((v) => params.append("destination", v));
  state.category.forEach((v) => params.append("category", v));
  if (state.website) params.set("website", "1");
  if (state.coords) params.set("coords", "1");
  if (state.sort && state.sort !== "name") params.set("sort", state.sort);
  const next = params.toString();
  const url = next ? `${window.location.pathname}?${next}` : window.location.pathname;
  window.history.replaceState({}, "", url);
}

export function detectModKeyHint() {
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform || "");
  return isMac ? "⌘ K" : "Ctrl K";
}
