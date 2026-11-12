// Frontend data layer. Put in your project next to index.js.
// Flip USE_MOCK to false once Anika's API is live and set API_BASE to the Function App URL.
const USE_MOCK = true;
const API_BASE = "https://YOUR-FUNCTION-APP.azurewebsites.net/api";

let mockCache = null;
async function loadMock() {
  if (!mockCache) mockCache = await (await fetch("data/mock-data.json")).json();
  return mockCache;
}

async function getStores() {
  if (USE_MOCK) return (await loadMock()).stores;
  const res = await fetch(`${API_BASE}/stores`);
  if (!res.ok) throw new Error("Could not load stores");
  return res.json();
}

async function getStore(id) {
  if (USE_MOCK) {
    const s = (await loadMock()).stores.find(s => s.id === id);
    if (!s) throw new Error("Store not found");
    return s;
  }
  const res = await fetch(`${API_BASE}/stores/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error("Store not found");
  return res.json();
}

async function getHistory(id) {
  if (USE_MOCK) return (await loadMock()).readings.filter(r => r.storeId === id);
  const res = await fetch(`${API_BASE}/stores/${encodeURIComponent(id)}/history`);
  if (!res.ok) throw new Error("History unavailable");
  return res.json();
}

// White (empty) -> dark red (full), for markers and cards
function crowdColor(pct) {
  if (pct == null) return "#9e9e9e"; // unavailable
  const t = Math.max(0, Math.min(100, pct)) / 100;
  const g = Math.round(255 - t * 255 * 0.95);
  const b = Math.round(255 - t * 255 * 0.95);
  const r = Math.round(255 - t * 115); // 255 -> 140
  return `rgb(${r},${g},${b})`;
}