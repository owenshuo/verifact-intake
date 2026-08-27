# Nutrient DWS challenge compliance

| Requirement | VeriFact evidence | Status |
|---|---|---|
| Meaningful DWS API/SDK use | Build API `json-content` is the only production adapter; typed assertion values and exact quotes are derived from its blocks | Implemented and validated against the live response shape |
| Core document operation | All semantic assertions require content produced through `DocumentExtractor` | Implemented and tested |
| Inspectable project | Public-safe PDFs, runtime profile, isolated golden benchmark, architecture, tests, and demo guide | Complete |
| Reproducible code | Docker Compose and fixture replay use the same downstream pipeline | Complete; Linux container smoke test passes in GitHub Actions |
| Project description | Full Devpost draft and one-line DWS role | Complete locally |
| Submission images | Hero, review inbox, resolved facts, and audit proof screenshots | Complete from a verified Fixture rehearsal |
| Demo video | Timed 2:40 walkthrough covering problem, DWS, four reviews, and proof | [Published publicly on YouTube](https://youtu.be/4BP6WnA3pnA) |
| Source access | New repository has clean history and public-safety gate | Public at `owenshuo/verifact-intake`; CI passes |
| Final submission | Public Devpost project, repository, video, backup video, and thumbnail | Submitted and verified on August 27, 2026 |

The runtime assertion profile contains evidence patterns, types, and source
authority but no expected values or quotes. Golden expected results are isolated
to tests, so fixture replay cannot inject prewritten ontology facts.

## Credit-safety status

- Live DWS response mapping was verified against the account's real payload shape.
- Unlimited event credits are active on the official hackathon campaign account.
- The controlled live path has been exercised, and validated DWS responses are
  preserved in the content-addressed local cache for replay without repeat calls.
- Content-addressed caching, explicit live enablement, a three-call/nine-credit default
  process budget, and non-retrying HTTP 402 handling are implemented and tested.
- The UI identifies fresh Live DWS, DWS cache replay, and fixture replay separately.

## Post-submission enhancements

- The public demo now includes a 30-case deterministic trust benchmark.
- A downstream agent gate demonstrates fail-closed behavior before review and emits
  an evidence-qualified operation contract only after every required fact is promoted.
