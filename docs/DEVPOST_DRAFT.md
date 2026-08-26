# Devpost submission draft

## Project name

VeriFact Intake

## Elevator pitch

Turns messy business documents into evidence-linked ontology facts with
deterministic extraction, conflict detection, human review, and replayable
audit trails.

## Inspiration

Document AI is good at finding text, but extraction confidence is not the same
as business truth. API references, operations guides, and governance policies
often disagree. Most pipelines silently select a value or place everything in
a search index, leaving operators unable to explain why a downstream system
believed a particular statement.

VeriFact Intake adds a trust boundary between document extraction and ontology
truth.

## What it does

VeriFact processes three deliberately conflicting business documents. It uses
Nutrient DWS to produce structured document content, compiles only claims that
retain direct evidence, and applies deterministic authority and conflict rules.
Safe claims are promoted automatically. Conflicting or lower-authority claims
enter a human decision inbox where reviewers compare values, source authority,
confidence, and exact quotes.

Every decision is appended rather than overwritten. Every effective fact is
versioned and names the assertions that justify it. The final ontology export
includes page-level evidence and a verifiable hash-chained audit head.

## How we built it

- FastAPI provides the intake, review, run history, and ontology export API.
- Nutrient DWS Build API performs the core PDF-to-structured-content operation.
- A provider-neutral extraction port supports both live DWS and public fixture replay.
- Content-addressed response caching, an explicit live switch, and a per-process
  credit budget prevent development retries from becoming accidental billable calls.
- Pydantic models enforce immutable source, assertion, review, conflict, and fact contracts.
- Deterministic trust and promotion policies keep `Assertion != EffectiveFact`.
- SQLite stores the run projection and rejects mutation of review and audit records with triggers.
- A dependency-free browser UI makes the trust decisions inspectable.
- Docker Compose, CI, strict typing, tests, golden evidence, and a public-safety scanner make the demo reproducible.

## Meaningful use of Nutrient DWS

Nutrient DWS is the core document operation: it converts each source PDF into
structured JSON content used by the evidence compiler. VeriFact then adds the
semantic authority, conflict, review, promotion, provenance, and audit layers
that decide whether extracted content may become ontology truth.

## Challenges

The hardest design problem was preserving a clear boundary between parser
output, a candidate assertion, a human decision, and an effective fact. We also
needed an offline path judges could replay without disguising fixture data as a
live vendor call. Both providers therefore use the exact same extraction port,
all downstream code is shared, and the UI labels live, cached, and fixture runs
separately.

## Accomplishments

- A complete source-to-truth loop rather than a document chat demo.
- Three intentional conflicts detected from twelve evidence-backed assertions.
- Four human decisions clear the review queue and produce nine effective facts.
- Append-only review records and a tamper-evident audit chain.
- Portable ontology export with source quote, page, block, and assertion provenance.
- Public synthetic documents, golden assertions, and one-command reproducibility.

## What we learned

Document extraction and semantic truth are complementary capabilities. A
better parser improves evidence quality, but authority, conflict resolution,
and promotion remain explicit domain decisions. Designing those boundaries
first makes an AI-assisted workflow safer and easier to audit.

## What's next

The next step is replacing the rule pack with a constrained agent that proposes
new semantic mappings while the same evidence, policy, and human-review gates
remain mandatory. Additional document types can then join through versioned
module profiles rather than product-specific forks.

## Built with

Nutrient DWS, Python, FastAPI, Pydantic, SQLite, HTTPX, Docker, Pytest, Ruff,
MyPy, HTML, CSS, and JavaScript.

## Submission media

- Hero and trust boundary: `docs/assets/verifact-hero.png`
- Evidence comparison and decision inbox: `docs/assets/verifact-review-workspace.png`
- Cleared review queue and promoted facts: `docs/assets/verifact-resolved-proof.png`
- Verified append-only audit ledger: `docs/assets/verifact-audit-proof.png`
