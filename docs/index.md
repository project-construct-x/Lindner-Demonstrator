# Construct-X Demonstrator — Notes

Knowledge base for agents. Describe the current system and point at source files. Dated change history belongs in the changelog, not here.

## Repository

| Path | Role |
| --- | --- |
| `frontend/` | Vue 3 + Vuetify UI. Session is an SSCC Digital Link; steps call the backend and follow progress over SSE. |
| `backend/` | FastAPI app. Renders EPCIS templates, stores session fields in memory, writes `output/`, posts to EPCAT2. |
| `backend/epcis/` | Runtime templates and generator. Registry: `steps.py`. |
| `backend/epcis-original/` | Reference templates. Not loaded at runtime. |
| `docs/epcis-eventstrecke/` | Reference EPCIS JSON and the ingestion graph in `README.md`. |
| `helm/` | Kubernetes chart for frontend and backend. |
| `pi/` | Raspberry Pi QR scanner deployed separately. See `pi/README.md`. |
| `scripts/` | Operator helpers, including EPCAT queries. |
| `compose.yml` | Local dev (bind mounts, reload). |
| `compose.deploy.yml` | Deploy compose. |

## Notes

- [Demonstrator model](./demonstrator.md) — goal, request flow, GS1 identifiers, seven lifecycle steps.
- [Frontend](./frontend.md) — UI stack, session, step buttons, scanner, print, SSE.
- [Backend and API](./backend.md) — generation, in-memory session, persistence, routes.
- [EPCIS templates](./epcis-templates.md) — `document.json`, placeholders, how a step is registered.
- [EPCIS event path](./epcis-eventstrecke/README.md) — ingestion graph from Fertigung through Montage, plus the reference JSON samples.
- [EPCAT2](./epcat2.md) — capture and query against the Construct-X EPCIS repository.
- [EPCAT2 subscriptions](./epcat2-subscriptions.md) — webhook subscriptions on saved queries.
- [Deployment](./deployment.md) — Compose, images, Helm, Pi.
