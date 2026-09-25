-- =========================================================================
-- CrowdSafe: AI-Based Stampede Risk Reporting System
-- PostgreSQL Database Schema & Initial Seed Data
-- =========================================================================

-- Clean existing tables (if any)
DROP TABLE IF EXISTS crowd_telemetry CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS zones CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- -------------------------------------------------------------------------
-- 1. USERS TABLE
-- -------------------------------------------------------------------------
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'citizen', -- 'citizen', 'authority', 'admin'
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- -------------------------------------------------------------------------
-- 2. ZONES TABLE (Monitored sectors, corridors, gates, stairwells)
-- -------------------------------------------------------------------------
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50) NOT NULL DEFAULT 'plaza', -- 'gate', 'corridor', 'plaza', 'stairwell'
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    area_sqm DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    capacity_limit INTEGER NOT NULL DEFAULT 200,
    is_bottleneck BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_zones_code ON zones(zone_code);

-- -------------------------------------------------------------------------
-- 3. REPORTS TABLE (Citizen and Camera Ingestion)
-- -------------------------------------------------------------------------
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    media_type VARCHAR(20) DEFAULT 'image', -- 'image', 'video'
    media_path VARCHAR(255),
    processed_image_path VARCHAR(255),
    estimated_count INTEGER NOT NULL DEFAULT 0,
    density DOUBLE PRECISION NOT NULL DEFAULT 0.0, -- persons per m^2
    risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW', -- 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    surge_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0, -- persons per min
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSED',
    user_description TEXT,
    recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_zone_created ON reports(zone_id, created_at DESC);
CREATE INDEX idx_reports_risk_level ON reports(risk_level);

-- -------------------------------------------------------------------------
-- 4. ALERTS TABLE (Emergency Warnings & Dispatches)
-- -------------------------------------------------------------------------
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
    risk_level VARCHAR(20) NOT NULL, -- 'HIGH', 'CRITICAL'
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    message TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    acknowledged_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_active ON alerts(is_active, created_at DESC);

-- -------------------------------------------------------------------------
-- 5. CROWD TELEMETRY TABLE (Time-Series Analytics)
-- -------------------------------------------------------------------------
CREATE TABLE crowd_telemetry (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    headcount INTEGER NOT NULL DEFAULT 0,
    density DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    surge_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_zone_time ON crowd_telemetry(zone_id, timestamp DESC);

-- =========================================================================
-- INITIAL SEED DATA
-- =========================================================================

-- Seed Users (Passwords hashed for 'password123')
INSERT INTO users (username, email, password_hash, role, phone) VALUES
('commander', 'police.command@crowdsafe.gov', 'scrypt:32768:8:1$u7xK38rZc...$sample', 'authority', '+91 99999 11111'),
('inspector_raj', 'raj@venue.org', 'scrypt:32768:8:1$u7xK38rZc...$sample', 'authority', '+91 99999 22222'),
('citizen_sam', 'sam@example.com', 'scrypt:32768:8:1$u7xK38rZc...$sample', 'citizen', '+91 88888 33333');

-- Seed Monitored Zones
INSERT INTO zones (zone_code, name, zone_type, latitude, longitude, area_sqm, capacity_limit, is_bottleneck) VALUES
('GATE_NORTH_1', 'North Main Gate 1', 'gate', 28.6139, 77.2090, 80.0, 300, TRUE),
('PLAZA_CONCOURSE', 'Central Stadium Concourse', 'plaza', 28.6148, 77.2105, 500.0, 2000, FALSE),
('CORRIDOR_EAST_B', 'East Exit Corridor B', 'corridor', 28.6130, 77.2082, 45.0, 150, TRUE),
('STAIRWELL_SOUTH_4', 'South Grand Stairwell 4', 'stairwell', 28.6122, 77.2075, 40.0, 120, TRUE);

-- Seed Sample Active Alerts
INSERT INTO alerts (zone_id, risk_level, risk_score, message, is_active) VALUES
(1, 'CRITICAL', 88.5, 'Critical crowd surge detected at North Main Gate 1. Inflow exceeds safe bottleneck capacity. Diversion advised.', TRUE),
(3, 'HIGH', 68.0, 'Impeded flow detected at East Exit Corridor B. Density at 4.2 persons/m2.', TRUE);

-- Seed Initial Telemetry History for Charting
INSERT INTO crowd_telemetry (zone_id, headcount, density, surge_rate, timestamp) VALUES
(1, 140, 1.75, 5.0, CURRENT_TIMESTAMP - INTERVAL '30 minutes'),
(1, 190, 2.37, 10.0, CURRENT_TIMESTAMP - INTERVAL '25 minutes'),
(1, 230, 2.87, 8.0, CURRENT_TIMESTAMP - INTERVAL '20 minutes'),
(1, 280, 3.50, 10.0, CURRENT_TIMESTAMP - INTERVAL '15 minutes'),
(1, 330, 4.12, 10.0, CURRENT_TIMESTAMP - INTERVAL '10 minutes'),
(1, 390, 4.87, 12.0, CURRENT_TIMESTAMP - INTERVAL '5 minutes'),
(1, 440, 5.50, 10.0, CURRENT_TIMESTAMP);
