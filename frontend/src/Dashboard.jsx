import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  MapPin,
  Users,
  Clock,
  Video,
  ImageIcon,
  CheckCircle2,
  Flame,
  MapPinned,
  X,
  Radio,
  Activity,
  Layers,
  ShieldAlert,
} from "lucide-react";
import { getReports, acknowledgeReport, RISK_LEVELS } from "./reportsApi";

const RISK_COLORS = {
  Low: "#22C55E",
  Moderate: "#FACC15",
  High: "#F97316",
  Critical: "#EF4444",
};

const RISK_TEXT_ON_COLOR = {
  Low: "#052e14",
  Moderate: "#2a1f00",
  High: "#2a0f00",
  Critical: "#ffffff",
};

const HEAT_WEIGHT = { Low: 0.25, Moderate: 0.5, High: 0.75, Critical: 1 };
const CONTEXT_LABELS = {
  open_ground: "Open ground",
  narrow_lane: "Narrow lane",
  stairway: "Stairway",
  platform: "Platform",
};

const POLL_MS = 30000;
const OSM_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const timeAgo = (iso) => {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (m < 1) return "just now";
  if (m < 60) return `${m} min ago`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h} h ago` : `${Math.floor(h / 24)} d ago`;
};

const fullTime = (iso) =>
  new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });

const clock = () => new Date().toLocaleTimeString([], { hour12: false });
const severity = (r) => RISK_LEVELS.indexOf(r.risk_level);

function RiskBadge({ level, size = "sm" }) {
  const pad = size === "lg" ? "px-3 py-1 text-xs" : "px-2.5 py-0.5 text-[11px]";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md font-bold uppercase tracking-wider ${pad} shadow-sm`}
      style={{
        background: RISK_COLORS[level],
        color: RISK_TEXT_ON_COLOR[level],
      }}
    >
      {level === "Critical" && <AlertTriangle size={12} className="animate-bounce" />}
      {level}
    </span>
  );
}

function MediaIcon({ type, size = 14 }) {
  return type === "video" ? <Video size={size} /> : <ImageIcon size={size} />;
}

/* ---------------- Map Component ---------------- */

