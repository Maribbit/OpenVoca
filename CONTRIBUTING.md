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

## Gitee Mirror

The Gitee repository is a read-only mirror synced automatically from GitHub. Do not open Issues or PRs on Gitee — please use GitHub instead.

To set up the mirror:
1. Create a new Gitee repository → select "Import from GitHub".
2. Enable automatic sync in the Gitee repository settings.
3. Set the Gitee repository description to: `GitHub 镜像，Issue 和 PR 请提交至 GitHub`.
4. Optionally set the default README to `README.zh-CN.md` in the Gitee repository settings.

## License

By contributing to OpenVoca, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0) that covers this project.
