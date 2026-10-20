# Backend and API

Python 3.12, FastAPI, Uvicorn, httpx, pydantic-settings. Dev port 8000. Swagger: `/api/docs`.

## Layout

```
backend/
├── main.py                 # routes, CORS, SSE publish on step completion
├── models.py               # TriggerRequest is { sscc } only
├── config.py               # APP_ENV, paths, EPCAT_BASE_URL
├── health.py               # readiness
├── subscriptions.py        # in-memory SSE fan-out
├── epcis/
│   ├── generator.py        # render, document build, persist, capture
│   ├── capture.py          # POST {EPCAT_BASE_URL}/capture
│   ├── session_store.py    # in-memory SSCC session and step order
│   ├── steps.py
│   └── document.json, *.json
└── output/                 # gitignored EPCIS documents
```

## Generation

`POST /api/trigger/{step_number}` (`backend/main.py`, `backend/epcis/generator.py`):

1. Resolve step `1`–`7`. Unknown number → 404.
2. Validate the SSCC and that the previous step is done and this step is not (`session_store.validate_step_can_run`). Violation → 422.
3. On steps that need material, fill LGTINs. On step 1, also fill DESADV and PO.
4. Render each template with `string.Template`. Event times are staggered; each event gets a new `eventID`.
5. Wrap events in `document.json`. Write `output/{18-digit-sscc}/{n}.json`.
6. Log the document. POST it to EPCAT2. Capture HTTP failure → 502 (file is already on disk).
7. Mark the step complete and publish SSE `step_completed`.

Completed steps are not overwritten. A backend restart clears the in-memory session.

## Routes

| Method | Path | Role |
| --- | --- | --- |
| `GET` | `/health` | Liveness, body `ok` |
| `GET` | `/ready` | 503 when EPCAT URL, templates, or `output/` fail the checks in `health.py` |
| `POST` | `/api/trigger/{1-7}` | Body `{ "sscc": "https://id.gs1.org/00/…" }`. Returns `step_id`, `sscc`, `document_file`, `event_count` |
| `GET` | `/api/sscc/status?sscc=` | `{ sscc, completed_steps, completed_step_ids }` |
| `GET` | `/api/sscc/stream?sscc=` | SSE: `snapshot`, `step_completed`, `heartbeat` (~15s) |

Trigger errors: 404 unknown step or missing template, 422 bad SSCC or illegal step order, 502 capture failure, 500 filesystem error.

## Environment

`APP_ENV=development` loads `backend/.env.development`; `production` loads `.env.production`. Overrides: `.env.development.local`, `.env.local`.

| Variable | Role |
| --- | --- |
| `LOG_LEVEL` | Console level |
| `CORS_ORIGINS` | Allowed frontend origins |
| `EPCAT_BASE_URL` | API base; capture URL is `{base}/capture` |
| `OUTPUT_DIR` | Default `output`, relative to the backend root |