function pinIcon(report, selected) {
  const glow =
    report.risk_level === "Critical" && report.status === "new"
      ? "box-shadow: 0 0 14px 4px rgba(239, 68, 68, 0.95), 0 0 28px 8px rgba(239, 68, 68, 0.5);"
      : "box-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);";
  const scale = selected ? "transform: scale(1.4);" : "";
  return L.divIcon({
    className: "",
    html: `<span style="display:block; width:22px; height:22px; border-radius:50%; background:${RISK_COLORS[report.risk_level]}; border:3px solid #0B1220; ${glow}${scale}${
      selected ? "outline: 2px solid #3B82F6; outline-offset: 3px;" : ""
    }"></span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function ReportMap({ reports, selectedId, onSelect, mode }) {
  const el = useRef(null);
  const map = useRef(null);
  const markerLayer = useRef(null);
  const heatLayer = useRef(null);
  const fitted = useRef(false);

  useEffect(() => {
    map.current = L.map(el.current, { zoomControl: false }).setView(
      [12.9716, 77.5946],
      12
    );
    L.control.zoom({ position: "bottomleft" }).addTo(map.current);
    L.tileLayer(OSM_TILES, {
      maxZoom: 19,
      attribution: TILE_ATTR,
      className: "map-tiles-dark",
    }).addTo(map.current);

    markerLayer.current = L.layerGroup();
    heatLayer.current = L.heatLayer([], {
      radius: 36,
      blur: 28,
      maxZoom: 15,
      gradient: {
        0.2: "#22C55E",
        0.5: "#FACC15",
        0.75: "#F97316",
        1: "#EF4444",
      },
    });

    return () => map.current.remove();
  }, []);

  useEffect(() => {
    if (!map.current) return;
    if (mode === "pins") {
      heatLayer.current.remove();
      markerLayer.current.addTo(map.current);
    } else {
      markerLayer.current.remove();
      heatLayer.current.addTo(map.current);
    }
  }, [mode]);

  useEffect(() => {
    markerLayer.current.clearLayers();
    reports.forEach((r) => {
      L.marker([r.lat, r.long], {
        icon: pinIcon(r, r.id === selectedId),
        zIndexOffset: r.id === selectedId ? 1000 : (3 - severity(r)) * 10,
      })
        .on("click", () => onSelect(r.id))
        .addTo(markerLayer.current);
    });

    heatLayer.current.setLatLngs(
      reports.map((r) => [r.lat, r.long, HEAT_WEIGHT[r.risk_level]])
    );

    if (!fitted.current && reports.length) {
      map.current.fitBounds(
        L.latLngBounds(reports.map((r) => [r.lat, r.long])).pad(0.25)
      );
      fitted.current = true;
    }
  }, [reports, selectedId, onSelect]);

  useEffect(() => {
    const r = reports.find((x) => x.id === selectedId);
    if (r)
      map.current.flyTo([r.lat, r.long], Math.max(map.current.getZoom(), 15), {
        duration: 0.6,
      });
  }, [selectedId]);

  return <div ref={el} className="absolute inset-0 z-0" />;
}

/* ---------------- Redesigned Header ---------------- */

function TopBar({ now }) {
  return (
    <header className="glass-header sticky top-0 z-30 px-6 py-3.5 shadow-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/20 text-accent ring-1 ring-accent/40 shadow-inner">
            <ShieldAlert size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-extrabold tracking-tight text-ink">
                CrowdSafe
              </h1>
              <span className="rounded bg-accent/15 px-2 py-0.5 text-[10px] font-semibold text-accent border border-accent/30 uppercase tracking-wider">
                V2.0 AI Surveillance
              </span>
            </div>
            <p className="text-xs font-medium text-ink-secondary">
              Public Safety Command Center
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-1.5 text-xs shadow-inner">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-low opacity-75"></span>
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-low"></span>
            </span>
            <span className="font-bold tracking-wider text-ink">SYSTEM ONLINE</span>
            <span className="hidden text-muted sm:inline">| Live Feed {now}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

/* ---------------- Redesigned Statistic Cards ---------------- */

function KpiCard({ icon, label, value, color, delay, glowClass = "" }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className={`group relative flex items-center justify-between gap-3 rounded-2xl border border-line bg-surface p-4 transition-all duration-300 hover:-translate-y-1 hover:border-line-light hover:bg-surface-hover shadow-lg ${glowClass}`}
    >
      <div className="space-y-1">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-200">
          {label}
        </span>
        <div className="text-3xl font-black text-white">{value}</div>
      </div>
      <div
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
        style={{ background: `${color}25`, color: color, border: `1px solid ${color}45` }}
      >
        {icon}
      </div>
    </motion.div>
  );
}

function KpiStrip({ counts, newCount, ackCount }) {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 pt-5 pb-3">
      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard
          icon={<AlertTriangle size={22} />}
          label="Critical Alerts"
          value={counts.Critical}
          color={RISK_COLORS.Critical}
          delay={0}
          glowClass={counts.Critical > 0 ? "glow-critical border-critical/40" : ""}
        />
        <KpiCard
          icon={<Radio size={22} />}
          label="High Risk"
          value={counts.High}
          color={RISK_COLORS.High}
          delay={0.04}
          glowClass={counts.High > 0 ? "glow-high border-high/30" : ""}
        />
        <KpiCard
          icon={<Activity size={22} />}
          label="Moderate Risk"
          value={counts.Moderate}
          color={RISK_COLORS.Moderate}
          delay={0.08}
        />
        <KpiCard
          icon={<CheckCircle2 size={22} />}
          label="Low Risk"
          value={counts.Low}
          color={RISK_COLORS.Low}
          delay={0.12}
        />
        <KpiCard
          icon={<Clock size={22} />}
          label="New Reports"
          value={newCount}
          color="#3B82F6"
          delay={0.16}
          glowClass={newCount > 0 ? "glow-accent border-accent/30" : ""}
        />
        <KpiCard
          icon={<CheckCircle2 size={22} />}
          label="Acknowledged"
          value={ackCount}
          color="#10B981"
          delay={0.2}
        />
      </div>
    </div>
  );
}

/* ---------------- Filter & View Controls ---------------- */

function FilterBar({ hidden, toggle, counts }) {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-2">
      <div className="flex flex-wrap items-center justify-between gap-3.5 rounded-2xl border border-line bg-surface/90 p-3.5 shadow-lg backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="text-xs font-extrabold uppercase tracking-widest text-slate-200 mr-2 flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Severity Filter
          </span>
          {RISK_LEVELS.map((l) => {
            const active = !hidden.has(l);
            return (
              <button
                key={l}
                onClick={() => toggle(l)}
                aria-pressed={active}
                className="flex items-center gap-2 rounded-xl border px-3.5 py-1.5 text-xs font-bold transition-all duration-200 hover:scale-105"
                style={{
                  borderColor: active ? RISK_COLORS[l] : "#26344D",
                  color: active ? "#F8FAFC" : "#94A3B8",
                  background: active ? `${RISK_COLORS[l]}22` : "rgba(11, 18, 32, 0.5)",
                  boxShadow: active ? `0 0 14px -2px ${RISK_COLORS[l]}40` : "none",
                }}
              >
                <span
                  className="h-2.5 w-2.5 rounded-full transition-transform"
                  style={{
                    background: active ? RISK_COLORS[l] : "#475569",
                    boxShadow: active ? `0 0 8px ${RISK_COLORS[l]}` : "none",
                  }}
                />
                <span className="text-slate-100 font-bold">{l}</span>
                <span
                  className="rounded-md px-2 py-0.5 text-[10px] font-extrabold"
                  style={{
                    background: active ? `${RISK_COLORS[l]}35` : "#1E2A40",
                    color: active ? "#FFFFFF" : "#CBD5E1",
                  }}
                >
                  {counts[l]}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Incident Drawer Details ---------------- */

function IncidentDrawer({ report, onClose, onAcknowledge, busy }) {
  if (!report) return null;
  const acked = report.status === "acknowledged";

  return (
    <AnimatePresence>
      <motion.aside
        initial={{ x: 420, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 420, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="dark-scroll fixed inset-y-0 right-0 z-[2000] w-full max-w-[420px] overflow-y-auto border-l border-line bg-surface/95 backdrop-blur-xl shadow-2xl"
      >
        <div className="relative p-5">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 z-20 flex h-8 w-8 items-center justify-center rounded-full bg-bg/80 text-slate-100 hover:bg-line hover:text-white transition"
            aria-label="Close drawer"
          >
            <X size={18} />
          </button>

          <div className="mb-4">
            <span className="text-[11px] font-extrabold uppercase tracking-widest text-accent">
              Incident Analysis
            </span>
            <h3 className="text-lg font-bold text-white mt-0.5">Report #{report.id}</h3>
          </div>

          <div className="overflow-hidden rounded-2xl border border-line bg-bg shadow-inner mb-4">
            <div className="aspect-video bg-black relative flex items-center justify-center">
              {report.media_type === "video" ? (
                <video
                  src={report.media_url}
                  controls
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="h-full w-full object-contain"
                />
              ) : (
                <img
                  src={report.media_url}
                  alt={`Crowd evidence report ${report.id}`}
                  className="h-full w-full object-contain"
                />
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-line bg-surface2 p-3">
              <RiskBadge level={report.risk_level} size="lg" />
              <span className="text-xs font-semibold text-slate-200">
                Status:{" "}
                <span
                  className={acked ? "text-low font-bold" : "text-accent font-bold"}
                >
                  {acked ? "ACKNOWLEDGED" : "ACTION REQUIRED"}
                </span>
              </span>
            </div>

            <div className="space-y-3 rounded-xl border border-line bg-surface2 p-4 text-xs">
              <div className="flex items-start gap-3">
                <MapPin size={16} className="mt-0.5 text-accent shrink-0" />
                <div>
                  <div className="font-bold text-white text-sm">
                    {report.location_name}
                  </div>
                  <div className="text-slate-300">
                    {report.lat.toFixed(5)}, {report.long.toFixed(5)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Users size={16} className="text-accent shrink-0" />
                <div>
                  <span className="text-slate-300">Estimated Density: </span>
                  <span className="font-bold text-white text-sm">
                    {report.person_count} people
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Clock size={16} className="text-accent shrink-0" />
                <div>
                  <span className="text-slate-300">Timestamp: </span>
                  <span className="font-semibold text-slate-200">
                    {fullTime(report.timestamp)} ({timeAgo(report.timestamp)})
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <MediaIcon type={report.media_type} size={16} />
                <div>
                  <span className="text-slate-300">Evidence Type: </span>
                  <span className="font-semibold text-slate-200 capitalize">
                    {report.media_type} submission
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Layers size={16} className="text-accent shrink-0" />
                <div>
                  <span className="text-slate-300">Environment Tag: </span>
                  <span className="font-semibold text-slate-200">
                    {CONTEXT_LABELS[report.context_tag] || report.context_tag}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onAcknowledge(report.id)}
              disabled={acked || busy}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-3.5 text-sm font-bold text-white shadow-lg transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-line disabled:text-slate-400"
            >
              <CheckCircle2 size={18} />
              {acked ? "Acknowledged by Authority" : busy ? "Updating Status..." : "Acknowledge Incident"}
            </button>
          </div>
        </div>
      </motion.aside>
    </AnimatePresence>
  );
}

/* ---------------- Incident Cards & Feed ---------------- */

function FeedCard({ r, active, onClick }) {
  const isCritical = r.risk_level === "Critical" && r.status === "new";

  return (
    <motion.button
      layout
      onClick={onClick}
      whileHover={{ y: -4, scale: 1.01 }}
      className={`group relative flex w-72 shrink-0 flex-col gap-2.5 rounded-2xl border p-4 text-left transition-all duration-200 bg-surface shadow-md ${
        active
          ? "border-accent ring-2 ring-accent/50 bg-surface-hover"
          : "border-line hover:border-line-light hover:bg-surface-hover"
      } ${r.status === "acknowledged" ? "opacity-75" : ""} ${
        isCritical ? "glow-critical border-critical/50" : ""
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <RiskBadge level={r.risk_level} />
        <span
          className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            r.status === "acknowledged"
              ? "bg-low/15 text-low border border-low/30"
              : "bg-accent/15 text-accent border border-accent/30"
          }`}
        >
          {r.status === "acknowledged" ? "ACKNOWLEDGED" : "NEW"}
        </span>
      </div>

      <div>
        <h4 className="flex items-center gap-1.5 text-sm font-bold text-slate-100 truncate group-hover:text-accent transition-colors">
          <MapPin size={14} className="shrink-0 text-accent" />
          <span className="truncate">{r.location_name}</span>
        </h4>
        <p className="text-[11px] text-slate-400 ml-5 font-mono">
          {r.lat.toFixed(4)}, {r.long.toFixed(4)}
        </p>
      </div>

      <div className="flex items-center justify-between border-t border-line/60 pt-2.5 text-xs text-slate-200">
        <span className="flex items-center gap-1.5 font-medium">
          <Users size={13} className="text-accent" /> {r.person_count}
        </span>
        <span className="flex items-center gap-1.5 text-slate-300">
          <Clock size={13} /> {timeAgo(r.timestamp)}
        </span>
        <span className="flex items-center gap-1 rounded bg-bg p-1 text-accent">
          <MediaIcon type={r.media_type} size={13} />
        </span>
      </div>
    </motion.button>
  );
}

function BottomFeed({ reports, selectedId, onSelect }) {
  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-4">
      <div className="rounded-3xl border border-line bg-surface/70 p-4 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-3 px-1">
          <div className="flex items-center gap-2">
            <Radio size={16} className="text-accent animate-pulse" />
            <h3 className="text-xs font-extrabold uppercase tracking-widest text-slate-200">
              Recent Incidents
            </h3>
            <span className="rounded-full bg-accent/20 px-2.5 py-0.5 text-[11px] font-bold text-accent">
              {reports.length}
            </span>
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line p-6 text-center text-sm text-slate-300">
            No incidents match the active severity filters.
          </div>
        ) : (
          <div className="dark-scroll flex gap-3.5 overflow-x-auto pb-2 pt-1 px-1">
            <AnimatePresence>
              {reports.map((r) => (
                <FeedCard
                  key={r.id}
                  r={r}
                  active={r.id === selectedId}
                  onClick={() => onSelect(r.id)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </section>
  );
}

/* ---------------- Main Dashboard Layout ---------------- */

export default function Dashboard() {
  const [reports, setReports] = useState([]);
  const [status, setStatus] = useState("loading");
  const [selectedId, setSelectedId] = useState(null);
  const [hidden, setHidden] = useState(new Set());
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState("pins");
  const [now, setNow] = useState(clock());

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

  useEffect(() => {
    const t = setInterval(() => setNow(clock()), 1000);
    return () => clearInterval(t);
  }, []);

  const counts = useMemo(
    () =>
      Object.fromEntries(
        RISK_LEVELS.map((l) => [
          l,
          reports.filter((r) => r.risk_level === l).length,
        ])
      ),
    [reports]
  );
  const newCount = reports.filter((r) => r.status === "new").length;
  const ackCount = reports.filter((r) => r.status === "acknowledged").length;

  const visible = useMemo(
    () =>
      reports
        .filter((r) => !hidden.has(r.risk_level))
        .sort(
          (a, b) =>
            severity(a) - severity(b) ||
            new Date(b.timestamp) - new Date(a.timestamp)
        ),
    [reports, hidden]
  );
  const selected = reports.find((r) => r.id === selectedId);

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
    <div className="min-h-screen bg-bg text-ink flex flex-col font-sans selection:bg-accent selection:text-white">
      <TopBar now={now} />
      <KpiStrip counts={counts} newCount={newCount} ackCount={ackCount} />
      <FilterBar
        hidden={hidden}
        toggle={toggle}
        counts={counts}
      />

      {/* Main Command Center Map Panel (rounded-24px) */}
      <main className="mx-auto w-full max-w-7xl px-4 py-3 flex-1 flex flex-col min-h-[460px]">
        <div className="relative w-full flex-1 rounded-[24px] border border-line bg-surface overflow-hidden shadow-2xl min-h-[440px]">
          {status === "loading" && (
            <div className="absolute inset-0 z-[500] flex items-center justify-center bg-bg/80 backdrop-blur-sm text-sm font-semibold text-slate-200">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                Synchronizing live crowd reports...
              </div>
            </div>
          )}
          {status === "error" && (
            <div className="absolute inset-0 z-[500] flex items-center justify-center bg-bg/80 backdrop-blur-sm text-sm text-slate-300">
              Unable to load telemetry.{" "}
              <button
                className="ml-2 font-bold text-accent underline hover:text-blue-400"
                onClick={load}
              >
                Retry connection
              </button>
            </div>
          )}

          {/* Map Command Center Overlay Header - TOP-LEFT PILL (top: 18px, left: 18px) */}
          <div className="absolute top-[18px] left-[18px] z-[400] flex h-[48px] items-center gap-2 rounded-full border border-line bg-[#0B1220]/90 px-5 shadow-xl backdrop-blur-md text-xs font-bold text-slate-100 border-box">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-accent"></span>
            </span>
            <span className="tracking-wide">LIVE CROWD MONITORING</span>
          </div>

          {/* Floating Pins / Heatmap Display Segmented Control - TOP-RIGHT PILL (top: 18px, right: 18px) */}
          <div className="segmented-pill-wrapper">
            <button
              type="button"
              onClick={() => setMode("pins")}
              className={`segmented-pill-btn ${mode === "pins" ? "active" : ""}`}
            >
              <MapPin size={15} />
              <span>Pins</span>
            </button>
            <button
              type="button"
              onClick={() => setMode("heat")}
              className={`segmented-pill-btn ${mode === "heat" ? "active" : ""}`}
            >
              <Flame size={15} />
              <span>Heatmap</span>
            </button>
          </div>

          <ReportMap
            reports={visible}
            selectedId={selectedId}
            onSelect={setSelectedId}
            mode={mode}
          />
        </div>
      </main>

      <BottomFeed
        reports={visible}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />

      {/* Incident Detail Drawer Modal */}
      <AnimatePresence>
        {selected && (
          <IncidentDrawer
            report={selected}
            onClose={() => setSelectedId(null)}
            onAcknowledge={acknowledge}
            busy={busy}
          />
        )}
      </AnimatePresence>
    </div>
  );
}