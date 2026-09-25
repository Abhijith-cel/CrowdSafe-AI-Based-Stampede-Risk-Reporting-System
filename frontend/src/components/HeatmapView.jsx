import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function HeatmapView({ zones = [], center = [28.6139, 77.2090], zoom = 15 }) {
  const getColor = (level) => {
    switch (level) {
      case 'CRITICAL': return '#dc3545';
      case 'HIGH': return '#fd7e14';
      case 'MODERATE': return '#ffc107';
      default: return '#198754';
    }
  };

  return (
    <div className="card shadow-sm mb-4">
      <div className="card-header bg-dark text-white fw-bold d-flex justify-content-between align-items-center">
        <span>🗺️ Geographic Zone Risk & Sensor Map</span>
        <span className="small text-muted">Real-time GPS / Venue coordinates</span>
      </div>
      <div className="card-body p-0" style={{ height: '400px', width: '100%' }}>
        <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {zones.map((item) => {
            const z = item.zone || item;
            const level = item.latest_risk_level || 'LOW';
            const lat = z.latitude || 28.6139;
            const lng = z.longitude || 77.2090;

            return (
              <CircleMarker
                key={z.id}
                center={[lat, lng]}
                radius={20}
                pathOptions={{
                  color: getColor(level),
                  fillColor: getColor(level),
                  fillOpacity: 0.6,
                }}
              >
                <Popup>
                  <div className="p-1">
                    <h6 className="mb-1">{z.name}</h6>
                    <p className="mb-1 small"><strong>Risk:</strong> {level}</p>
                    <p className="mb-1 small"><strong>Capacity:</strong> {z.capacity_limit} max</p>
                    <p className="mb-0 small"><strong>Bottleneck:</strong> {z.is_bottleneck ? '⚠️ Yes' : 'No'}</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
