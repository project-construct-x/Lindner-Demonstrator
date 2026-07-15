# Construct-X Dataspace Demonstrator

A demo application for the **Construct-X Dataspace** project. It simulates the lifecycle tracking of construction materials using GS1 SSCC identifiers and EPCIS events.

The demonstrator lets users walk through seven supply-chain steps — from manufacturer dispatch to refurbishment — by pressing buttons that represent QR-code scans. Each step triggers the backend to generate and persist an EPCIS event from a template.

## Architecture

```
┌─────────────────┐     POST /trigger/{step-id}     ┌─────────────────┐
│  Vue + Vuetify  │ ──────────────────────────────► │  FastAPI        │
│  Frontend       │         { sscc: "..." }           │  Backend        │
│                 │ ◄──────────────────────────────   │                 │
│  - SSCC display │         200 OK / error            │  - EPCIS gen    │
│  - QR code      │                                   │  - File persist │
│  - 7 step btns  │                                   │  - Console log  │
└─────────────────┘                                   └────────┬────────┘
                                                               │
                                                               ▼
                                                    ┌─────────────────────┐
                                                    │  Volume: /data/     │
                                                    │  epcis/{sscc}/      │
                                                    └─────────────────────┘
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Vue 3, Vuetify 3 | UI for SSCC display, QR code, and lifecycle step simulation |
| Backend | Python, FastAPI | EPCIS event generation from templates, persistence, logging |
| Dev runtime | Docker Compose | Local development with hot-reload |
| Prod runtime | Docker (multi-stage) | Deployable service images |

## Lifecycle Steps

Each button simulates scanning a QR code containing a GS1 Digital Link SSCC at a specific point in the material lifecycle:

| Step ID | Label (DE) | Description |
|---------|------------|-------------|
| `ausgang-hersteller` | Ausgang beim Hersteller | Material leaves the manufacturer |
| `baustellen-eingang` | Baustellen-Eingang | Arrival at the construction site |
| `einbau` | Einbau | Installation on site |
| `rueckbau` | Rückbau | Deconstruction / removal |
| `ausgang-baustelle` | Ausgang Baustelle | Material leaves the construction site |
| `eingang-hersteller` | Eingang beim Hersteller | Return to manufacturer |
| `aufbereitung` | Aufbereitung | Refurbishment / reprocessing |

After a step is triggered, its button becomes disabled. Generating a new SSCC resets all buttons.

## GS1 SSCC & Digital Link

The frontend generates a new 18-digit SSCC on every page load. It is displayed as a GS1 Digital Link URI:

```
https://id.gs1.org/00/{18-digit-sscc}
```

A QR code encoding this URI is rendered on the page so it can be scanned (or simulated via the buttons).

## Quick Start

> **Status:** Frontend and backend are not initialized yet. Use the official scaffolding tools first (see [docs/index.md](docs/index.md#project-initialization)), then start the dev environment.

### Prerequisites

- Docker and Docker Compose
- Node.js 22+ and Python 3.12+ (for project initialization)

### 1. Initialize projects

See [docs/index.md — Project Initialization](docs/index.md#project-initialization) for the recommended commands.

### 2. Local development (hot-reload)

`Dockerfile.dev` runs development servers (Vite + Uvicorn `--reload`). Source code is bind-mounted — **no container restart needed** on file changes.

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### Production images

```bash
docker build -t demonstrator-backend ./backend
docker build -t demonstrator-frontend ./frontend
```

## API

### `POST /trigger/{step-id}`

Triggers EPCIS event generation for a lifecycle step.

**Path parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `step-id` | string | One of the seven step IDs (see table above) |

**Request body**

```json
{
  "sscc": "https://id.gs1.org/00/006141411234567890"
}
```

**Response**

```json
{
  "step_id": "ausgang-hersteller",
  "sscc": "https://id.gs1.org/00/006141411234567890",
  "event_file": "ausgang-hersteller.json"
}
```

The backend loads the matching template from `backend/epcis/templates/`, substitutes the SSCC, writes the event to the persistent volume under `epcis/{sscc}/`, and logs it to the console.

## Project Structure

```
demonstrator-dev-umgebung/
├── backend/
│   ├── Dockerfile              # Production image
│   ├── Dockerfile.dev          # Development image (used by compose)
│   ├── epcis/
│   │   └── templates/          # EPCIS event templates (one per step)
│   └── app/                    # FastAPI application
├── frontend/
│   ├── Dockerfile              # Production image (nginx)
│   ├── Dockerfile.dev          # Development image (Vite dev server)
│   └── src/                    # Vue application
├── docs/
│   └── index.md                # Development documentation
├── docker-compose.yaml         # Local dev environment
└── README.md
```

## Data Persistence

Generated EPCIS events are stored on a Docker volume mounted at `/data` in the backend container:

```
/data/epcis/{sscc}/
├── ausgang-hersteller.json
├── baustellen-eingang.json
└── ...
```

Each SSCC gets its own subfolder; each triggered step appends one event file.

## Documentation

See [docs/index.md](docs/index.md) for detailed development notes, design decisions, and ongoing learnings.

## License

Internal Construct-X project — license TBD.
