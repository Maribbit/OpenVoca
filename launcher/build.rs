fn main() {
    let version = std::fs::read_to_string("../VERSION")
        .expect("Cannot read ../VERSION — run from the launcher/ directory")
        .trim()
        .to_string();
    println!("cargo:rustc-env=OPENVOCA_VERSION={version}");
    println!("cargo:rerun-if-changed=../VERSION");
}
