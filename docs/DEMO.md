# Demo walkthrough

The complete walkthrough takes about two minutes.

## 1. Establish the problem

Open the three synthetic documents from the source cards. They intentionally
disagree on the HTTP method, approval count, and retention period. The
operations guide is older and less authoritative than the API reference and
quality policy.

## 2. Run trusted intake

Choose **Run trusted intake**. The application extracts three artifacts, derives
twelve typed values from matching evidence blocks, detects three conflicts, and
automatically promotes only five unambiguous high-authority facts.

The default fixture provider makes this result replayable. Nutrient mode first
checks the content-addressed response cache. Only an explicitly enabled Live DWS
run sends the PDFs through the JSON-content operation before the common trust
pipeline runs. The provider badge distinguishes all three modes.

## 3. Resolve uncertainty

The review inbox shows each candidate value beside its document, authority,
confidence, and direct quote. Select:

- `POST` from the API reference;
- `2` approvals from the quality policy;
- `180` retention days from the quality policy;
- `Network Operations` after business-owner confirmation.

Each choice appends approval and rejection decisions for that fact key. It does
not overwrite the source assertion. After all four decisions, the queue reaches
zero and the run contains nine effective facts.

## 4. Inspect proof

The effective-fact panel grows only after promotion succeeds. Export the
ontology to inspect its evidence locators. The audit panel shows the hash chain;
changing any prior event makes verification fail. The completed walkthrough
contains seventeen append-only audit events.

## Presenter line

> Nutrient DWS turns the source PDFs into structured content; VeriFact adds the
> trust boundary that prevents extracted text from silently becoming truth.
