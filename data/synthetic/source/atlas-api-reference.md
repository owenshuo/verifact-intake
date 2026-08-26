# Atlas Change Service API Reference

Version: 2.1
Document authority: Product API specification
Effective: 2026-07-15

## Service identity

- Service name: Atlas Change Service
- Base path: `/change-api`
- API version: `v2`

## Create change

The create-change operation uses the `POST` method.

The create-change relative path is `/v2/changes`.

- Header `Idempotency-Key` is required.
- Synchronous validation timeout is 30 seconds.
- A successful request returns HTTP 202.

## Get change

`GET /v2/changes/{changeId}` returns the latest workflow state.

Possible states are `DRAFT`, `PENDING_APPROVAL`, `SCHEDULED`, `RUNNING`,
`SUCCEEDED`, and `FAILED`.
