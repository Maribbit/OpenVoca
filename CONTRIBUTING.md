# Contributing Guide

This project follows a minimal and stable monorepo workflow.

## Branch and Commit Scope
- Work in small feature branches.
- Keep each commit focused on one logical change.
- Use concise commit messages. Conventional style is recommended (for example, `feat:`, `fix:`, `docs:`, `refactor:`, `test:`).

## Feature Completion Checklist
Before considering a feature complete, run all relevant checks.

### Frontend
```bash
cd frontend
pnpm run check
```

### Backend
```bash
cd backend
uv run ruff format --check .; uv run ruff check .; uv run pytest
```

### Workspace (VS Code)
Run the task `✅ Check OpenVoca (All)`.

## TDD Requirement
- Write failing tests first (Red).
- Implement the minimum code to pass tests (Green).
- Refactor while keeping tests green (Refactor).

## Before Opening a PR or Preparing a Release
- Confirm checks pass locally.
- Ensure documentation is updated when behavior changes.
- Keep comments and docstrings in English.
