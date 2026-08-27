from pathlib import Path

from verifact_intake.application.benchmark import run_synthetic_trust_benchmark

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = ROOT / "data" / "synthetic"


def test_trust_benchmark_quantifies_confidence_only_risk() -> None:
    report = run_synthetic_trust_benchmark(
        profile_path=SYNTHETIC / "profiles" / "atlas-change-service-v1.json",
        fixture_dir=SYNTHETIC / "fixtures",
        pdf_dir=ROOT / "output" / "pdf",
        golden_path=SYNTHETIC / "golden" / "expected-run.json",
    )

    assert report.cases == 30
    assert report.confidence_baseline.conflict_choices == 90
    assert report.confidence_baseline.unsafe_conflict_choices == 90
    assert report.confidence_baseline.wrong_conflict_values == 60
    assert report.confidence_baseline.wrong_conflict_value_rate == 2 / 3
    assert report.verifact.expected_conflicts == 90
    assert report.verifact.detected_conflicts == 90
    assert report.verifact.conflict_recall == 1
    assert report.verifact.unsafe_auto_promotions == 0
    assert report.verifact.final_fact_accuracy == 1
    assert report.verifact.evidence_coverage == 1
