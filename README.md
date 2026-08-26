# VeriFact Intake

VeriFact Intake turns messy business documents into evidence-linked ontology
facts. It combines deterministic document extraction, normalized assertions,
conflict detection, human review, and a replayable audit trail.

This repository is a new project for the DevNetwork API + Cloud + AI Hackathon
2026, targeting the **Nutrient DWS Challenge**. It is informed by prior work on
quality-operations ontologies, but contains only new, public-safe code and
synthetic data created for this event.

## The trust boundary

```text
Source document
    -> Nutrient DWS extraction
    -> evidence-linked assertions
    -> deterministic validation and conflict detection
    -> automatic acceptance or human review
    -> versioned effective facts
    -> exportable ontology + append-only audit trail
```

An extracted statement is never treated as truth merely because an AI or a
document parser produced it. Every effective fact must retain its source
evidence and promotion history.

## What works now

- Three generated, public-safe PDFs form a reproducible conflict benchmark.
- Fixture and Nutrient DWS extraction share one adapter contract.
- Twelve evidence-linked assertions are assessed by a deterministic trust policy.
- Conflicting and lower-authority claims enter a human review inbox.
- Review decisions are append-only and target immutable assertion fingerprints.
- Effective facts retain their source quote, page, artifact, and assertion IDs.
- A hash-chained audit ledger detects mutation and can be replayed.
- SQLite persists demo runs; the API exports a portable ontology JSON document.
- The browser demo, tests, CI, public-safety scan, and Docker startup are included.

The default mode is a fully replayable fixture run so judges can reproduce the
story without credentials. Set the extraction provider to `nutrient` to execute
the same intake against the real Nutrient DWS API.

## One-command demo

With Docker installed:

```bash
docker compose up --build
```

Open <http://localhost:8080>, choose **Run trusted intake**, compare the
conflicting claims, and select the normative evidence. The ontology and audit
export is available from the workspace header.

## Local setup

Prerequisites: Python 3.12+.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
.venv\Scripts\python -m uvicorn verifact_intake.api:app --reload
```

Copy `.env.example` to `.env` for local settings. Secrets belong in `.env` or
`.secrets/`; both are excluded from Git. Never commit a Nutrient or LLM key.

Useful project guides:

- [Demo walkthrough](docs/DEMO.md)
- [Nutrient DWS integration](docs/NUTRIENT_DWS.md)
- [Architecture and trust invariants](docs/ARCHITECTURE.md)
- [Security policy](SECURITY.md)

## License

Apache-2.0.
