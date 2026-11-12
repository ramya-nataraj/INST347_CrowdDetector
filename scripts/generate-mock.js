// Generates data/mock-data.json (stores + 24h of hourly readings per store).
// Run: node scripts/generate-mock.js
// NOTE: coordinates, capacities and deals are PLACEHOLDERS - replace with your real tracked stores.
const fs = require("fs");
const path = require("path");

// Agree on this mapping with Ramya/Anika. The AI only returns small/medium/large.
const LEVEL_TO_PCT = { small: 20, medium: 50, large: 85 };

const stores = [
  { id: "target-hyattsville", name: "Target - Hyattsville", address: "Prince George's Plaza, Hyattsville, MD", lat: 38.9657, lng: -76.9558, maxCapacity: 250, deals: ["20% off toys"] },
  { id: "walmart-beltsville", name: "Walmart - Beltsville", address: "Beltsville, MD", lat: 39.0348, lng: -76.9075, maxCapacity: 400, deals: ["Black Friday electronics doorbusters"] },
  { id: "bestbuy-silver-spring", name: "Best Buy - Silver Spring", address: "Silver Spring, MD", lat: 38.9907, lng: -77.0261, maxCapacity: 180, deals: ["Up to $200 off TVs"] },
  { id: "macys-wheaton", name: "Macy's - Wheaton", address: "Westfield Wheaton, Wheaton, MD", lat: 39.0376, lng: -77.0561, maxCapacity: 300, deals: ["Extra 25% off clearance"] },
  { id: "costco-white-oak", name: "Costco - White Oak", address: "White Oak, MD", lat: 39.0357, lng: -76.9933, maxCapacity: 500, deals: [] },
];

const hours = { mon: "8:00-22:00", tue: "8:00-22:00", wed: "8:00-22:00", thu: "8:00-22:00", fri: "8:00-23:00", sat: "8:00-23:00", sun: "9:00-21:00" };

// Fake busy-ness curve by hour of day (0-1), so the history chart looks realistic.
const curve = h => (h < 8 ? 0.05 : Math.min(1, 0.2 + 0.8 * Math.exp(-Math.pow((h - 14) / 4, 2))));
const toLevel = x => (x < 0.35 ? "small" : x < 0.7 ? "medium" : "large");

const now = new Date();
now.setMinutes(0, 0, 0);

const readings = [];
const outStores = stores.map((s, i) => {
  let last = null;
  for (let back = 23; back >= 0; back--) {
    const t = new Date(now.getTime() - back * 3600 * 1000);
    const x = Math.max(0, Math.min(1, curve(t.getHours()) + ((i * 7 + back) % 5) * 0.04 - 0.08));
    const level = toLevel(x);
    last = { level, capacityPct: LEVEL_TO_PCT[level], timestamp: t.toISOString() };
    readings.push({ id: `${s.id}-${t.getTime()}`, storeId: s.id, ...last });
  }
  return {
    ...s,
    hours,
    photoUrl: `stores/${s.id}.jpg`,
    latest: { level: last.level, capacityPct: last.capacityPct, status: "ok", updatedAt: last.timestamp },
  };
});
// Example of an unavailable camera, so the UI can handle it
outStores[4].latest = { level: null, capacityPct: null, status: "unavailable", updatedAt: null };

fs.writeFileSync(path.join(__dirname, "../data/mock-data.json"), JSON.stringify({ levelToPct: LEVEL_TO_PCT, stores: outStores, readings }, null, 2));
console.log(`Wrote ${outStores.length} stores and ${readings.length} readings.`);