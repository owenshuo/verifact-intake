# Nutrient DWS challenge compliance

| Requirement | VeriFact evidence | Status |
|---|---|---|
| Meaningful DWS API/SDK use | Build API `json-content` extraction is the only production document adapter | Implemented and validated against the live response shape |
| Core document operation | All semantic assertions require content produced through `DocumentExtractor` | Implemented and tested |
| Inspectable project | Public-safe PDFs, golden assertions, architecture, tests, and demo guide | Complete |
| Reproducible code | Docker Compose and fixture replay use the same downstream pipeline | Complete; Linux container smoke test passes in GitHub Actions |
| Project description | Full Devpost draft and one-line DWS role | Complete locally |
| Submission images | Hero, review inbox, resolved facts, and audit proof screenshots | Complete from a verified Fixture rehearsal |
| Demo video | Timed 2:40 walkthrough covering problem, DWS, four reviews, and proof | [Published publicly on YouTube](https://youtu.be/4BP6WnA3pnA) |
| Source access | New repository has clean history and public-safety gate | Public at `owenshuo/verifact-intake`; CI passes |
| Final submission | Draft exists on Devpost | External form completion pending |

## Credit-safety status

- Live DWS response mapping was verified against the account's real payload shape.
- Unlimited event credits are active on the official hackathon campaign account.
- The controlled live path has been exercised, and validated DWS responses are
  preserved in the content-addressed local cache for replay without repeat calls.
- Content-addressed caching, explicit live enablement, a three-call/nine-credit default
  process budget, and non-retrying HTTP 402 handling are implemented and tested.
- The UI identifies fresh Live DWS, DWS cache replay, and fixture replay separately.

## Submission blockers

1. Add the repository and video links to Devpost.
2. Verify the rendered entry and complete the final submission.
