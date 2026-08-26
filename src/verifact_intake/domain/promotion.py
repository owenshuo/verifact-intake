from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from verifact_intake.domain.models import (
    Assertion,
    AssertionStatus,
    EffectiveFact,
    ReviewDecision,
    ReviewOutcome,
)


@dataclass(frozen=True)
class PromotionResult:
    new_facts: tuple[EffectiveFact, ...]
    unresolved_fact_keys: tuple[str, ...]


class PromotionPolicy:
    """Promote only claims that satisfy deterministic trust and review gates."""

    def promote(
        self,
        assertions: Iterable[Assertion],
        reviews: Iterable[ReviewDecision],
        existing_facts: Iterable[EffectiveFact] = (),
    ) -> PromotionResult:
        grouped: dict[str, list[Assertion]] = defaultdict(list)
        assertion_list = list(assertions)
        for assertion in assertion_list:
            grouped[assertion.fact_key].append(assertion)

        latest_reviews = self._latest_valid_reviews(assertion_list, reviews)
        existing = list(existing_facts)
        new_facts: list[EffectiveFact] = []
        unresolved: list[str] = []

        for fact_key, candidates in grouped.items():
            selected = self._select(candidates, latest_reviews)
            if selected is None:
                unresolved.append(fact_key)
                continue
            winner, value, supporting_ids = selected
            prior = [fact for fact in (*existing, *new_facts) if fact.fact_key == fact_key]
            if prior and prior[-1].value == value:
                continue
            new_facts.append(
                EffectiveFact(
                    subject_id=winner.subject_id,
                    predicate=winner.predicate,
                    value=value,
                    assertion_ids=supporting_ids,
                    version=max((fact.version for fact in prior), default=0) + 1,
                )
            )

        return PromotionResult(
            new_facts=tuple(new_facts),
            unresolved_fact_keys=tuple(sorted(unresolved)),
        )

    @staticmethod
    def _latest_valid_reviews(
        assertions: list[Assertion], reviews: Iterable[ReviewDecision]
    ) -> dict[UUID, ReviewDecision]:
        by_id = {assertion.id: assertion for assertion in assertions}
        latest: dict[UUID, ReviewDecision] = {}
        for decision in sorted(reviews, key=lambda item: item.created_at):
            assertion = by_id.get(decision.assertion_id)
            if assertion is None or decision.assertion_fingerprint != assertion.fingerprint:
                continue
            latest[decision.assertion_id] = decision
        return latest

    @staticmethod
    def _approved_value(
        assertion: Assertion, decision: ReviewDecision | None
    ) -> Any | None:
        if decision is None or decision.outcome is ReviewOutcome.REJECT:
            return None
        if decision.outcome is ReviewOutcome.CORRECT:
            return decision.corrected_value
        return assertion.value

    def _select(
        self,
        candidates: list[Assertion],
        reviews: dict[UUID, ReviewDecision],
    ) -> tuple[Assertion, Any, tuple[UUID, ...]] | None:
        if any(candidate.status is AssertionStatus.CONFLICTED for candidate in candidates):
            decisions = [reviews.get(candidate.id) for candidate in candidates]
            if any(decision is None for decision in decisions):
                return None
            approved = [
                (candidate, self._approved_value(candidate, decision))
                for candidate, decision in zip(candidates, decisions, strict=True)
                if decision is not None and decision.outcome is not ReviewOutcome.REJECT
            ]
            if len(approved) != 1:
                return None
            winner, value = approved[0]
            return winner, value, (winner.id,)

        accepted = [
            candidate for candidate in candidates if candidate.status is AssertionStatus.ACCEPTED
        ]
        if accepted:
            winner = max(accepted, key=lambda item: (item.authority, item.confidence))
            return winner, winner.value, tuple(candidate.id for candidate in accepted)

        reviewed = [
            (candidate, self._approved_value(candidate, reviews.get(candidate.id)))
            for candidate in candidates
            if reviews.get(candidate.id) is not None
            and reviews[candidate.id].outcome is not ReviewOutcome.REJECT
        ]
        if len(reviewed) != 1:
            return None
        winner, value = reviewed[0]
        return winner, value, (winner.id,)
