# Architecture baseline

## Goal

Prove one complete and inspectable path from a business document to a trusted,
versioned ontology fact. The application is intentionally smaller than the
long-running ontology platform: it keeps the trust semantics and removes
infrastructure that does not improve this demo.

![VeriFact Intake trust architecture](assets/verifact-trust-architecture.svg)

## Components

1. **Web/API** — upload synthetic PDFs, run intake, review uncertain claims,
   inspect evidence, and export results.
2. **Application service** — loads a versioned assertion profile and coordinates
   extraction, value derivation, validation, review, and promotion without
   depending on a specific document vendor.
3. **Nutrient DWS adapter** — performs a meaningful core extraction operation
   and preserves the provider response needed for traceability.
4. **Deterministic trust kernel** — fingerprints evidence, finds incompatible
   values, applies acceptance policy, and appends review decisions.
5. **SQLite repository** — durable local demo state. It is authoritative for
   the demo; no graph database is required.
6. **Trust benchmark** — deterministic evidence variations compare an unsafe
   confidence-only selector with the production trust and promotion policies.
7. **Downstream agent gate** — refuses to issue an operation contract until all
   required facts have passed their promotion gates.

SQLite stores a current run projection for fast reads and separate append-only
tables for review decisions and audit events. Database triggers reject updates
or deletes against those evidence tables. Effective facts are unique by run,
fact key, and version.

## Invariants

- A `SourceArtifact` is immutable and content-addressed.
- An `Assertion` is a claim with evidence, not a fact.
- Conflicting assertions cannot be promoted automatically.
- Review decisions are append-only and target an assertion fingerprint.
- An approved review is necessary but not sufficient for promotion when a
  policy gate still fails.
- Every `EffectiveFact` names the assertions and evidence that justify it.
- Vendor responses are retained only in public-safe demo storage and are never
  treated as the authority of record.
- Runtime profiles declare source metadata, evidence patterns, value types, and
  authority; they do not contain expected values or prewritten evidence quotes.
- The golden expected-run document is a test oracle and is never loaded by the
  runtime API or application service.

## Dependency direction

```text
api -> application -> domain
                    -> ports
adapters ----------> ports + domain
```

The domain never imports FastAPI, HTTP clients, Nutrient SDKs, databases, or an
LLM provider.

## Runtime path

```text
Browser
  -> FastAPI
     -> IntakeService
        -> DocumentExtractor port -> fixture or Nutrient DWS adapter
        -> AssertionCompiler       -> pattern match + typed value from evidence
        -> TrustPolicy             -> accepted / review_required / conflicted
        -> PromotionPolicy         -> EffectiveFact or unresolved
        -> SQLiteRunRepository     -> projection + append-only proof records
     -> AgentExecutionGate         -> blocked or evidence-qualified contract
```

The fixture mode is not a second implementation. It replays checked-in
extraction responses through the same compiler, policy, repository, API, and UI
used by real DWS mode.

## Deliberately omitted from the hackathon slice

- Neo4j projection
- Temporal orchestration
- multi-tenant identity
- generic ontology DSL
- production-scale distributed queues

These are useful platform capabilities, but they do not strengthen the
Nutrient judging story within the available build window.
