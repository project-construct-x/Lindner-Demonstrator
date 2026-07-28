# EPCAT 2.0

EPCAT2 is the Construct-X EPCIS 2.0 repository used by the demonstrator to **capture** and **query** lifecycle events.

| Resource | URL |
| -------- | --- |
| API base | `https://epcat2.construct-x.prod-k8s.eecc.de/api` |
| Swagger UI | https://epcat2.construct-x.prod-k8s.eecc.de/api/swagger-ui/index.html |
| OpenAPI spec | https://epcat2.construct-x.prod-k8s.eecc.de/api/api-docs |

Configure the base URL via `EPCAT_BASE_URL` in `backend/.env.development` / `backend/.env.production`.

---

## Capture (write events)

The demonstrator backend sends generated EPCIS documents to:

```http
POST {EPCAT_BASE_URL}/capture
Content-Type: application/json
```

Example:

```bash
curl -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/capture" \
  -H "Content-Type: application/json" \
  -d @backend/output/<sscc>/03.json
```

See also [EPCAT Capture](index.md#epcat-capture) in the main docs.

---

## Query (read events)

Query responses use the EPCIS 2.0 query document format. Events are returned in:

```json
{
  "type": "EPCISQueryDocument",
  "epcisBody": {
    "queryResults": {
      "resultsBody": {
        "eventList": [ /* ... */ ]
      }
    }
  }
}
```

Common query parameters:

| Parameter | Description |
| --------- | ----------- |
| `perPage` | Maximum number of events to return (use `10` for the latest ten) |
| `nextPageToken` | Token from a previous response for pagination |
| `history` | Include historical event revisions (`true` / `false`, default `false`) |

Filter parameters use the EPCIS query prefix style, e.g. `EQ_bizStep=packing`.

Results are ordered by **`recordTime` descending** (most recently captured events first).

---

## Packing events in the demonstrator

Packing steps emit **AggregationEvent** records with:

| Field | Value |
| ----- | ----- |
| `type` | `AggregationEvent` |
| `action` | `ADD` |
| `bizStep` | `packing` |
| `disposition` | `in_progress` |

These correspond to lifecycle steps **3** (initial packing) and **7b** (re-packing after demontage). Templates: `backend/epcis/03.json`, `backend/epcis/07b.json`.

---

## Latest 10 packing events

### Option 1 — simple GET (recommended)

Filter by business step and limit to ten events:

```bash
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/bizSteps/packing/events?perPage=10"
```

Equivalent using the generic events endpoint:

```bash
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/events?perPage=10&EQ_bizStep=packing"
```

### Option 2 — named temporary query

Create a reusable query and fetch its results:

```bash
# Create query (returns first page of results)
curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/latest-packing?perPage=10" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "latest-packing",
    "temporary": true,
    "query": {
      "EQ_bizStep": "packing"
    }
  }'

# Re-run the saved query later
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/latest-packing/events?perPage=10"
```

Set `"temporary": false` to keep the query definition permanently.

---

## Find packing events by parentID (SSCC)

In the demonstrator, packing events use the SSCC as `parentID` (GS1 Digital Link URI).

**Example parentID:** `https://id.gs1.org/00/040471116815749833`

### Option 1 — simple GET

Combine `EQ_bizStep` and `EQ_parentID` (URL-encode the parent ID):

```bash
curl -fsS --get "https://epcat2.construct-x.prod-k8s.eecc.de/api/events" \
  --data-urlencode "EQ_bizStep=packing" \
  --data-urlencode "EQ_parentID=https://id.gs1.org/00/040471116815749833" \
  --data-urlencode "perPage=10"
```

Inspect the result with `jq`:

```bash
curl -fsS --get "https://epcat2.construct-x.prod-k8s.eecc.de/api/events" \
  --data-urlencode "EQ_bizStep=packing" \
  --data-urlencode "EQ_parentID=https://id.gs1.org/00/040471116815749833" \
  --data-urlencode "perPage=10" \
  | jq '.epcisBody.queryResults.resultsBody.eventList[] | {eventID, eventTime, bizStep, parentID, childQuantityList}'
```

### Option 2 — named query

```bash
curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-by-sscc?perPage=10" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "packing-by-sscc",
    "temporary": true,
    "query": {
      "EQ_bizStep": "packing",
      "EQ_parentID": "https://id.gs1.org/00/040471116815749833"
    }
  }'
```

Re-run later:

```bash
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-by-sscc/events?perPage=10"
```

For other sessions, replace `https://id.gs1.org/00/040471116815749833` with the SSCC from the demonstrator UI / QR code.

---

## Subscribe to packing events

Subscriptions push query results to a **webhook URL** (`dest`) whenever the query runs — either on a **schedule** (cron) or when a **trigger** fires. A query must exist and be **persistent** (`"temporary": false`) before you can subscribe.

Flow:

1. Create a saved query for packing events
2. Register a subscription with your callback URL
3. EPCAT2 POSTs matching events to your webhook as an `EPCISQueryDocument`

### Step 1 — create a persistent packing query

```bash
curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "packing-events",
    "temporary": false,
    "query": {
      "EQ_bizStep": "packing"
    }
  }'
```

### Step 2 — subscribe with a webhook

Replace `https://your-service.example.com/epcis-events` with a URL that accepts `POST` requests.

```bash
curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events/subscriptions" \
  -H "Content-Type: application/json" \
  -d '{
    "subscriptionID": "my-packing-subscription",
    "dest": "https://your-service.example.com/epcis-events",
    "schedule": "*/30 * * * * *",
    "initialRecordTime": "2026-01-01T00:00:00Z",
    "reportIfEmpty": false,
    "destAuth": {
      "type": "NONE"
    }
  }'
```

| Field | Description |
| ----- | ----------- |
| `subscriptionID` | Your identifier for this subscription |
| `dest` | Webhook URL that receives `POST` requests with query results |
| `schedule` | Cron expression (6 fields, incl. seconds). Example above: every 30 seconds |
| `initialRecordTime` | Only events captured **after** this timestamp are considered on the first run |
| `reportIfEmpty` | Send a callback even when no new events matched (`false` = skip empty runs) |
| `destAuth` | Authentication for the webhook: `NONE`, `BASIC`, or `BEARER` |

**Webhook authentication example (Bearer token):**

```json
"destAuth": {
  "type": "BEARER",
  "token": "your-secret-token"
}
```

### Manage subscriptions

```bash
# List subscriptions for a query
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events/subscriptions"

# Get one subscription
curl -fsS "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events/subscriptions/my-packing-subscription"

# Unsubscribe
curl -fsS -X DELETE "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events/subscriptions/my-packing-subscription"
```

### What your webhook receives

EPCAT2 delivers an `EPCISQueryDocument` JSON body — the same format as a poll/query response. New packing events since the last run appear in:

```
epcisBody.queryResults.resultsBody.eventList
```

For local testing, expose a temporary endpoint with [ngrok](https://ngrok.com/) or similar and use that URL as `dest`.

---

## Useful related endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/events/{eventID}` | Single event by ID |
| `GET` | `/epcs/{epc}/events` | Events for a specific EPC/SSCC/LGTIN |
| `GET` | `/eventTypes/AggregationEvent/events` | Events by type |
| `GET` | `/queries` | List saved queries |
| `GET` | `/queries/{queryName}/count` | Count matching events |
| `POST` | `/queries/{queryName}/subscriptions` | Subscribe to a query (webhook) |
| `GET` | `/queries/{queryName}/subscriptions` | List subscriptions |
| `DELETE` | `/queries/{queryName}/subscriptions/{subscriptionID}` | Unsubscribe |

Swagger groups these under **events-controller** and **query-controller**.

---

## Example: inspect packing event fields

```bash
curl -fsS --get "https://epcat2.construct-x.prod-k8s.eecc.de/api/events" \
  --data-urlencode "EQ_bizStep=packing" \
  --data-urlencode "EQ_parentID=https://id.gs1.org/00/040471116815749833" \
  --data-urlencode "perPage=1" \
  | jq '.epcisBody.queryResults.resultsBody.eventList[0] | {eventID, eventTime, recordTime, type, bizStep, parentID, childQuantityList}'
```

Example output shape:

```json
{
  "eventID": "urn:uuid:…",
  "eventTime": "2026-04-16T14:04:53.369Z",
  "recordTime": "2026-07-11T18:26:57.513Z",
  "type": "AggregationEvent",
  "bizStep": "packing",
  "parentID": "https://id.gs1.org/00/040471116815749833",
  "childQuantityList": [
    { "epcClass": "https://id.gs1.org/01/…/10/…", "quantity": 13 }
  ]
}
```
