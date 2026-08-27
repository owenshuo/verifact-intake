#!/usr/bin/env sh
set -eu

python -m pytest
python -m ruff check .
python -m mypy src tests scripts
python scripts/scan_public_safety.py
python scripts/validate_demo.py
python scripts/run_trust_benchmark.py
