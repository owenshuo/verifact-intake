# Demo video script — v2

Target length: about 2 minutes 50 seconds. The final video is 1920×1080 with
synthetic English narration and burned-in English subtitles. Every provider
badge shown in the recording must match the actual run mode.

## 0:00–0:17 — Evidence before action

Show the hero after one fresh Nutrient DWS run. Keep the `LIVE DWS` badge and
the four-stage trust pipeline visible.

> Can an operational agent act on a sentence just because a document parser
> extracted it with high confidence? VeriFact says no. It turns documents into
> operational facts only after evidence, authority, conflict, and promotion
> gates have all agreed.

## 0:17–0:38 — Three sources, three disagreements

Scroll from the three source cards into the trust-boundary section.

> These three public synthetic documents deliberately disagree about the HTTP
> method, approval count, and evidence-retention period. Nutrient DWS converts
> each PDF into structured content. VeriFact keeps every derived value attached
> to its page, exact quote, artifact hash, and source authority.

## 0:38–0:59 — Measured trust difference

Show all four benchmark cards and the result sentence.

> The trust boundary is measured, not merely claimed. Across thirty
> deterministic evidence variations, a confidence-only selector makes ninety
> unreviewed conflict choices and picks the wrong value sixty times. VeriFact
> detects all ninety conflicts and performs zero unsafe automatic promotions.

## 0:59–1:19 — Intake and fail-closed agent gate

Show the five run counters, decision inbox, effective facts, and then the
blocked downstream Agent gate.

> The live run compiles twelve assertions. Five safe, high-authority claims are
> promoted automatically. Three conflicts and one ownership confirmation remain
> open. The downstream agent receives no operation contract, because four
> required ontology facts have not passed their promotion gates.

## 1:19–1:42 — Evidence-based review

Show the method decision, ownership confirmation, approval count, and retention
decision in sequence. Use the four real post-click states rather than a static
overview.

> A reviewer compares candidate values beside authority, confidence, document,
> and direct quote. We choose POST from the API contract, confirm Network
> Operations as owner, require two approvals, and retain evidence for one
> hundred eighty days. Decisions are appended; incompatible claims are rejected,
> never overwritten.

## 1:42–2:22 — From BLOCKED to READY

Show the incremental review state, the cleared queue, nine promoted facts, and
the complete READY contract.

> The review is visibly incremental. Each accepted claim reduces the open queue,
> adds a versioned fact, and leaves the remaining uncertainty blocked. There is
> no hidden bulk promotion and no mutable status field pretending that a claim
> has always been true.

> The queue reaches zero and nine versioned, evidence-linked facts remain. Only
> now does the Agent gate release an evidence-qualified POST contract for the
> change endpoint. The contract includes the service owner, approval rule,
> retention period, eight fact versions, and their supporting assertion IDs—not
> raw extracted guesses.

## 2:22–2:39 — Replayable proof

Hold on the READY contract and append-only audit ledger.

> Every promotion and review is recorded in an append-only, hash-chained ledger.
> Changing prior history breaks verification. The ontology export can therefore
> be replayed and audited as operational knowledge, rather than trusted as a
> one-time chat answer.

## 2:39–2:50 — Close

Return to the hero and finish on the trust invariant.

> Nutrient answers what the documents contain. VeriFact decides what is allowed
> to become truth—and what an Agent is finally allowed to do.
