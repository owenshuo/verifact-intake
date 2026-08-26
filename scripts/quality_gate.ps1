$ErrorActionPreference = "Stop"

& .\.venv\Scripts\python.exe -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m mypy src tests scripts
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe scripts\scan_public_safety.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe scripts\validate_demo.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
