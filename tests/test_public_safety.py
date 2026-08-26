from pathlib import Path

from scripts.scan_public_safety import scan


def test_public_safety_scanner_detects_private_endpoints_and_secrets(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe.txt"
    private_endpoint = "http://" + ".".join(("10", "9", "8", "7")) + ":8080"
    secret_value = "real-" + "looking-secret"
    unsafe.write_text(
        f'endpoint = "{private_endpoint}"\napi_key = "{secret_value}"\n',
        encoding="utf-8",
    )

    findings = scan(tmp_path)

    assert {finding.rule for finding in findings} == {"private-ipv4", "credential-literal"}


def test_repository_is_public_safe() -> None:
    root = Path(__file__).resolve().parents[1]
    assert scan(root) == ()
