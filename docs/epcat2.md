# EPCAT 2.0

EPCAT2 is the Construct-X EPCIS 2.0 repository the demonstrator uses to capture and query lifecycle events.

| Resource | URL |
| --- | --- |
| API base | `https://epcat2.construct-x.prod-k8s.eecc.de/api` |
| Swagger UI | https://epcat2.construct-x.prod-k8s.eecc.de/api/swagger-ui/index.html |
| OpenAPI spec | https://epcat2.construct-x.prod-k8s.eecc.de/api/api-docs |

Set `EPCAT_BASE_URL` in `backend/.env.development` or `backend/.env.production`. The backend posts documents from `backend/epcis/capture.py`. Webhook subscriptions: [EPCAT2 subscriptions](./epcat2-subscriptions.md).

## Capture

```http
POST {EPCAT_BASE_URL}/capture
Content-Type: application/json
```

```bash
curl -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/capture" \
  -H "Content-Type: application/json" \
  -d @backend/output/<sscc>/03.json
```

## Query

Responses are `EPCISQueryDocument` values. Events sit at `epcisBody.queryResults.resultsBody.eventList`. Results are ordered by `recordTime` descending.

| Parameter | Role |
| --- | --- |
| `perPage` | Page size (`10` for the latest ten) |
| `nextPageToken` | Pagination token from the previous response |
| `history` | Include historical revisions (`true` / `false`, default `false`) |

Filters use EPCIS query names, for example `EQ_bizStep=packing`.

Packing in this demo is an `AggregationEvent` with `action` `ADD`, `bizStep` `packing`, `disposition` `in_progress`, and the SSCC as `parentID`. Templates: `backend/epcis/03.json`, `backend/epcis/07b.json`.

Latest ten packing events:

```bash
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/bizSteps/packing/events?perPage=10"
```

The same filter on the generic route is `GET /events?perPage=10&EQ_bizStep=packing`.

Packing events for one SSCC (URL-encode `parentID`):

```bash
curl -fsS --get "https://epcat2.construct-x.prod-k8s.eecc.de/api/events" \
  --data-urlencode "EQ_bizStep=packing" \
  --data-urlencode "EQ_parentID=https://id.gs1.org/00/040471116815749833" \
  --data-urlencode "perPage=10"
```

Replace the parent ID with the SSCC from the UI. A named temporary query is `POST /queries/{name}` with body `{ "name", "temporary": true, "query": { … } }`, then `GET /queries/{name}/events`.

`scripts/query-versand-packing.sh` loads shipping events for a despatch advice (`EQ_bizStep=shipping` and `EQ_bizTransaction_desadv`) and then packing events for the SSCCs in `epcList`. Default host is the EPCAT2 base above; override with `EPCAT_URL` and `EPCAT_TOKEN`.

## Related routes

| Method | Path | Role |
| --- | --- | --- |
| `GET` | `/events/{eventID}` | One event |
| `GET` | `/epcs/{epc}/events` | Events for an EPC, SSCC, or LGTIN |
| `GET` | `/eventTypes/AggregationEvent/events` | Events by type |
| `GET` | `/queries` | Saved queries |
| `GET` | `/queries/{queryName}/count` | Match count |

Swagger groups these under **events-controller** and **query-controller**.
