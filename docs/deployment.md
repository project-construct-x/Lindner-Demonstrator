# Deployment

## Local dev

`compose.yml` builds `backend/Dockerfile.dev` and `frontend/Dockerfile.dev`, publishes ports 8000 and 3000, and bind-mounts both trees. Uvicorn runs with `--reload`. Vite uses polling so HMR works in Docker (`frontend/vite.config.mts`).

```bash
docker compose up --build
```

The backend entrypoint creates `.venv` on first start. After `requirements.txt` changes, reinstall inside the container or delete `backend/.venv`.

## Images and deploy compose

Production images: `backend/Dockerfile`, `frontend/Dockerfile` (build, then nginx). `compose.deploy.yml` is the deploy compose file. Set `EPCAT_BASE_URL` before the backend serves traffic. The frontend must call the API with `VITE_BACKEND_BASE_URL` ending in `/api`.

A reverse proxy should send `/api/**` to FastAPI and every other path to the static frontend. See `README.md`.

## Helm

Chart `helm/` (`Chart.yaml` name `demonstrator`) deploys both services. Image names, ingress, and the backend PVC for `/backend/output` are in `helm/values.yaml`. EECC overrides: `helm/values-eecc.yaml`. Scripts: `install.sh`, `upgrade.sh`, `uninstall.sh`, `setup-pull-secret.sh`.

## Raspberry Pi

`pi/` is the scanner image deployed on a Pi (`pi/README.md`, `pi/qr_scanner.py`). It is not part of the web app containers.
