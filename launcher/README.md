# OpenVoca Launcher

Native launcher for the OpenVoca portable bundle. Starts the Python backend, waits for it to be ready, then opens the browser.

## Architecture

```
openvoca.exe  (this binary)
    │
    ├─ reads   openvoca.json        (port, host, flags)
    ├─ spawns  backend/.venv/…/python -m uvicorn src.main:app
    ├─ polls   http://127.0.0.1:{port}/api/provider
    ├─ opens   default browser
    └─ waits   for Ctrl+C → graceful shutdown
```

## Development

```bash
cd launcher

# Build (debug)
cargo build

# Build (release — stripped, LTO)
cargo build --release

# Run all quality checks
cargo fmt --check && cargo clippy -- -D warnings && cargo test
```

The release binary is about 2 MB. Version is embedded from `../VERSION` at compile time via `build.rs`.

## Modules

| Module | Purpose |
|--------|---------|
| `config` | Parse `openvoca.json` with serde; defaults for all fields |
| `port` | Scan downward from configured port to find a free one |
| `server` | Spawn and manage the uvicorn child process |
| `health` | Poll health endpoint until ready or timeout |

## Roadmap

- **Tray icon** — `tray-icon` + `winit` for system tray menu (Open in Browser / Quit). Prerequisite for `#![windows_subsystem = "windows"]`.
- **Update check** — On startup, GET GitHub releases API; show "Update available" in tray menu.
- **Log rotation** — Cap `data/openvoca.log` at 5 MB.
