# Nutrient DWS integration

Nutrient DWS is the core document operation in VeriFact Intake. The adapter
uploads each PDF to the Build API and requests `json-content` with key-value
pair extraction enabled. Provider responses are retained behind the extraction
port for traceability but are not treated as ontology authority.

## Configure real extraction

Create a local `.env` file:

```dotenv
VERIFACT_EXTRACTION_PROVIDER=nutrient
NUTRIENT_API_KEY=replace-with-your-local-key
NUTRIENT_API_BASE_URL=https://api.nutrient.io
NUTRIENT_LIVE_MODE=true
NUTRIENT_CACHE_DIR=./data/runtime/nutrient-cache
NUTRIENT_MAX_LIVE_CALLS=3
NUTRIENT_ESTIMATED_CREDITS_PER_CALL=3
NUTRIENT_MAX_ESTIMATED_CREDITS=9
```

Then start the application normally or with Docker Compose. Do not commit the
file. The repository's public-safety scan rejects common credential literals,
private endpoints, and private-key material.

## Credit safety

The adapter computes a cache identity from the PDF SHA-256 and the versioned
Build API instructions. A successful live response is stored in a local,
Git-ignored cache. Reprocessing the same file with the same instruction version
returns `nutrient-dws-cache` and sends no vendor request.

Network access is fail-closed:

- `NUTRIENT_LIVE_MODE=false` permits cache replay but rejects a cache miss;
- the default process budget permits three live calls and approximately nine credits;
- HTTP 402 fails immediately and is never retried by the adapter;
- `NUTRIENT_CACHE_REFRESH=true` deliberately bypasses existing entries and therefore
  must only be used for an approved final validation;
- deleting or changing a source PDF creates a new cache identity.

The budget is intentionally process-local. Restarting the application resets it,
so a restart is not approval to repeat billable calls. The final demo procedure
uses one three-document live run, preserves the resulting cache, then returns
`NUTRIENT_LIVE_MODE` to `false`.

## Offline replay

The checked-in fixture responses mirror the `ExtractedDocument` port rather
than bypassing the application. They exist so reviewers can reproduce the
entire semantic, review, persistence, export, and audit behavior without a
vendor account.

The browser always labels the active mode as `LIVE DWS`, `DWS CACHE`, or
`FIXTURE`; a cached or fixture run is never presented as a fresh vendor call.

## Trust boundary

DWS extraction answers: *what text and structure are present in this file?*
The VeriFact policy answers: *which competing statement, if any, is eligible to
become an effective ontology fact?* Those are intentionally separate decisions.
