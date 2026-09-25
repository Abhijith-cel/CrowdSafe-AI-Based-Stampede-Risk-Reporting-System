import React from 'react';

export default function AlertBanner({ alerts = [], onAcknowledge }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="container-fluid py-2">
      {alerts.map((alert) => {
        const isCritical = alert.risk_level === 'CRITICAL';
        return (
          <div
            key={alert.id}
            className={`alert ${isCritical ? 'alert-danger' : 'alert-warning'} alert-dismissible fade show shadow-sm d-flex justify-content-between align-items-center mb-2`}
            role="alert"
          >
            <div>
              <span className={`badge ${isCritical ? 'bg-danger' : 'bg-warning text-dark'} me-2`}>
                {alert.risk_level}
              </span>
              <strong>{alert.zone_name || 'Zone'}</strong>: {alert.message}
            </div>
            {onAcknowledge && (
              <button
                type="button"
                className="btn btn-sm btn-outline-dark ms-3"
                onClick={() => onAcknowledge(alert.id)}
              >
                Acknowledge
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
