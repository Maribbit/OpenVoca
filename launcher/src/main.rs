// Hides the console window in release builds on Windows.
// NOTE: Without a tray icon this means the only way to quit is Task Manager.
// Enable this AFTER implementing the tray-icon menu (Phase C-3).
// #![cfg_attr(
//     all(not(debug_assertions), target_os = "windows"),
//     windows_subsystem = "windows"
// )]

mod config;
mod health;
mod port;
mod server;

use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

const VERSION: &str = env!("OPENVOCA_VERSION");
const HEALTH_TIMEOUT: Duration = Duration::from_secs(15);

fn main() {
    let base_dir = resolve_base_dir();
    let data_dir = base_dir.join("data");
    std::fs::create_dir_all(&data_dir).expect("Failed to create data directory");

    init_logging(&data_dir);
    log::info!("OpenVoca Launcher v{VERSION}");

    let cfg = config::load(&base_dir.join("openvoca.json"));
    log::info!(
        "Config: host={} port={} open_browser={}",
        cfg.host,
        cfg.port,
        cfg.open_browser
    );

    // Find an available port (scan downward from the configured value).
    let port = port::find_available(cfg.port).unwrap_or_else(|| {
        log::error!("No available port (scanned down from {})", cfg.port);
        std::process::exit(1);
    });
    if port != cfg.port {
        log::info!("Port {} busy — using {} instead", cfg.port, port);
    }

    // Spawn the Python backend.
    let backend_dir = base_dir.join("backend");
    let mut backend = server::BackendProcess::spawn(&backend_dir, &cfg.host, port, &data_dir)
        .unwrap_or_else(|e| {
            log::error!("Failed to start backend: {e}");
            std::process::exit(1);
        });

    // Wait until the backend is ready to serve requests.
    let health_url = format!("http://{}:{}/api/provider", cfg.host, port);
    if !health::wait_for_ready(&health_url, HEALTH_TIMEOUT) {
        if !backend.is_running() {
            log::error!("Backend process exited unexpectedly");
        }
        backend.shutdown();
        std::process::exit(1);
    }

    // Open the app in the default browser.
    if cfg.open_browser {
        let url = format!("http://{}:{}", cfg.host, port);
        if let Err(e) = open::that(&url) {
            log::warn!("Failed to open browser: {e}");
        }
    }

    // Block until Ctrl+C.
    log::info!(
        "OpenVoca running on http://{}:{} — press Ctrl+C to stop",
        cfg.host,
        port
    );
    wait_for_shutdown();

    log::info!("Shutting down…");
    backend.shutdown();
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Resolve the directory that contains the launcher executable.
/// All relative paths (backend/, data/, openvoca.json) are resolved from here.
fn resolve_base_dir() -> std::path::PathBuf {
    std::env::current_exe()
        .expect("Cannot determine executable path")
        .parent()
        .expect("Executable has no parent directory")
        .to_path_buf()
}

/// Block the current thread until a Ctrl+C signal is received.
fn wait_for_shutdown() {
    let running = Arc::new(AtomicBool::new(true));
    let flag = running.clone();
    ctrlc::set_handler(move || flag.store(false, Ordering::Relaxed))
        .expect("Failed to set Ctrl+C handler");

    while running.load(Ordering::Relaxed) {
        std::thread::sleep(Duration::from_millis(200));
    }
}

/// Set up dual logging: console (stderr) + file (`data/openvoca.log`).
fn init_logging(data_dir: &Path) {
    use simplelog::{
        CombinedLogger, Config as LogConfig, LevelFilter, SharedLogger, SimpleLogger, WriteLogger,
    };

    let mut loggers: Vec<Box<dyn SharedLogger>> = Vec::new();

    // Console logger (output goes nowhere in a windowless release build — harmless).
    loggers.push(SimpleLogger::new(LevelFilter::Info, LogConfig::default()));

    // File logger.
    let log_path = data_dir.join("openvoca.log");
    if let Ok(file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_path)
    {
        loggers.push(WriteLogger::new(
            LevelFilter::Info,
            LogConfig::default(),
            file,
        ));
    }

    CombinedLogger::init(loggers).ok();
}
