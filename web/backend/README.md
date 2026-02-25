# cleAIr Backend

FastAPI service that receives traces from the Python SDK and streams them to the frontend via SSE.

## Endpoints

- `POST /v1/traces` — OTLP/JSON trace ingestion
- `GET /runs/latest/stream` — SSE stream of the latest run's events

## Run

```bash
cd web/backend
pip install -e .
python -m cleair_backend.main
```

Runs on `http://localhost:8000`.

## Connect the Python SDK

```python
cleair.init(CleairConfig(service_name="my-agent", exporter="cleair_http"))
```

Or via environment variables:

```bash
CLEAIR_EXPORTER=cleair_http python your_agent.py
```

The endpoint defaults to `http://localhost:8000/v1/traces`. Override with `CLEAIR_HTTP_ENDPOINT`.
