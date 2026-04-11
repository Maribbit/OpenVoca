"""
OpenVoca Portable Bundle Script (Phase B)
=========================================
Assembles a self-contained Windows ZIP that can be extracted and run without
any prior Python or Node.js installation.

Usage:
    cd <repo-root>
    uv run python scripts/bundle.py

Output:
    dist/openvoca-{version}-win-x64.zip
    └── openvoca/
        ├── openvoca.bat        ← Double-click entry point (interim; Phase C adds openvoca.exe)
        ├── start.py            ← Python launcher (health-poll, browser-open)
        ├── openvoca.json       ← Runtime config (port, host, open_browser, log_level)
        ├── backend/
        │   ├── src/            ← Python source + __pycache__ (pre-compiled)
        │   ├── data/           ← dictionary.db
        │   └── .venv/          ← Embedded Python + production deps only
        ├── frontend/
        │   └── dist/           ← Pre-built Vite SPA
        └── data/               ← User DB directory (empty; populated at runtime)

Venv isolation strategy
-----------------------
Rather than copying the dev venv and manually stripping packages (error-prone),
we create a *fresh* venv via ``uv sync --frozen --no-dev --no-install-project``
in a temporary workspace that contains only pyproject.toml + uv.lock.  This
delegates the dep-resolution entirely to uv's own lock-file machinery, so the
bundle will always be consistent with the lock file regardless of future dep
changes — zero maintenance overhead.
"""

import compileall
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"
VERSION = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
BUILD_DIR = REPO_ROOT / "build" / "openvoca"
VENV_WORK_DIR = REPO_ROOT / "build" / "_prod_venv"  # temp workspace for prod venv
DIST_DIR = REPO_ROOT / "dist"
ZIP_NAME = f"openvoca-{VERSION}-win-x64.zip"

