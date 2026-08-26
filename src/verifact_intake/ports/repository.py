from __future__ import annotations

from typing import Protocol
from uuid import UUID

from verifact_intake.domain.run import IntakeRun


class RunRepository(Protocol):
    def save(self, run: IntakeRun) -> None: ...

    def get(self, run_id: UUID) -> IntakeRun | None: ...

    def list(self) -> tuple[IntakeRun, ...]: ...
