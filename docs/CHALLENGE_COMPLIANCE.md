# Nutrient DWS challenge compliance

| Requirement | VeriFact evidence | Status |
|---|---|---|
| Meaningful DWS API/SDK use | Build API `json-content` extraction is the only production document adapter | Implemented; live key validation pending |
| Core document operation | All semantic assertions require content produced through `DocumentExtractor` | Implemented and tested |
| Inspectable project | Public-safe PDFs, golden assertions, architecture, tests, and demo guide | Complete |
| Reproducible code | Docker Compose and fixture replay use the same downstream pipeline | Complete; Linux image build pending |
| Project description | Full Devpost draft and one-line DWS role | Complete locally |
| Demo video | Timed 2:40 script covering problem, DWS, intake, review, proof | Script complete; recording pending |
| Source access | New repository has clean history and public-safety gate | Local complete; GitHub publish pending |
| Final submission | Draft exists on Devpost | External form completion pending |

## Submission blockers

1. Configure a Nutrient DWS API key locally and capture a successful live run.
2. Build and smoke-test the Docker image on a Linux/Docker host.
3. Publish `owenshuo/verifact-intake` after action-time approval.
4. Record the live-DWS demo and upload the final 2–4 minute video.
5. Replace the Devpost draft body, add repository/video links, and submit.
