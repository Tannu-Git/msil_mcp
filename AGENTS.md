# AGENTS.md

This repository contains the MSIL MCP Server (FastAPI) with Admin and Chat UIs (React/Vite), plus a mock API, infrastructure, and docs.

## Structure
- mcp-server/app: FastAPI app entrypoint and core logic.
  - app/api: REST and MCP endpoints.
  - app/core: OpenAPI import, metrics, tool registry/execution.
  - app/main.py: FastAPI wiring.
- mcp-server/tests: pytest suite.
- admin-ui/src: Admin portal UI.
- chat-ui/src: Chat UI.
- mock-api/app: Optional mock backend.
- sample-apis: OpenAPI specs for import.
- docs and infrastructure: architecture and deployment references.

## Local development
- Recommended (Windows): `./start-demo.ps1` (starts backend + UIs).
- Manual:
  - Backend: `cd mcp-server; python -m pip install -r requirements.txt; python -m uvicorn app.main:app --reload --port 8000`
  - Admin UI: `cd admin-ui; npm install; npm run dev` (Vite port 3001)
  - Chat UI: `cd chat-ui; npm install; npm run dev` (Vite port 3000)
- Note: `start-demo.ps1` uses ports 5174/5173; keep ports consistent if you change configs.
- API docs: http://localhost:8000/docs

## Tests and lint
- Backend tests: `cd mcp-server; pytest` (pytest.ini requires Python 3.11+)
- Frontend lint: `cd admin-ui; npm run lint` and `cd chat-ui; npm run lint`
- Frontend build: `npm run build`

## Configuration
- `mcp-server/.env` or `.env.example` for `OPENAI_API_KEY` and optional DB/Redis URLs.
- Proxy configuration lives in `admin-ui/vite.config.ts` and `chat-ui/vite.config.ts`.

## Change guidance
- API routes: `mcp-server/app/api`
- Core services/utilities: `mcp-server/app/core`
- Configuration: `mcp-server/app/config.py`
- UI pages/components: `admin-ui/src` and `chat-ui/src`
