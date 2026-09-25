# CrowdSafe: AI-Based Stampede Risk Reporting System
## Comprehensive Project Report & Technical Specifications

### 1. Abstract
Stampedes and crowd crushes at mass gatherings (religious pilgrimages, sports arenas, music festivals, transport transit hubs) represent catastrophic public safety failures. The CrowdSafe system provides continuous computer-vision-based density monitoring, automated velocity tracking, real-time crush hazard classification, and multi-channel emergency alerting to empower security authorities to intervene before crowd density reaches fatal shockwave thresholds.

### 2. Objectives
- Automated person counting and density estimation using YOLOv8 and CSRNet dilated convolutional networks.
- Multi-tier risk classification based on Fruin's Level of Service (LOS) and Keith Still crowd safety guidelines ($>5.0 \text{ persons/m}^2$ critical crush boundary).
- Rate-of-change and surge detection to forecast crowd collapse 5 to 15 minutes in advance.
- Citizen mobile reporting pipeline for ground truth crowdsourced incident escalation.
- Situational awareness dashboard for police and venue commanders with Leaflet GIS mapping, real-time alert dispatch, and emergency gate actuation directives.

### 3. Architecture Overview
- **Backend API Layer**: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, PostgreSQL.
- **Deep Learning Layer**: PyTorch, Torchvision, Ultralytics YOLOv8, CSRNet ShanghaiTech Part-A.
- **Frontend Layer**: React, Vite, Leaflet GIS, Chart.js, Bootstrap 5.
- **Background Pipeline**: Frame extraction, rate limiting, and prioritized async queues.
