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

Run the generator from the repository root:

```powershell
python scripts/generate_synthetic_pdfs.py
```

The three generated PDFs are written to `output/pdf/`.
