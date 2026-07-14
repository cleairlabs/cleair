# cleAIr Web

## Structure

- `frontend/`: React trace UI
- `backend/`: FastAPI ingest + SSE service

## Backend

The backend trace store is in-memory. Runs are keyed by `runId`, so multiple runs can share the same `serviceName`; data is reset when the backend process restarts.

## Endpoints

- `GET /auth/session`: cookie-backed auth status
- `POST /auth/verify`: verify the demo access code
- `POST /api-key`: create or return the single API key used by the workspace
- `GET /agents`: list in-memory trace runs, including metadata and UI events, ordered by most recently updated first
- `POST /v1/traces`: OTLP trace ingestion
- `POST /v1/live`: transient live span-start ingestion
- `GET /events`: SSE stream of live agent updates

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
cleair.init(service_name="my-agent", cleair_api_key="<api-key>")
```

cleAIr exports OTLP traces to `https://api.cleair.ai/v1/traces` by default and sends
best-effort span-start updates to `https://api.cleair.ai/v1/live`.
When sending traces to the local backend instead, set `CLEAIR_BASE_URL=http://localhost:8000`.

## Frontend

Stack: React 19, TypeScript, Vite, Vitest.

Source layout:

```
src/
├── types.ts              — core data model (FlowNode, TraceTreeState, TraceTreeEvent)
├── traceTree.ts          — pure event reducer + display utilities
├── nodeTypes.ts          — visual config per node type (colors)
├── App.tsx               — agent list, trace panel, details panel
├── index.css             — layout and styling
├── components/
│   ├── AgentList.tsx     — agent selector
│   └── TraceTree.tsx     — waterfall tree renderer
└── hooks/
    └── useAgents.ts      — API key bootstrap + live agent stream
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
