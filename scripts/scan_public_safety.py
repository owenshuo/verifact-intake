from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv"}
SKIP_SUFFIXES = {".db", ".gif", ".ico", ".jpeg", ".jpg", ".pdf", ".png", ".pyc"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str


RULES = {
    "private-ipv4": re.compile(
        r"(?<![\d.])(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\d.])"
    ),
    "private-key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "credential-literal": re.compile(
        r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'$<{\s][^'\"]{7,}['\"]"
    ),
}


def iter_public_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES or path.name == ".env":
            continue
        yield path


def scan(root: Path) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for path in iter_public_text_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            if "test-key" in line or "example-token" in line:
                continue
            for name, pattern in RULES.items():
                if pattern.search(line):
                    findings.append(Finding(path.relative_to(root), number, name))
    return tuple(findings)


def main() -> int:
    findings = scan(ROOT)
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.rule}")
        return 1
    print("Public-safety scan passed: no private endpoints or credential literals found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
