<<<<<<< HEAD
# Construct-X Template Repository

Template repository for Construct-X.

## About
Use this template during repository creation to include relevant files and a default configuration. For your project, please add a description with additional details about your project here.

## Documentation
This documentation is located in the `/docs` folder.

## Getting Started
Relevant prerequisites and installation instructions are introduced.

### Prerequisites
To run and work with this project, the following prerequisites are needed:
- Tool 1
- Tool 2

### Installation
To run this project, execute the following steps:
1. Clone this repository
   ```sh
   git clone https://github.com/Projekt-Construct-X/XXX.git
   ```
2. Do this
   ```sh
   cd XXX
   ```
3. Do that
   ```sh
   docker compose up
   ```

## License
All code files are distributed under the Apache 2.0 license. See [LICENSE](./LICENSE) for more information.

All non-code files are distributed under the Creative Commons Attribution 4.0 International license. See [LICENSE_non-code](./LICENSE_non-code) for more information.
=======
# Construct-X Dataspace Demonstrator

Demo app for the **Construct-X Dataspace**: it simulates tracking construction materials through their lifecycle using GS1 identifiers and EPCIS 2.0 events.

The Vue frontend generates an SSCC Digital Link, displays it as a QR code, and walks through seven lifecycle steps (Einbau / Rückbau). Each step triggers the FastAPI backend to:

1. Render one or more EPCIS events from JSON templates
2. Wrap them in an `EPCISDocument`
3. Persist the document to `backend/output/{sscc}/`
4. POST the document to the EPCAT2 capture endpoint

## Development

**Prerequisites:** Docker and Docker Compose

```bash
docker compose up --build
```

| Service            | URL |
| ------------------ | --- |
| Frontend           | http://localhost:3000 |
| Backend API        | http://localhost:8000/api |
| Trigger endpoint   | `POST http://localhost:8000/api/trigger/<1-7>` |
| API docs (Swagger) | http://localhost:8000/api/docs |

Source is bind-mounted — changes reload without rebuilding containers.

> After adding Python dependencies, recreate the backend venv or run  
> `docker compose exec backend .venv/bin/pip install -r requirements.txt`  
> inside the running container.

## Production

Build deployable images from the production Dockerfiles (not the dev variants used by Compose):

```bash
docker build -t demonstrator-backend ./backend
docker build -t demonstrator-frontend ./frontend
```

Set `EPCAT_BASE_URL` in `backend/.env.production` before deploying the backend.

### Reverse proxy

In production, a reverse proxy must route traffic by path:

| Path | Target |
|------|--------|
| `/api/**` | Backend (FastAPI) — includes `POST /api/trigger/<1-7>` and Swagger at `/api/docs` |
| Everything else | Frontend (static Vue app) |

Example:

```
https://demonstrator.example.com/              → frontend
https://demonstrator.example.com/api/trigger/1 → backend
https://demonstrator.example.com/api/docs      → backend (Swagger)
```

Set `VITE_BACKEND_BASE_URL=https://demonstrator.example.com/api` in `frontend/.env.production` so the UI calls the proxied API path.

## Repository layout

```
backend/
  main.py              FastAPI app and routes
  epcis/               Event templates, document template, generator, capture client
  epcis-original/      Reference templates (not used at runtime)
  output/              Generated EPCIS documents per SSCC (gitignored)
frontend/              Vue 3 + Vuetify UI
docs/                  Detailed development documentation
```

## Documentation

For architecture, API, lifecycle steps, EPCIS templates, and deployment, see **[docs/index.md](docs/index.md)**.
>>>>>>> cab749405c4cfb775eaa9e9e369aad76a5e17cef
