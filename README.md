# Construct-X Dataspace Demonstrator

Demo app for the **Construct-X Dataspace**: it simulates tracking construction materials through their lifecycle using GS1 SSCC identifiers and EPCIS events.

The Vue frontend shows a generated SSCC with QR code and seven lifecycle steps (Einbau / Rückbau). Each step triggers the FastAPI backend to create and persist an EPCIS event from a template.

## Quick start

**Prerequisites:** Docker and Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

Source is bind-mounted — changes reload without rebuilding containers.

## Production

Build deployable images from the production Dockerfiles (not the dev variants used by Compose):

```bash
docker build -t demonstrator-backend ./backend
docker build -t demonstrator-frontend ./frontend
```

## Repository layout

```
backend/     FastAPI app, EPCIS templates, generated events (output/)
frontend/    Vue 3 + Vuetify UI
docs/        Detailed development documentation
```

## Documentation

For architecture, API details, lifecycle steps, Docker notes, and development log, see **[docs/index.md](docs/index.md)**.
