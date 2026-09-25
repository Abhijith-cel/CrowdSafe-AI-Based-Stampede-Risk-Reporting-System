import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem('crowdsafe_token');
  const user = JSON.parse(localStorage.getItem('crowdsafe_user') || 'null');

  const handleLogout = () => {
    localStorage.removeItem('crowdsafe_token');
    localStorage.removeItem('crowdsafe_user');
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm px-3">
      <div className="container-fluid">
        <Link className="navbar-brand fw-bold d-flex align-items-center gap-2" to="/">
          <span className="badge bg-danger">AI</span> CrowdSafe
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarContent"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarContent">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <Link className="nav-link" to="/upload">
                📸 Citizen Report
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/dashboard">
                🛡️ Authority Dashboard
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/analytics">
                📈 Analytics & Trends
              </Link>
            </li>
          </ul>

          <div className="d-flex align-items-center gap-3">
            {token && user ? (
              <>
                <span className="text-light small">
                  👤 <strong>{user.username}</strong> ({user.role})
                </span>
                <button
                  onClick={handleLogout}
                  className="btn btn-outline-light btn-sm"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login" className="btn btn-primary btn-sm">
                Login / Register
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
