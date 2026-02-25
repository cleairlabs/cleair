# cleAIr Web

This folder contains the web product surface for cleAIr.

## Structure

- `frontend/`: React application for live trace visualization and interaction.
- `backend/`: FastAPI service for trace ingestion, streaming APIs, databases, and analysis.

## Plan

The web area should stay separate from SDKs so both can evolve independently.

1. Keep `sdks/` focused on distributable SDKs; keep web/ focused on product UX and APIs.
2. Build a FastAPI backend that exposes a streaming endpoint for trace event streams.
3. Build a React frontend with a Flow pane/chart/diagram and a detail pane for click-to-inspect behavior.
4. Connect frontend to backend with incremental graph updates over WebSocket or SSE.
5. Normalize backend trace events into a small graph event model for stable frontend rendering.
6. Keep the Flow pane component reusable inside `web/frontend` first; extract to an npm package only after usage stabilizes.
7. Add docs, tests, and developer scripts for local startup across frontend and backend.


- [ ] Define a minimal trace graph event schema (`node_added`, `edge_added`, `node_status_changed`, `run_completed`).
- [ ] Scaffold `frontend/` React app shell with Flow pane + right detail pane.
- [ ] Implement static graph rendering with clickable nodes and selection state.
- [ ] Implement incremental updates in the Flow pane from backend stream events.
- [ ] Scaffold `backend/` FastAPI app with OpenTel trace stream endpoint.
- [ ] Add backend event broadcaster abstraction.
- [ ] Add local run commands for both apps in this README.
- [ ] Add a simple end-to-end demo path (start backend, start frontend).
- [ ] Add tests for event schema parsing and frontend graph reducer logic.
- [ ] Re-evaluate whether to extract Flow pane into a standalone npm package.