# Runtime packages that must be importable in the bundled venv
_REQUIRED_IMPORTS = ["fastapi", "uvicorn", "spacy", "sqlmodel", "httpx"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"  $ {' '.join(str(c) for c in cmd)}", flush=True)
    # On Windows, pnpm/uv are .cmd wrappers; shell=True lets the OS find them.
    result = subprocess.run(cmd, cwd=cwd, shell=(sys.platform == "win32"))
    if result.returncode != 0:
        print(f"ERROR: command failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _build_prod_venv(work_dir: Path) -> Path:
    """
    Create a production-only venv via ``uv sync --frozen --no-dev
    --no-install-project`` in a temporary workspace (pyproject.toml + uv.lock).
    Returns the path of the resulting .venv.

    Using uv's lock-file resolution instead of manual package-name matching
    means dev packages are excluded reliably, and future dep changes need no
    script maintenance.
    """
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    shutil.copy2(BACKEND / "pyproject.toml", work_dir / "pyproject.toml")
    shutil.copy2(BACKEND / "uv.lock", work_dir / "uv.lock")
    _run(
        ["uv", "sync", "--frozen", "--no-dev", "--no-install-project"],
        cwd=work_dir,
    )
    return work_dir / ".venv"


def _verify_bundle(bundle_dir: Path) -> None:
    """
    Sanity-check: verify all required runtime packages are importable in the
    bundled venv.  Fails hard if any import is broken so problems are caught
    before the ZIP is created.
    """
    python = bundle_dir / "backend" / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        print(f"  ERROR: bundled Python not found at {python}", file=sys.stderr)
        sys.exit(1)
    print("  Verifying runtime imports in bundled venv ...")
    failed: list[str] = []
    for pkg in _REQUIRED_IMPORTS:
        r = subprocess.run(
            [str(python), "-c", f"import {pkg}"],
            capture_output=True,
            shell=(sys.platform == "win32"),
        )
        if r.returncode == 0:
            print(f"    ✓ {pkg}")
        else:
            print(f"    ✗ {pkg}  ← FAILED")
            failed.append(pkg)
    if failed:
        print(
            f"\nERROR: {len(failed)} package(s) failed to import: {', '.join(failed)}",
            file=sys.stderr,
        )
        sys.exit(1)


def _copy_tree(
    src: Path, dst: Path, *, exclude_dirs: frozenset[str] = frozenset()
) -> None:
    """Recursive copy that skips specific directory names."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            if item.name in exclude_dirs:
                continue
            _copy_tree(item, dst / item.name, exclude_dirs=exclude_dirs)
        else:
            shutil.copy2(item, dst / item.name)


# ---------------------------------------------------------------------------
# Launcher scripts written into the bundle
# ---------------------------------------------------------------------------

_START_PY = '''\
"""
OpenVoca launcher (start.py)
============================
Spawns the uvicorn backend, waits for it to become ready, then opens the
browser.  Run via openvoca.bat (or directly with the bundled Python).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
DATA_DIR = ROOT / "data"
MAX_WAIT_SECONDS = 45


def _read_config() -> dict:
    cfg_path = ROOT / "openvoca.json"
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    cfg = _read_config()
    host: str = cfg.get("host", "127.0.0.1")
    port: int = cfg.get("port", 18099)
    log_level: str = cfg.get("log_level", "warning")
    open_browser: bool = cfg.get("open_browser", True)
    health_url = f"http://{host}:{port}/api/health"

    DATA_DIR.mkdir(exist_ok=True)
    env = {**os.environ, "OPENVOCA_DATA_DIR": str(DATA_DIR)}

    print(f"Starting OpenVoca {cfg.get(\'version\', \'\')} on http://{host}:{port} ...")
    proc = subprocess.Popen(
        [
            str(PYTHON), "-m", "uvicorn", "src.main:app",
            "--host", host, "--port", str(port),
            "--log-level", log_level,
        ],
        cwd=str(BACKEND),
        env=env,
    )

    print(f"Waiting for server to be ready (up to {MAX_WAIT_SECONDS}s) ...", flush=True)
    ready = False
    for i in range(MAX_WAIT_SECONDS):
        time.sleep(1)
        if proc.poll() is not None:
            print("ERROR: Backend exited unexpectedly.", file=sys.stderr)
            sys.exit(1)
        try:
            with urllib.request.urlopen(health_url, timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass
        if (i + 1) % 5 == 0:
            print(f"  Still waiting ... ({i + 1}s)", flush=True)

    if not ready:
        print("ERROR: Server did not become ready in time.", file=sys.stderr)
        proc.terminate()
        sys.exit(1)

    url = f"http://{host}:{port}"
    print(f"OpenVoca is ready at {url}")
    if open_browser:
        webbrowser.open(url)

    print("Press Ctrl+C or close this window to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
    print("OpenVoca stopped.")


if __name__ == "__main__":
    main()
'''

_OPENVOCA_BAT = (
    "@echo off\r\n"
    "title OpenVoca\r\n"
    'cd /d "%~dp0"\r\n'
    '"%~dp0backend\\.venv\\Scripts\\python.exe" "%~dp0start.py"\r\n'
    "if %errorlevel% neq 0 pause\r\n"
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"\n=== OpenVoca Bundle Script  v{VERSION}  (Windows x64) ===\n")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Clean previous build
    if BUILD_DIR.exists():
        print("Cleaning previous build ...")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    # ------------------------------------------------------------------ #
    # 1. Build frontend
    # ------------------------------------------------------------------ #
    print("\n[1/7] Building frontend ...")
    if not (FRONTEND / "node_modules").exists():
        _run(["pnpm", "install", "--frozen-lockfile"], cwd=FRONTEND)
    _run(["pnpm", "run", "build"], cwd=FRONTEND)

    # ------------------------------------------------------------------ #
    # 2. Build production-only venv (no dev deps, via uv lock-file)
    # ------------------------------------------------------------------ #
    print("\n[2/8] Building production venv (no dev deps) ...")
    print("  Using uv lock-file resolution — no manual package filtering needed.")
    prod_venv = _build_prod_venv(VENV_WORK_DIR)

    # ------------------------------------------------------------------ #
    # 3. Sync dev venv (needed so tests pass on the host machine)
    # ------------------------------------------------------------------ #
    print("\n[3/8] Syncing host dev venv ...")
    _run(["uv", "sync", "--frozen"], cwd=BACKEND)

    # ------------------------------------------------------------------ #
    # 4. Pre-compile Python source to bytecode
    # ------------------------------------------------------------------ #
    print("\n[4/8] Compiling Python source ...")
    compileall.compile_dir(str(BACKEND / "src"), force=True, quiet=1)

    # ------------------------------------------------------------------ #
    # 5. Assemble directory tree
    # ------------------------------------------------------------------ #
    print("\n[5/8] Assembling directory structure ...")

    # backend/src  (with __pycache__ pre-populated by step 4)
    print("  Copying backend source ...")
    _copy_tree(
        BACKEND / "src",
        BUILD_DIR / "backend" / "src",
        exclude_dirs=frozenset({".ruff_cache", ".pytest_cache", "node_modules"}),
    )

    # backend/data  (dictionary.db)
    (BUILD_DIR / "backend" / "data").mkdir(parents=True, exist_ok=True)
    dict_db = BACKEND / "data" / "dictionary.db"
    if dict_db.exists():
        shutil.copy2(dict_db, BUILD_DIR / "backend" / "data" / "dictionary.db")
    else:
        print("  [warn] dictionary.db not found; skipping.")

    # backend/assets
    if (BACKEND / "assets").exists():
        shutil.copytree(BACKEND / "assets", BUILD_DIR / "backend" / "assets")

    # backend/.venv  (production-only venv from step 2)
    print("  Copying production venv ...")
    shutil.copytree(prod_venv, BUILD_DIR / "backend" / ".venv", symlinks=True)

    # frontend/dist
    print("  Copying frontend dist ...")
    shutil.copytree(FRONTEND / "dist", BUILD_DIR / "frontend" / "dist")

    # data/  (empty; created at runtime by start.py)
    (BUILD_DIR / "data").mkdir()

    # ------------------------------------------------------------------ #
    # 6. Write openvoca.json
    # ------------------------------------------------------------------ #
    print("\n[6/8] Writing openvoca.json ...")
    config: dict = {
        "version": VERSION,
        "port": 18099,
        "host": "127.0.0.1",
        "open_browser": True,
        "log_level": "warning",
    }
    (BUILD_DIR / "openvoca.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ------------------------------------------------------------------ #
    # 7. Write launcher scripts
    # ------------------------------------------------------------------ #
    print("\n[7/8] Writing launcher scripts ...")
    (BUILD_DIR / "start.py").write_text(_START_PY, encoding="utf-8")
    (BUILD_DIR / "openvoca.bat").write_text(_OPENVOCA_BAT, encoding="utf-8")

    # ------------------------------------------------------------------ #
    # 7b. Verify bundled imports (fail-fast before ZIP)
    # ------------------------------------------------------------------ #
    print("\n  [verify] ")
    _verify_bundle(BUILD_DIR)

    # ------------------------------------------------------------------ #
    # 8. Zip
    # ------------------------------------------------------------------ #
    zip_path = DIST_DIR / ZIP_NAME
    print(f"\n[8/8] Creating {zip_path.name} ...")
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in BUILD_DIR.rglob("*"):
            if f.is_file():
                arc_name = Path("openvoca") / f.relative_to(BUILD_DIR)
                zf.write(f, arc_name)
                file_count += 1

    mb = zip_path.stat().st_size / 1_048_576
    print(f"\n✅  Done: {zip_path}  ({mb:.1f} MB, {file_count:,} files)")
    print(
        "\nTo test: extract the ZIP, double-click openvoca.bat, "
        "and wait for the browser to open.\n"
    )


if __name__ == "__main__":
    main()
