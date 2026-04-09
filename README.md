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