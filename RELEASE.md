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
