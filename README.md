# OpenVoca

**Learn Naturally.** 

A minimalistic, LLM-powered language learning application focused on reading contextually generated sentences.

---

## Architecture 
OpenVoca is designed as a Mono-repository containing both frontend and backend.

- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS v4
  *👉 See [frontend/README.md](./frontend/README.md) for startup & testing details.*
- **Backend**: Python 3.12+ (managed by uv) + FastAPI + SQLModel + SQLite
  *👉 See [backend/README.md](./backend/README.md) for API & testing details.*

## Testing & TDD
This project embraces Test-Driven Development (TDD):
- **Frontend**: Run `pnpm run check` in the `frontend` directory.
- **Backend**: Run `uv run ruff format --check .; uv run ruff check .; uv run pytest` in the `backend` directory.
- **Workspace Task**: Run VS Code task `✅ Check OpenVoca (All)` to execute both checks.
Please write tests before implementing any core logic and run checks before completing any task.

## Building a Release Package (Windows)

The `scripts/bundle.py` script assembles a self-contained Windows ZIP that requires no installation. It embeds the Python runtime (via uv) and the compiled frontend assets.

**Prerequisites** (must be in PATH):
- `uv` — Python environment manager
- `pnpm` — frontend package manager

**Run from the repository root:**
```bash
uv run python scripts/bundle.py
```

**Output:** `dist/openvoca-{version}-win-x64.zip`

**What the script does (8 steps):**
1. Builds the frontend (`pnpm run build`)
2. Creates a production-only Python venv via `uv sync --frozen --no-dev` (no dev dependencies)
3. Restores the host dev venv (`uv sync --frozen`)
4. Pre-compiles Python source to `.pyc` bytecode
5. Assembles the directory: backend source + prod venv + frontend dist + dictionary DB
6. Writes `openvoca.json` (version + port config)
7. Writes launcher scripts (`start.py`, `openvoca.bat`) and verifies runtime imports
8. ZIPs the assembled directory

**To test the bundle:** extract the ZIP, double-click `openvoca.bat`, and wait for the browser to open automatically.

> **Dependency changes are handled automatically** — the bundle always uses the current `uv.lock` for resolution. No manual package list to maintain.

## Versioning and Contribution
- **Project Version**: Maintained in `VERSION` at the repository root.
- **Contribution Guide**: See `CONTRIBUTING.md` for feature checklist and pre-commit checks.
- **Release Guide**: See `RELEASE.md` for how to publish a new version.

## License

Copyright (C) 2026 OpenVoca Contributors

OpenVoca is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).

You are free to use, modify, and distribute this software under the terms of the AGPL-3.0. Any modified version distributed or run as a network service must also be released under the AGPL-3.0 with source code made available to users.

**Commercial use is permitted**, but any commercial product or service that includes or is derived from OpenVoca must comply with AGPL-3.0 requirements (including making source code available).

The built-in dictionary data is derived from [ECDICT](https://github.com/skywind3000/ECDICT), licensed under the MIT License.