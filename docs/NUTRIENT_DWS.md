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
```

Then start the application normally or with Docker Compose. Do not commit the
file. The repository's public-safety scan rejects common credential literals,
private endpoints, and private-key material.

## Offline replay

The checked-in fixture responses mirror the `ExtractedDocument` port rather
than bypassing the application. They exist so reviewers can reproduce the
entire semantic, review, persistence, export, and audit behavior without a
vendor account.

## Trust boundary

DWS extraction answers: *what text and structure are present in this file?*
The VeriFact policy answers: *which competing statement, if any, is eligible to
become an effective ontology fact?* Those are intentionally separate decisions.
