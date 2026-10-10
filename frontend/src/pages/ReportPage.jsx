import { useCallback, useEffect, useState } from "react";
import { Camera, MapPin, Loader2, CheckCircle2, RefreshCw, Phone } from "lucide-react";
import { submitReport } from "../reportsApi";

const MAX_BYTES = 15 * 1024 * 1024; // matches the backend limit
const TAGS = [
  { value: "open_ground", label: "Open ground", hint: "Field, plaza, wide road" },
  { value: "narrow_lane", label: "Narrow lane", hint: "Alley, small street" },
  { value: "stairway", label: "Stairway", hint: "Steps, ramp, footbridge" },
  { value: "platform", label: "Platform", hint: "Station, bus stand, gate" },
];
const RISK_COLORS = { Low: "#22C55E", Moderate: "#FBBF24", High: "#F97316", Critical: "#EF4444" };

const GEO_MESSAGES = {
  denied: "Location is blocked for this site. Allow location in your browser settings, then tap Retry.",
  insecure: "Location only works on a secure (https) page. Open this page using an https address.",
  unavailable: "This browser can't provide location.",
  failed: "Couldn't get your location. Move somewhere with a clearer sky and tap Retry.",
};

export default function ReportPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [geo, setGeo] = useState({ status: "locating" });
  const [tag, setTag] = useState("");
  const [address, setAddress] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const locate = useCallback(() => {
    if (!window.isSecureContext) return setGeo({ status: "insecure" });
    if (!navigator.geolocation) return setGeo({ status: "unavailable" });
    setGeo({ status: "locating" });
    navigator.geolocation.getCurrentPosition(
      (p) => setGeo({ status: "ok", lat: p.coords.latitude, long: p.coords.longitude, accuracy: p.coords.accuracy }),
      (e) => setGeo({ status: e.code === 1 ? "denied" : "failed" }),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }, []);

  useEffect(() => {
    locate();
  }, [locate]);

  useEffect(() => {
    if (!file) return setPreview(null);
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > MAX_BYTES) {
      setError("That photo is larger than 15 MB. Please take a new one.");
      return;
    }
    setError("");
    setFile(f);
  };

  const canSubmit = file && geo.status === "ok" && tag && !sending;

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSending(true);
    setError("");
    const fd = new FormData();
    fd.append("file", file);
    fd.append("lat", geo.lat);
    fd.append("long", geo.long);
    fd.append("context_tag", tag);
    if (address.trim()) fd.append("address", address.trim());
    try {
      setResult(await submitReport(fd));
    } catch (err) {
      setError(err.message === "Failed to fetch" ? "Couldn't reach the server. Check your connection and try again." : err.message);
    } finally {
      setSending(false);
    }
  };

  const reset = () => {
    setFile(null);
    setTag("");
    setAddress("");
    setResult(null);
    setError("");
    locate();
  };

  const shell = "mx-auto flex min-h-full w-full max-w-md flex-col gap-4 px-4 py-6";

  if (result) {
    const level = result.assessment.risk_level;
    return (
      <div className="min-h-full bg-bg text-ink">
        <div className={shell}>
          <div className="flex items-center gap-2 text-low">
            <CheckCircle2 size={22} />
            <h1 className="text-xl font-bold text-ink">Report sent</h1>
          </div>
          <div className="rounded-xl border border-line bg-surface p-4">
            <p className="text-xs uppercase tracking-wide text-muted">AI estimate</p>
            <p className="mt-1 text-2xl font-bold" style={{ color: RISK_COLORS[level] }}>{level} risk</p>
            <p className="mt-1 text-sm text-muted">About {result.assessment.people_estimated} people in your photo.</p>
            <p className="mt-3 text-xs text-muted">{result.assessment.note}</p>
          </div>
          <p className="text-sm text-muted">
            Your report is now on the authority dashboard. It may not be seen right away. If anyone is in danger, call 112.
          </p>
          <button onClick={reset} className="rounded-lg bg-accent py-3 text-sm font-semibold text-white">
            Send another report
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-bg text-ink">
      <form onSubmit={onSubmit} className={shell}>
        <div>
          <h1 className="text-xl font-bold">Report a crowd</h1>
          <p className="text-sm text-muted">Take a photo of the crowd. Your location is added automatically.</p>
        </div>

        <div className="flex items-start gap-2 rounded-lg border border-high/40 bg-high/10 p-3 text-sm">
          <Phone size={16} className="mt-0.5 shrink-0 text-high" />
          <span>If anyone is in immediate danger, call <b>112</b> first. This app is not an emergency line.</span>
        </div>

        {/* 1. Photo */}
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">1. Photo</h2>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line bg-surface py-6 text-sm font-semibold">
            <Camera size={20} className="text-accent" />
            {file ? "Retake photo" : "Take photo"}
            <input type="file" accept="image/*" capture="environment" onChange={onFile} className="sr-only" />
          </label>
          {preview && <img src={preview} alt="Your photo" className="max-h-64 w-full rounded-lg object-contain bg-black" />}
        </section>

        {/* 2. Location */}
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">2. Location</h2>
          <div className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface p-3 text-sm">
            <div className="flex items-center gap-2">
              {geo.status === "locating" ? <Loader2 size={16} className="animate-spin text-accent" /> : <MapPin size={16} className={geo.status === "ok" ? "text-low" : "text-high"} />}
              <span>
                {geo.status === "locating" && "Finding your location…"}
                {geo.status === "ok" && `Location captured (±${Math.round(geo.accuracy)} m)`}
                {GEO_MESSAGES[geo.status]}
              </span>
            </div>
            {geo.status !== "ok" && geo.status !== "locating" && geo.status !== "insecure" && (
              <button type="button" onClick={locate} className="flex shrink-0 items-center gap-1 text-accent">
                <RefreshCw size={14} /> Retry
              </button>
            )}
          </div>
          {geo.status === "ok" && geo.accuracy > 100 && (
            <p className="text-xs text-high">Your location is rough. Adding the address below will help.</p>
          )}
          <input
            type="text"
            value={address}
            maxLength={150}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Exact address or landmark (optional)"
            className="w-full rounded-lg border border-line bg-surface px-3 py-3 text-sm placeholder:text-muted"
          />
        </section>

        {/* 3. Place type */}
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">3. What kind of place is this?</h2>
          <div className="grid grid-cols-2 gap-2">
            {TAGS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setTag(t.value)}
                aria-pressed={tag === t.value}
                className={`rounded-lg border p-3 text-left ${tag === t.value ? "border-accent bg-accent/15" : "border-line bg-surface"}`}
              >
                <div className="text-sm font-semibold">{t.label}</div>
                <div className="text-xs text-muted">{t.hint}</div>
              </button>
            ))}
          </div>
        </section>

        {error && <p role="alert" className="rounded-lg border border-critical/40 bg-critical/10 p-3 text-sm text-critical">{error}</p>}

        <button
          type="submit"
          disabled={!canSubmit}
          className="flex items-center justify-center gap-2 rounded-lg bg-accent py-3 text-sm font-semibold text-white disabled:bg-line disabled:text-muted"
        >
          {sending && <Loader2 size={16} className="animate-spin" />}
          {sending ? "Analysing your photo…" : "Send report"}
        </button>
        {!canSubmit && !sending && (
          <p className="text-center text-xs text-muted">
            {!file ? "Take a photo to continue." : geo.status !== "ok" ? "Waiting for your location." : "Choose the kind of place."}
          </p>
        )}
      </form>
    </div>
  );
}
