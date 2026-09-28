// Data layer for the authority dashboard.
// Swap step: replace the bodies of getReports() and acknowledgeReport()
// with fetch calls to authority_routes.py. Nothing else in the UI changes.

export const RISK_LEVELS = ["Critical", "High", "Moderate", "Low"]; // severity order

const mins = (m) => new Date(Date.now() - m * 60000).toISOString();
const photo = (label, hue) =>
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='640' height='400'><rect width='640' height='400' fill='hsl(${hue},18%,26%)'/><text x='320' y='210' text-anchor='middle' font-family='sans-serif' font-size='22' fill='#cfd6dd'>${label}</text></svg>`
  );
const VIDEO = "https://www.w3schools.com/html/mov_bbb.mp4";

let MOCK_REPORTS = [
  { id: 1, lat: 12.9767, long: 77.5713, risk_level: "Critical", media_type: "video", media_url: VIDEO, timestamp: mins(4), context_tag: "platform", status: "new" },
  { id: 2, lat: 12.9788, long: 77.5996, risk_level: "High", media_type: "image", media_url: photo("Sample photo: MG Road", 210), timestamp: mins(11), context_tag: "stairway", status: "new" },
  { id: 3, lat: 12.9788, long: 77.5996, risk_level: "Moderate", media_type: "image", media_url: photo("Sample photo: Cubbon Park gate", 150), timestamp: mins(26), context_tag: "open_ground", status: "new" },
  { id: 4, lat: 12.9634, long: 77.5755, risk_level: "High", media_type: "video", media_url: VIDEO, timestamp: mins(42), context_tag: "narrow_lane", status: "acknowledged" },
  { id: 5, lat: 12.9507, long: 77.5848, risk_level: "Low", media_type: "image", media_url: photo("Sample photo: Lalbagh", 120), timestamp: mins(75), context_tag: "open_ground", status: "new" },
  { id: 6, lat: 12.9698, long: 77.5063, risk_level: "Moderate", media_type: "image", media_url: photo("Sample photo: Temple road", 30), timestamp: mins(130), context_tag: "narrow_lane", status: "new" },
  { id: 7, lat: 12.9791, long: 77.5913, risk_level: "Critical", media_type: "image", media_url: photo("Sample photo: Stadium exit", 350), timestamp: mins(8), context_tag: "stairway", status: "new" },
];

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// MOCK version. API version later, e.g.:
//   const res = await fetch("/api/authority/reports");
//   if (!res.ok) throw new Error("Could not load reports");
//   return res.json();
export async function getReports() {
  await delay(250);
  return MOCK_REPORTS.map((r) => ({ ...r }));
}

// MOCK version. API version later, e.g.:
//   const res = await fetch(`/api/authority/reports/${id}/acknowledge`, { method: "POST" });
export async function acknowledgeReport(id) {
  await delay(200);
  MOCK_REPORTS = MOCK_REPORTS.map((r) => (r.id === id ? { ...r, status: "acknowledged" } : r));
  return MOCK_REPORTS.find((r) => r.id === id);
}
