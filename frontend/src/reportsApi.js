// Data layer: the only file that knows where data comes from.

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

// Citizen upload. formData: file, lat, long, context_tag, and optionally address.
// Don't set Content-Type here: the browser adds the multipart boundary itself.
export async function submitReport(formData) {
  const res = await fetch(`${API_BASE}/api/reports`, { method: "POST", body: formData });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || "Could not send the report");
  return body;
}