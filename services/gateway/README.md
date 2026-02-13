# cleair gateway

Minimal llmSHAP inference gateway scaffold.

## Endpoints

- `GET /health/live` returns service liveness.
- `POST /v1/inference` runs synchronous inference and supports attribution delivery modes:
  - `fast`: returns inference + attribution synchronously.
  - `full`: returns inference + attribution synchronously.
  - `deferred`: returns inference immediately and queues attribution (`attribution_meta.job_id`).
- Current provider support: `openai` (via llmSHAP `OpenAIInterface`).
- `GET /attributions/{job_id}` returns deferred attribution job status and result.

## Architecture (v1)

- API plane (FastAPI) handles request validation, request IDs, and response composition.
- Worker plane (Celery) handles deferred llmSHAP jobs.
- Redis is the Celery broker and result backend.
- Provider inference payload is preserved under `response`.
- llmSHAP output is returned under `attribution` with metrics in `attribution_meta`.
- `run_llmshap_attribution` uses the real `llmSHAP` package via `llmSHAP.llm.openai.OpenAIInterface`.

## Local Run

Install:

```bash
pip install "llmshap[full]"
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
