// Data layer for the authority dashboard. This is the only file that knows
// where data comes from; nothing else in the UI changes.

export const RISK_LEVELS = ["Critical", "High", "Moderate", "Low"]; // severity order

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export async function getReports() {
  const res = await fetch(`${API_BASE}/api/authority/reports`);
  if (!res.ok) throw new Error("Could not load reports");
  return res.json();
}

export async function acknowledgeReport(id) {
  const res = await fetch(`${API_BASE}/api/authority/reports/${id}/acknowledge`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Could not acknowledge report");
  return res.json();
}