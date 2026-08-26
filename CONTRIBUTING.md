# Contributing

Contributions should preserve the central invariant: an assertion is not an
effective fact.

Before opening a change, run:

```bash
python -m pip install -e ".[dev]"
sh scripts/quality_gate.sh
```

New extraction providers implement the `DocumentExtractor` port. New semantic
rules must name a source quote and pass the evidence compiler. Promotion or
review changes need tests for conflicts, stale fingerprints, and audit replay.
