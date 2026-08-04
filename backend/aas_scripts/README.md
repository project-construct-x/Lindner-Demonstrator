# AAS Scripts

Utilities for mapping EPCIS events from EPCAT2 into the AAS environment.

## Purpose

The normal flow is:

1. The web app triggers a lifecycle step.
2. The backend sends the generated EPCIS document to EPCAT2.
3. An EPCAT2 query subscription detects matching `receiving` events.
4. EPCAT2 calls a webhook.
5. The webhook runs the EPCIS-to-AAS mapper in this folder.

## Main Files

| File | Purpose |
| --- | --- |
| `receiver.py` | Local JSON webhook receiver. |
| `aas_link.py` | Extracts EPCIS events from a payload and maps them to AAS. |
| `epcat2_query.py` | Creates/deletes EPCAT2 named queries and webhook subscriptions. |
| `basyx_components/` | Helper modules for AAS shell, submodel, and element mapping. |

## Local Development

From this folder:

```sh
python receiver.py --aas-link
```

The local receiver listens on:

```text
http://0.0.0.0:8088/epcis-events
```

To map a saved EPCIS payload directly:

```sh
python aas_link.py payload.json
```

## Production Deployment

The deployed FastAPI backend should expose a webhook endpoint, for example:

```text
POST https://demonstrator.construct-x.prod-k8s.eecc.de/api/epcis-events
```

That endpoint should call:

```python
aas_scripts.aas_link.map_payload_to_aas(...)
```

The EPCAT2 subscription destination should be the deployed webhook URL:

```text
https://demonstrator.construct-x.prod-k8s.eecc.de/api/epcis-events
```

## Creating the EPCAT2 Subscription

Use `epcat2_query.py` to create or recreate the EPCAT2 query subscription.

Example:

```sh
python epcat2_query.py aas-receiving-events \
  --recreate \
  --dest https://demonstrator.construct-x.prod-k8s.eecc.de/api/epcis-events
```

The default query filters:

```text
EQ_bizStep = receiving
```

## Configuration

Default AAS environment:

```text
http://132.195.160.222:8081
```

Override it locally with:

```sh
python receiver.py --aas-link --aas-environment http://host:port
python aas_link.py payload.json --aas-environment http://host:port
```

For production, keep this as backend configuration, not hardcoded in the webhook handler.

## Deploying With This Repo

Make sure the production backend Docker image copies this folder:

```dockerfile
COPY aas_scripts/ aas_scripts/
```

After committing the code and pushing to `main` or `master`, GitHub Actions builds and pushes the backend image. Then upgrade the Helm release:

```sh
cd helm
./upgrade.sh -- --set backend.image.tag=<commit-sha>
```

## Do Not Commit

Do not commit generated runtime files:

```text
__pycache__/
*.pyc
receiver-aas-link.log
*.log
```
