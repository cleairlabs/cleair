# cleAIr Web

This folder contains the web product surface for cleAIr.

## Structure

- `frontend/` — React app for live trace visualization.
- `backend/` — FastAPI service for trace ingestion and streaming *(not yet implemented)*.

## Frontend

A dark-themed trace viewer that renders agent execution as a hierarchical waterfall list, inspired by LangSmith's trace view.

**Stack:** React 19 · TypeScript · Vite · Vitest

**Source layout:**

```
src/
├── types.ts              — core data model (FlowNode, FlowGraph, FlowGraphEvent)
├── flowGraph.ts          — pure event reducer + display utilities
├── kinds.ts              — visual config per node kind (colors)
├── App.tsx               — layout, playback state, details panel
├── index.css             — dark theme, tree connectors, layout
├── components/
│   └── TraceTree.tsx     — waterfall tree renderer
└── data/
    └── agentRagRunEvents.ts — demo event stream
```

**Run locally:**

```bash
cd frontend
npm install
npm run dev
```

**Test:**

```bash
npm test
```

## Architecture notes

- The frontend event model (`node_added`, `node_status_changed`, `node_finished`, `run_completed`) is designed for direct streaming from the backend over WebSocket or SSE.
- The `FlowGraph` state is built by applying events through a pure reducer (`applyFlowGraphEvent`), making it straightforward to connect to a real stream.
- Node hierarchy is expressed via `parentId` (not explicit edges), which drives the tree layout automatically.
