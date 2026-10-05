# CrowdSafe Project Overview

## What the project is intended to do

CrowdSafe is intended to help identify dangerous crowd conditions before they
become stampede or crush incidents. A citizen submits a crowd photo or video;
the backend estimates crowd size and density, assigns a risk level, and makes
reports and alerts available to authorities.

The repository contains parts of this workflow, but the application is not yet
fully integrated. In particular, the currently wired dashboard/API path and
the newer upload/AI/analytics code use different database models and routes.

## Current application path

The path wired into the root React app is:

```text
frontend/src/main.jsx
  -> frontend/src/App.jsx
  -> frontend/src/Dashboard.jsx
  -> frontend/src/reportsApi.js
  -> GET /api/authority/reports
  -> backend/app/routes/authority_routes.py
  -> backend/app/database.py + backend/app/models.py
  -> PostgreSQL
```

`Dashboard.jsx` requests reports when it loads and polls every 30 seconds. It
can also acknowledge a report. The Flask app factory in
`backend/app/__init__.py` currently registers only the authority blueprint. It
also serves uploaded media from `/uploads/...` and provides `/health`.

## Intended report-processing flow

The citizen upload and AI pipeline code describes a broader, intended path:

```text
frontend/src/pages/CitizenUpload.jsx
  -> POST /api/reports
  -> backend/app/routes/report_routes.py
  -> FrameExtractor (video) / CrowdCounter (image)
  -> TrendAnalyzer + RiskClassifier
  -> persist report and crowd telemetry
  -> create and dispatch an alert for HIGH or CRITICAL risk
```

The authority and analytics pages are intended to display the reports, alerts,
zones, and historical trends created by this pipeline. They are not currently
the pages rendered by `frontend/src/App.jsx`.

## File responsibilities and dependencies

| Area | Main files | Responsibility and dependencies |
|---|---|---|
| Backend startup | `run.py`, `backend/run.py` | Create the Flask application. The root `run.py` adds `backend/` to Python's import path before importing the app. |
| Flask setup | `backend/app/__init__.py` | Creates the app, configures CORS, registers the authority blueprint, serves uploads, and exposes `/health`. |
| Current frontend entry | `frontend/src/main.jsx`, `frontend/src/App.jsx` | Loads the styles and renders `Dashboard.jsx`. |
| Current dashboard | `frontend/src/Dashboard.jsx`, `frontend/src/reportsApi.js` | Displays report data and calls the authority reports/acknowledgement API. |
| Current authority API | `backend/app/routes/authority_routes.py` | Uses `SessionLocal` from `backend/app/database.py` and `Report`/`Alert` from `backend/app/models.py`. |
| Database connection and ORM | `backend/app/database.py`, `backend/app/models.py` | Creates the SQLAlchemy engine/session and defines the `User`, `Authority`, `Report`, and `Alert` tables. |
| SQL schema and seed data | `database/schema.sql` | Defines an alternate schema containing `users`, `zones`, `reports`, `alerts`, and `crowd_telemetry`, plus sample data. |
| Citizen upload UI | `frontend/src/pages/CitizenUpload.jsx` | Expects a zones endpoint and submits multipart form data to `/api/reports`. |
| Report-processing API | `backend/app/routes/report_routes.py` | Expects Flask-SQLAlchemy `db`, `Zone`, `CrowdTelemetry`, and report models; calls the analysis and alert services. |
| Analysis services | `backend/app/services/*.py` | Separate processing responsibilities, described below. |
| Authority page | `frontend/src/pages/AuthorityDashboard.jsx` | Expects dashboard, zone, alert acknowledgement, and emergency-dispatch endpoints. |
| Analytics page/API | `frontend/src/pages/Analytics.jsx`, `backend/app/routes/analytics_routes.py` | The page requests summary and zone trend data; the API reads reports, zones, and telemetry. |
| Authentication | `frontend/src/pages/Login.jsx`, `backend/app/routes/auth_routes.py` | Login UI and JWT route code. The auth blueprint is not currently registered by the app factory. |

### Analysis services

| Service | Purpose |
|---|---|
| `backend/app/services/frame_extractor.py` | Samples frames from a video or stream for further processing. |
| `backend/app/services/crowd_counter.py` | Estimates the number of people and density using YOLO when available, otherwise a lightweight heuristic. |
| `backend/app/services/risk_classifier.py` | Maps density, crowd surge, bottleneck status, and capacity into a risk level and recommendation. |
| `backend/app/services/trend_analyzer.py` | Tracks observations and calculates rate of change, surge status, and a short-term forecast. |
| `backend/app/services/heatmap_generator.py` | Produces heatmap overlays and spatial grid summaries from detection points. |
| `backend/app/services/geo_matcher.py` | Stores zone/camera/exit relationships and performs basic spatial matching. |
| `backend/app/services/notifier.py` | Dispatches alert messages to registered handlers, including a console handler. |
| `backend/app/services/rate_limiter.py` | Suppresses repeated alerts during a cooldown period. |
| `backend/app/services/task_queue.py` | Provides an in-memory asynchronous priority queue for background tasks. |

## Integration gaps to resolve

These differences matter when adding features, because the pages and routes
cannot all work together until their contracts are aligned:

1. **Blueprint registration:** `backend/app/__init__.py` registers only
   `authority_bp`. The report, auth, and analytics blueprints are not currently
   registered.
2. **Database/API model mismatch:** The registered authority API uses the
   plain SQLAlchemy session and `User`, `Authority`, `Report`, and `Alert`
   models. The report/auth/analytics route modules import a Flask-SQLAlchemy
   `db` object and models such as `Zone` and `CrowdTelemetry`, which are not
   present in the current `backend/app/database.py` and `backend/app/models.py`.
3. **Schema mismatch:** `database/schema.sql` describes zones and telemetry and
   uses fields such as `created_at`. The current ORM model set instead has
   authorities and fields such as `submitted_at`. Choose one schema and make
   the ORM models and routes match it.
4. **Frontend routing:** `frontend/src/App.jsx` renders only `Dashboard.jsx`.
   The upload, login, authority-dashboard, and analytics pages are not
   reachable through the current app entry.
5. **Frontend API configuration:** `frontend/src/reportsApi.js` uses an
   explicit API base URL. Other pages use relative `/api/...` URLs, while
   `frontend/vite.config.js` does not currently configure an API proxy.
6. **Duplicate backend files and outdated docs:** There are also
   `backend/database.py` and `backend/models.py`. The root README and
   `PROJECT_STRUCTURE.md` describe differing project states, so verify which
   implementation is current before extending those duplicate files.

## Suggested development order

1. Select the canonical database schema and ORM approach.
2. Align the models, schema, configuration, and route imports with that choice.
3. Register and test the report, authority, analytics, and auth blueprints
   that are in scope.
4. Connect the citizen upload page to the report API and verify upload
   validation and persistence.
5. Connect the authority and analytics pages to real API responses; configure
   a consistent API base URL or development proxy.
6. Validate the AI pipeline against sample images/videos and replace demo or
   fallback data with explicit, measurable behavior.

## Local development entry points

- Backend: run `python run.py` from the repository root, or use the documented
  backend entry point with its required working directory.
- Frontend: run `npm run dev` from `frontend/`.
- Backend dependencies are listed in `backend/requirements.txt`.
- Frontend scripts and dependencies are listed in `frontend/package.json`.

Check the README and environment configuration before running locally, and do
not commit database passwords, JWT secrets, or other credentials.
