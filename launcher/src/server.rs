use std::path::Path;
use std::process::{Child, Command, Stdio};

/// Manages the uvicorn backend as a child process.
pub struct BackendProcess {
    child: Child,
}

impl BackendProcess {
    /// Spawn the uvicorn backend server.
    pub fn spawn(
        backend_dir: &Path,
        host: &str,
        port: u16,
        data_dir: &Path,
    ) -> Result<Self, std::io::Error> {
        let python = if cfg!(windows) {
            backend_dir.join(".venv/Scripts/python.exe")
        } else {
            backend_dir.join(".venv/bin/python3")
        };

        log::info!("Spawning backend: {} -m uvicorn …", python.display());

        let child = Command::new(&python)
            .args([
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                host,
                "--port",
                &port.to_string(),
            ])
            .current_dir(backend_dir)
            .env("OPENVOCA_DATA_DIR", data_dir.as_os_str())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;

        log::info!("Backend started (pid {})", child.id());
        Ok(Self { child })
    }

    /// Check whether the child process is still alive.
    pub fn is_running(&mut self) -> bool {
        matches!(self.child.try_wait(), Ok(None))
    }

    /// Kill the child process and wait for it to exit.
    pub fn shutdown(&mut self) {
        log::info!("Shutting down backend…");
        let _ = self.child.kill();
        let _ = self.child.wait();
        log::info!("Backend stopped.");
    }
}

impl Drop for BackendProcess {
    fn drop(&mut self) {
        self.shutdown();
    }
}
