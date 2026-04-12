# Release Guide

This project uses a single repository-level version in `VERSION`.

## Version Source
- `VERSION` is the single source of truth.
- Keep package metadata in sync:
  - `frontend/package.json` -> `version`
  - `backend/pyproject.toml` -> `[project].version`

## Release Steps

1. Run full local checks.

```bash
cd frontend && pnpm run check
cd ../backend && uv run ruff format --check . && uv run ruff check . && uv run pytest
```

Or use the VS Code task: **✅ Check OpenVoca (All)**

2. Bump the version in `VERSION`, `frontend/package.json`, and `backend/pyproject.toml`.

3. Add a new entry to `CHANGELOG.md` with the user-visible changes. Mention breaking changes explicitly.

4. Commit and tag:

```bash
git add -A
git commit -m "Release v0.9.0"
git tag v0.9.0
git push origin main --tags
```

5. CI automatically:
   - Runs all tests (frontend, backend).
   - Builds portable bundles for Windows, macOS, and Linux.
   - Creates a GitHub Release with the CHANGELOG section and bundle archives attached.

## Versioning Rule (SemVer)
- PATCH: bug fixes only.
- MINOR: backward-compatible features.
- MAJOR: breaking changes.
