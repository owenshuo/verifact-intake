# Synthetic Atlas document pack

Atlas Change Service is a fictional product created for the VeriFact Intake
demo. No company documentation, customer data, real endpoints, credentials, or
proprietary test material is present in this directory.

The pack intentionally contains realistic disagreements:

- the API reference defines `POST /v2/changes`, while an older operations guide
  incorrectly says `PUT /v2/changes`;
- the quality policy requires two approvals for high-risk changes, while the
  older guide says one;
- the current retention policy is 180 days, while the older guide says 90.

These conflicts demonstrate why extracted assertions cannot automatically
become trusted facts.

The pack deliberately separates runtime configuration from expected results:

- `profiles/atlas-change-service-v1.json` declares sources, semantic fields,
  extraction patterns, value types, confidence ceilings, and authority scores;
  it contains no expected values or prewritten evidence quotes;
- `golden/expected-run.json` is a regression oracle loaded only by tests and the
  validation script;
- `fixtures/*.json` replay normalized extraction blocks through the same
  compiler used by Nutrient DWS live and cache modes.

To onboard another document set, add its PDFs and a versioned profile. The
trust, review, promotion, persistence, export, and audit components do not need
product-specific forks.

Run the generator from the repository root:

```powershell
python scripts/generate_synthetic_pdfs.py
```

The three generated PDFs are written to `output/pdf/`.
