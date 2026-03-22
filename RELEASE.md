# Release Guide

This project uses a single repository-level version in `VERSION`.

## Current Version Source
- `VERSION` is the single source of truth.
- Keep package metadata in sync:
  - `frontend/package.json` -> `version`
  - `backend/pyproject.toml` -> `[project].version`

## Release Steps
1. Run full local checks.

```bash
cd frontend
pnpm run check

cd ../backend
uv run ruff format --check .; uv run ruff check .; uv run pytest
```

2. Update version files.
- Bump `VERSION`.
- Sync the same version into frontend and backend package metadata.

3. Update release notes.
- Add a short summary of user-visible changes.
- Mention breaking changes explicitly.

4. Tag the release.
- Create a git tag like `v0.2.0`.

## Versioning Rule (SemVer)
- PATCH: bug fixes only.
- MINOR: backward-compatible features.
- MAJOR: breaking changes.

## v0.1.0

Date: 2026-03-22

### Highlights
- Delivered the Phase 1 minimal closed loop for sentence generation with local Ollama (`gemma3:4b`).
- Added a focused Reading page with Zen-style layout and single-sentence rendering.
- Added a Preferences menu to configure target words and generation prompt from the frontend.
- Moved prompt and target word ownership to the frontend and persisted settings with local storage.
- Added lightweight i18n support with automatic locale detection (`zh`/`en`) and manual language switch.

### Backend
- Added an Ollama integration layer for `/api/generate` calls.
- Added `POST /api/reading-sentence` to generate one sentence from frontend-provided words and prompt template.
- Added tests for Ollama request construction, payload validation, and endpoint behavior.

### Frontend
- Implemented Reading view with sentence request-on-load flow.
- Implemented Preferences overlay based on the design draft.
- Added i18n regression test for switching UI language and persisting locale.

### Breaking Changes
- None.
