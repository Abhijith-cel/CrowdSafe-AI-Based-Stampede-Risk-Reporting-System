import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import CitizenUpload from './pages/CitizenUpload';
import AuthorityDashboard from './pages/AuthorityDashboard';
import Analytics from './pages/Analytics';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-vh-100 bg-light d-flex flex-column">
        <Navbar />
        <main className="flex-grow-1">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/upload" element={<CitizenUpload />} />
            <Route path="/dashboard" element={<AuthorityDashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
        <footer className="bg-white border-top py-3 text-center text-muted small mt-auto">
          CrowdSafe &copy; {new Date().getFullYear()} — AI-Based Stampede Risk Reporting & Public Safety
        </footer>
      </div>
    </BrowserRouter>
  );
}
