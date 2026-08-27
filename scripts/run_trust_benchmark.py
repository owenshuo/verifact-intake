from __future__ import annotations

from pathlib import Path

from verifact_intake.application.benchmark import run_synthetic_trust_benchmark

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ROOT / "data" / "synthetic"


def main() -> None:
    report = run_synthetic_trust_benchmark(
        profile_path=SYNTHETIC / "profiles" / "atlas-change-service-v1.json",
        fixture_dir=SYNTHETIC / "fixtures",
        pdf_dir=ROOT / "output" / "pdf",
        golden_path=SYNTHETIC / "golden" / "expected-run.json",
    )
    print(report.model_dump_json(by_alias=True, indent=2))


if __name__ == "__main__":
    main()
