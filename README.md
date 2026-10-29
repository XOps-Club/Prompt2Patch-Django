# LinkSnip - URL Shortener & Real-Time Analytics Dashboard

LinkSnip is a high-performance URL shortener and real-time telemetry analytics dashboard built with **Python 3.14**, **Django 6.1**, **SQLite**, and modern Vanilla HTML5/CSS/JavaScript.

---

## Features
- **Instant URL Shortening**: Create fast, reliable short links with custom or auto-generated 6-character slugs.
- **Real-Time Click Analytics**: Track total clicks, unique visitors, referrers, and conversion rates.
- **Modern Dark SaaS Dashboard**: Cyberpunk-inspired dashboard with live telemetry cards and an interactive link directory.
- **Link Management**: Archive (soft-delete) and restore links seamlessly.
- **QR Code Support**: Instant QR code preview and download for shortened links.
- **Developer Ready**: Built on SQLite with zero external database configuration required.

---

## Tech Stack
- **Framework**: Django 6.1 (Python 3.14)
- **Database**: SQLite 3 (`db.sqlite3`)
- **Frontend**: Django Templates, Semantic HTML5, Modern Vanilla CSS, Vanilla JavaScript (zero Node/React dependency)
- **Dependencies**: `django`, `qrcode[pil]`, `pillow`
- **Testing**: Django Test Runner (`python manage.py test`)

---

## Project Structure
```text
├── backend/                  # Django Python Application
│   ├── config/               # Settings, WSGI/ASGI, URLs
│   ├── links/                # Core links app (models, views, services, tests)
│   ├── manage.py             # Backend management CLI
│   └── db.sqlite3            # SQLite database
├── frontend/                 # Presentation Layer
│   ├── static/               # Static assets (CSS styles, Vanilla JS)
│   │   ├── css/styles.css    # Cyberpunk SaaS styling
│   │   └── js/app.js         # Reactive client interactions
│   └── templates/            # Django HTML templates
│       ├── base.html         # Base shell & layout
│       ├── index.html        # Main dashboard
│       └── 404.html          # Redirect 404 page
├── manage.py                 # Root CLI wrapper
├── Makefile                  # Developer build & test targets
├── requirements.txt          # Python dependencies
├── NOTES.md                  # Team notes & AI prompting log
└── README.md
```

---

## Challenge Quickstart

### Automated Setup
```bash
# 1. Create branch
git checkout -b team-solution

# 2. Automated environment setup (venv, dependencies, migrations, seeds)
make setup

# 3. Run baseline test suite (identifies failing tests)
make test

# 4. Run local development server
make run
```
Open your browser at **`http://localhost:8000`**.

---

## Manual Setup (Alternative)

### 1. Prerequisites
Ensure Python 3.10+ is installed.

### 2. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization & Seeding
```bash
# Run migrations
python manage.py migrate

# Add sample links & telemetry data without deleting existing records
python manage.py seed

# Explicitly clear all links and click logs before reseeding
python manage.py seed --reset
```

### 4. Running the Development Server
```bash
python manage.py runserver
# Or using Makefile
make run
```
Open your browser at **`http://localhost:8000`**.

For deployment, set `DJANGO_DEBUG=false`, provide a strong `DJANGO_SECRET_KEY`, and set
`DJANGO_ALLOWED_HOSTS` to a comma-separated list of the hostnames serving the app.

---

## Running Tests
Run the test suite using:
```bash
python manage.py test links
# Or using Makefile
make test
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main interactive dashboard UI |
| `POST` | `/links` or `/api/links` | Create a shortened URL (`{ "originalUrl": "...", "customSlug": "..." }`) |
| `GET` | `/links?page=1&limit=10` | List paginated active or archived links (`includeDeleted=true`) |
| `GET` | `/links/stats` | Global analytics & telemetry overview |
| `GET` | `/links/<id_or_slug>` | Detailed link metrics |
| `DELETE` | `/links/<id>` | Soft-delete / archive a link |
| `POST` | `/links/<id>/restore` | Restore an archived link |
| `GET` | `/links/<id>/qr` | Generate QR code image URL for a short link |
| `GET` | `/<code_or_slug>` | Top-level redirect with referrer and IP hash telemetry logging |

---

## 🛠️ Incident Report: Reported Defects & Mission Brief

Your engineering squad has received production incident reports regarding several critical regressions in LinkSnip:

1. **INC-01: Lifecycle Archive Failure**
   - *Symptom*: When an operator archives a link (`DELETE /links/<id>`), the database state remains active, allowing short code redirection to continue.
2. **INC-02: Slug Collision on Restore**
   - *Symptom*: Restoring an archived link does not verify if its slug was claimed by another active link in the interim, causing state collisions.
3. **INC-03: Telemetry Dashboard Desync**
   - *Symptom*: The `/links/stats` endpoint and telemetry cards fail to return the active link count.
4. **INC-04: Pagination Bleed**
   - *Symptom*: Navigating pages in the active links directory counts archived records towards the total link count.
5. **INC-05: Missing QR Generator Implementation**
   - *Symptom*: QR code previews return empty strings on both the backend service and the client-side helper (`app.js`).
6. **INC-06: Strict Target URL Protocol Enforcement**
   - *Symptom*: The service layer must strictly reject unsupported protocols (`javascript:`, `file:`, etc.) and ensure only valid `http://` and `https://` URLs are accepted.

---

## 🎯 Evaluation Criteria
Judges evaluate your submission based on:
1. **Public & Hidden Test Suites**: All public tests (`make test`) and hidden judge checks (`eval_hidden`) must pass.
2. **Surgical Precision**: Minimal, focused diffs without unnecessary formatting rewrites or bloated AI boilerplate.
3. **Prompt Engineering Evidence**: Documented prompt sequences in `NOTES.md` demonstrating structured reasoning.
4. **Live Code Defense**: Defending your diagnosis and solutions during judge Q&A.
