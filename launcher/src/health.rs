use std::thread;
use std::time::{Duration, Instant};

const POLL_INTERVAL: Duration = Duration::from_millis(300);

/// Poll `url` until a 2xx response arrives or `timeout` elapses.
pub fn wait_for_ready(url: &str, timeout: Duration) -> bool {
    let start = Instant::now();

    while start.elapsed() < timeout {
        if ureq::get(url).call().is_ok() {
            log::info!("Backend ready at {url}");
            return true;
        }
        thread::sleep(POLL_INTERVAL);
    }

    log::error!("Backend did not respond within {}s", timeout.as_secs());
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unreachable_url_returns_false() {
        // Port 19999 should have nothing listening.
        let ok = wait_for_ready("http://127.0.0.1:19999/nope", Duration::from_millis(600));
        assert!(!ok);
    }
}
