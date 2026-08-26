# Nutrient DWS challenge compliance

| Requirement | VeriFact evidence | Status |
|---|---|---|
| Meaningful DWS API/SDK use | Build API `json-content` extraction is the only production document adapter | Implemented and validated against the live response shape |
| Core document operation | All semantic assertions require content produced through `DocumentExtractor` | Implemented and tested |
| Inspectable project | Public-safe PDFs, golden assertions, architecture, tests, and demo guide | Complete |
| Reproducible code | Docker Compose and fixture replay use the same downstream pipeline | Complete; Linux container smoke test passes in GitHub Actions |
| Project description | Full Devpost draft and one-line DWS role | Complete locally |
| Demo video | Timed 2:40 script covering problem, DWS, intake, review, proof | Script complete; recording pending |
| Source access | New repository has clean history and public-safety gate | Public at `owenshuo/verifact-intake`; CI passes |
| Final submission | Draft exists on Devpost | External form completion pending |

## Credit-safety status

- Live DWS response mapping was verified against the account's real payload shape.
- The initial free quota was effectively exhausted during integration and
  response-shape diagnosis (two credits remain, below the next operation cost).
- A request for 500 event credits has been sent to the official Nutrient contact.
- Content-addressed caching, explicit live enablement, a three-call/nine-credit default
  process budget, and non-retrying HTTP 402 handling are implemented and tested.
- The UI identifies fresh Live DWS, DWS cache replay, and fixture replay separately.

## Submission blockers

1. Receive the requested event-credit top-up and run one budgeted three-document live regression.
2. Preserve the validated responses, disable Live mode, and rerun the offline quality gate.
3. Record and upload the final 2–4 minute video.
4. Add the repository and video links to Devpost, verify the rendered entry, and submit.
