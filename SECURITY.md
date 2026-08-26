# Security policy

VeriFact Intake is a hackathon demonstration built entirely from synthetic
documents. Do not upload confidential or regulated material to a public demo.

## Secrets

- Put local credentials in `.env` or `.secrets/`; both are ignored by Git.
- Use environment variables or a secret manager in deployed environments.
- Never include credentials in fixture responses, logs, screenshots, or issues.
- Run `python scripts/scan_public_safety.py` before publishing.

## Reporting

Please report a suspected vulnerability privately to the repository owner. Do
not include live credentials or confidential documents in the report.
