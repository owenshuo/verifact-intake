# Devpost submission draft

## Project name

VeriFact Intake

## Elevator pitch

Prevents agents from silently choosing between conflicting API references,
runbooks, and policies by turning DWS evidence into reviewed, versioned ontology
facts.

## Inspiration

Document AI is good at finding text, but extraction confidence is not the same
as business truth. In our benchmark, an API reference says `POST` while an old
runbook says `PUT`; a quality policy requires two approvals while the runbook
says one; and retention is either 180 or 90 days depending on the document.
Most pipelines retrieve both values or silently select one, leaving operators
unable to explain why a downstream agent acted on a particular statement.

VeriFact Intake adds a trust boundary between document extraction and ontology
truth.

## What it does

VeriFact processes three deliberately conflicting business documents. Nutrient
DWS produces structured evidence blocks. A versioned runtime profile identifies
semantic fields and source authority but contains no expected values or quotes;
the compiler derives each typed value and exact quote from DWS output. VeriFact
then applies deterministic authority and conflict rules.
Safe claims are promoted automatically. Conflicting or lower-authority claims
enter a human decision inbox where reviewers compare values, source authority,
confidence, and exact quotes.

Every decision is appended rather than overwritten. Every effective fact is
versioned and names the assertions that justify it. The final ontology export
includes page-level evidence and a verifiable hash-chained audit head.

A checked-in 30-case benchmark measures the trust boundary rather than merely
describing it. A confidence-only selector makes 90 unreviewed conflict choices
and selects the wrong value 60 times. VeriFact detects all 90 expected conflicts,
automatically promotes none of them, and reaches 100% expected-fact accuracy after
gated review. A downstream agent gate then refuses to issue an operation contract
until every required fact is promoted.

## How we built it

- FastAPI provides the intake, review, run history, and ontology export API.
- Nutrient DWS Build API performs the core PDF-to-structured-content operation.
- Runtime assertion profiles declare patterns, types, and source authority—not
  the values that the demo is expected to produce.
- A provider-neutral extraction port supports both live DWS and public fixture replay.
- Content-addressed response caching, an explicit live switch, and a per-process
  credit budget prevent development retries from becoming accidental billable calls.
- Pydantic models enforce immutable source, assertion, review, conflict, and fact contracts.
- Deterministic trust and promotion policies keep `Assertion != EffectiveFact`.
- SQLite stores the run projection and rejects mutation of review and audit records with triggers.
- A dependency-free browser UI makes the trust decisions inspectable.
- A deterministic benchmark reuses the production compiler, trust policy, and
  promotion policy across 30 evidence variations.
- A downstream agent gate converts eight versioned effective facts into an
  evidence-qualified operation contract and fails closed on missing or invalid facts.
- Docker Compose, CI, strict typing, tests, golden evidence, and a public-safety scanner make the demo reproducible.

## Meaningful use of Nutrient DWS

Nutrient DWS is the core document operation: it converts each source PDF into
structured JSON blocks with text and page location. The evidence compiler
matches declared semantic patterns against those blocks and derives the typed
value and exact quote. If DWS does not provide matching evidence, compilation
fails and no assertion is created. VeriFact then adds the authority, conflict,
review, promotion, provenance, and audit layers that decide whether extracted
content may become ontology truth.

## Challenges

The hardest design problem was preserving a clear boundary between parser
output, a candidate assertion, a human decision, and an effective fact. We also
separated runtime extraction profiles from golden expected results so the demo
cannot pass by feeding its answers into the compiler. Finally, we needed an
offline path judges could replay without disguising fixture data as a live
vendor call. Both providers therefore use the exact same extraction port, all
downstream code is shared, and the UI labels live, cached, and fixture runs.

## Accomplishments

- A complete source-to-truth loop rather than a document chat demo.
- Three intentional conflicts detected from twelve evidence-backed assertions.
- Four human decisions clear the review queue and produce nine effective facts.
- Append-only review records and a tamper-evident audit chain.
- Portable ontology export with source quote, page, block, and assertion provenance.
- Values derived from extracted blocks rather than copied from the golden test oracle.
- Public synthetic documents, an isolated golden expected-run benchmark, and
  one-command reproducibility.
- Quantified evidence that confidence-only selection is unsafe on unresolved conflicts.
- A visible blocked-to-ready agent contract transition driven only by reviewed facts.

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

## Why it can become a product

The first buyer is a platform, quality, or governance team preparing operational
knowledge for agents. Each new domain supplies documents plus a small, versioned
profile of semantic patterns and authority rules. The trust kernel, review
workflow, provenance model, and audit proof stay unchanged. That turns one demo
into a repeatable intake product for regulated and high-consequence operations.

## Built with

Nutrient DWS, Python, FastAPI, Pydantic, SQLite, HTTPX, Docker, Pytest, Ruff,
MyPy, HTML, CSS, and JavaScript.

## Submission media

- Public demo video: https://youtu.be/I6F505D6CLI
- Public source repository: https://github.com/owenshuo/verifact-intake
- Document AI versus VeriFact: `docs/assets/document-ai-vs-verifact.svg`
- Hero and trust boundary: `docs/assets/verifact-hero.png`
- Evidence comparison and decision inbox: `docs/assets/verifact-review-workspace.png`
- Cleared review queue and promoted facts: `docs/assets/verifact-resolved-proof.png`
- Verified append-only audit ledger: `docs/assets/verifact-audit-proof.png`
- Measured 30-case trust benchmark: `docs/assets/verifact-trust-benchmark.png`
- Evidence-qualified downstream agent contract: `docs/assets/verifact-agent-gate-ready.png`
- Trust benchmark methodology: `docs/BENCHMARK.md`
