from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from verifact_intake.domain.models import EffectiveFact, FrozenModel
from verifact_intake.domain.run import IntakeRun


class AgentGateStatus(StrEnum):
    BLOCKED = "blocked"
    READY = "ready"


class ContractEvidence(FrozenModel):
    fact_key: str
    version: int = Field(ge=1)
    assertion_ids: tuple[UUID, ...] = Field(min_length=1)


class TrustedOperationContract(FrozenModel):
    operation: str
    service_owner: str
    method: str
    path: str
    approval_required_count: int = Field(ge=1)
    evidence_retention_days: int = Field(ge=1)
    idempotency_key_required: bool
    post_change_verification_required: bool
    evidence: tuple[ContractEvidence, ...] = Field(min_length=1)


class AgentExecutionGate(FrozenModel):
    schema_name: str = Field(alias="schema")
    run_id: UUID
    status: AgentGateStatus
    reason: str
    missing_fact_keys: tuple[str, ...] = ()
    invalid_fact_keys: tuple[str, ...] = ()
    contract: TrustedOperationContract | None = None


SERVICE_BASE_PATH = "service:atlas-change::service.base_path"
SERVICE_OWNER = "service:atlas-change::business.owner"
HTTP_METHOD = "operation:create-change::http.method"
HTTP_RELATIVE_PATH = "operation:create-change::http.relative_path"
IDEMPOTENCY_REQUIRED = "operation:create-change::request.idempotency_key_required"
APPROVAL_COUNT = "workflow:high-risk-change::approval.required_count"
RETENTION_DAYS = "policy:change-evidence::retention.days"
VERIFICATION_REQUIRED = "workflow:change-execution::success.requires_verification"

REQUIRED_FACT_KEYS = (
    SERVICE_BASE_PATH,
    SERVICE_OWNER,
    HTTP_METHOD,
    HTTP_RELATIVE_PATH,
    IDEMPOTENCY_REQUIRED,
    APPROVAL_COUNT,
    RETENTION_DAYS,
    VERIFICATION_REQUIRED,
)


def build_agent_execution_gate(run: IntakeRun) -> AgentExecutionGate:
    facts = _latest_facts(run.facts)
    missing = tuple(key for key in REQUIRED_FACT_KEYS if key not in facts)
    if missing:
        return AgentExecutionGate(
            schema="verifact.agent-execution-gate/v1",
            run_id=run.id,
            status=AgentGateStatus.BLOCKED,
            reason=(
                f"Execution blocked: {len(missing)} required ontology facts have not passed "
                "their promotion gates."
            ),
            missing_fact_keys=missing,
        )

    values = {key: facts[key].value for key in REQUIRED_FACT_KEYS}
    invalid = tuple(
        key
        for key in REQUIRED_FACT_KEYS
        if not _is_valid_contract_value(key, values[key])
    )
    if invalid:
        return AgentExecutionGate(
            schema="verifact.agent-execution-gate/v1",
            run_id=run.id,
            status=AgentGateStatus.BLOCKED,
            reason="Execution blocked: promoted facts do not satisfy the operation contract types.",
            invalid_fact_keys=invalid,
        )

    base_path = _string_value(values[SERVICE_BASE_PATH]).rstrip("/")
    relative_path = _string_value(values[HTTP_RELATIVE_PATH])
    path = f"{base_path}/{relative_path.lstrip('/')}"
    evidence = tuple(
        ContractEvidence(
            fact_key=key,
            version=facts[key].version,
            assertion_ids=facts[key].assertion_ids,
        )
        for key in REQUIRED_FACT_KEYS
    )
    return AgentExecutionGate(
        schema="verifact.agent-execution-gate/v1",
        run_id=run.id,
        status=AgentGateStatus.READY,
        reason="All required ontology facts passed their promotion gates.",
        contract=TrustedOperationContract(
            operation="create-change",
            service_owner=_string_value(values[SERVICE_OWNER]),
            method=_string_value(values[HTTP_METHOD]),
            path=path,
            approval_required_count=_integer_value(values[APPROVAL_COUNT]),
            evidence_retention_days=_integer_value(values[RETENTION_DAYS]),
            idempotency_key_required=_boolean_value(values[IDEMPOTENCY_REQUIRED]),
            post_change_verification_required=_boolean_value(values[VERIFICATION_REQUIRED]),
            evidence=evidence,
        ),
    )


def _latest_facts(facts: tuple[EffectiveFact, ...]) -> dict[str, EffectiveFact]:
    latest: dict[str, EffectiveFact] = {}
    for fact in facts:
        previous = latest.get(fact.fact_key)
        if previous is None or fact.version > previous.version:
            latest[fact.fact_key] = fact
    return latest


def _is_valid_contract_value(fact_key: str, value: Any) -> bool:
    if fact_key in {SERVICE_BASE_PATH, HTTP_RELATIVE_PATH}:
        return isinstance(value, str) and value.startswith("/") and len(value) > 1
    if fact_key == SERVICE_OWNER:
        return isinstance(value, str) and bool(value.strip())
    if fact_key == HTTP_METHOD:
        return isinstance(value, str) and value in {
            "DELETE",
            "GET",
            "PATCH",
            "POST",
            "PUT",
        }
    if fact_key in {APPROVAL_COUNT, RETENTION_DAYS}:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 1
    return isinstance(value, bool)


def _string_value(value: Any) -> str:
    assert isinstance(value, str)
    return value


def _integer_value(value: Any) -> int:
    assert isinstance(value, int) and not isinstance(value, bool)
    return value


def _boolean_value(value: Any) -> bool:
    assert isinstance(value, bool)
    return value
