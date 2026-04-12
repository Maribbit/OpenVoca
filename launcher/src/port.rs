use std::net::TcpListener;

/// Find an available port, scanning downward from `start` to 1024.
pub fn find_available(start: u16) -> Option<u16> {
    (1024..=start)
        .rev()
        .find(|&port| TcpListener::bind(("127.0.0.1", port)).is_ok())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn returns_a_bindable_port() {
        let port = find_available(18099).expect("should find a port");
        assert!(port >= 1024);
        assert!(port <= 18099);
        // Confirm the returned port is actually free right now.
        TcpListener::bind(("127.0.0.1", port)).expect("port should be bindable");
    }

    #[test]
    fn skips_occupied_port() {
        // Occupy a port, then ask for it — should get a different one.
        let listener = TcpListener::bind(("127.0.0.1", 0)).unwrap();
        let occupied = listener.local_addr().unwrap().port();
        let found = find_available(occupied).expect("should find a port");
        // The occupied port should not be returned (it may return one below).
        assert_ne!(found, occupied);
    }
}
