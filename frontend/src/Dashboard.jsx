import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./dashboard.css";
import { getReports, acknowledgeReport, RISK_LEVELS } from "./reportsApi";

const RISK_COLORS = { Low: "#2f9e6e", Moderate: "#e6a700", High: "#e8590c", Critical: "#d1122f" };
const CONTEXT_LABELS = { open_ground: "Open ground", narrow_lane: "Narrow lane", stairway: "Stairway", platform: "Platform" };
const POLL_MS = 30000;

const timeAgo = (iso) => {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (m < 1) return "just now";
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h} h ago` : `${Math.floor(h / 24)} d ago`;
};
const fullTime = (iso) => new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
const severity = (r) => RISK_LEVELS.indexOf(r.risk_level);

function RiskBadge({ level }) {
  return (
    <span className="badge" style={{ "--c": RISK_COLORS[level] }}>
      {level}
    </span>
  );
}

function pinIcon(report, selected) {
  const cls = ["pin", selected && "sel", report.risk_level === "Critical" && report.status === "new" && "pulse", report.status === "acknowledged" && "ack"]
    .filter(Boolean)
    .join(" ");
  return L.divIcon({
    className: "pin-wrap",
    html: `<span class="${cls}" style="--c:${RISK_COLORS[report.risk_level]}"></span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function ReportMap({ reports, selectedId, onSelect }) {
  const el = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);
  const markers = useRef({});
  const fitted = useRef(false);

  useEffect(() => {
    map.current = L.map(el.current, { zoomControl: false }).setView([12.9716, 77.5946], 12);
    L.control.zoom({ position: "bottomleft" }).addTo(map.current);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => map.current.remove();
  }, []);

  useEffect(() => {
    layer.current.clearLayers();
    markers.current = {};
    reports.forEach((r) => {
      const m = L.marker([r.lat, r.long], { icon: pinIcon(r, r.id === selectedId), zIndexOffset: r.id === selectedId ? 1000 : (3 - severity(r)) * 10 })
        .on("click", () => onSelect(r.id))
        .addTo(layer.current);
      markers.current[r.id] = m;
    });
    if (!fitted.current && reports.length) {
      map.current.fitBounds(L.latLngBounds(reports.map((r) => [r.lat, r.long])).pad(0.2));
      fitted.current = true;
    }
  }, [reports, selectedId, onSelect]);

  useEffect(() => {
    const r = reports.find((x) => x.id === selectedId);
    if (r) map.current.flyTo([r.lat, r.long], Math.max(map.current.getZoom(), 15), { duration: 0.6 });
  }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={el} className="map" />;
}

function DetailPanel({ report, onClose, onAcknowledge, busy }) {
  const acked = report.status === "acknowledged";
  return (
    <aside className="detail" aria-label="Report details">
      <button className="close" onClick={onClose} aria-label="Close details">×</button>
      <div className="media">
        {report.media_type === "video" ? (
          <video src={report.media_url} controls playsInline />
        ) : (
          <img src={report.media_url} alt={`Crowd photo, report ${report.id}`} />
        )}
      </div>
      <div className="detail-body">
        <div className="row">
          <RiskBadge level={report.risk_level} />
          <span className="muted">Report #{report.id}</span>
        </div>
        <dl>
          <dt>Reported</dt>
          <dd>{fullTime(report.timestamp)} ({timeAgo(report.timestamp)})</dd>
          <dt>Coordinates</dt>
          <dd>{report.lat.toFixed(5)}, {report.long.toFixed(5)}</dd>
          <dt>Setting</dt>
          <dd>{CONTEXT_LABELS[report.context_tag] || report.context_tag}</dd>
          <dt>Media</dt>
          <dd>{report.media_type === "video" ? "Video" : "Photo"}</dd>
        </dl>
        <button className="ack" onClick={() => onAcknowledge(report.id)} disabled={acked || busy}>
          {acked ? "Acknowledged" : busy ? "Saving…" : "Acknowledge"}
        </button>
      </div>
    </aside>
  );
}

export default function Dashboard() {
  const [reports, setReports] = useState([]);
  const [status, setStatus] = useState("loading");
  const [selectedId, setSelectedId] = useState(null);
  const [hidden, setHidden] = useState(new Set());
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setReports(await getReports());
      setStatus("ok");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  const counts = useMemo(() => Object.fromEntries(RISK_LEVELS.map((l) => [l, reports.filter((r) => r.risk_level === l).length])), [reports]);
  const visible = useMemo(
    () => reports.filter((r) => !hidden.has(r.risk_level)).sort((a, b) => severity(a) - severity(b) || new Date(b.timestamp) - new Date(a.timestamp)),
    [reports, hidden]
  );
  const selected = reports.find((r) => r.id === selectedId);
  const pending = reports.filter((r) => r.status === "new").length;

  const toggle = (lvl) =>
    setHidden((h) => {
      const n = new Set(h);
      n.has(lvl) ? n.delete(lvl) : n.add(lvl);
      return n;
    });

  const acknowledge = async (id) => {
    setBusy(true);
    try {
      const updated = await acknowledgeReport(id);
      setReports((rs) => rs.map((r) => (r.id === id ? updated : r)));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app">
      <header className="top">
        <h1>CrowdSafe</h1>
        <span className="muted">{pending} awaiting acknowledgement</span>
      </header>

      <div className="body">
        <section className="side">
          <div className="filters" role="group" aria-label="Filter by risk level">
            {RISK_LEVELS.map((l) => (
              <button key={l} className={`chip ${hidden.has(l) ? "off" : ""}`} style={{ "--c": RISK_COLORS[l] }} aria-pressed={!hidden.has(l)} onClick={() => toggle(l)}>
                <i /> {l} <b>{counts[l]}</b>
              </button>
            ))}
          </div>

          <ul className="list">
            {status === "loading" && <li className="empty">Loading reports…</li>}
            {status === "error" && (
              <li className="empty">
                Couldn't load reports. <button className="link" onClick={load}>Try again</button>
              </li>
            )}
            {status === "ok" && visible.length === 0 && <li className="empty">No reports match these filters. Turn a risk level back on above.</li>}
            {visible.map((r) => (
              <li key={r.id}>
                <button className={`item ${r.id === selectedId ? "active" : ""} ${r.status === "acknowledged" ? "done" : ""}`} style={{ "--c": RISK_COLORS[r.risk_level] }} onClick={() => setSelectedId(r.id)}>
                  <div className="row">
                    <strong>{CONTEXT_LABELS[r.context_tag] || r.context_tag}</strong>
                    <RiskBadge level={r.risk_level} />
                  </div>
                  <div className="coords">{r.lat.toFixed(4)}, {r.long.toFixed(4)}</div>
                  <div className="row muted">
                    <span>{timeAgo(r.timestamp)}</span>
                    <span>{r.media_type === "video" ? "Video" : "Photo"}{r.status === "acknowledged" ? " · Acknowledged" : ""}</span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <main className="stage">
          <ReportMap reports={visible} selectedId={selectedId} onSelect={setSelectedId} />
          {selected && <DetailPanel report={selected} onClose={() => setSelectedId(null)} onAcknowledge={acknowledge} busy={busy} />}
        </main>
      </div>
    </div>
  );
}
