# cleAIr Web

## Structure

- `frontend/`: React trace UI
- `backend/`: FastAPI ingest + SSE service

## Backend

## Endpoints

- `GET /auth/session`: cookie-backed auth status
- `POST /auth/verify`: verify the demo access code
- `POST /v1/traces`: OTLP/JSON trace ingestion
- `POST /v1/events`: cleair-native event ingestion (streaming)
- `GET /channels/{api_key}/stream`: SSE stream of latest run events

## Run

```bash
cp web/backend/auth_codes.template.json web/backend/auth_codes.json
cd web/backend
pip install -e .
CLEAIR_AUTH_SECRET=local-demo-secret python -m cleair_backend.main --reload
```

Runs at `http://localhost:8000`.

## Python SDK

```python
cleair.init(service_name="my-agent", cleair_api_key="<channel-api-key>")
```

This is the default path. `cleair_http` sends to `https://api.cleair.ai/v1/events`.
When sending traces to the local backend instead, set `CLEAIR_HTTP_ENDPOINT=http://localhost:8000/v1/events`.
For OTLP, terminal, or console output, set an explicit exporter in `cleair.init(...)`.

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
