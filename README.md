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
