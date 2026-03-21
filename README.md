# OpenVoca

**Learn Naturally.** 

A minimalistic, LLM-powered language learning application focused on reading contextually generated sentences.

---

## Architecture 
OpenVoca is designed as a Mono-repository containing both frontend and backend.

- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS v4 + Pinia
  *👉 See [frontend/README.md](./frontend/README.md) for startup & testing details.*
- **Backend**: Python 3.12+ (managed by uv) + FastAPI + SQLModel + SQLite
  *👉 See [backend/README.md](./backend/README.md) for API & testing details.*

## Quick Start
Launch both frontend and backend servers concurrently using VS Code's tasks:
1. Press `Ctrl+Shift+B` (or `Cmd+Shift+B` on macOS).
2. Select **🚀 Run OpenVoca (All)** from the quick pick menu.

## Testing & TDD
This project embraces Test-Driven Development (TDD):
- **Frontend**: Run `pnpm test` in the frontend directory.
- **Backend**: Run `uv run pytest` in the backend directory.
Please write tests before implementing core logic to ensure a robust foundation.