import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function CitizenUpload() {
  const [zones, setZones] = useState([]);
  const [zoneId, setZoneId] = useState('');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch available zones
    axios.get('/api/authority/zones')
      .then((res) => {
        setZones(res.data.zones || []);
        if (res.data.zones && res.data.zones.length > 0) {
          setZoneId(res.data.zones[0].id);
        }
      })
      .catch((err) => {
        console.warn('Zones fallback:', err);
        setZones([
          { id: 1, name: 'Gate 1 (North Entrance)', is_bottleneck: true },
          { id: 2, name: 'Main Concourse Plaza', is_bottleneck: false },
          { id: 3, name: 'Exit Corridor 4', is_bottleneck: true },
        ]);
        setZoneId(1);
      });
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      if (selected.type.startsWith('image/')) {
        setPreview(URL.createObjectURL(selected));
      } else {
        setPreview(null);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (!zoneId) {
      setError('Please select the affected venue zone.');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('zone_id', zoneId);
    formData.append('description', description);
    if (file) {
      formData.append('file', file);
    }

    const user = JSON.parse(localStorage.getItem('crowdsafe_user') || '{}');
    if (user.id) {
      formData.append('user_id', user.id);
    }

    try {
      const res = await axios.post('/api/reports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-4">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-primary text-white py-3">
              <h5 className="mb-0 fw-bold">📢 Report Crowd Congestion / Stampede Hazard</h5>
              <small className="opacity-75">Upload live CCTV, smartphone video, or photo for AI density estimation</small>
            </div>
            <div className="card-body p-4">
              {error && <div className="alert alert-danger py-2 small">{error}</div>}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label fw-semibold">Select Monitored Sector / Gate</label>
                  <select
                    className="form-select"
                    value={zoneId}
                    onChange={(e) => setZoneId(e.target.value)}
                    required
                  >
                    {zones.map((z) => (
                      <option key={z.id} value={z.id}>
                        {z.name} {z.is_bottleneck ? '⚠️ (Bottleneck Point)' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="mb-3">
                  <label className="form-label fw-semibold">Upload Photo or Video Feed</label>
                  <input
                    type="file"
                    className="form-control"
                    accept="image/*,video/*"
                    onChange={handleFileChange}
                  />
                  <div className="form-text">Supported formats: JPG, PNG, MP4, AVI (Max 100MB)</div>
                </div>

                {preview && (
                  <div className="mb-3 text-center">
                    <img
                      src={preview}
                      alt="Upload Preview"
                      className="img-fluid rounded border shadow-sm"
                      style={{ maxHeight: '250px' }}
                    />
                  </div>
                )}

                <div className="mb-4">
                  <label className="form-label fw-semibold">Incident Details / Observations</label>
                  <textarea
                    rows="3"
                    className="form-control"
                    placeholder="Describe crowd movement, stuck gates, panic signs, or physical obstruction..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  ></textarea>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100 py-2 fw-semibold"
                  disabled={loading}
                >
                  {loading ? 'Analyzing with AI Pipeline...' : 'Submit Real-Time Report'}
                </button>
              </form>
            </div>
          </div>

          {result && (
            <div className="card shadow-sm border-0 border-start border-4 border-warning mb-4">
              <div className="card-body p-4">
                <h5 className="fw-bold text-dark mb-3">🔍 AI Risk Assessment Report</h5>
                <div className="row g-3">
                  <div className="col-md-4">
                    <div className="p-3 bg-light rounded text-center">
                      <div className="text-muted small">Risk Level</div>
                      <h4 className={`fw-bold mb-0 ${
                        result.risk_assessment.level === 'CRITICAL' ? 'text-danger' :
                        result.risk_assessment.level === 'HIGH' ? 'text-warning' : 'text-success'
                      }`}>
                        {result.risk_assessment.level}
                      </h4>
                      <small className="text-muted">Score: {result.risk_assessment.score}/100</small>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="p-3 bg-light rounded text-center">
                      <div className="text-muted small">Estimated Headcount</div>
                      <h4 className="fw-bold mb-0 text-primary">{result.report.estimated_count}</h4>
                      <small className="text-muted">Density: {result.report.density} p/m²</small>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="p-3 bg-light rounded text-center">
                      <div className="text-muted small">Surge Velocity</div>
                      <h4 className="fw-bold mb-0 text-dark">
                        {result.risk_assessment.rate_of_change_per_min > 0 ? '+' : ''}
                        {result.risk_assessment.rate_of_change_per_min}
                      </h4>
                      <small className="text-muted">persons/min</small>
                    </div>
                  </div>
                </div>

                <div className="alert alert-info mt-3 mb-0">
                  <strong>Safety Recommendation:</strong> {result.risk_assessment.recommendation}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
