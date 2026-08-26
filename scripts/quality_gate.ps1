$ErrorActionPreference = "Stop"

& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m ruff check .
& .\.venv\Scripts\python.exe -m mypy src tests scripts
& .\.venv\Scripts\python.exe scripts\scan_public_safety.py
& .\.venv\Scripts\python.exe scripts\validate_demo.py
