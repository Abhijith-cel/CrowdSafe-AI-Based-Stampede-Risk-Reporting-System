import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'citizen',
    phone: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
    const payload = isRegister
      ? formData
      : { identifier: formData.username || formData.email, password: formData.password };

    try {
      const res = await axios.post(endpoint, payload);
      localStorage.setItem('crowdsafe_token', res.data.access_token);
      localStorage.setItem('crowdsafe_user', JSON.stringify(res.data.user));

      if (res.data.user.role === 'authority' || res.data.user.role === 'admin') {
        navigate('/dashboard');
      } else {
        navigate('/upload');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-lg border-0 rounded-4">
            <div className="card-body p-5">
              <div className="text-center mb-4">
                <h3 className="fw-bold text-dark">
                  {isRegister ? 'Create Account' : 'CrowdSafe Login'}
                </h3>
                <p className="text-muted small">
                  AI-Powered Stampede Risk Reporting & Public Safety
                </p>
              </div>

              {error && <div className="alert alert-danger py-2 small">{error}</div>}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label small fw-semibold">Username or Email</label>
                  <input
                    type="text"
                    name="username"
                    className="form-control"
                    placeholder="Enter username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </div>

                {isRegister && (
                  <>
                    <div className="mb-3">
                      <label className="form-label small fw-semibold">Email</label>
                      <input
                        type="email"
                        name="email"
                        className="form-control"
                        placeholder="name@domain.com"
                        value={formData.email}
                        onChange={handleChange}
                        required
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label small fw-semibold">Account Role</label>
                      <select
                        name="role"
                        className="form-select"
                        value={formData.role}
                        onChange={handleChange}
                      >
                        <option value="citizen">Citizen Reporter</option>
                        <option value="authority">Venue Authority / Police</option>
                      </select>
                    </div>
                    <div className="mb-3">
                      <label className="form-label small fw-semibold">Contact Phone (Optional)</label>
                      <input
                        type="text"
                        name="phone"
                        className="form-control"
                        placeholder="+91 98765 43210"
                        value={formData.phone}
                        onChange={handleChange}
                      />
                    </div>
                  </>
                )}

                <div className="mb-4">
                  <label className="form-label small fw-semibold">Password</label>
                  <input
                    type="password"
                    name="password"
                    className="form-control"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100 py-2 fw-semibold"
                  disabled={loading}
                >
                  {loading ? 'Processing...' : isRegister ? 'Register' : 'Sign In'}
                </button>
              </form>

              <div className="text-center mt-4">
                <button
                  className="btn btn-link text-decoration-none small text-secondary"
                  onClick={() => {
                    setIsRegister(!isRegister);
                    setError('');
                  }}
                >
                  {isRegister
                    ? 'Already have an account? Sign In'
                    : "Don't have an account? Register as Citizen/Authority"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
