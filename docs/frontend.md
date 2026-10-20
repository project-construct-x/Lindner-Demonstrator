# Frontend

Vue 3.5, Vuetify 4, Vite 8, TypeScript 5.9, Pinia, Vue Router. QR rendering: `qrcode.vue`. Dev server port 3000.

## Key files

| File | Role |
| --- | --- |
| `frontend/src/pages/index.vue` | Demo page: QR, step buttons, progress, scanner, print |
| `frontend/src/utils/epcis-session.ts` | Create or parse an SSCC Digital Link |
| `frontend/src/utils/sscc-check-digit.ts` | GS1 check digit |
| `frontend/src/constants/steps.ts` | Story groups, labels, images |
| `frontend/src/services/trigger.service.ts` | `POST /trigger/{1-7}` with `{ sscc }` |
| `frontend/src/services/sscc-subscription.service.ts` | SSE client for `/sscc/stream` |
| `frontend/src/components/QrScannerDialog.vue` | Scan a code into the session |
| `frontend/src/components/SsccPrintDialog.vue` | Print SSCC labels |
| `frontend/src/config/env.ts` | `VITE_BACKEND_BASE_URL` |

## Behaviour

- Only the next incomplete step is enabled. Completed steps show a checkmark.
- A click posts the SSCC. On success the snackbar shows the document file and event count.
- `GET /api/sscc/stream` sends a `snapshot` of completed steps, then `step_completed` events. The page applies those IDs so another client on the same SSCC stays in sync.
- **Neu generieren** creates a new SSCC and resets local progress.
- A scanned or typed code is accepted only when it normalizes to a valid SSCC Digital Link.

## Environment

| Mode | File | `VITE_BACKEND_BASE_URL` |
| --- | --- | --- |
| development | `frontend/.env.development` | `http://localhost:8000/api` |
| production | `frontend/.env.production` | proxied API origin, path `/api` |

Import `env` from `@/config/env`. Local overrides: `.env.local`, `.env.development.local` (gitignored).
