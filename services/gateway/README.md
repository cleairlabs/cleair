# cleair gateway

Minimal llmSHAP inference gateway scaffold.

## Endpoints

- `GET /health/live` returns service liveness.
- `POST /inferences` submits a background inference job.
- `GET /inferences/{job_id}` returns job status and result when available.

## Local Run

Install:

```bash
pip install -e services/gateway[test]
```

Run API:

```bash
scripts/dev/run_gateway_api.sh
```

Run worker:

```bash
scripts/dev/run_gateway_worker.sh
```

## Environment Variables

- `CLEAIR_GATEWAY_NAME` (default: `cleair-gateway`)
- `CLEAIR_REDIS_URL` (default: `redis://localhost:6379/0`)
