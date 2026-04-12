use std::path::Path;

use serde::Deserialize;

/// Runtime configuration loaded from `openvoca.json`.
#[derive(Debug, Deserialize, PartialEq, Eq)]
pub struct Config {
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_open_browser")]
    pub open_browser: bool,
    #[serde(default = "default_log_level")]
    pub log_level: String,
}

fn default_port() -> u16 {
    18099
}
fn default_host() -> String {
    "127.0.0.1".to_string()
}
fn default_open_browser() -> bool {
    true
}
fn default_log_level() -> String {
    "info".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            port: default_port(),
            host: default_host(),
            open_browser: default_open_browser(),
            log_level: default_log_level(),
        }
    }
}

/// Load config from the given path. Returns defaults on missing/invalid file.
pub fn load(path: &Path) -> Config {
    if let Ok(content) = std::fs::read_to_string(path) {
        serde_json::from_str(&content).unwrap_or_else(|e| {
            log::warn!("Invalid config {}: {e}. Using defaults.", path.display());
            Config::default()
        })
    } else {
        log::info!("No config at {}. Using defaults.", path.display());
        Config::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_values() {
        let c = Config::default();
        assert_eq!(c.port, 18099);
        assert_eq!(c.host, "127.0.0.1");
        assert!(c.open_browser);
        assert_eq!(c.log_level, "info");
    }

    #[test]
    fn parse_full_json() {
        let json = r#"{
            "port": 8080,
            "host": "0.0.0.0",
            "open_browser": false,
            "log_level": "debug"
        }"#;
        let c: Config = serde_json::from_str(json).unwrap();
        assert_eq!(c.port, 8080);
        assert_eq!(c.host, "0.0.0.0");
        assert!(!c.open_browser);
        assert_eq!(c.log_level, "debug");
    }

    #[test]
    fn parse_partial_json_fills_defaults() {
        let json = r#"{"port": 9000}"#;
        let c: Config = serde_json::from_str(json).unwrap();
        assert_eq!(c.port, 9000);
        assert_eq!(c.host, "127.0.0.1");
        assert!(c.open_browser);
        assert_eq!(c.log_level, "info");
    }

    #[test]
    fn parse_empty_object_uses_defaults() {
        let json = "{}";
        let c: Config = serde_json::from_str(json).unwrap();
        assert_eq!(c, Config::default());
    }

    #[test]
    fn missing_file_returns_default() {
        let c = load(Path::new("does_not_exist_42.json"));
        assert_eq!(c, Config::default());
    }

    #[test]
    fn invalid_json_returns_default() {
        let dir = std::env::temp_dir().join("openvoca_test_bad_config.json");
        std::fs::write(&dir, "NOT JSON").unwrap();
        let c = load(&dir);
        assert_eq!(c, Config::default());
        std::fs::remove_file(&dir).ok();
    }

    #[test]
    fn valid_file_round_trip() {
        let dir = std::env::temp_dir().join("openvoca_test_good_config.json");
        std::fs::write(&dir, r#"{"port":3000,"open_browser":false}"#).unwrap();
        let c = load(&dir);
        assert_eq!(c.port, 3000);
        assert!(!c.open_browser);
        assert_eq!(c.host, "127.0.0.1");
        std::fs::remove_file(&dir).ok();
    }
}
