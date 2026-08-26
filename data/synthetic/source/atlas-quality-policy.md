# Atlas Change Quality Policy

Policy version: 2026-Q3
Document authority: Quality governance policy
Effective: 2026-07-01

## Approval control

Every high-risk change requires two independent approvals before scheduling.
The requester cannot approve the same change.

## Evidence retention

Change plans, approvals, execution logs, and verification results must be
retained for 180 days after completion.

## Verification

A change can enter `SUCCEEDED` only after the post-change verification suite
passes. A failed verification moves the change to `FAILED` and requires an
incident reference.

## Audit

Approval and promotion decisions are append-only. A later correction creates a
new decision and never overwrites the original record.
