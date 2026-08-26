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

## Development status

The project is under active hackathon development. The first checked-in slice
defines the domain contract and the real Nutrient DWS adapter boundary. A
public-safe synthetic document pack and the review UI follow next.

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

## License

Apache-2.0.

