# cleAIr Web

## Structure

- `frontend/`: React trace UI
- `backend/`: FastAPI ingest + SSE service

## Backend

## Endpoints

- `POST /v1/traces`: OTLP/JSON trace ingestion
- `POST /v1/events`: cleair-native event ingestion (streaming)
- `GET /runs/latest/stream`: SSE stream of latest run events

## Run

```bash
cd web/backend
pip install -e .
python -m cleair_backend.main --reload
```

Runs at `http://localhost:8000`.

## Python SDK

```python
cleair.init(CleairConfig(service_name="my-agent", exporter="cleair_http"))
```

Or via environment variables:

```bash
CLEAIR_EXPORTER=cleair_http python your_agent.py
```

Default `CLEAIR_HTTP_ENDPOINT` is `http://localhost:8000/v1/events`.
Set `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` for OTLP mode (`/v1/traces`).

## Frontend

Stack: React 19, TypeScript, Vite, Vitest.

Source layout:

```
src/
├── types.ts              — core data model (FlowNode, TraceTreeState, TraceTreeEvent)
├── traceTree.ts          — pure event reducer + display utilities
├── kinds.ts              — visual config per node kind (colors)
├── App.tsx               — layout, playback state, details panel
├── index.css             — dark theme, tree connectors, layout
├── components/
│   └── TraceTree.tsx     — waterfall tree renderer
└── data/
    └── agentRagRunEvents.ts — demo event stream
```

Run:

```bash
cd web/frontend
npm install
npm run dev
```

Test:

```bash
npm test
```
