# EPCAT2 subscriptions

Subscriptions push query results to a webhook (`dest`) on a cron schedule or a trigger. The query must already exist and be persistent (`"temporary": false`).

Base URL and capture/query basics: [EPCAT2](./epcat2.md).

1. Create a saved query.
2. Register a subscription with the callback URL.
3. EPCAT2 POSTs an `EPCISQueryDocument` to the webhook. New matches are in `epcisBody.queryResults.resultsBody.eventList`.

```bash
curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "packing-events",
    "temporary": false,
    "query": { "EQ_bizStep": "packing" }
  }'

curl -fsS -X POST "https://epcat2.construct-x.prod-k8s.eecc.de/api/queries/packing-events/subscriptions" \
  -H "Content-Type: application/json" \
  -d '{
    "subscriptionID": "my-packing-subscription",
    "dest": "https://your-service.example.com/epcis-events",
    "schedule": "*/30 * * * * *",
    "initialRecordTime": "2026-01-01T00:00:00Z",
    "reportIfEmpty": false,
    "destAuth": { "type": "NONE" }
  }'
```

| Field | Role |
| --- | --- |
| `subscriptionID` | Caller-chosen id |
| `dest` | Webhook that accepts POST |
| `schedule` | Six-field cron (seconds included). Example: every 30 seconds |
| `initialRecordTime` | First run only considers events captured after this time |
| `reportIfEmpty` | `false` skips callbacks with no new events |
| `destAuth` | `NONE`, `BASIC`, or `BEARER` |

Bearer auth is `destAuth.type` `BEARER` plus `token`. List, get, and delete subscriptions under `/queries/{queryName}/subscriptions` and `/queries/{queryName}/subscriptions/{subscriptionID}`.

For a local webhook, expose it (for example with ngrok) and use that URL as `dest`.
