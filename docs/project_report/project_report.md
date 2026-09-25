# CrowdSafe: AI-Based Stampede Risk Reporting System
## Comprehensive Project Report & System Architecture Specification

---

### 1. Executive Summary

Crowd crushes and stampedes represent preventable public safety emergencies. In mass gatherings—including religious festivals, major athletic events, music concerts, and multimodal transport hubs—rapid accumulation of pedestrians in constrained geometry creates deadly compressive asphyxia and progressive crowd collapse. 

**CrowdSafe** is an intelligent, real-time edge-to-cloud monitoring and reporting system that combines:
1. **Computer Vision Headcount & Density Estimation** (YOLOv8 + CSRNet).
2. **Surge & Velocity Dynamics Analysis** to detect shockwaves and turbulence.
3. **Crowdsourced Citizen Reporting** for direct ground-truth incident escalation.
4. **Command & Control Authority Dashboard** with Leaflet GIS mapping, automated alerts, and emergency response workflows.

---

### 2. Objectives
- Automated person counting and density estimation using YOLOv8 and CSRNet dilated convolutional networks.
- Multi-tier risk classification based on Fruin's Level of Service (LOS) and Keith Still crowd safety guidelines (>5.0 persons/m^2 critical crush boundary).
- Rate-of-change and surge detection to forecast crowd collapse 5 to 15 minutes in advance.
- Citizen mobile reporting pipeline for ground truth crowdsourced incident escalation.
- Situational awareness dashboard for police and venue commanders with Leaflet GIS mapping, real-time alert dispatch, and emergency gate actuation directives.

---

### 3. System Architecture

```
                    +--------------------------------+
                    |        Input Ingestion         |
                    |  - Fixed CCTV RTSP Feeds       |
                    |  - Citizen Media Uploads       |
                    +---------------+----------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                         Flask Backend API                             |
|  - Auth & Role-Based Access Control (JWT)                             |
|  - Ingestion & Validation (/api/reports/upload)                       |
|  - Frame Extraction & Preprocessing (OpenCV)                          |
+-------------------+-----------------------------------+---------------+
                    |                                   |
                    v                                   v
+-----------------------------------+   +-------------------------------+
|     Computer Vision Inference     |   |      Spatial & Analytics      |
|  - YOLOv8 (Low-Moderate density)  |   |  - Fruin Level of Service     |
|  - CSRNet (High-density crowds)   |   |  - Surge Velocity (dCount/dt) |
|  - Heatmap Generation (Gaussian)  |   |  - Telemetry Recording        |
+-------------------+---------------+   +---------------+---------------+
                    |                                   |
                    +-----------------+-----------------+
                                      |
                                      v
                    +-----------------------------------+
                    |         PostgreSQL Database       |
                    |  - users, zones, reports          |
                    |  - alerts, crowd_telemetry        |
                    +-----------------+-----------------+
                                      |
                                      v
+-----------------------------------------------------------------------+
|                    React + Vite Frontend Interface                    |
|  - Live Interactive GIS Map (Leaflet)                                 |
|  - Headcount, Density & Surge Trend Charts (Chart.js)                 |
|  - Real-Time Warning Banner & Emergency Action Dispatch              |
|  - Mobile-Optimized Citizen Report Portal                             |
+-----------------------------------------------------------------------+
```

---

### 4. Core Risk Assessment Methodology

The system evaluates risk using **Fruin's Level of Service (LOS)** standards and empirical crowd dynamics:

| Level | Density (P/m^2) | Flow Characteristics | System Status |
| :--- | :--- | :--- | :--- |
| **LOS A-B** | < 1.0 | Free pedestrian movement, unimpeded crossing | `LOW` (Normal) |
| **LOS C-D** | 1.0 - 2.0 | Restricted movement, bypass requires effort | `LOW` (Monitoring) |
| **LOS E** | 2.0 - 3.5 | Significant friction, shuffling gait | `MODERATE` (Advisory) |
| **LOS F** | 3.5 - 5.0 | Severe jamming, physical contact, stop-and-go | `HIGH` (Intervention) |
| **Crush Threshold**| > 5.0 | Shockwave propagation, involuntary movement | `CRITICAL` (Evacuation) |

**Surge Velocity Metric**:
`Surge Rate = (Count_current - Count_previous) / delta_time (persons/min)`

When `Surge Rate > 15 persons/min` concurrently with `Density > 3.5 persons/m^2`, an immediate emergency dispatch recommendation is triggered.
