# CrowdSafe: AI-Based Stampede Risk Reporting System

MCA final year project. Citizens upload a **photo or short video** of a crowd along with their GPS location. An AI model estimates crowd density and assigns a risk level. The nearest authority sees the report on a dashboard and responds.

- **Citizen end:** mobile-first upload (photo/video + auto GPS)
- **Authority end:** web dashboard, usable on laptop and on mobile during patrol
- **Risk levels (4 tiers):** Low, Moderate, High, Critical
- **No CCTV** required

---

## 1. Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Flask |
| Database | PostgreSQL via plain SQLAlchemy (`engine` / `Base` / `SessionLocal`) |
| AI | OpenCV, PyTorch, pretrained YOLOv8 or CSRNet (no training from scratch) |
| Frontend | React (authority dashboard first) |
| Maps | Leaflet.js + OpenStreetMap |
| Environment | Windows, PowerShell, virtual environment at `backend/venv` |

> Python 3.14 is not supported by `psycopg2-binary`. Always use the 3.12 venv.

---

## 2. Folder Structure

```
CrowdSafe AI-Based Stampede Risk Reporting System/
├── apps.py                     # Entry point (decide: keep apps.py or rename to run.py)
├── struct.txt                  # Folder listing reference
│
├── backend/
│   ├── .env                    # DB credentials and secrets (never commit)
│   ├── config.py               # Flask config (auto-generated, not yet wired in)
│   ├── requirements.txt        # Installed package versions
│   ├── test_connection.py      # Verifies DB connection and creates tables
│   ├── venv/                   # Python 3.12 virtual environment
│   ├── models_pretrained/      # CSRNet / YOLOv8 weight files (gitignored)
│   │
│   └── app/
│       ├── __init__.py         # Currently empty (see Section 4)
│       ├── database.py         # SQLAlchemy engine, session, Base
│       ├── models.py           # Table definitions (User, Authority, Report, Alert)
│       │
│       ├── routes/             # API endpoints (planned)
│       │   ├── auth_routes.py
│       │   ├── report_routes.py
│       │   ├── authority_routes.py
│       │   └── analytics_routes.py
│       │
│       ├── services/           # AI and business logic (planned)
│       │   ├── crowd_counter.py
│       │   ├── frame_extractor.py
│       │   ├── risk_classifier.py
│       │   ├── trend_analyzer.py
│       │   ├── heatmap_generator.py
│       │   ├── geo_matcher.py
│       │   ├── notifier.py
│       │   ├── rate_limiter.py
│       │   └── task_queue.py
│       │
│       └── uploads/            # Citizen photo/video files
│
├── frontend/                   # React app (not yet created)
├── database/                   # schema.sql (not yet created)
└── docs/project_report/        # MCA documentation (not yet created)
```

---

## 3. What Each Key File Does

### Working

| File | Purpose | Connects to |
|---|---|---|
| `backend/.env` | Stores `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, JWT secret, SMTP settings, density thresholds | Read by `database.py` |
| `backend/app/database.py` | Finds `.env` using `Path(__file__)`, builds the `postgresql+psycopg2://` URL, creates `engine`, `SessionLocal`, `Base`, and `get_db()` | Used by `models.py`, `test_connection.py`, and later all routes |
| `backend/app/models.py` | Defines the four tables and their relationships | Imports `Base` from `database.py` |
| `backend/test_connection.py` | Opens a real DB connection and runs `Base.metadata.create_all()` | Imports `database.py` and `models.py` |

### Planned

| Folder | Purpose |
|---|---|
| `routes/` | Flask endpoints: auth, report upload, authority dashboard, analytics |
| `services/` | `crowd_counter` (model inference), `frame_extractor` (video only), `risk_classifier` (count to tier), `geo_matcher` (Haversine nearest authority), `notifier`, `rate_limiter`, `task_queue`, `trend_analyzer`, `heatmap_generator` |

---

## 4. How the Files Connect

```
.env
  │  (read via Path(__file__), explicit path)
  ▼
app/database.py ──► engine, SessionLocal, Base
  │                      │
  │                      ▼
  │                app/models.py ──► User, Authority, Report, Alert
  │                      │
  ▼                      ▼
test_connection.py ──► create_all() ──► tables in PostgreSQL (crowdsafe_db)
```

Later stages:

```
Citizen upload ──► report_routes.py ──► services/ (frame_extractor, crowd_counter,
                                        risk_classifier, geo_matcher, notifier)
                                              │
                                              ▼
                                        reports + alerts tables
                                              │
                                              ▼
Authority dashboard (React) ◄── authority_routes.py
```

### Notes on `app/__init__.py`

The IDE's built-in assistant generated a full Flask app factory here (CORS, JWT, blueprints). It imported things that did not exist yet, so it was emptied. Reintroduce it once `routes/` and `config.py` are ready.

---

## 5. Database Tables

| Table | Key columns |
|---|---|
| `users` | id, name, email, password_hash, role (`citizen` / `authority` / `admin`) |
| `authorities` | id, name, station_lat, station_long, jurisdiction_radius_km, contact_email |
| `reports` | id, user_id, media_path, media_type, lat, long, context_tag, person_count, density_score, risk_level, status |
| `alerts` | id, report_id, authority_id, status, acknowledged_by, acknowledged_at |

**Pending schema changes to `models.py`:**

- Rename `video_path` to `media_path`
- Add `media_type` (`image` or `video`)
- Add `context_tag` if not present (`open_ground`, `narrow_lane`, `stairway`, `platform`)
- `risk_level` values: `Low`, `Moderate`, `High`, `Critical`

---

## 6. Build Order

1. Database: **done**
2. Authority dashboard in React, on mock data first, then seeded DB data (**next**)
3. AI pipeline as a standalone script, tested on a sample image before any Flask wiring
4. Citizen upload page
5. Connect everything
6. Polish (analytics, notifications, rate limiting)

Login is skipped for the first build. One test authority is seeded directly in the database.

---

## 7. Open Items

- Check `backend/config.py` and `app/routes/` contents (auto-generated, may cause import errors)
- Confirm no duplicate `.env`, `config.py`, `database.py`, `models.py` at the project root or directly under `backend/`
- Decide `apps.py` vs `run.py` as the entry point
- Seed 2-3 authorities (not just one) so nearest-authority matching can be tested
- Choose YOLOv8 or CSRNet
- Choose per-context-tag density baselines
- Design real authentication later (JWT is installed but unused)
- Decide how the dashboard learns about new reports (polling vs WebSocket)
- Add upload validation (file size, allowed types)
- Collect 10-20 test photos/videos

---

## 8. Environment Reminders

- Activate the venv before any command: `venv\Scripts\activate` (prompt must show `(venv)`)
- Use PowerShell syntax, for example `Remove-Item -Recurse -Force venv`
- The project folder path contains spaces, so always resolve `.env` with an explicit path
- The IDE assistant may regenerate `.env` with different variable names. `database.py` reads the `POSTGRES_*` names.
- Save files (Ctrl+S) before running. An unsaved dot on the tab means the disk copy is stale.
