# Demo video script

Target length: 2 minutes 40 seconds. Use a 1920×1080 capture and keep the
browser zoom at 100%.

## 0:00–0:18 — Problem

Show the hero and the three document cards.

> Document AI can extract a statement, but it cannot silently decide that the
> statement is business truth. These three documents deliberately disagree on
> an API method, an approval rule, and evidence retention.

## 0:18–0:38 — Nutrient DWS

Open one synthetic PDF, then return to the pipeline panel.

> Nutrient DWS performs the core document operation, turning each PDF into
> structured JSON content. VeriFact derives typed values from those blocks and
> keeps the page, exact quote, and artifact hash as evidence rather than treating
> parser output as authority.

Show the `LIVE DWS` extraction-provider badge. The final recording must capture
one budgeted `nutrient-dws-live` run, not represent cache or fixture replay as a
fresh vendor call.

## 0:38–1:00 — Intake

Choose **Run trusted intake** and scroll to the workspace.

> Twelve assertions were compiled. Five safe, high-authority claims became
> effective facts. Three conflicts plus one business confirmation remain in the
> review queue. Assertion is deliberately not the same thing as fact.

## 1:00–1:45 — Review

Resolve the method conflict with `POST`, confirm `Network Operations` as the
business owner, choose `2` approvals, and select `180` retention days.

> The reviewer sees every candidate beside its authority, extraction
> confidence, document, and direct quote. Choosing one appends an approval for
> that assertion and rejections for its incompatible competitors. Nothing is
> overwritten. The queue reaches zero and nine evidence-linked facts remain.

## 1:45–2:15 — Proof

Show the growing fact list and audit events. Export the ontology JSON.

> Each promoted fact carries the assertion and evidence that justify it. The
> append-only event ledger is hash chained, so changing prior history breaks
> verification. The completed run contains seventeen replayable events. The
> result is portable ontology data, not just a chat answer.

## 2:15–2:40 — Close

Return to the hero.

> Nutrient answers what is in the document. VeriFact answers what is allowed to
> become truth. Together they turn conflicting business material into trusted,
> reviewable operational knowledge.
