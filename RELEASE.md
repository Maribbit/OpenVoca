# Release Guide

This project uses a single repository-level version in `VERSION`.

## Version Source
- `VERSION` is the single source of truth.
- Keep package metadata in sync:
  - `frontend/package.json` → `version`
  - `backend/pyproject.toml` → `[project].version`

## Release Steps

1. Run full local checks.

```bash
cd frontend
pnpm run check

cd ../backend
uv run ruff format --check .; uv run ruff check .; uv run pytest
```

2. Bump the version in `VERSION`, `frontend/package.json`, and `backend/pyproject.toml`.

3. Add a new entry to `CHANGELOG.md` with the user-visible changes. Mention breaking changes explicitly.

4. Create a git tag: `git tag v0.7.0`.

## Versioning Rule (SemVer)
- PATCH: bug fixes only.
- MINOR: backward-compatible features.
- MAJOR: breaking changes.
